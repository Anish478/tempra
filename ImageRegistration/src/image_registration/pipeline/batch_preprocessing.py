# src/image_registration/pipeline/batch_preprocessing.py
"""
Batch preprocessing pipeline for processing all patients in a directory
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import json
import csv
from datetime import datetime
import concurrent.futures
from tqdm import tqdm
import SimpleITK as sitk

from .base_pipeline import BasePipeline, PipelineStep
from .comprehensive_pipeline import PreprocessingPipeline

class BatchPreprocessingPipeline(BasePipeline):
    """
    Batch processing pipeline for entire patient directories
    """
    
    def __init__(self,
                 registration_type: str = 'rigid',
                 standardization_method: str = 'nyul',
                 enable_segmentation: bool = True,
                 parallel_processing: bool = True,
                 max_workers: Optional[int] = None):
        
        super().__init__(
            name="BatchPreprocessingPipeline",
            description="Batch preprocessing for all patients in directory"
        )
        
        self.registration_type = registration_type
        self.standardization_method = standardization_method
        self.enable_segmentation = enable_segmentation
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers or os.cpu_count()
        
        # Setup steps
        self.add_step(PatientDiscoveryStep())
        self.add_step(BatchStandardizationStep(method=standardization_method))
        self.add_step(BatchProcessingStep(
            registration_type=registration_type,
            enable_segmentation=enable_segmentation,
            parallel=parallel_processing,
            max_workers=self.max_workers
        ))
        self.add_step(BatchReportingStep())

class PatientDiscoveryStep(PipelineStep):
    """
    Discover all patients in the directory
    """
    
    def __init__(self):
        super().__init__("PatientDiscoveryStep", "Discover all patients in directory")
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Find all patient directories with required files
        """
        base_dir = Path(data['base_directory'])
        
        # Pattern matching for different naming conventions
        patterns = [
            ('*_t2w.nii.gz', '*_adc.nii.gz'),  # Pranav's convention
            ('*_T2W.nii.gz', '*_ADC.nii.gz'),  # Alternative
            ('*t2.nii.gz', '*adc.nii.gz'),     # Shorter version
        ]
        
        patients = []
        
        # Find all patient directories
        for patient_dir in base_dir.iterdir():
            if not patient_dir.is_dir():
                continue
            
            if patient_dir.name.startswith('.'):
                continue
            
            patient_id = patient_dir.name
            
            # Check for required files
            t2w_path = None
            adc_path = None
            
            for t2w_pattern, adc_pattern in patterns:
                t2w_candidates = list(patient_dir.glob(t2w_pattern))
                adc_candidates = list(patient_dir.glob(adc_pattern))
                
                if t2w_candidates and adc_candidates:
                    t2w_path = t2w_candidates[0]
                    adc_path = adc_candidates[0]
                    break
            
            # Also check for exact naming
            if not t2w_path:
                exact_t2w = patient_dir / f"{patient_id}_t2w.nii.gz"
                exact_adc = patient_dir / f"{patient_id}_adc.nii.gz"
                
                if exact_t2w.exists() and exact_adc.exists():
                    t2w_path = exact_t2w
                    adc_path = exact_adc
            
            if t2w_path and adc_path:
                patients.append({
                    'patient_id': patient_id,
                    't2w_path': str(t2w_path),
                    'adc_path': str(adc_path),
                    'patient_dir': str(patient_dir)
                })
                self.logger.info(f"Found patient {patient_id}")
            else:
                self.logger.warning(f"Skipping {patient_id}: missing required files")
        
        self.logger.info(f"Found {len(patients)} patients with complete data")
        
        return {
            'patients': patients,
            'total_patients': len(patients)
        }

class BatchStandardizationStep(PipelineStep):
    """
    Train standardization on all images before processing
    """
    
    def __init__(self, method: str = 'nyul'):
        super().__init__("BatchStandardizationStep", "Train standardization on all images")
        self.method = method
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Train standardization models on all available images
        """
        patients = data['patients']
        
        if self.method == 'nyul':
            from ..preprocessing.standardization import NyulStandardizer
            
            self.logger.info("Training Nyul standardization on all T2W images")
            
            # Load all T2W images for training
            t2w_images = []
            for patient in patients[:20]:  # Use first 20 for training
                try:
                    img = sitk.ReadImage(patient['t2w_path'])
                    t2w_images.append(img)
                except Exception as e:
                    self.logger.warning(f"Failed to load {patient['patient_id']}: {e}")
            
            # Train standardizer
            t2w_standardizer = NyulStandardizer()
            t2w_standardizer.train(t2w_images)
            
            # Save parameters
            output_dir = Path(data['output_directory'])
            param_file = output_dir / 'nyul_parameters.json'
            t2w_standardizer.save_parameters(str(param_file))
            
            return {
                't2w_standardizer': t2w_standardizer,
                'standardization_trained': True,
                'training_samples': len(t2w_images)
            }
        
        else:
            # Z-score doesn't need training
            return {'standardization_trained': False}

class BatchProcessingStep(PipelineStep):
    """
    Process all patients with optional parallel processing
    """
    
    def __init__(self, 
                 registration_type: str = 'rigid',
                 enable_segmentation: bool = True,
                 parallel: bool = True,
                 max_workers: int = 4):
        
        super().__init__("BatchProcessingStep", "Process all patients")
        self.registration_type = registration_type
        self.enable_segmentation = enable_segmentation
        self.parallel = parallel
        self.max_workers = max_workers
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Process all patients
        """
        patients = data['patients']
        output_dir = Path(data['output_directory'])
        
        # Get standardizer if available
        t2w_standardizer = data.get('t2w_standardizer')
        
        # Results tracking
        results = {
            'successful': [],
            'failed': [],
            'detailed_results': {}
        }
        
        # Process function for single patient
        def process_patient(patient_info):
            return self._process_single_patient(
                patient_info, 
                output_dir,
                t2w_standardizer
            )
        
        # Process patients
        if self.parallel and len(patients) > 1:
            self.logger.info(f"Processing {len(patients)} patients in parallel (max {self.max_workers} workers)")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_patient = {
                    executor.submit(process_patient, patient): patient 
                    for patient in patients
                }
                
                # Process results with progress bar
                with tqdm(total=len(patients), desc="Processing patients") as pbar:
                    for future in concurrent.futures.as_completed(future_to_patient):
                        patient = future_to_patient[future]
                        try:
                            result = future.result()
                            if result['success']:
                                results['successful'].append(patient['patient_id'])
                            else:
                                results['failed'].append(patient['patient_id'])
                            results['detailed_results'][patient['patient_id']] = result
                        except Exception as e:
                            self.logger.error(f"Failed to process {patient['patient_id']}: {e}")
                            results['failed'].append(patient['patient_id'])
                            results['detailed_results'][patient['patient_id']] = {
                                'success': False,
                                'error': str(e)
                            }
                        pbar.update(1)
        else:
            # Sequential processing
            self.logger.info(f"Processing {len(patients)} patients sequentially")
            
            for patient in tqdm(patients, desc="Processing patients"):
                try:
                    result = process_patient(patient)
                    if result['success']:
                        results['successful'].append(patient['patient_id'])
                    else:
                        results['failed'].append(patient['patient_id'])
                    results['detailed_results'][patient['patient_id']] = result
                except Exception as e:
                    self.logger.error(f"Failed to process {patient['patient_id']}: {e}")
                    results['failed'].append(patient['patient_id'])
                    results['detailed_results'][patient['patient_id']] = {
                        'success': False,
                        'error': str(e)
                    }
        
        # Summary
        success_rate = len(results['successful']) / len(patients) if patients else 0
        self.logger.info(f"Batch processing complete: {success_rate:.1%} success rate")
        
        return results
    
    def _process_single_patient(self, 
                               patient_info: Dict[str, Any],
                               output_dir: Path,
                               t2w_standardizer: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process a single patient
        """
        patient_id = patient_info['patient_id']
        patient_output_dir = output_dir / patient_id
        patient_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load images
            t2w_image = sitk.ReadImage(patient_info['t2w_path'])
            adc_image = sitk.ReadImage(patient_info['adc_path'])
            
            # Create preprocessing pipeline
            pipeline = PreprocessingPipeline(
                registration_type=self.registration_type,
                standardization_method='nyul' if t2w_standardizer else 'zscore',
                enable_segmentation=self.enable_segmentation
            )
            
            # Inject trained standardizer if available
            if t2w_standardizer:
                pipeline.steps[0].standardizer = t2w_standardizer
            
            # Run pipeline
            input_data = {
                't2w_image': t2w_image,
                'adc_image': adc_image
            }
            
            pipeline_results = pipeline.execute(input_data)
            
            # Save results
            outputs_saved = []
            
            # Define what to save
            outputs_to_save = [
                ('t2w_standardized', 'StandardizationStep'),
                ('adc_standardized', 'StandardizationStep'),
                ('prostate_segmentation', 'SegmentationStep'),
                ('registered_adc', 'RegistrationStep'),
                ('t2w_standardized_roi', 'ROIExtractionStep'),
                ('adc_standardized_roi', 'ROIExtractionStep')
            ]
            
            for output_name, step_name in outputs_to_save:
                if step_name in pipeline_results['step_results']:
                    step_result = pipeline_results['step_results'][step_name].get('result', {})
                    if output_name in step_result:
                        output_path = patient_output_dir / f"{output_name}.nii.gz"
                        sitk.WriteImage(step_result[output_name], str(output_path))
                        outputs_saved.append(output_name)
            
            # Save transform if available
            if 'RegistrationStep' in pipeline_results['step_results']:
                transform = pipeline_results['step_results']['RegistrationStep']['result'].get('registration_transform')
                if transform:
                    transform_path = patient_output_dir / 'registration_transform.tfm'
                    sitk.WriteTransform(transform, str(transform_path))
            
            return {
                'success': True,
                'patient_id': patient_id,
                'outputs_saved': outputs_saved,
                'output_directory': str(patient_output_dir),
                'execution_time': pipeline_results['metadata']['total_execution_time']
            }
            
        except Exception as e:
            return {
                'success': False,
                'patient_id': patient_id,
                'error': str(e),
                'error_type': type(e).__name__
            }

class BatchReportingStep(PipelineStep):
    """
    Generate comprehensive batch processing report
    """
    
    def __init__(self):
        super().__init__("BatchReportingStep", "Generate batch processing report")
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate reports
        """
        output_dir = Path(data['output_directory'])
        batch_results = data.get('BatchProcessingStep', {})
        
        # Create reports directory
        reports_dir = output_dir / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        # Generate summary report
        summary = {
            'pipeline_name': 'BatchPreprocessingPipeline',
            'timestamp': datetime.now().isoformat(),
            'total_patients': data['total_patients'],
            'successful': len(batch_results.get('successful', [])),
            'failed': len(batch_results.get('failed', [])),
            'success_rate': len(batch_results.get('successful', [])) / data['total_patients'] if data['total_patients'] > 0 else 0,
            'configuration': {
                'registration_type': data.get('registration_type', 'unknown'),
                'standardization_method': data.get('standardization_method', 'unknown'),
                'enable_segmentation': data.get('enable_segmentation', False)
            }
        }
        
        # Save JSON summary
        summary_path = reports_dir / 'batch_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate CSV report
        csv_path = reports_dir / 'batch_results.csv'
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['PatientID', 'Status', 'ExecutionTime', 'OutputsSaved', 'Error'])
            
            for patient_id, result in batch_results.get('detailed_results', {}).items():
                writer.writerow([
                    patient_id,
                    'Success' if result.get('success') else 'Failed',
                    result.get('execution_time', 'N/A'),
                    ','.join(result.get('outputs_saved', [])),
                    result.get('error', '')
                ])
        
        # Generate error log
        if batch_results.get('failed'):
            error_log_path = reports_dir / 'error_log.txt'
            with open(error_log_path, 'w') as f:
                f.write(f"Batch Processing Error Log\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                
                for patient_id in batch_results.get('failed', []):
                    result = batch_results.get('detailed_results', {}).get(patient_id, {})
                    f.write(f"Patient: {patient_id}\n")
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n")
                    f.write(f"Error Type: {result.get('error_type', 'Unknown')}\n")
                    f.write("-" * 40 + "\n\n")
        
        self.logger.info(f"Reports saved to {reports_dir}")
        
        return {
            'summary_path': str(summary_path),
            'csv_path': str(csv_path),
            'reports_directory': str(reports_dir)
        }
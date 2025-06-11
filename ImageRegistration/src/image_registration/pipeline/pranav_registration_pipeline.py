"""
Professional wrapper around Pranav's ADC-T2W registration code
"""
import os
import subprocess
import shutil
import csv
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
import json

from .base_pipeline import BasePipeline, PipelineStep

class PranavRegistrationEngine:
    """
    Enhanced version of Pranav's registration approach with professional infrastructure
    """
    
    def __init__(self, 
                 elastix_installation_path: Optional[str] = None,
                 rigid_params_path: Optional[str] = None):
        """
        Initialize Pranav's registration engine
        """
        
        # Auto-detect platform and set paths
        self.platform = platform.system().lower()
        self.elastix_path, self.transformix_path = self._setup_elastix_paths(elastix_installation_path)
        self.rigid_params_path = rigid_params_path or self._find_rigid_params()
        
        # Setup environment
        self.env = self._setup_environment()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Verify installation
        self._verify_elastix_installation()
    
    def _setup_elastix_paths(self, installation_path: Optional[str]) -> Tuple[str, str]:
        """Setup elastix and transformix executable paths based on platform"""
        
        if installation_path:
            base_path = Path(installation_path)
        else:
            # Try to auto-detect common installation paths
            common_paths = {
                'darwin': [  # macOS
                    '/usr/local/elastix',
                    '/opt/elastix',
                    f'{Path.home()}/elastix-5',
                ],
                'linux': [
                    '/usr/local/elastix',
                    '/opt/elastix',
                    '/usr/bin'
                ],
                'windows': [
                    'C:\\Program Files\\elastix',
                    'C:\\elastix'
                ]
            }
            
            base_path = None
            for path in common_paths.get(self.platform, []):
                if Path(path).exists():
                    base_path = Path(path)
                    break
            
            if base_path is None:
                raise RuntimeError(f"Could not find elastix installation for {self.platform}")
        
        # Platform-specific executable paths
        if self.platform == 'windows':
            elastix_exe = base_path / 'elastix.exe'
            transformix_exe = base_path / 'transformix.exe'
        else:
            elastix_exe = base_path / 'bin' / 'elastix'
            transformix_exe = base_path / 'bin' / 'transformix'
        
        return str(elastix_exe), str(transformix_exe)
    
    def _setup_environment(self) -> Dict[str, str]:
        """Setup environment variables for elastix"""
        env = os.environ.copy()
        
        if self.platform == 'darwin':  # macOS
            elastix_base = str(Path(self.elastix_path).parent.parent)
            lib_path = f"{elastix_base}/lib"
            env["DYLD_LIBRARY_PATH"] = f"{lib_path}:{env.get('DYLD_LIBRARY_PATH', '')}"
        
        elif self.platform == 'linux':
            elastix_base = str(Path(self.elastix_path).parent.parent)
            lib_path = f"{elastix_base}/lib"
            env["LD_LIBRARY_PATH"] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}"
        
        return env
    
    def _find_rigid_params(self) -> str:
        """Find rigid.txt parameter file"""
        # Look in common locations
        search_paths = [
            Path(__file__).parent.parent.parent.parent / 'configs' / 'rigid.txt',
            Path.cwd() / 'rigid.txt',
            Path.cwd() / 'configs' / 'rigid.txt'
        ]
        
        for path in search_paths:
            if path.exists():
                return str(path)
        
        raise FileNotFoundError("Could not find rigid.txt parameter file")
    
    def _verify_elastix_installation(self):
        """Verify that elastix is properly installed"""
        try:
            result = subprocess.run([self.elastix_path, '--help'], 
                                  capture_output=True, text=True, timeout=10, env=self.env)
            if result.returncode != 0:
                raise RuntimeError("elastix not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            raise RuntimeError(f"elastix not found or not executable at {self.elastix_path}")
    
    def register_adc_to_t2w(self,
                           patient_id: str,
                           adc_path: str,
                           t2w_path: str,
                           output_dir: str) -> Dict[str, Any]:
        """
        Register ADC to T2W using Pranav's approach
        """
        
        # Create patient-specific output directory
        patient_output_dir = Path(output_dir) / patient_id
        patient_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define output paths
        transform_params_path = patient_output_dir / 'TransformParameters.0.txt'
        registered_adc_path = Path(adc_path).parent / f"{patient_id}_adc_reg.nii.gz"
        
        self.logger.info(f"Starting ADC-T2W registration for patient {patient_id}")
        
        try:
            # Step 1: Run elastix registration
            elastix_cmd = [
                self.elastix_path,
                '-f', t2w_path,        # T2W is fixed (reference)
                '-m', adc_path,        # ADC is moving (gets aligned)
                '-p', self.rigid_params_path,
                '-out', str(patient_output_dir)
            ]
            
            self.logger.debug(f"Elastix command: {' '.join(elastix_cmd)}")
            
            elastix_result = subprocess.run(
                elastix_cmd, 
                env=self.env, 
                capture_output=True, 
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if elastix_result.returncode != 0:
                raise subprocess.CalledProcessError(
                    elastix_result.returncode, elastix_cmd, elastix_result.stderr
                )
            
            # Step 2: Apply transformation to ADC
            transformix_cmd = [
                self.transformix_path,
                '-in', adc_path,
                '-out', str(Path(adc_path).parent),
                '-tp', str(transform_params_path)
            ]
            
            self.logger.debug(f"Transformix command: {' '.join(transformix_cmd)}")
            
            transformix_result = subprocess.run(
                transformix_cmd,
                env=self.env,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout
            )
            
            if transformix_result.returncode != 0:
                raise subprocess.CalledProcessError(
                    transformix_result.returncode, transformix_cmd, transformix_result.stderr
                )
            
            # Step 3: Handle output files (following Pranav's approach)
            result_temp_path = Path(adc_path).parent / "result.nii.gz"
            
            if result_temp_path.exists():
                # Move and rename result file
                shutil.move(str(result_temp_path), str(registered_adc_path))
                
                # Move log files
                transformix_log_src = Path(adc_path).parent / "transformix.log"
                if transformix_log_src.exists():
                    transformix_log_dst = patient_output_dir / "transformix.log"
                    shutil.move(str(transformix_log_src), str(transformix_log_dst))
            else:
                raise FileNotFoundError(f"Registration result file not found for {patient_id}")
            
            # Prepare results
            results = {
                'patient_id': patient_id,
                'success': True,
                'registered_adc_path': str(registered_adc_path),
                'transform_parameters_path': str(transform_params_path),
                'output_directory': str(patient_output_dir),
                'elastix_log': elastix_result.stdout,
                'transformix_log': transformix_result.stdout
            }
            
            self.logger.info(f"Successfully registered ADC to T2W for patient {patient_id}")
            return results
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Registration failed for {patient_id}: {e.stderr}"
            self.logger.error(error_msg)
            return {
                'patient_id': patient_id,
                'success': False,
                'error': error_msg,
                'error_type': 'subprocess_error'
            }
        
        except Exception as e:
            error_msg = f"Unexpected error for {patient_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'patient_id': patient_id,
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }

class PranavBatchProcessor(PipelineStep):
    """
    Batch processor using Pranav's directory structure and approach
    """
    
    def __init__(self, 
                 elastix_installation_path: Optional[str] = None,
                 rigid_params_path: Optional[str] = None):
        super().__init__("PranavBatchProcessor", "Batch ADC-T2W registration using Pranav's approach")
        
        self.registration_engine = PranavRegistrationEngine(
            elastix_installation_path, rigid_params_path
        )
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute batch registration on directory of patients
        """
        
        base_dir = Path(data['base_directory'])
        output_dir = Path(data['output_directory'])
        
        # Find patient directories (following Pranav's logic)
        patient_dirs = [
            d for d in base_dir.iterdir() 
            if d.is_dir() 
            and not d.name.startswith('._') 
            and d.name != '.DS_Store'
        ]
        
        self.logger.info(f"Found {len(patient_dirs)} patient directories")
        
        # Results tracking
        results = {
            'total_patients': len(patient_dirs),
            'successful': [],
            'failed': [],
            'detailed_results': {},
            'summary': {}
        }
        
        # Error logging (following Pranav's CSV approach)
        error_log_path = output_dir / 'registration_errors.csv'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(error_log_path, 'w', newline='') as error_file:
            error_writer = csv.writer(error_file)
            error_writer.writerow(['PatientID', 'Error', 'Timestamp'])
            
            for patient_dir in patient_dirs:
                patient_id = patient_dir.name
                self.logger.info(f"Processing patient: {patient_id}")
                
                # Check for required files
                adc_path = patient_dir / f"{patient_id}_adc.nii.gz"
                t2w_path = patient_dir / f"{patient_id}_t2w.nii.gz"
                
                if not adc_path.exists():
                    error_msg = f"ADC file not found: {adc_path}"
                    self.logger.warning(error_msg)
                    error_writer.writerow([patient_id, error_msg, datetime.now().isoformat()])
                    results['failed'].append(patient_id)
                    continue
                
                if not t2w_path.exists():
                    error_msg = f"T2W file not found: {t2w_path}"
                    self.logger.warning(error_msg)
                    error_writer.writerow([patient_id, error_msg, datetime.now().isoformat()])
                    results['failed'].append(patient_id)
                    continue
                
                # Run registration
                reg_result = self.registration_engine.register_adc_to_t2w(
                    patient_id=patient_id,
                    adc_path=str(adc_path),
                    t2w_path=str(t2w_path),
                    output_dir=str(output_dir)
                )
                
                # Track results
                results['detailed_results'][patient_id] = reg_result
                
                if reg_result['success']:
                    results['successful'].append(patient_id)
                    self.logger.info(f"✓ Successfully processed {patient_id}")
                else:
                    results['failed'].append(patient_id)
                    error_writer.writerow([
                        patient_id, 
                        reg_result.get('error', 'Unknown error'),
                        datetime.now().isoformat()
                    ])
                    self.logger.error(f"✗ Failed to process {patient_id}")
        
        # Generate summary
        success_rate = len(results['successful']) / len(patient_dirs) if patient_dirs else 0
        results['summary'] = {
            'success_rate': success_rate,
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'error_log_path': str(error_log_path)
        }
        
        self.logger.info(f"Batch processing complete: {success_rate:.1%} success rate")
        
        return results

class ProstateADCRegistrationPipeline(BasePipeline):
    """
    Complete pipeline for prostate ADC-T2W registration
    Professional wrapper around Pranav's approach
    """
    
    def __init__(self, 
                 elastix_installation_path: Optional[str] = None,
                 rigid_params_path: Optional[str] = None):
        super().__init__(
            name="ProstateADCRegistrationPipeline",
            description="Professional ADC-T2W registration pipeline based on Pranav's approach"
        )
        
        # Add pipeline steps
        self.add_step(PranavBatchProcessor(elastix_installation_path, rigid_params_path))
    
    def process_patient_directory(self,
                                 base_directory: str,
                                 output_directory: str,
                                 generate_report: bool = True) -> Dict[str, Any]:
        """
        Process entire patient directory using Pranav's structure
        """
        
        input_data = {
            'base_directory': base_directory,
            'output_directory': output_directory
        }
        
        # Execute pipeline
        results = self.execute(input_data)
        
        # Generate report if requested
        if generate_report:
            self._generate_summary_report(results, output_directory)
        
        return results
    
    def _generate_summary_report(self, results: Dict[str, Any], output_dir: str):
        """Generate comprehensive summary report"""
        
        report_path = Path(output_dir) / 'registration_summary_report.json'
        
        # Extract batch results
        batch_results = results['step_results']['PranavBatchProcessor']['result']
        
        report = {
            'pipeline_info': {
                'pipeline_name': self.name,
                'timestamp': datetime.now().isoformat(),
                'total_execution_time': results['metadata']['total_execution_time']
            },
            'processing_summary': batch_results['summary'],
            'successful_patients': batch_results['successful'],
            'failed_patients': batch_results['failed'],
            'detailed_results': batch_results['detailed_results']
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Summary report saved: {report_path}")

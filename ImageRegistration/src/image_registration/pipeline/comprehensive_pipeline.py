# src/image_registration/pipeline/comprehensive_pipeline.py
"""
Comprehensive preprocessing pipeline integrating all modules
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import SimpleITK as sitk
import logging

from .base_pipeline import BasePipeline, PipelineStep
from ..preprocessing.coregistration import RegistrationFactory
from ..preprocessing.standardization import NyulStandardizer, ZScoreStandardizer
from ..preprocessing.roi_segmentation import ROIExtractor, ProstateSegmentor

class PreprocessingPipeline(BasePipeline):
    """
    Complete preprocessing pipeline for medical images
    Includes: standardization -> segmentation -> registration
    """
    
    def __init__(self,
                 registration_type: str = 'rigid',
                 standardization_method: str = 'nyul',
                 enable_segmentation: bool = True):
        
        super().__init__(
            name="ComprehensivePreprocessingPipeline",
            description="Full preprocessing pipeline with standardization, segmentation, and registration"
        )
        
        # Add pipeline steps
        self.add_step(StandardizationStep(method=standardization_method))
        
        if enable_segmentation:
            self.add_step(SegmentationStep())
            self.add_step(ROIExtractionStep())
        
        self.add_step(RegistrationStep(registration_type=registration_type))

class StandardizationStep(PipelineStep):
    """Intensity standardization step"""
    
    def __init__(self, method: str = 'nyul'):
        super().__init__("StandardizationStep", f"Intensity standardization using {method}")
        self.method = method
        
        if method == 'nyul':
            self.standardizer = NyulStandardizer()
        elif method == 'zscore':
            self.standardizer = ZScoreStandardizer()
        else:
            raise ValueError(f"Unknown standardization method: {method}")
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Apply intensity standardization"""
        
        # Get images
        t2w_image = data.get('t2w_image')
        adc_image = data.get('adc_image')
        
        results = {}
        
        # Standardize T2W
        if t2w_image is not None:
            self.logger.info("Standardizing T2W image")
            if not self.standardizer.trained:
                self.standardizer.train([t2w_image])  # Simple single-image training
            results['t2w_standardized'] = self.standardizer.transform(t2w_image)
        
        # Standardize ADC
        if adc_image is not None:
            self.logger.info("Standardizing ADC image")
            # ADC uses different standardization
            adc_standardizer = ZScoreStandardizer()
            results['adc_standardized'] = adc_standardizer.transform(adc_image)
        
        return results

class SegmentationStep(PipelineStep):
    """Prostate segmentation step"""
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__("SegmentationStep", "Prostate segmentation")
        self.segmentor = ProstateSegmentor(model_path)
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Perform segmentation"""
        
        # Use standardized T2W if available, otherwise original
        t2w_image = data.get('t2w_standardized', data.get('t2w_image'))
        
        if t2w_image is None:
            raise ValueError("No T2W image available for segmentation")
        
        self.logger.info("Segmenting prostate")
        segmentation = self.segmentor.segment(t2w_image)
        
        return {'prostate_segmentation': segmentation}

class ROIExtractionStep(PipelineStep):
    """ROI extraction step"""
    
    def __init__(self, padding: int = 10):
        super().__init__("ROIExtractionStep", "Extract ROI around prostate")
        self.extractor = ROIExtractor()
        self.padding = padding
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Extract ROI"""
        
        segmentation = data.get('prostate_segmentation')
        if segmentation is None:
            self.logger.warning("No segmentation available, skipping ROI extraction")
            return {}
        
        results = {}
        
        # Extract ROI from all available images
        for key in ['t2w_standardized', 'adc_standardized', 't2w_image', 'adc_image']:
            if key in data and data[key] is not None:
                roi_img, roi_mask = self.extractor.extract_bounding_box(
                    data[key], segmentation, self.padding
                )
                results[f'{key}_roi'] = roi_img
        
        results['roi_mask'] = roi_mask
        
        return results

class RegistrationStep(PipelineStep):
    """Registration step"""
    
    def __init__(self, registration_type: str = 'rigid'):
        super().__init__("RegistrationStep", f"{registration_type} registration")
        self.registration_type = registration_type
    
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Perform registration"""
        
        # Get images (prefer ROI versions if available)
        fixed_image = data.get('t2w_standardized_roi', 
                               data.get('t2w_standardized',
                                       data.get('t2w_image')))
        
        moving_image = data.get('adc_standardized_roi',
                                data.get('adc_standardized', 
                                        data.get('adc_image')))
        
        if fixed_image is None or moving_image is None:
            raise ValueError("Both fixed and moving images required for registration")
        
        # Create registration
        self.logger.info(f"Performing {self.registration_type} registration")
        registration = RegistrationFactory.create_registration(self.registration_type)
        
        # Get masks if available
        fixed_mask = data.get('roi_mask')
        moving_mask = None  # ADC typically doesn't have separate mask
        
        # Perform registration
        registered_image, transform = registration.register(
            fixed_image, moving_image, fixed_mask, moving_mask
        )
        
        return {
            'registered_adc': registered_image,
            'registration_transform': transform,
            'registration_type': self.registration_type
        }
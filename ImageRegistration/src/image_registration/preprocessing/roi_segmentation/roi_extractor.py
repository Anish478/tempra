# src/image_registration/preprocessing/roi_segmentation/roi_extractor.py
"""
ROI extraction utilities
"""
import SimpleITK as sitk
import numpy as np
from typing import Tuple, Optional, Dict
import logging

class ROIExtractor:
    """
    Extract regions of interest from medical images
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_bounding_box(self, 
                           image: sitk.Image, 
                           mask: sitk.Image,
                           padding: int = 10) -> Tuple[sitk.Image, sitk.Image]:
        """
        Extract bounding box around mask region
        
        Args:
            image: Input image
            mask: Binary mask
            padding: Padding around bounding box in voxels
            
        Returns:
            Cropped image and mask
        """
        # Get bounding box
        label_shape_filter = sitk.LabelShapeStatisticsImageFilter()
        label_shape_filter.Execute(mask)
        
        bbox = label_shape_filter.GetBoundingBox(1)  # Assuming label 1
        
        # Add padding
        start = [max(0, bbox[i] - padding) for i in range(0, len(bbox)//2)]
        size = [min(image.GetSize()[i] - start[i], 
                    bbox[i + len(bbox)//2] + 2*padding) 
                for i in range(0, len(bbox)//2)]
        
        # Extract ROI
        roi_image = sitk.RegionOfInterest(image, size, start)
        roi_mask = sitk.RegionOfInterest(mask, size, start)
        
        self.logger.info(f"Extracted ROI: size={size}, start={start}")
        
        return roi_image, roi_mask
    
    def extract_prostate_region(self,
                               t2w_image: sitk.Image,
                               segmentation: Optional[sitk.Image] = None) -> Dict[str, sitk.Image]:
        """
        Extract prostate region from T2W image
        
        Args:
            t2w_image: T2-weighted MRI
            segmentation: Optional prostate segmentation
            
        Returns:
            Dictionary with extracted regions
        """
        if segmentation is None:
            # Use simple thresholding as fallback
            self.logger.warning("No segmentation provided, using threshold-based extraction")
            
            # Smooth image
            smoothed = sitk.SmoothingRecursiveGaussian(t2w_image, 2.0)
            
            # Otsu threshold
            otsu_filter = sitk.OtsuThresholdImageFilter()
            otsu_filter.SetInsideValue(0)
            otsu_filter.SetOutsideValue(1)
            segmentation = otsu_filter.Execute(smoothed)
            
            # Clean up with morphological operations
            segmentation = sitk.BinaryMorphologicalClosing(segmentation, [3, 3, 3])
            segmentation = sitk.BinaryMorphologicalOpening(segmentation, [2, 2, 2])
        
        # Extract bounding box
        roi_image, roi_mask = self.extract_bounding_box(t2w_image, segmentation)
        
        return {
            'roi_image': roi_image,
            'roi_mask': roi_mask,
            'original_image': t2w_image,
            'segmentation': segmentation
        }
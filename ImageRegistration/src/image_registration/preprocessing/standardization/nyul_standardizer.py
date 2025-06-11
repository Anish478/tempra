# src/image_registration/preprocessing/standardization/nyul_standardizer.py
"""
Nyul intensity standardization method
Referenced in elastix manual and commonly used for MRI standardization
"""
import SimpleITK as sitk
import numpy as np
from typing import List, Tuple
from .intensity_standardizer import IntensityStandardizer

class NyulStandardizer(IntensityStandardizer):
    """
    Nyul histogram matching standardization
    Maps intensity landmarks to standard scale
    """
    
    def __init__(self, 
                 landmarks_percentage: List[float] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                 standard_scale: Tuple[float, float] = (0, 100)):
        """
        Initialize Nyul standardizer
        
        Args:
            landmarks_percentage: Percentile landmarks to use
            standard_scale: Target intensity range
        """
        super().__init__()
        self.landmarks_percentage = landmarks_percentage
        self.standard_scale = standard_scale
        self.standard_landmarks = None
    
    def train(self, images: List[sitk.Image]) -> None:
        """
        Learn the standard intensity landmarks
        """
        self.logger.info("Training Nyul standardization on {} images".format(len(images)))
        
        all_landmarks = []
        
        for img in images:
            # Convert to numpy array
            img_array = sitk.GetArrayFromImage(img)
            
            # Get non-zero voxels (assuming background is 0)
            non_zero = img_array[img_array > 0]
            
            # Calculate percentile landmarks
            landmarks = np.percentile(non_zero, self.landmarks_percentage)
            all_landmarks.append(landmarks)
        
        # Calculate mean landmarks as standard
        self.standard_landmarks = np.mean(all_landmarks, axis=0)
        
        # Map to standard scale
        self.standard_landmarks[0] = self.standard_scale[0]
        self.standard_landmarks[-1] = self.standard_scale[1]
        
        # Linear interpolation for intermediate landmarks
        for i in range(1, len(self.standard_landmarks) - 1):
            self.standard_landmarks[i] = (
                self.standard_scale[0] + 
                (self.standard_scale[1] - self.standard_scale[0]) * 
                (i / (len(self.standard_landmarks) - 1))
            )
        
        self.parameters['standard_landmarks'] = self.standard_landmarks.tolist()
        self.parameters['landmarks_percentage'] = self.landmarks_percentage
        self.trained = True
        
        self.logger.info("Training completed")
    
    def transform(self, image: sitk.Image) -> sitk.Image:
        """
        Apply Nyul standardization to an image
        """
        if not self.trained:
            raise RuntimeError("Standardizer must be trained before transform")
        
        # Convert to array
        img_array = sitk.GetArrayFromImage(image)
        
        # Get non-zero mask
        mask = img_array > 0
        non_zero = img_array[mask]
        
        # Calculate image landmarks
        img_landmarks = np.percentile(non_zero, self.landmarks_percentage)
        
        # Create standardized image
        standardized = np.zeros_like(img_array)
        
        # Apply piecewise linear mapping
        for i in range(len(self.landmarks_percentage) - 1):
            # Find voxels in this intensity range
            lower = img_landmarks[i]
            upper = img_landmarks[i + 1]
            mask_range = (img_array >= lower) & (img_array < upper)
            
            # Linear mapping
            if upper > lower:
                slope = (self.standard_landmarks[i + 1] - self.standard_landmarks[i]) / (upper - lower)
                standardized[mask_range] = (
                    self.standard_landmarks[i] + 
                    slope * (img_array[mask_range] - lower)
                )
        
        # Handle maximum value
        standardized[img_array >= img_landmarks[-1]] = self.standard_landmarks[-1]
        
        # Preserve zeros
        standardized[img_array == 0] = 0
        
        # Convert back to SimpleITK image
        standardized_img = sitk.GetImageFromArray(standardized)
        standardized_img.CopyInformation(image)
        
        return standardized_img
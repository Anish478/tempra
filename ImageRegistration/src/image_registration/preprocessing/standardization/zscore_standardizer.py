# src/image_registration/preprocessing/standardization/zscore_standardizer.py
"""
Z-score standardization
Simple but effective for many applications
"""
import SimpleITK as sitk
import numpy as np
from .intensity_standardizer import IntensityStandardizer

class ZScoreStandardizer(IntensityStandardizer):
    """
    Z-score (zero mean, unit variance) standardization
    """
    
    def __init__(self, use_robust_statistics: bool = True):
        """
        Initialize Z-score standardizer
        
        Args:
            use_robust_statistics: Use median/MAD instead of mean/std
        """
        super().__init__()
        self.use_robust_statistics = use_robust_statistics
        self.global_mean = None
        self.global_std = None
    
    def train(self, images: list) -> None:
        """
        Calculate global statistics from training images
        """
        self.logger.info("Training Z-score standardization")
        
        all_values = []
        
        for img in images:
            img_array = sitk.GetArrayFromImage(img)
            # Only use non-zero values
            non_zero = img_array[img_array > 0]
            all_values.extend(non_zero)
        
        all_values = np.array(all_values)
        
        if self.use_robust_statistics:
            self.global_mean = np.median(all_values)
            # Median absolute deviation
            self.global_std = np.median(np.abs(all_values - self.global_mean)) * 1.4826
        else:
            self.global_mean = np.mean(all_values)
            self.global_std = np.std(all_values)
        
        self.parameters['global_mean'] = float(self.global_mean)
        self.parameters['global_std'] = float(self.global_std)
        self.parameters['use_robust'] = self.use_robust_statistics
        
        self.trained = True
        self.logger.info(f"Training completed: mean={self.global_mean:.2f}, std={self.global_std:.2f}")
    
    def transform(self, image: sitk.Image) -> sitk.Image:
        """
        Apply Z-score standardization
        """
        if not self.trained:
            # Use per-image standardization
            img_array = sitk.GetArrayFromImage(image)
            mask = img_array > 0
            
            if self.use_robust_statistics:
                mean = np.median(img_array[mask])
                std = np.median(np.abs(img_array[mask] - mean)) * 1.4826
            else:
                mean = np.mean(img_array[mask])
                std = np.std(img_array[mask])
        else:
            mean = self.global_mean
            std = self.global_std
            img_array = sitk.GetArrayFromImage(image)
            mask = img_array > 0
        
        # Standardize
        standardized = np.zeros_like(img_array)
        standardized[mask] = (img_array[mask] - mean) / (std + 1e-8)
        
        # Convert back
        standardized_img = sitk.GetImageFromArray(standardized)
        standardized_img.CopyInformation(image)
        
        return standardized_img
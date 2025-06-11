# src/image_registration/preprocessing/standardization/intensity_standardizer.py
"""
Base class for intensity standardization
Based on preprocessing requirements from the papers
"""
import SimpleITK as sitk
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import logging

class IntensityStandardizer(ABC):
    """
    Base class for intensity standardization methods
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trained = False
        self.parameters = {}
    
    @abstractmethod
    def train(self, images: list) -> None:
        """Train standardization parameters on a set of images"""
        pass
    
    @abstractmethod
    def transform(self, image: sitk.Image) -> sitk.Image:
        """Apply standardization to an image"""
        pass
    
    def fit_transform(self, images: list) -> list:
        """Train and transform images"""
        self.train(images)
        return [self.transform(img) for img in images]
    
    def save_parameters(self, filepath: str) -> None:
        """Save standardization parameters"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.parameters, f)
    
    def load_parameters(self, filepath: str) -> None:
        """Load standardization parameters"""
        import json
        with open(filepath, 'r') as f:
            self.parameters = json.load(f)
        self.trained = True
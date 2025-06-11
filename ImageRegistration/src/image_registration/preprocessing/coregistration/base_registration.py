"""
Base registration class following elastix manual principles
"""
import SimpleITK as sitk
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import logging
from pathlib import Path

class BaseRegistration(ABC):
    """
    Base class for all registration methods
    Implements the registration framework described in elastix manual Chapter 2
    """
    
    def __init__(self, 
                 metric: str = "AdvancedMattesMutualInformation",
                 optimizer: str = "AdaptiveStochasticGradientDescent",
                 interpolator: str = "LinearInterpolator",
                 number_of_resolutions: int = 3,
                 parameter_file: Optional[str] = None):
        """
        Initialize registration with elastix-compatible parameters
        
        Args:
            metric: Similarity metric (Section 2.3 of elastix manual)
            optimizer: Optimization method (Section 2.7)
            interpolator: Interpolation method (Section 2.5)
            number_of_resolutions: Multi-resolution levels (Section 2.8)
            parameter_file: Optional path to elastix parameter file
        """
        self.metric = metric
        self.optimizer = optimizer
        self.interpolator = interpolator
        self.number_of_resolutions = number_of_resolutions
        self.logger = logging.getLogger(__name__)
        
        # Initialize SimpleITK registration
        self.registration_method = sitk.ImageRegistrationMethod()
        
        if parameter_file:
            self._load_parameter_file(parameter_file)
        else:
            self._setup_registration()
    
    def _load_parameter_file(self, parameter_file: str):
        """Load registration parameters from elastix parameter file"""
        if not Path(parameter_file).exists():
            raise FileNotFoundError(f"Parameter file not found: {parameter_file}")
            
        # Read parameter file
        with open(parameter_file, 'r') as f:
            params = f.readlines()
        
        # Parse parameters
        param_dict = {}
        for line in params:
            line = line.strip()
            if line and not line.startswith('//'):
                # Extract parameter name and value
                if '(' in line and ')' in line:
                    param = line.split('(')[1].split(')')[0].split(' ')
                    if len(param) >= 2:
                        name = param[0]
                        value = ' '.join(param[1:]).strip('"')
                        param_dict[name] = value
        
        # Set registration parameters
        if 'Metric' in param_dict:
            self.metric = param_dict['Metric']
        if 'Optimizer' in param_dict:
            self.optimizer = param_dict['Optimizer']
        if 'Interpolator' in param_dict:
            self.interpolator = param_dict['Interpolator']
        if 'NumberOfResolutions' in param_dict:
            self.number_of_resolutions = int(param_dict['NumberOfResolutions'])
            
        # Setup registration with loaded parameters
        self._setup_registration()
        
        # Additional optimizer parameters
        if 'MaximumNumberOfIterations' in param_dict:
            self.registration_method.SetOptimizerScalesFromPhysicalShift()
            self.registration_method.SetOptimizerAsGradientDescent(
                learningRate=float(param_dict.get('SP_a', '500.0')),
                numberOfIterations=int(param_dict['MaximumNumberOfIterations']),
                convergenceMinimumValue=1e-6,
                convergenceWindowSize=10
            )
        
        # Additional metric parameters
        if 'NumberOfHistogramBins' in param_dict:
            if self.metric == 'AdvancedMattesMutualInformation':
                self.registration_method.SetMetricAsMattesMutualInformation(
                    numberOfHistogramBins=int(param_dict['NumberOfHistogramBins'])
                )
        
        # Additional sampler parameters
        if 'NumberOfSpatialSamples' in param_dict:
            self.registration_method.SetMetricSamplingStrategy(self.registration_method.RANDOM)
            self.registration_method.SetMetricSamplingPercentage(
                float(param_dict['NumberOfSpatialSamples']) / 10000
            )
    
    @abstractmethod
    def get_transform(self) -> sitk.Transform:
        """Get the specific transform type"""
        pass
    
    def _setup_registration(self):
        """Setup registration components based on elastix manual"""
        # Set up metric
        if self.metric == "AdvancedMattesMutualInformation":
            self.registration_method.SetMetricAsMattesMutualInformation(
                numberOfHistogramBins=32
            )
        elif self.metric == "AdvancedMeanSquares":
            self.registration_method.SetMetricAsMeanSquares()
        elif self.metric == "AdvancedNormalizedCorrelation":
            self.registration_method.SetMetricAsCorrelation()
        
        # Set up optimizer
        if self.optimizer == "AdaptiveStochasticGradientDescent":
            self.registration_method.SetOptimizerAsGradientDescent(
                learningRate=1.0,
                numberOfIterations=500,
                convergenceMinimumValue=1e-6,
                convergenceWindowSize=10
            )
        
        # Set up interpolator
        if self.interpolator == "LinearInterpolator":
            self.registration_method.SetInterpolator(sitk.sitkLinear)
        elif self.interpolator == "BSplineInterpolator":
            self.registration_method.SetInterpolator(sitk.sitkBSpline)
        
        # Set up multi-resolution
        self.registration_method.SetShrinkFactorsPerLevel(
            shrinkFactors=[4, 2, 1][:self.number_of_resolutions]
        )
        self.registration_method.SetSmoothingSigmasPerLevel(
            smoothingSigmas=[2, 1, 0][:self.number_of_resolutions]
        )
    
    def register(self, 
                 fixed_image: sitk.Image, 
                 moving_image: sitk.Image,
                 fixed_mask: Optional[sitk.Image] = None,
                 moving_mask: Optional[sitk.Image] = None) -> Tuple[sitk.Image, sitk.Transform]:
        """
        Perform registration following elastix framework
        
        Args:
            fixed_image: Reference image (I_F in elastix notation)
            moving_image: Image to be registered (I_M in elastix notation)
            fixed_mask: Optional mask for fixed image
            moving_mask: Optional mask for moving image
            
        Returns:
            Registered image and transformation
        """
        self.logger.info(f"Starting {self.__class__.__name__} registration")
        
        # Set up transform
        initial_transform = self.get_transform()
        self.registration_method.SetInitialTransform(initial_transform)
        
        # Set masks if provided
        if fixed_mask is not None:
            self.registration_method.SetMetricFixedMask(fixed_mask)
        if moving_mask is not None:
            self.registration_method.SetMetricMovingMask(moving_mask)
        
        # Execute registration
        final_transform = self.registration_method.Execute(fixed_image, moving_image)
        
        # Apply transformation
        resampler = sitk.ResampleImageFilter()
        resampler.SetReferenceImage(fixed_image)
        resampler.SetInterpolator(sitk.sitkBSpline)
        resampler.SetDefaultPixelValue(0)
        resampler.SetTransform(final_transform)
        
        registered_image = resampler.Execute(moving_image)
        
        self.logger.info("Registration completed successfully")
        return registered_image, final_transform
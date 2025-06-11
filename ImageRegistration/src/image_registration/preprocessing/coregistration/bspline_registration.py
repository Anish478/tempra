# src/image_registration/preprocessing/coregistration/bspline_registration.py
"""
B-spline nonrigid registration implementation
Based on elastix manual Section 2.6
"""
import SimpleITK as sitk
import numpy as np
from pathlib import Path
from .base_registration import BaseRegistration
from typing import Optional, Tuple

class BSplineRegistration(BaseRegistration):
    """
    B-spline transformation for nonrigid registration
    T(x) = x + sum(p_k * beta^3((x-x_k)/sigma))
    """
    
    def __init__(self, 
                 parameter_file: str = None,
                 grid_spacing_schedule: list = None,
                 **kwargs):
        """
        Initialize B-spline registration
        
        Args:
            parameter_file: Path to elastix parameter file (default: configs/registration/bspline.txt)
            grid_spacing_schedule: Multi-grid spacing factors (overrides parameter file if provided)
            **kwargs: Additional parameters passed to BaseRegistration
        """
        if parameter_file is None:
            # Use default parameter file
            parameter_file = str(Path(__file__).parent.parent.parent.parent / 'configs' / 'registration' / 'bspline.txt')
        
        super().__init__(parameter_file=parameter_file, **kwargs)
        self.transform_type = "BSplineTransform"
        
        # Override grid spacing if provided
        self.grid_spacing_schedule = grid_spacing_schedule or [6.0, 4.0, 2.0]
    
    def get_transform(self) -> sitk.Transform:
        """
        Get B-spline transform with control point grid
        """
        # This will be initialized properly during registration
        dimension = 3
        transform = sitk.BSplineTransform(dimension)
        return transform
    
    def register(self, 
                 fixed_image: sitk.Image, 
                 moving_image: sitk.Image,
                 fixed_mask: Optional[sitk.Image] = None,
                 moving_mask: Optional[sitk.Image] = None) -> Tuple[sitk.Image, sitk.Transform]:
        """
        Override to handle multi-resolution B-spline grid
        """
        # Initialize with rigid/affine first
        initial_transform = sitk.CenteredTransformInitializer(
            fixed_image, moving_image,
            sitk.AffineTransform(fixed_image.GetDimension()),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )
        
        # Set up B-spline on top of initial alignment
        transform_domain_mesh_size = [8, 8, 8]  # Initial grid
        bspline = sitk.BSplineTransform(fixed_image.GetDimension())
        bspline.SetTransformDomainOrigin(fixed_image.GetOrigin())
        bspline.SetTransformDomainDirection(fixed_image.GetDirection())
        bspline.SetTransformDomainPhysicalDimensions(
            [size * spacing for size, spacing in 
             zip(fixed_image.GetSize(), fixed_image.GetSpacing())]
        )
        bspline.SetTransformDomainMeshSize(transform_domain_mesh_size)
        
        # Composite transform
        composite = sitk.CompositeTransform(fixed_image.GetDimension())
        composite.AddTransform(initial_transform)
        composite.AddTransform(bspline)
        
        self.registration_method.SetInitialTransform(composite)
        self.registration_method.SetOptimizerScalesFromPhysicalShift()
        
        return super().register(fixed_image, moving_image, fixed_mask=fixed_mask, moving_mask=moving_mask)
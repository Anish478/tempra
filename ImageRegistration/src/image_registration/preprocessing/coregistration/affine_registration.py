"""
Affine registration implementation

"""
import SimpleITK as sitk
from pathlib import Path
from .base_registration import BaseRegistration

class AffineRegistration(BaseRegistration):
    """
    Affine transformation: T(x) = A(x-c) + t + c
    Where A is affine matrix (rotation, scale, shear), c is center, t is translation
    """
    
    def __init__(self, parameter_file: str = None, **kwargs):
        """
        Initialize affine registration
        
        Args:
            parameter_file: Path to elastix parameter file (default: configs/registration/affine.txt)
            **kwargs: Additional parameters passed to BaseRegistration
        """
        if parameter_file is None:
            # Use default parameter file
            parameter_file = str(Path(__file__).parent.parent.parent.parent / 'configs' / 'registration' / 'affine.txt')
        
        super().__init__(parameter_file=parameter_file, **kwargs)
        self.transform_type = "AffineTransform"
    
    def get_transform(self) -> sitk.Transform:
        """
        Get affine transform
        In 3D: 12 parameters (9 matrix elements + 3 translations)
        """
        dimension = 3
        transform = sitk.CenteredTransformInitializer(
            sitk.AffineTransform(dimension),
            sitk.Image([1, 1, 1], sitk.sitkUInt8),  # Dummy
            sitk.Image([1, 1, 1], sitk.sitkUInt8),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )
        return transform
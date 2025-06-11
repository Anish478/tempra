"""
Rigid registration implementation (translation + rotation)

"""
import SimpleITK as sitk
from pathlib import Path
from .base_registration import BaseRegistration

class RigidRegistration(BaseRegistration):
    """
    Rigid transformation: T(x) = R(x-c) + t + c
    Where R is rotation matrix, c is center of rotation, t is translation
    """
    
    def __init__(self, parameter_file: str = None, **kwargs):
        """
        Initialize rigid registration
        
        Args:
            parameter_file: Path to elastix parameter file (default: configs/rigid.txt)
            **kwargs: Additional parameters passed to BaseRegistration
        """
        if parameter_file is None:
            # Use default parameter file
            parameter_file = str(Path(__file__).parent.parent.parent.parent / 'configs' / 'rigid.txt')
        
        super().__init__(parameter_file=parameter_file, **kwargs)
        self.transform_type = "Euler3DTransform"
    
    def get_transform(self) -> sitk.Transform:
        """
        Get Euler transform for rigid registration
        In 3D: 6 parameters (3 rotations + 3 translations)
        """
        dimension = 3  # For medical images
        transform = sitk.CenteredTransformInitializer(
            sitk.Euler3DTransform(),
            sitk.Image([1, 1, 1], sitk.sitkUInt8),  # Dummy for initialization
            sitk.Image([1, 1, 1], sitk.sitkUInt8),
            sitk.CenteredTransformInitializerFilter.GEOMETRY
        )
        return transform
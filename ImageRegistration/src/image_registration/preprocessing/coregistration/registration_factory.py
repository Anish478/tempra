# src/image_registration/preprocessing/coregistration/registration_factory.py
"""
Factory pattern for creating registration instances
"""
from typing import Dict, Any
from .rigid_registration import RigidRegistration
from .affine_registration import AffineRegistration
from .bspline_registration import BSplineRegistration

class RegistrationFactory:
    """
    Factory for creating registration instances based on type
    """
    
    REGISTRATION_TYPES = {
        'rigid': RigidRegistration,
        'affine': AffineRegistration,
        'bspline': BSplineRegistration,
        'nonrigid': BSplineRegistration  # Alias
    }
    
    @classmethod
    def create_registration(cls, 
                           registration_type: str,
                           **kwargs) -> 'BaseRegistration':
        """
        Create registration instance
        
        Args:
            registration_type: Type of registration ('rigid', 'affine', 'bspline')
            **kwargs: Additional parameters for registration
            
        Returns:
            Registration instance
        """
        if registration_type.lower() not in cls.REGISTRATION_TYPES:
            raise ValueError(f"Unknown registration type: {registration_type}")
        
        registration_class = cls.REGISTRATION_TYPES[registration_type.lower()]
        return registration_class(**kwargs)
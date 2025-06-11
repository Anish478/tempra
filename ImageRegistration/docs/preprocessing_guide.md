# Preprocessing Pipeline Guide

## Overview

The preprocessing pipeline provides a comprehensive framework for medical image preprocessing with three main components:

1. **Co-registration**: Aligning images from different modalities
2. **Intensity Standardization**: Harmonizing intensity distributions
3. **ROI Segmentation**: Extracting regions of interest

## Components

### 1. Co-registration Module

Supports multiple transformation types based on the elastix framework:

- **Rigid Registration**: Translation + rotation only
- **Affine Registration**: Rigid + scaling + shearing  
- **B-spline Registration**: Nonrigid deformation

```python
from image_registration.preprocessing.coregistration import RegistrationFactory

# Create registration instance
registration = RegistrationFactory.create_registration('affine')

# Perform registration
registered_image, transform = registration.register(fixed_image, moving_image)
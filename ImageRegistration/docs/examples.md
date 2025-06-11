# Usage Examples

## Registration with Parameter Files

### Rigid Registration
```python
from image_registration.preprocessing.coregistration import RigidRegistration
import SimpleITK as sitk

# Load images
fixed_image = sitk.ReadImage("fixed.nii")
moving_image = sitk.ReadImage("moving.nii")

# Create registration using default parameter file (configs/rigid.txt)
registration = RigidRegistration()

# Or specify a custom parameter file
registration = RigidRegistration(parameter_file="path/to/custom_rigid.txt")

# Run registration
registered_image, transform = registration.register(fixed_image, moving_image)

# Save result
sitk.WriteImage(registered_image, "rigid_registered.nii")
```

### Affine Registration
```python
from image_registration.preprocessing.coregistration import AffineRegistration
import SimpleITK as sitk

# Load images
fixed_image = sitk.ReadImage("fixed.nii")
moving_image = sitk.ReadImage("moving.nii")

# Create registration using default parameter file (configs/registration/affine.txt)
registration = AffineRegistration()

# Or specify custom parameters while using default file
registration = AffineRegistration(
    metric="AdvancedNormalizedCorrelation",  # Override specific parameters
    number_of_resolutions=4
)

registered_image, transform = registration.register(fixed_image, moving_image)

# Save result
sitk.WriteImage(registered_image, "affine_registered.nii")
```

### B-spline Registration
```python
from image_registration.preprocessing.coregistration import BSplineRegistration
import SimpleITK as sitk

# Load images
fixed_image = sitk.ReadImage("fixed.nii")
moving_image = sitk.ReadImage("moving.nii")

# Create registration using default parameter file (configs/registration/bspline.txt)
registration = BSplineRegistration()

# Or customize grid spacing while using default parameters
registration = BSplineRegistration(
    grid_spacing_schedule=[8.0, 4.0, 2.0, 1.0]  # Override grid spacing
)

# Run deformable registration
registered_image, transform = registration.register(fixed_image, moving_image)

# Generate deformation field (useful for visualization)
displacement_filter = sitk.TransformToDisplacementFieldFilter()
displacement_filter.SetReferenceImage(fixed_image)
deformation_field = displacement_filter.Execute(transform)

# Save results
sitk.WriteImage(registered_image, "bspline_registered.nii")
sitk.WriteImage(deformation_field, "deformation_field.nii")
```

### Progressive Registration (Rigid → Affine → Deformable)
```python
from image_registration.preprocessing.coregistration import (
    RigidRegistration, AffineRegistration, BSplineRegistration
)

# Each registration step uses its corresponding parameter file
rigid_reg = RigidRegistration()  # Uses configs/rigid.txt
affine_reg = AffineRegistration()  # Uses configs/registration/affine.txt
bspline_reg = BSplineRegistration()  # Uses configs/registration/bspline.txt

# 1. Start with rigid registration
rigid_result, rigid_transform = rigid_reg.register(fixed_image, moving_image)

# 2. Use rigid result as initialization for affine
affine_result, affine_transform = affine_reg.register(fixed_image, rigid_result)

# 3. Finally, apply deformable registration
final_result, bspline_transform = bspline_reg.register(fixed_image, affine_result)

# Save final result
sitk.WriteImage(final_result, "progressive_registered.nii")
```

## Parameter File Locations

The registration parameter files are located in:
- Rigid: `configs/rigid.txt`
- Affine: `configs/registration/affine.txt`
- B-spline: `configs/registration/bspline.txt`

Each parameter file contains settings for:
- Image types and dimensions
- Registration components (metric, optimizer, interpolator)
- Multi-resolution pyramid settings
- Transform-specific parameters
- Optimizer parameters
- Sampling strategy

You can modify these files to tune the registration behavior for your specific use case.

## Basic Registration

### Affine Registration
```python
from image_registration.preprocessing.coregistration import AffineRegistration
import SimpleITK as sitk

# Load images
fixed_image = sitk.ReadImage("fixed.nii")
moving_image = sitk.ReadImage("moving.nii")

# Create and run registration
registration = AffineRegistration()
registered_image, transform = registration.register(fixed_image, moving_image)

# Save result
sitk.WriteImage(registered_image, "registered.nii")
```

### B-spline Registration
```python
from image_registration.preprocessing.coregistration import BSplineRegistration

# Create registration with custom parameters
registration = BSplineRegistration(
    grid_spacing_schedule=[8.0, 4.0, 2.0],
    metric="AdvancedNormalizedCorrelation"
)
registered_image, transform = registration.register(fixed_image, moving_image)
```

### Deformable Registration (B-spline)
```python
from image_registration.preprocessing.coregistration import BSplineRegistration
import SimpleITK as sitk

# Load images
fixed_image = sitk.ReadImage("fixed.nii")
moving_image = sitk.ReadImage("moving.nii")

# Create deformable registration with fine control
registration = BSplineRegistration(
    # Control point grid spacing schedule (from coarse to fine)
    grid_spacing_schedule=[8.0, 4.0, 2.0],
    
    # Use mutual information for better handling of intensity differences
    metric="AdvancedMattesMutualInformation",
    
    # More resolution levels for better accuracy
    number_of_resolutions=4
)

# Run deformable registration
registered_image, transform = registration.register(fixed_image, moving_image)

# The transform can be used to:
# 1. Transform other images from the same space
# 2. Analyze local deformation
# 3. Generate deformation field visualization

# Generate deformation field (useful for visualization)
displacement_filter = sitk.TransformToDisplacementFieldFilter()
displacement_filter.SetReferenceImage(fixed_image)
deformation_field = displacement_filter.Execute(transform)

# Save results
sitk.WriteImage(registered_image, "deformably_registered.nii")
sitk.WriteImage(deformation_field, "deformation_field.nii")

# Example of applying transform to another image from same space
another_moving_image = sitk.ReadImage("another_image.nii")
resampler = sitk.ResampleImageFilter()
resampler.SetReferenceImage(fixed_image)
resampler.SetTransform(transform)
another_registered = resampler.Execute(another_moving_image)
```

### Progressive Registration (Rigid → Affine → Deformable)
```python
from image_registration.preprocessing.coregistration import (
    RigidRegistration, AffineRegistration, BSplineRegistration
)

# 1. Start with rigid registration
rigid_reg = RigidRegistration()
rigid_result, rigid_transform = rigid_reg.register(fixed_image, moving_image)

# 2. Use rigid result as initialization for affine
affine_reg = AffineRegistration()
affine_result, affine_transform = affine_reg.register(fixed_image, rigid_result)

# 3. Finally, apply deformable registration
bspline_reg = BSplineRegistration(
    grid_spacing_schedule=[6.0, 4.0, 2.0]  # Finer control point spacing
)
final_result, bspline_transform = bspline_reg.register(fixed_image, affine_result)

# The final result combines rigid alignment, affine correction, 
# and local deformable adjustments
```

## Intensity Standardization

### Z-score Standardization
```python
from image_registration.preprocessing.standardization import ZScoreStandardizer

# Create standardizer with robust statistics
standardizer = ZScoreStandardizer(use_robust_statistics=True)

# Single image standardization
standardized_image = standardizer.transform(image)

# Multiple image standardization with training
standardizer.train([image1, image2, image3])
standardized_images = [standardizer.transform(img) for img in images]
```

### Nyul Standardization
```python
from image_registration.preprocessing.standardization import NyulStandardizer

# Create standardizer with custom landmarks
standardizer = NyulStandardizer(
    landmarks_percentage=[0, 25, 50, 75, 100],
    standard_scale=(0, 1000)
)

# Train on a set of images
standardizer.train(training_images)

# Save trained parameters
standardizer.save_parameters("nyul_params.json")

# Load parameters and transform new images
standardizer.load_parameters("nyul_params.json")
standardized = standardizer.transform(new_image)
```

## Complete Pipeline

### Basic Pipeline Usage
```python
from image_registration.pipeline import PreprocessingPipeline

# Create pipeline
pipeline = PreprocessingPipeline(
    registration_type="affine",
    standardization_method="nyul",
    enable_segmentation=True
)

# Prepare input data
input_data = {
    't2w_image': t2w_image,
    'adc_image': adc_image
}

# Run pipeline
results = pipeline.execute(input_data)

# Access results
standardized_t2w = results['t2w_standardized']
registered_adc = results['registered_adc']
roi = results['t2w_standardized_roi']
```

### Batch Processing
```python
from image_registration.pipeline import BatchPreprocessingPipeline
from pathlib import Path

# Setup batch pipeline
pipeline = BatchPreprocessingPipeline(
    registration_type="affine",
    output_dir=Path("output")
)

# Process multiple patients
patient_data = [
    {
        'patient_id': 'patient1',
        't2w_path': 'data/patient1/t2w.nii',
        'adc_path': 'data/patient1/adc.nii'
    },
    # ... more patients
]

# Run batch processing
pipeline.execute({'patients': patient_data})
```

## ROI Extraction

### Basic ROI Extraction
```python
from image_registration.preprocessing.roi_segmentation import ROIExtractor

# Create extractor
extractor = ROIExtractor(
    padding_mm=15,
    minimum_size_mm=[50, 50, 30]
)

# Extract ROI
roi_image = extractor.extract(image)
``` 
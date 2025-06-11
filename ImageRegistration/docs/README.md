# Image Registration Documentation

## Table of Contents
1. [Installation Guide](installation.md)
2. [Preprocessing Guide](preprocessing_guide.md)
3. [API Reference](api_reference.md)
4. [Examples](examples.md)
5. [Configuration Guide](configuration_guide.md)
6. [Troubleshooting](troubleshooting.md)

## Overview
This package provides tools for medical image registration and preprocessing, including:
- Multiple registration methods (Rigid, Affine, B-spline)
- Intensity standardization
- ROI segmentation
- Comprehensive preprocessing pipeline

## Quick Start
```python
from image_registration.pipeline import PreprocessingPipeline
from image_registration.preprocessing.standardization import NyulStandardizer

# Create and run pipeline
pipeline = PreprocessingPipeline(
    registration_type="affine",
    standardization_method="nyul"
)
results = pipeline.execute(input_data)
```

## Directory Structure
```
src/image_registration/
├── preprocessing/
│   ├── coregistration/      # Registration implementations
│   ├── standardization/     # Intensity standardization
│   └── roi_segmentation/    # ROI extraction tools
├── pipeline/                # Pipeline implementations
└── utils/                   # Utility functions
``` 
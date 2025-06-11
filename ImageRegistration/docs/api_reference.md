# API Reference

## Registration

### BaseRegistration
Abstract base class for all registration methods.

```python
class BaseRegistration(ABC):
    def __init__(self, 
                 metric: str = "AdvancedMattesMutualInformation",
                 optimizer: str = "AdaptiveStochasticGradientDescent",
                 interpolator: str = "LinearInterpolator",
                 number_of_resolutions: int = 3):
        """
        Initialize registration with elastix-compatible parameters
        
        Args:
            metric: Similarity metric (Options: AdvancedMattesMutualInformation, 
                   AdvancedMeanSquares, AdvancedNormalizedCorrelation)
            optimizer: Optimization method
            interpolator: Interpolation method
            number_of_resolutions: Multi-resolution levels
        """
```

### AffineRegistration
```python
class AffineRegistration(BaseRegistration):
    """
    Affine transformation: T(x) = A(x-c) + t + c
    Where:
        A: affine matrix (rotation, scale, shear)
        c: center point
        t: translation vector
    """
```

### BSplineRegistration (Deformable Registration)
```python
class BSplineRegistration(BaseRegistration):
    """
    B-spline transformation for deformable (non-rigid) registration
    Implements free-form deformation using a B-spline transformation model
    
    The transformation is defined by a grid of control points that can be
    moved to create local deformations. The deformation between control
    points is interpolated using B-spline basis functions.
    
    Args:
        grid_spacing_schedule: List of control point spacings for multi-resolution
                             [default: [6.0, 4.0, 2.0]]
                             - Larger values = coarser grid = global deformations
                             - Smaller values = finer grid = local deformations
        metric: Similarity metric (default: "AdvancedMattesMutualInformation")
        optimizer: Optimization method (default: "AdaptiveStochasticGradientDescent")
        number_of_resolutions: Number of multi-resolution levels (default: 3)
    
    Methods:
        register(fixed_image, moving_image, fixed_mask=None, moving_mask=None):
            Performs deformable registration
            Returns: (registered_image, transform)
    
    Example:
        ```python
        registration = BSplineRegistration(
            grid_spacing_schedule=[8.0, 4.0, 2.0],  # From coarse to fine deformation
            number_of_resolutions=4  # More levels for better accuracy
        )
        registered_image, transform = registration.register(fixed_image, moving_image)
        ```
    
    Notes:
        - Best used after rigid/affine pre-registration
        - Can handle local anatomical differences
        - More computationally intensive than rigid/affine
        - Transform can be used to analyze local deformation
    """
```

## Intensity Standardization

### IntensityStandardizer
Base class for intensity standardization methods.

```python
class IntensityStandardizer(ABC):
    def train(self, images: list) -> None:
        """Train standardization parameters on a set of images"""
        
    def transform(self, image: sitk.Image) -> sitk.Image:
        """Apply standardization to an image"""
```

### NyulStandardizer
```python
class NyulStandardizer(IntensityStandardizer):
    """
    Nyul histogram matching standardization
    
    Args:
        landmarks_percentage: Percentile landmarks [default: [0,10,20,...,100]]
        standard_scale: Target intensity range [default: (0,100)]
    """
```

### ZScoreStandardizer
```python
class ZScoreStandardizer(IntensityStandardizer):
    """
    Z-score standardization (zero mean, unit variance)
    
    Args:
        use_robust_statistics: Use median/MAD instead of mean/std [default: True]
    """
```

## ROI Segmentation

### ROIExtractor
```python
class ROIExtractor:
    """
    Extract region of interest from images
    
    Args:
        padding_mm: Padding around ROI in millimeters
        minimum_size_mm: Minimum ROI size in millimeters
    """
```

## Pipeline

### PreprocessingPipeline
```python
class PreprocessingPipeline:
    """
    Complete preprocessing pipeline
    
    Args:
        registration_type: Type of registration ("rigid", "affine", "bspline")
        standardization_method: Method for intensity standardization ("nyul", "zscore")
        enable_segmentation: Whether to perform ROI segmentation
    """
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute pipeline on input data
        
        Args:
            data: Dictionary containing input images and parameters
        
        Returns:
            Dictionary containing processed images and results
        """
```

## Configuration

### Example Configuration
```yaml
preprocessing:
  standardization:
    t2w:
      method: "nyul"
      landmarks_percentage: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
      standard_scale: [0, 100]
    adc:
      method: "zscore"
      use_robust_statistics: true
  
  registration:
    type_hierarchy: ["rigid", "affine", "bspline"]
    metric: "AdvancedMattesMutualInformation"
    optimizer: "AdaptiveStochasticGradientDescent"
    number_of_resolutions: 3 
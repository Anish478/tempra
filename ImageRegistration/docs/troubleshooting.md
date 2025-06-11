# Troubleshooting Guide

## Common Issues and Solutions

### Registration Issues

#### Registration Failed to Converge
**Symptoms:**
- Registration takes too long
- Results show poor alignment
- Optimizer reports convergence failure

**Solutions:**
1. Try different initialization:
   ```python
   registration = AffineRegistration(
       metric="AdvancedNormalizedCorrelation",  # Try different metric
       number_of_resolutions=4  # Increase resolution levels
   )
   ```

2. Adjust optimizer parameters:
   ```python
   registration.registration_method.SetOptimizerAsGradientDescent(
       learningRate=0.5,  # Try different learning rate
       numberOfIterations=1000,  # Increase iterations
       convergenceMinimumValue=1e-8
   )
   ```

3. Check image orientation and spacing:
   ```python
   # Ensure consistent orientation
   fixed_image.SetDirection(moving_image.GetDirection())
   ```

### Intensity Standardization Issues

#### Unexpected Intensity Values
**Symptoms:**
- Output intensities are not in expected range
- Background values are modified

**Solutions:**
1. Check mask application:
   ```python
   # Ensure only foreground is processed
   standardizer = ZScoreStandardizer()
   mask = image > 0
   ```

2. Verify training data:
   ```python
   # Print statistics of training data
   for img in training_images:
       arr = sitk.GetArrayFromImage(img)
       print(f"Mean: {np.mean(arr[arr>0])}, Std: {np.std(arr[arr>0])}")
   ```

3. Try robust statistics:
   ```python
   standardizer = ZScoreStandardizer(use_robust_statistics=True)
   ```

### ROI Segmentation Issues

#### ROI Too Small/Large
**Symptoms:**
- Extracted ROI misses important regions
- ROI includes too much background

**Solutions:**
1. Adjust padding:
   ```python
   extractor = ROIExtractor(
       padding_mm=20,  # Increase padding
       minimum_size_mm=[60, 60, 40]  # Adjust minimum size
   )
   ```

2. Check input segmentation:
   ```python
   # Visualize segmentation
   sitk.Show(segmentation)
   ```

### Pipeline Issues

#### Memory Errors
**Symptoms:**
- Out of memory errors
- System becomes unresponsive

**Solutions:**
1. Process in batches:
   ```python
   # Process images in smaller batches
   batch_size = 10
   for i in range(0, len(images), batch_size):
       batch = images[i:i+batch_size]
       process_batch(batch)
   ```

2. Release memory explicitly:
   ```python
   import gc
   
   # After processing each image
   del result
   gc.collect()
   ```

#### File I/O Errors
**Symptoms:**
- Cannot read/write images
- Missing directories

**Solutions:**
1. Check file permissions:
   ```python
   from pathlib import Path
   
   output_dir = Path("output")
   output_dir.mkdir(parents=True, exist_ok=True)
   ```

2. Verify file formats:
   ```python
   # Ensure correct file format
   if not str(filepath).endswith(('.nii', '.nii.gz')):
       raise ValueError("Unsupported file format")
   ```

## Performance Optimization

### Speed Improvements
1. Use multi-resolution approach:
   ```python
   registration.registration_method.SetShrinkFactorsPerLevel([8,4,2,1])
   ```

2. Optimize memory usage:
   ```python
   # Clear cache between patients
   import gc
   gc.collect()
   ```

3. Parallel processing:
   ```python
   from concurrent.futures import ProcessPoolExecutor
   
   with ProcessPoolExecutor() as executor:
       results = list(executor.map(process_single_case, cases))
   ```

## Getting Help
If you encounter issues not covered here:
1. Check the logs for detailed error messages
2. Verify input data integrity
3. Test with simplified test cases
4. Open an issue on the project repository 
# tests/test_coregistration.py
"""
Unit tests for co-registration module
"""
import unittest
import SimpleITK as sitk
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_registration.preprocessing.coregistration import (
    RigidRegistration, AffineRegistration, BSplineRegistration, RegistrationFactory
)

class TestRegistrationFactory(unittest.TestCase):
    """Test registration factory"""
    
    def test_create_rigid(self):
        """Test rigid registration creation"""
        reg = RegistrationFactory.create_registration('rigid')
        self.assertIsInstance(reg, RigidRegistration)
    
    def test_create_affine(self):
        """Test affine registration creation"""
        reg = RegistrationFactory.create_registration('affine')
        self.assertIsInstance(reg, AffineRegistration)
    
    def test_create_bspline(self):
        """Test B-spline registration creation"""
        reg = RegistrationFactory.create_registration('bspline')
        self.assertIsInstance(reg, BSplineRegistration)
    
    def test_invalid_type(self):
        """Test invalid registration type"""
        with self.assertRaises(ValueError):
            RegistrationFactory.create_registration('invalid')

class TestRigidRegistration(unittest.TestCase):
    """Test rigid registration"""
    
    def setUp(self):
        """Create test images"""
        # Create simple test images
        size = [64, 64, 32]
        self.fixed = sitk.Image(size, sitk.sitkFloat32)
        self.moving = sitk.Image(size, sitk.sitkFloat32)
        
        # Add some structure
        self.fixed = sitk.GaussianSource(
            sitk.sitkFloat32, 
            size=size,
            sigma=[10.0, 10.0, 10.0],
            mean=[32.0, 32.0, 16.0]
        )
        
        # Create translated version
        transform = sitk.TranslationTransform(3)
        transform.SetOffset([5.0, -3.0, 2.0])
        self.moving = sitk.Resample(self.fixed, transform)
    
def test_rigid_registration(self):
       """Test rigid registration recovers translation"""
       reg = RigidRegistration(number_of_resolutions=2)
       
       registered, transform = reg.register(self.fixed, self.moving)
       
       # Check that images are similar after registration
       diff = sitk.GetArrayFromImage(self.fixed) - sitk.GetArrayFromImage(registered)
       mse = np.mean(diff**2)
       
       self.assertLess(mse, 0.1)  # Should be very small

class TestIntensityStandardization(unittest.TestCase):
   """Test intensity standardization methods"""
   
   def setUp(self):
       """Create test images with different intensity ranges"""
       size = [64, 64, 32]
       
       # Create images with different intensity scales
       self.images = []
       for scale, offset in [(1.0, 0), (2.0, 100), (0.5, 50)]:
           img = sitk.GaussianSource(
               sitk.sitkFloat32,
               size=size,
               sigma=[10.0, 10.0, 10.0],
               mean=[32.0, 32.0, 16.0],
               scale=scale
           )
           img = sitk.Add(img, offset)
           self.images.append(img)
   
   def test_nyul_standardization(self):
       """Test Nyul standardization"""
       from image_registration.preprocessing.standardization import NyulStandardizer
       
       standardizer = NyulStandardizer()
       standardizer.train(self.images)
       
       # Transform images
       standardized = [standardizer.transform(img) for img in self.images]
       
       # Check that intensity ranges are similar
       ranges = []
       for img in standardized:
           arr = sitk.GetArrayFromImage(img)
           ranges.append((arr[arr > 0].min(), arr[arr > 0].max()))
       
       # Ranges should be similar after standardization
       for i in range(1, len(ranges)):
           self.assertAlmostEqual(ranges[0][0], ranges[i][0], delta=10)
           self.assertAlmostEqual(ranges[0][1], ranges[i][1], delta=10)
   
   def test_zscore_standardization(self):
       """Test Z-score standardization"""
       from image_registration.preprocessing.standardization import ZScoreStandardizer
       
       standardizer = ZScoreStandardizer(use_robust_statistics=False)
       
       # Test per-image standardization
       for img in self.images:
           standardized = standardizer.transform(img)
           arr = sitk.GetArrayFromImage(standardized)
           non_zero = arr[arr != 0]
           
           # Should have zero mean and unit variance
           self.assertAlmostEqual(np.mean(non_zero), 0, places=2)
           self.assertAlmostEqual(np.std(non_zero), 1, places=2)

class TestROIExtraction(unittest.TestCase):
   """Test ROI extraction"""
   
   def setUp(self):
       """Create test image with ROI"""
       size = [128, 128, 64]
       self.image = sitk.Image(size, sitk.sitkFloat32)
       
       # Create a sphere as ROI
       center = [64, 64, 32]
       radius = 20
       
       for z in range(size[2]):
           for y in range(size[1]):
               for x in range(size[0]):
                   dist = np.sqrt((x-center[0])**2 + (y-center[1])**2 + (z-center[2])**2)
                   if dist < radius:
                       self.image.SetPixel(x, y, z, 100)
       
       # Create mask
       self.mask = sitk.BinaryThreshold(self.image, 50, 200, 1, 0)
   
   def test_bounding_box_extraction(self):
       """Test bounding box extraction"""
       from image_registration.preprocessing.roi_segmentation import ROIExtractor
       
       extractor = ROIExtractor()
       roi_img, roi_mask = extractor.extract_bounding_box(self.image, self.mask, padding=5)
       
       # Check that ROI is smaller than original
       self.assertLess(roi_img.GetSize()[0], self.image.GetSize()[0])
       self.assertLess(roi_img.GetSize()[1], self.image.GetSize()[1])
       
       # Check that ROI contains the sphere
       roi_arr = sitk.GetArrayFromImage(roi_img)
       self.assertGreater(np.sum(roi_arr > 50), 0)

if __name__ == '__main__':
   unittest.main()
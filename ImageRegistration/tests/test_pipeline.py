#!/usr/bin/env python3
"""
Basic tests for the registration pipeline
"""
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestPipelineImports(unittest.TestCase):
    """Test that all modules can be imported"""
    
    def test_base_pipeline_import(self):
        """Test base pipeline import"""
        try:
            from image_registration.pipeline.base_pipeline import BasePipeline, PipelineStep
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import base pipeline: {e}")
    
    def test_pranav_pipeline_import(self):
        """Test Pranav's pipeline import"""
        try:
            from image_registration.pipeline.pranav_registration_pipeline import ProstateADCRegistrationPipeline
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import Pranav's pipeline: {e}")
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized"""
        try:
            from image_registration.pipeline.pranav_registration_pipeline import ProstateADCRegistrationPipeline
            # This should work even without elastix installed
            # (it will fail later when actually running registration)
            pipeline = ProstateADCRegistrationPipeline()
            self.assertIsNotNone(pipeline)
        except Exception as e:
            # Expected to fail if elastix not installed
            self.assertIn("elastix", str(e).lower())

class TestDataStructure(unittest.TestCase):
    """Test data structure validation"""
    
    def test_path_handling(self):
        """Test Path handling works correctly"""
        from pathlib import Path
        test_path = Path("/test/path")
        self.assertEqual(str(test_path), "/test/path")

if __name__ == '__main__':
    unittest.main()

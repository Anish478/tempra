# src/image_registration/pipeline/unified_batch_pipeline.py
"""
Unified batch pipeline that combines Pranav's approach with new preprocessing
"""
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .base_pipeline import BasePipeline
from .pranav_registration_pipeline import PranavBatchProcessor
from .batch_preprocessing import BatchPreprocessingPipeline

class UnifiedBatchPipeline(BasePipeline):
    """
    Unified pipeline that can run either Pranav's original approach
    or the new comprehensive preprocessing
    """
    
    def __init__(self, 
                 mode: str = 'comprehensive',
                 elastix_path: Optional[str] = None,
                 **kwargs):
        """
        Initialize unified pipeline
        
        Args:
            mode: 'pranav' for original approach, 'comprehensive' for new approach
            elastix_path: Path to elastix installation (for Pranav mode)
            **kwargs: Additional arguments for comprehensive mode
        """
        super().__init__(
            name="UnifiedBatchPipeline",
            description="Unified batch processing pipeline"
        )
        
        self.mode = mode
        
        if mode == 'pranav':
            # Use Pranav's original approach
            self.add_step(PranavBatchProcessor(elastix_path))
        else:
            # Use new comprehensive approach
            self.pipeline = BatchPreprocessingPipeline(**kwargs)
    
    def process_all_patients(self, 
                           input_directory: str,
                           output_directory: str) -> Dict[str, Any]:
        """
        Process all patients in directory
        """
        self.logger.info(f"Processing all patients in {input_directory} using {self.mode} mode")
        
        input_data = {
            'base_directory': input_directory,
            'output_directory': output_directory
        }
        
        if self.mode == 'pranav':
            # Pranav's approach
            results = self.execute(input_data)
        else:
            # Comprehensive approach
            results = self.pipeline.execute(input_data)
        
        return results
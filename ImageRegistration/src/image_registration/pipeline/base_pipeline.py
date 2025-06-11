

"""
Base pipeline framework for medical image processing
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import logging
import time
from pathlib import Path
import json
from datetime import datetime

class PipelineStep(ABC):
    """Base class for pipeline steps"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.execution_time = 0
        self.status = "pending"
        self.error_message = None
    
    @abstractmethod
    def execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute the pipeline step"""
        pass
    
    def validate_inputs(self, data: Dict[str, Any]) -> bool:
        """Validate input data for this step"""
        return True
    
    def cleanup(self) -> None:
        """Cleanup resources after step execution"""
        pass

class BasePipeline(ABC):
    """
    Base class for all processing pipelines
    Provides common functionality like logging, error handling, progress tracking
    """
    
    def __init__(self, 
                 name: str,
                 description: str = "",
                 log_level: str = "INFO"):
        
        self.name = name
        self.description = description
        self.steps: List[PipelineStep] = []
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.status = "initialized"
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Progress tracking
        self.progress_callbacks = []
        self.current_step_index = 0
        
        # Error handling
        self.continue_on_error = False
        self.errors = []
    
    def add_step(self, step: PipelineStep) -> None:
        """Add a processing step to the pipeline"""
        self.steps.append(step)
        self.logger.info(f"Added step: {step.name}")
    
    def execute(self, 
                input_data: Dict[str, Any],
                continue_on_error: bool = False,
                **kwargs) -> Dict[str, Any]:
        """
        Execute the complete pipeline
        """
        
        self.continue_on_error = continue_on_error
        self.start_time = time.time()
        self.status = "running"
        self.current_step_index = 0
        
        self.logger.info(f"Starting pipeline: {self.name}")
        
        # Initialize results
        current_data = input_data.copy()
        self.results = {
            'input_data': input_data,
            'step_results': {},
            'metadata': {
                'pipeline_name': self.name,
                'start_time': self.start_time,
                'steps_executed': []
            }
        }
        
        try:
            # Execute each step sequentially
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                self.logger.info(f"Executing step {i+1}/{len(self.steps)}: {step.name}")
                
                step_start_time = time.time()
                step.status = "running"
                
                try:
                    # Validate inputs
                    if not step.validate_inputs(current_data):
                        raise ValueError(f"Input validation failed for step: {step.name}")
                    
                    # Execute step
                    step_result = step.execute(current_data, **kwargs)
                    
                    # Update current data with step results
                    if step_result:
                        current_data.update(step_result)
                    
                    # Record step execution
                    step.execution_time = time.time() - step_start_time
                    step.status = "completed"
                    
                    self.results['step_results'][step.name] = {
                        'result': step_result,
                        'execution_time': step.execution_time,
                        'status': 'success'
                    }
                    
                    self.results['metadata']['steps_executed'].append({
                        'name': step.name,
                        'index': i,
                        'execution_time': step.execution_time,
                        'status': 'success'
                    })
                
                except Exception as e:
                    # Handle step failure
                    step.execution_time = time.time() - step_start_time
                    step.status = "failed"
                    step.error_message = str(e)
                    
                    error_info = {
                        'step_name': step.name,
                        'step_index': i,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    
                    self.errors.append(error_info)
                    self.logger.error(f"Step {step.name} failed: {e}")
                    
                    self.results['step_results'][step.name] = {
                        'result': None,
                        'execution_time': step.execution_time,
                        'status': 'failed',
                        'error': str(e)
                    }
                    
                    if not self.continue_on_error:
                        raise
                
                finally:
                    # Cleanup step resources
                    try:
                        step.cleanup()
                    except Exception as cleanup_error:
                        self.logger.warning(f"Cleanup failed for {step.name}: {cleanup_error}")
            
            # Pipeline completed successfully
            self.status = "completed"
            self.logger.info(f"Pipeline {self.name} completed successfully")
            
        except Exception as e:
            # Pipeline failed
            self.status = "failed"
            self.logger.error(f"Pipeline {self.name} failed: {e}")
            self.results['error'] = str(e)
            raise
        
        finally:
            # Finalize results
            self.end_time = time.time()
            self.results['metadata'].update({
                'end_time': self.end_time,
                'total_execution_time': self.end_time - self.start_time,
                'status': self.status,
                'errors': self.errors
            })
        
        return self.results

# examples/comprehensive_preprocessing.py
#!/usr/bin/env python3
"""
Example of using the comprehensive preprocessing pipeline
"""
import sys
from pathlib import Path
import SimpleITK as sitk
import logging

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.image_registration.pipeline.comprehensive_pipeline import PreprocessingPipeline

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def preprocess_patient_data(t2w_path: str, 
                          adc_path: str,
                          output_dir: str,
                          registration_type: str = 'rigid'):
    """
    Preprocess patient data with full pipeline
    """
    
    print(f"🏥 Comprehensive Preprocessing Pipeline")
    print(f"📁 T2W: {t2w_path}")
    print(f"📁 ADC: {adc_path}")
    print(f"🔧 Registration type: {registration_type}")
    print("=" * 60)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load images
    t2w_image = sitk.ReadImage(t2w_path)
    adc_image = sitk.ReadImage(adc_path)
    
    # Initialize pipeline
    pipeline = PreprocessingPipeline(
        registration_type=registration_type,
        standardization_method='nyul',
        enable_segmentation=True
    )
    
    # Prepare input data
    input_data = {
        't2w_image': t2w_image,
        'adc_image': adc_image
    }
    
    # Run pipeline
    try:
        results = pipeline.execute(input_data)
        
        # Extract results
        pipeline_results = results['step_results']
        
        # Save outputs
        outputs = {
            't2w_standardized': 'StandardizationStep',
            'adc_standardized': 'StandardizationStep',
            'prostate_segmentation': 'SegmentationStep',
            'registered_adc': 'RegistrationStep'
        }
        
        for output_name, step_name in outputs.items():
            if step_name in pipeline_results:
                step_result = pipeline_results[step_name]['result']
                if output_name in step_result:
                    img = step_result[output_name]
                    output_file = output_path / f"{output_name}.nii.gz"
                    sitk.WriteImage(img, str(output_file))
                    print(f"✅ Saved: {output_file}")
        
        print(f"\n🎉 Preprocessing completed successfully!")
        print(f"⏱️  Total time: {results['metadata']['total_execution_time']:.1f}s")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) != 4:
        print("Usage: python comprehensive_preprocessing.py <t2w_path> <adc_path> <output_dir>")
        sys.exit(1)
    
    t2w_path = sys.argv[1]
    adc_path = sys.argv[2]
    output_dir = sys.argv[3]
    
    preprocess_patient_data(t2w_path, adc_path, output_dir, registration_type='affine')
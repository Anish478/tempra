#!/usr/bin/env python3
"""
Simple interface for lab members to use the registration pipeline
"""
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_registration.pipeline.pranav_registration_pipeline import ProstateADCRegistrationPipeline

# Setup simple logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('registration.log')
    ]
)

def register_adc_to_t2w_simple(patient_directory: str, 
                              output_directory: str,
                              elastix_path: str = None) -> dict:
    """
    Simple function to register ADC to T2W for all patients in a directory
    
    Args:
        patient_directory: Directory containing patient folders
                          Each folder should have: {patientID}_adc.nii.gz and {patientID}_t2w.nii.gz
        output_directory: Where to save registration results
        elastix_path: Path to elastix installation (auto-detected if None)
    
    Returns:
        Dictionary with success rate and summary
    """
    
    print("🏥 AIMed Lab ADC-T2W Registration Pipeline")
    print(f"📁 Input directory: {patient_directory}")
    print(f"💾 Output directory: {output_directory}")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = ProstateADCRegistrationPipeline(
            elastix_installation_path=elastix_path
        )
        
        # Process all patients
        results = pipeline.process_patient_directory(
            base_directory=patient_directory,
            output_directory=output_directory,
            generate_report=True
        )
        
        # Extract summary
        batch_results = results['step_results']['PranavBatchProcessor']['result']
        summary = batch_results['summary']
        
        # Print results
        print("\n🎯 Registration Complete!")
        print(f"✅ Successful: {summary['successful_count']}")
        print(f"❌ Failed: {summary['failed_count']}")
        print(f"📊 Success Rate: {summary['success_rate']:.1%}")
        print(f"⏱️  Total Time: {results['metadata']['total_execution_time']:.1f} seconds")
        print(f"📋 Error log: {summary['error_log_path']}")
        print(f"📄 Full report: {output_directory}/registration_summary_report.json")
        
        # Show some successful cases
        if batch_results['successful']:
            print(f"\n✅ Successfully registered patients:")
            for patient in batch_results['successful'][:5]:  # Show first 5
                print(f"   - {patient}")
            if len(batch_results['successful']) > 5:
                print(f"   - ... and {len(batch_results['successful']) - 5} more")
        
        # Show some failed cases
        if batch_results['failed']:
            print(f"\n❌ Failed registrations:")
            for patient in batch_results['failed'][:3]:  # Show first 3
                print(f"   - {patient}")
            if len(batch_results['failed']) > 3:
                print(f"   - ... and {len(batch_results['failed']) - 3} more")
        
        return summary
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    # Example usage - UPDATE THESE PATHS!
    
    # Your data paths - CHANGE THESE
    PATIENT_DATA_DIR = "/Users/anish/Downloads/file_data"  # Your actual data directory
    RESULTS_DIR = "/Users/anish/file_data/registration_results"  # Where you want results
    ELASTIX_PATH = "/Users/anish/elastix-5"  # Your elastix installation
    
    # Run registration
    try:
        summary = register_adc_to_t2w_simple(
            patient_directory=PATIENT_DATA_DIR,
            output_directory=RESULTS_DIR,
            elastix_path=ELASTIX_PATH
        )
        
        print(f"\n🎉 Registration pipeline completed successfully!")
        print(f"📈 Final success rate: {summary['success_rate']:.1%}")
        
    except Exception as e:
        print(f"\n💥 Registration failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check that elastix is properly installed and accessible")
        print("2. Verify your data directory structure matches expected format")
        print("3. Ensure you have write permissions to the output directory")
        print("4. Check the log file for detailed error information")

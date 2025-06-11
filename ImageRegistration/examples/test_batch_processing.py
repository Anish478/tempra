# examples/test_batch_processing.py
#!/usr/bin/env python3
"""
Quick test to verify batch processing works
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_batch_discovery():
    """Test that we can discover patients"""
    from src.image_registration.pipeline.batch_preprocessing import PatientDiscoveryStep
    
    # Test data directory
    test_dir = "/path/to/your/data"  # UPDATE THIS
    
    step = PatientDiscoveryStep()
    results = step.execute({'base_directory': test_dir})
    
    print(f"Found {results['total_patients']} patients:")
    for patient in results['patients'][:5]:
        print(f"  - {patient['patient_id']}")
        print(f"    T2W: {Path(patient['t2w_path']).name}")
        print(f"    ADC: {Path(patient['adc_path']).name}")

if __name__ == "__main__":
    test_batch_discovery()
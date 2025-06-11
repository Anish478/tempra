#!/usr/bin/env python3
"""
Explore and validate prostate data structure
"""
from pathlib import Path
import sys

def explore_patient_data(data_directory: str, max_patients: int = 10):
    """
    Explore and validate the patient data structure
    
    Args:
        data_directory: Path to directory containing patient folders
        max_patients: Maximum number of patients to check in detail
    """
    
    data_path = Path(data_directory)
    
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_directory}")
        return []
    
    print(f"📁 Exploring data in: {data_directory}")
    print("=" * 70)
    
    # Find patient directories
    patient_dirs = [d for d in data_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    patient_dirs.sort()
    
    print(f"📊 Found {len(patient_dirs)} total directories")
    print()
    
    # Analyze patient data
    complete_patients = []
    incomplete_patients = []
    
    # Check first N patients in detail
    patients_to_check = patient_dirs[:max_patients]
    
    print(f"🔍 Checking first {len(patients_to_check)} patients in detail:")
    print("-" * 70)
    
    for patient_dir in patients_to_check:
        patient_id = patient_dir.name
        
        # Expected files
        adc_file = patient_dir / f"{patient_id}_adc.nii.gz"
        t2w_file = patient_dir / f"{patient_id}_t2w.nii.gz"
        
        # Check what files exist
        all_files = list(patient_dir.glob("*.nii.gz"))
        
        has_adc = adc_file.exists()
        has_t2w = t2w_file.exists()
        is_complete = has_adc and has_t2w
        
        status_emoji = "✅" if is_complete else "❌"
        status_text = "READY" if is_complete else "INCOMPLETE"
        
        print(f"{status_emoji} Patient {patient_id}: {status_text}")
        print(f"   📄 ADC: {'✅' if has_adc else '❌'} {adc_file.name}")
        print(f"   📄 T2W: {'✅' if has_t2w else '❌'} {t2w_file.name}")
        
        # Show other files
        other_files = [f.name for f in all_files if f not in [adc_file, t2w_file]]
        if other_files:
            print(f"   📋 Other files: {', '.join(other_files)}")
        
        print()
        
        if is_complete:
            complete_patients.append(patient_id)
        else:
            incomplete_patients.append(patient_id)
    
    # Quick check remaining patients
    if len(patient_dirs) > max_patients:
        print(f"🔍 Quick check of remaining {len(patient_dirs) - max_patients} patients...")
        
        for patient_dir in patient_dirs[max_patients:]:
            patient_id = patient_dir.name
            adc_file = patient_dir / f"{patient_id}_adc.nii.gz"
            t2w_file = patient_dir / f"{patient_id}_t2w.nii.gz"
            
            if adc_file.exists() and t2w_file.exists():
                complete_patients.append(patient_id)
            else:
                incomplete_patients.append(patient_id)
    
    # Summary
    print("=" * 70)
    print("📈 SUMMARY:")
    print(f"   🎯 Total patients analyzed: {len(patient_dirs)}")
    print(f"   ✅ Complete (ready for registration): {len(complete_patients)}")
    print(f"   ❌ Incomplete (missing files): {len(incomplete_patients)}")
    print(f"   📊 Completeness rate: {len(complete_patients)/len(patient_dirs):.1%}")
    
    if complete_patients:
        print(f"\n🚀 Ready for registration (first 10):")
        for patient in complete_patients[:10]:
            print(f"   - {patient}")
        if len(complete_patients) > 10:
            print(f"   - ... and {len(complete_patients) - 10} more")
    
    if incomplete_patients:
        print(f"\n⚠️  Incomplete patients (first 5):")
        for patient in incomplete_patients[:5]:
            print(f"   - {patient}")
        if len(incomplete_patients) > 5:
            print(f"   - ... and {len(incomplete_patients) - 5} more")
    
    print(f"\n💡 Next steps:")
    if complete_patients:
        print("   1. Test registration with a single patient first")
        print("   2. Run full batch processing when single test succeeds")
        print("   3. Use examples/simple_registration.py")
    else:
        print("   1. Check data directory structure")
        print("   2. Ensure files follow naming convention: {patientID}_{sequence}.nii.gz")
        print("   3. Verify file permissions and accessibility")
    
    return complete_patients

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python explore_data.py /path/to/patient/data")
        print("\nExample: python explore_data.py /Users/anish/file_data")
        sys.exit(1)
    
    data_directory = sys.argv[1]
    complete_patients = explore_patient_data(data_directory)
    
    print(f"\n🎯 Analysis complete!")
    if complete_patients:
        print(f"Ready to test with: {complete_patients[0]}")

# examples/batch_preprocessing.py
#!/usr/bin/env python3
"""
Batch preprocessing for all patients in a directory
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from image_registration.pipeline.batch_preprocessing import BatchPreprocessingPipeline

def main():
    parser = argparse.ArgumentParser(description='Batch preprocessing for medical images')
    parser.add_argument('input_dir', help='Directory containing patient folders')
    parser.add_argument('output_dir', help='Output directory for processed data')
    parser.add_argument('--registration', choices=['rigid', 'affine', 'bspline'], 
                       default='rigid', help='Registration type')
    parser.add_argument('--standardization', choices=['nyul', 'zscore'], 
                       default='nyul', help='Standardization method')
    parser.add_argument('--no-segmentation', action='store_true', 
                       help='Disable segmentation')
    parser.add_argument('--sequential', action='store_true', 
                       help='Process sequentially instead of parallel')
    parser.add_argument('--workers', type=int, default=4, 
                       help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path(args.output_dir) / 'preprocessing.log')
        ]
    )
    
    print("🏥 Batch Medical Image Preprocessing Pipeline")
    print(f"📁 Input directory: {args.input_dir}")
    print(f"💾 Output directory: {args.output_dir}")
    print(f"🔧 Registration: {args.registration}")
    print(f"📊 Standardization: {args.standardization}")
    print(f"🔍 Segmentation: {'Enabled' if not args.no_segmentation else 'Disabled'}")
    print(f"⚡ Parallel processing: {'Disabled' if args.sequential else f'Enabled ({args.workers} workers)'}")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = BatchPreprocessingPipeline(
        registration_type=args.registration,
        standardization_method=args.standardization,
        enable_segmentation=not args.no_segmentation,
        parallel_processing=not args.sequential,
        max_workers=args.workers
    )
    
    # Run pipeline
    try:
        results = pipeline.execute({
            'base_directory': args.input_dir,
            'output_directory': args.output_dir,
            'registration_type': args.registration,
            'standardization_method': args.standardization,
            'enable_segmentation': not args.no_segmentation
        })
        
        # Print summary
        batch_results = results['step_results'].get('BatchProcessingStep', {}).get('result', {})
        
        print("\n🎯 Batch Processing Complete!")
        print(f"✅ Successful: {len(batch_results.get('successful', []))}")
        print(f"❌ Failed: {len(batch_results.get('failed', []))}")
        
        if batch_results.get('successful'):
            print("\n✅ Successfully processed:")
            for patient in batch_results['successful'][:5]:
                print(f"   - {patient}")
            if len(batch_results['successful']) > 5:
                print(f"   - ... and {len(batch_results['successful']) - 5} more")
        
        if batch_results.get('failed'):
            print("\n❌ Failed to process:")
            for patient in batch_results['failed'][:5]:
                print(f"   - {patient}")
            if len(batch_results['failed']) > 5:
                print(f"   - ... and {len(batch_results['failed']) - 5} more")
        
        # Report locations
        reporting_results = results['step_results'].get('BatchReportingStep', {}).get('result', {})
        if reporting_results:
            print(f"\n📋 Reports saved to: {reporting_results['reports_directory']}")
            print(f"   - Summary: {Path(reporting_results['summary_path']).name}")
            print(f"   - Results CSV: {Path(reporting_results['csv_path']).name}")
        
        print("\n🎉 All processing complete!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        logging.exception("Pipeline failed")
        raise

if __name__ == "__main__":
    main()
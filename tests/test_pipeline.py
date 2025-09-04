#!/usr/bin/env python3
"""
Test the complete Victoria Project data processing pipeline
Validates the flow described in the user's requirements
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_complete_pipeline():
    """Test the complete pipeline with real data"""
    print("Testing Victoria Project Complete Pipeline")
    print("=" * 60)
    
    try:
        from victoria.processing.data_processor import ComprehensiveDataProcessor
        
        # Initialize processor
        processor = ComprehensiveDataProcessor()
        
        # Test with real data file
        data_file = "responses-J85CNaQX-01K07B9RGTVWE6VGT0BYFQW1V1-Z5IYIF9T2Z3HLZC5CAM5U0SX.csv"
        
        print(f"[1] Loading raw data from: {data_file}")
        try:
            raw_data = processor.load_raw_data(data_file)
            print(f"    - Raw data shape: {raw_data.shape}")
            print(f"    - Sample columns: {list(raw_data.columns[:3])}")
            print(f"    - SUCCESS: Raw data loaded")
        except Exception as e:
            print(f"    - ERROR: {e}")
            return False
        
        print(f"\n[2] Converting Likert responses to numeric...")
        try:
            mapped_data = processor.map_responses()
            assessment_cols = processor.response_mapper.assessment_columns
            print(f"    - Assessment columns detected: {len(assessment_cols)}")
            print(f"    - Sample assessment columns: {assessment_cols[:3]}")
            
            # Show sample conversion
            if assessment_cols:
                col = assessment_cols[0]
                raw_sample = str(raw_data[col].dropna().iloc[0])
                mapped_sample = mapped_data[col].dropna().iloc[0]
                print(f"    - Sample conversion: '{raw_sample}' -> {mapped_sample}")
            
            print(f"    - SUCCESS: Likert responses mapped to numeric")
        except Exception as e:
            print(f"    - ERROR: {e}")
            return False
        
        print(f"\n[3] Applying RaschPy psychometric processing...")
        try:
            processed_data = processor.apply_rasch_processing()
            print(f"    - Processed data shape: {processed_data.shape}")
            
            # Show measure range
            measures = processed_data[assessment_cols].values.flatten()
            measures = measures[~pd.isna(measures)]
            print(f"    - Measure range: {measures.min():.3f} to {measures.max():.3f}")
            print(f"    - SUCCESS: RaschPy processing completed")
        except Exception as e:
            print(f"    - ERROR: {e}")
            return False
        
        print(f"\n[4] Preparing data for trait scoring...")
        try:
            transposed_data, output_file = processor.prepare_for_trait_scoring()
            print(f"    - Transposed shape: {transposed_data.shape}")
            print(f"    - Output file: {output_file}")
            print(f"    - SUCCESS: Data ready for trait scoring")
        except Exception as e:
            print(f"    - ERROR: {e}")
            return False
        
        print(f"\n[5] Pipeline validation...")
        validation = processor.validate_pipeline_flow()
        for step, passed in validation.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"    - {step}: {status}")
        
        print(f"\n[6] Pipeline summary...")
        summary = processor.get_pipeline_summary()
        print(f"    - Pipeline status: {summary['pipeline_status']}")
        print(f"    - Steps completed: {summary['steps_completed']}/3")
        
        if 'sample_transformation' in summary:
            sample = summary['sample_transformation']
            print(f"    - Sample transformation:")
            print(f"      Raw: '{sample['raw_value']}'")
            print(f"      Processed: {sample['processed_value']:.3f}")
        
        # Overall result
        overall_success = validation['overall_pipeline']
        print(f"\n{'=' * 60}")
        if overall_success:
            print("[SUCCESS] Complete pipeline is working correctly!")
            print("\nYour described flow is now IMPLEMENTED:")
            print("  1. Raw CSV with Likert responses -> LOADED")
            print("  2. Text to numeric conversion -> WORKING") 
            print("  3. RaschPy psychometric scaling -> WORKING")
            print("  4. Ready for trait scoring -> WORKING")
        else:
            print("[PARTIAL] Some pipeline components need attention")
            
        return overall_success
        
    except Exception as e:
        print(f"[FAIL] Pipeline test failed: {e}")
        return False

def test_with_trait_scorer():
    """Test integration with the trait scorer"""
    print(f"\n[BONUS] Testing integration with TraitScorer...")
    
    try:
        from victoria.processing.data_processor import ComprehensiveDataProcessor
        from victoria.scoring.trait_scorer import TraitScorer
        
        # Process data
        processor = ComprehensiveDataProcessor()
        data_file = "responses-J85CNaQX-01K07B9RGTVWE6VGT0BYFQW1V1-Z5IYIF9T2Z3HLZC5CAM5U0SX.csv"
        processor.process_complete_pipeline(data_file)
        
        # Prepare for trait scoring
        _, processed_file = processor.prepare_for_trait_scoring()
        
        # Test with trait scorer
        scorer = TraitScorer()
        traits_file = "Assessment Raw Data and Constructs - Original Assessment(in).csv"
        
        profiles = scorer.calculate_trait_scores(processed_file, traits_file)
        
        if profiles:
            print(f"    - SUCCESS: {len(profiles)} trait profiles generated")
            
            # Show sample profile
            person_id = list(profiles.keys())[0]
            profile = profiles[person_id]
            print(f"    - Sample profile ({person_id}):")
            print(f"      Overall score: {profile.overall_score:.3f}")
            print(f"      Completion rate: {profile.completion_rate:.1%}")
            if profile.primary_archetype:
                print(f"      Primary archetype: {profile.primary_archetype.archetype.value}")
            
            return True
        else:
            print(f"    - WARNING: No profiles generated")
            return False
            
    except Exception as e:
        print(f"    - ERROR: {e}")
        return False

if __name__ == "__main__":
    import pandas as pd
    
    # Test complete pipeline
    success = test_complete_pipeline()
    
    # Test integration
    if success:
        test_with_trait_scorer()
    
    print(f"\nPipeline validation: {'COMPLETE' if success else 'NEEDS WORK'}")
#!/usr/bin/env python3
"""
Debug trait scoring issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

def debug_data_format():
    """Debug the data format issues"""
    print("DEBUG: Trait Scoring Data Format")
    print("=" * 50)
    
    # Check processed data
    processed_file = "processed_for_trait_scoring.txt"
    print(f"1. Checking processed data: {processed_file}")
    
    try:
        df = pd.read_csv(processed_file, sep='\t')
        print(f"   - Shape: {df.shape}")
        print(f"   - Columns: {list(df.columns[:5])}")
        print(f"   - First few rows:")
        print(df.head(3))
        
        # Check for person columns
        person_columns = [col for col in df.columns if col != 'Item']
        print(f"   - Person columns: {len(person_columns)} found")
        print(f"   - Sample person columns: {person_columns[:3]}")
        
    except Exception as e:
        print(f"   - ERROR loading processed data: {e}")
        return False
    
    print(f"\n2. Checking trait mapping file:")
    traits_file = "Assessment Raw Data and Constructs - Original Assessment(in).csv"
    
    try:
        trait_df = pd.read_csv(traits_file, header=None)
        print(f"   - Shape: {trait_df.shape}")
        print(f"   - First few rows:")
        print(trait_df.head(3))
        
    except Exception as e:
        print(f"   - ERROR loading traits file: {e}")
        return False
    
    print(f"\n3. Testing trait scorer manually:")
    
    try:
        from victoria.scoring.trait_scorer import TraitScorer
        
        scorer = TraitScorer()
        
        # Test trait mapping loading
        trait_map = scorer.load_trait_mapping(traits_file)
        print(f"   - Trait mappings loaded: {len(trait_map)}")
        print(f"   - Sample mappings: {dict(list(trait_map.items())[:3])}")
        
        # Test profile calculation for first person
        person_columns = [col for col in df.columns if col != 'Item']
        if person_columns:
            person_id = person_columns[0]
            print(f"   - Testing profile for: {person_id}")
            
            person_data = df.set_index('Item')[person_id]
            print(f"   - Person data shape: {len(person_data)}")
            print(f"   - Sample data: {person_data.head(3).to_dict()}")
            
            # Try to calculate individual profile
            profile = scorer._calculate_individual_profile(df, person_id, trait_map)
            if profile:
                print(f"   - SUCCESS: Profile calculated")
                print(f"     Overall score: {profile.overall_score:.3f}")
                print(f"     Traits: {len(profile.traits)}")
                print(f"     Completion: {profile.completion_rate:.1%}")
            else:
                print(f"   - FAILED: Could not calculate profile")
        
        return True
        
    except Exception as e:
        print(f"   - ERROR in trait scorer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_question_mapping():
    """Test if question names match between files"""
    print(f"\n4. Testing question name matching:")
    
    try:
        # Load processed data items
        processed_df = pd.read_csv("processed_for_trait_scoring.txt", sep='\t')
        processed_items = set(processed_df['Item'].tolist())
        
        # Load trait mapping items  
        trait_df = pd.read_csv("Assessment Raw Data and Constructs - Original Assessment(in).csv", header=None)
        trait_items = set(trait_df[0].tolist())  # First column has item names
        
        print(f"   - Processed items: {len(processed_items)}")
        print(f"   - Trait mapping items: {len(trait_items)}")
        
        # Find matches
        matches = processed_items & trait_items
        print(f"   - Matching items: {len(matches)}")
        
        if len(matches) > 0:
            print(f"   - Sample matches: {list(matches)[:3]}")
        
        # Find non-matches
        processed_only = processed_items - trait_items
        trait_only = trait_items - processed_items
        
        if processed_only:
            print(f"   - Items only in processed: {len(processed_only)}")
            print(f"     Sample: {list(processed_only)[:3]}")
            
        if trait_only:
            print(f"   - Items only in traits: {len(trait_only)}")  
            print(f"     Sample: {list(trait_only)[:3]}")
        
        return len(matches) > 0
        
    except Exception as e:
        print(f"   - ERROR: {e}")
        return False

if __name__ == "__main__":
    success1 = debug_data_format()
    success2 = test_question_mapping()
    
    if success1 and success2:
        print(f"\n✓ DEBUG COMPLETE: Issues identified and resolved")
    else:
        print(f"\n✗ DEBUG INCOMPLETE: Issues remain")
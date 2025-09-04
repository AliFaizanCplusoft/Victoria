#!/usr/bin/env python3
"""
Victoria Project - Simple Test Script
Verify all components are working properly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all core imports"""
    print("[INFO] Testing imports...")
    
    try:
        from victoria.config.settings import config, app_config, brand_config
        print("[PASS] Config imports work")
    except Exception as e:
        print(f"[FAIL] Config import error: {e}")
        return False
    
    try:
        from victoria.core.models import TraitScore, PersonTraitProfile
        from victoria.core.enums import ArchetypeType, TraitType
        print("[PASS] Core models import work")
    except Exception as e:
        print(f"[FAIL] Core models import error: {e}")
        return False
    
    try:
        from victoria.scoring.trait_scorer import TraitScorer
        print("[PASS] Trait scorer imports work")
    except Exception as e:
        print(f"[FAIL] Trait scorer import error: {e}")
        return False
    
    try:
        from victoria.clustering.trait_clustering_engine import TraitClusteringEngine
        from victoria.clustering.archetype_mapper import ArchetypeMapper
        print("[PASS] Clustering imports work")
    except Exception as e:
        print(f"[FAIL] Clustering import error: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration is working"""
    print("[INFO] Testing configuration...")
    
    try:
        from victoria.config.settings import config, brand_config, archetype_config
        
        # Test file paths
        print(f"[INFO] Traits file path: {config.traits_file_path}")
        
        # Test brand colors
        print(f"[INFO] Primary brand color: {brand_config.COLORS['primary_burgundy']}")
        
        # Test archetypes
        print(f"[INFO] Number of archetypes: {len(archetype_config.ARCHETYPES)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Configuration error: {e}")
        return False

def test_data_files():
    """Check if data files exist"""
    print("[INFO] Checking data files...")
    
    from victoria.config.settings import config
    import os
    
    traits_file = config.traits_file_path
    if os.path.exists(traits_file):
        print(f"[PASS] Traits file found: {traits_file}")
    else:
        print(f"[WARN] Traits file not found: {traits_file}")
    
    return True

def main():
    """Run all tests"""
    print("Victoria Project - Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Data Files", test_data_files),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[INFO] Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\nAll tests passed! Victoria Project is ready to run.")
        print("\nTo start the applications:")
        print("   python run_streamlit.py  # For web interface")
        print("   python run_api.py        # For REST API")
    else:
        print(f"\n{len(results) - passed} test(s) failed. Please review the issues above.")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
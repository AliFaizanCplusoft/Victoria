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
        print("✅ Config imports work")
    except Exception as e:
        print(f"❌ Config import error: {e}")
        return False
    
    try:
        from victoria.core.models import TraitScore, PersonTraitProfile
        from victoria.core.enums import ArchetypeType, TraitType
        print("✅ Core models import work")
    except Exception as e:
        print(f"❌ Core models import error: {e}")
        return False
    
    try:
        from victoria.scoring.trait_scorer import TraitScorer
        print("✅ Trait scorer imports work")
    except Exception as e:
        print(f"❌ Trait scorer import error: {e}")
        return False
    
    try:
        from victoria.clustering.trait_clustering_engine import TraitClusteringEngine
        from victoria.clustering.archetype_mapper import ArchetypeMapper
        print("✅ Clustering imports work")
    except Exception as e:
        print(f"❌ Clustering import error: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration is working"""
    print("⚙️ Testing configuration...")
    
    try:
        from victoria.config.settings import config, brand_config, archetype_config
        
        # Test file paths
        print(f"📁 Traits file path: {config.traits_file_path}")
        
        # Test brand colors
        print(f"🎨 Primary brand color: {brand_config.COLORS['primary_burgundy']}")
        
        # Test archetypes
        print(f"🏆 Number of archetypes: {len(archetype_config.ARCHETYPES)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("🧪 Testing basic functionality...")
    
    try:
        from victoria.scoring.trait_scorer import TraitScorer
        from victoria.clustering.trait_clustering_engine import TraitClusteringEngine
        
        # Initialize components
        scorer = TraitScorer()
        clustering_engine = TraitClusteringEngine()
        
        print("✅ Basic components initialize successfully")
        return True
        
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        return False

def test_data_files():
    """Check if data files exist"""
    print("📄 Checking data files...")
    
    from victoria.config.settings import config
    import os
    
    traits_file = config.traits_file_path
    if os.path.exists(traits_file):
        print(f"✅ Traits file found: {traits_file}")
    else:
        print(f"⚠️ Traits file not found: {traits_file}")
    
    return True

def test_app_structure():
    """Check if app structure exists"""
    print("🏗️ Checking app structure...")
    
    streamlit_app = project_root / "app" / "streamlit" / "main.py"
    api_app = project_root / "app" / "api" / "main.py"
    
    if streamlit_app.exists():
        print("✅ Streamlit app found")
    else:
        print("❌ Streamlit app not found")
    
    if api_app.exists():
        print("✅ API app found")
    else:
        print("❌ API app not found")
    
    return streamlit_app.exists() and api_app.exists()

def main():
    """Run all tests"""
    print("🚀 Victoria Project - Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Basic Functionality", test_basic_functionality), 
        ("Data Files", test_data_files),
        ("App Structure", test_app_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Victoria Project is ready to run.")
        print("\n🚀 To start the applications:")
        print("   python run_streamlit.py  # For web interface")
        print("   python run_api.py        # For REST API")
        print("   python victoria_project.py streamlit  # Main launcher")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed. Please review the issues above.")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
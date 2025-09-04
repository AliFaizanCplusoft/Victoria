#!/usr/bin/env python3
"""
Run the fixed Streamlit app
"""

import subprocess
import sys
import os
from pathlib import Path

# Import configuration
from config import config

def run_streamlit_app():
    """Run the corrected Streamlit app"""
    
    print("🚀 Starting Fixed Streamlit App")
    print("=" * 40)
    
    # Check if required files exist
    required_files = [
        config.get_file_path("streamlit_app.py"),
        config.traits_file_path,
        config.responses_file_path
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ ERROR: Required file not found: {file_path}")
            return False
    
    print("✅ All required files found")
    
    # Change to the project directory
    os.chdir("/mnt/d/Victoria_Project")
    
    # Run streamlit
    try:
        print("\n🌟 Starting Streamlit app...")
        print("📖 The app will be available at: http://localhost:8501")
        print("\n💡 FIXES APPLIED:")
        print("   - Fixed 'list' object has no attribute 'describe' error")
        print("   - Fixed 'builtin_function_or_method' object has no attribute 'tolist' error")
        print("   - Updated data processing to use correct file paths")
        print("   - Converted scoring results to DataFrame format")
        print("\n🎯 EXPECTED BEHAVIOR:")
        print("   - Group Analysis should now display statistics without errors")
        print("   - Individual Analysis should show person selection dropdown")
        print("   - Assessment_Items should show proper item codes (EnergizedByPotential, etc.)")
        print("   - Scoring Results should display trait scores correctly")
        print("\n" + "="*50)
        
        # Run streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py", 
            "--server.headless", "true",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Streamlit failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped by user")
        return True
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_streamlit_app()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Victoria Project Setup Script
Comprehensive assessment analysis system with RaschPy integration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print setup header."""
    print("=" * 60)
    print("Victoria Project - Assessment Analysis System Setup")
    print("=" * 60)
    print("Setting up comprehensive RaschPy integration system...")
    print()

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9 or higher is required!")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_requirements():
    """Install Python requirements."""
    print("\n📦 Installing Python requirements...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        # Install regular requirements
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Basic requirements installed")
        
        # Install RaschPy separately
        print("🔬 Installing RaschPy from GitHub...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "git+https://github.com/MarkElliott999/RaschPy.git"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ RaschPy installed successfully")
        else:
            print("⚠️  RaschPy installation failed, but system can still work without it")
            print(f"Error: {result.stderr}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_directories():
    """Create necessary directories."""
    print("\n📁 Setting up directories...")
    
    directories = [
        "temp/uploads",
        "temp/processing",
        "output/reports",
        "output/individual_profiles",
        "logs",
        "templates/html"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    return True

def install_wkhtmltopdf():
    """Install wkhtmltopdf for PDF generation."""
    print("\n📄 Setting up PDF generation...")
    
    system = platform.system().lower()
    
    if system == "windows":
        print("🪟 Windows detected")
        print("Please install wkhtmltopdf manually:")
        print("1. Download from: https://wkhtmltopdf.org/downloads.html")
        print("2. Install to default location")
        print("3. The system will auto-detect the installation")
        
    elif system == "darwin":  # macOS
        print("🍎 macOS detected")
        print("Installing wkhtmltopdf via Homebrew...")
        try:
            subprocess.run(["brew", "install", "wkhtmltopdf"], check=True)
            print("✅ wkhtmltopdf installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Homebrew not found. Please install manually:")
            print("1. Install Homebrew: https://brew.sh/")
            print("2. Run: brew install wkhtmltopdf")
    
    elif system == "linux":
        print("🐧 Linux detected")
        print("Installing wkhtmltopdf...")
        try:
            # Try apt-get first (Ubuntu/Debian)
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "wkhtmltopdf"], check=True)
            print("✅ wkhtmltopdf installed")
        except subprocess.CalledProcessError:
            try:
                # Try yum (CentOS/RHEL)
                subprocess.run(["sudo", "yum", "install", "-y", "wkhtmltopdf"], check=True)
                print("✅ wkhtmltopdf installed")
            except subprocess.CalledProcessError:
                print("⚠️  Auto-installation failed. Please install manually:")
                print("Ubuntu/Debian: sudo apt-get install wkhtmltopdf")
                print("CentOS/RHEL: sudo yum install wkhtmltopdf")
    
    return True

def create_sample_data():
    """Create sample data for testing."""
    print("\n📊 Creating sample data...")
    
    sample_data = """Please enter your prolific ID,EnergizedByPotential,EagertoPursue,PursuePerfection,DetailOriented,PersistentDrive
6728f3d973b4504d88a81299,Often (66-90%),Always (91-100%),Sometimes (36-65%),Often (66-90%),Always (91-100%)
56888951d7848e000c39a122,Sometimes (36-65%),Often (66-90%),Always (91-100%),Sometimes (36-65%),Often (66-90%)
6234a0a4e9db36c0d8336627,Always (91-100%),Sometimes (36-65%),Often (66-90%),Always (91-100%),Sometimes (36-65%)
"""
    
    sample_file = Path("sample_data.csv")
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_data)
    
    print(f"✅ Sample data created: {sample_file}")
    return True

def test_installation():
    """Test the installation."""
    print("\n🧪 Testing installation...")
    
    # Test imports
    try:
        from src.data.data_ingestion import PsychometricDataProcessor
        print("✅ Data ingestion module imported")
        
        from src.data.rasch_analysis import RaschAnalyzer
        print("✅ Rasch analysis module imported")
        
        from src.reports.multi_format_report_generator import MultiFormatReportGenerator
        print("✅ Report generation module imported")
        
        import streamlit
        print("✅ Streamlit imported")
        
        # Test basic functionality
        processor = PsychometricDataProcessor()
        print("✅ Data processor initialized")
        
        analyzer = RaschAnalyzer()
        print("✅ Rasch analyzer initialized")
        
        generator = MultiFormatReportGenerator()
        print("✅ Report generator initialized")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def create_run_scripts():
    """Create convenient run scripts."""
    print("\n📝 Creating run scripts...")
    
    # Streamlit run script
    streamlit_script = """#!/bin/bash
# Victoria Project - Streamlit Dashboard
echo "Starting Victoria Project Streamlit Dashboard..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
"""
    
    # FastAPI run script
    fastapi_script = """#!/bin/bash
# Victoria Project - FastAPI Server
echo "Starting Victoria Project FastAPI Server..."
python main.py --server --host 0.0.0.0 --port 8000
"""
    
    # Windows batch files
    streamlit_bat = """@echo off
echo Starting Victoria Project Streamlit Dashboard...
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
pause
"""
    
    fastapi_bat = """@echo off
echo Starting Victoria Project FastAPI Server...
python main.py --server --host 0.0.0.0 --port 8000
pause
"""
    
    # Write scripts
    with open("run_streamlit.sh", "w") as f:
        f.write(streamlit_script)
    os.chmod("run_streamlit.sh", 0o755)
    
    with open("run_fastapi.sh", "w") as f:
        f.write(fastapi_script)
    os.chmod("run_fastapi.sh", 0o755)
    
    with open("run_streamlit.bat", "w") as f:
        f.write(streamlit_bat)
    
    with open("run_fastapi.bat", "w") as f:
        f.write(fastapi_bat)
    
    print("✅ Run scripts created")
    return True

def print_completion_message():
    """Print completion message with instructions."""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Victoria Project is now ready to use!")
    print()
    print("🚀 QUICK START:")
    print("1. Streamlit Dashboard:")
    print("   streamlit run streamlit_app.py")
    print("   or run: ./run_streamlit.sh (Linux/Mac) or run_streamlit.bat (Windows)")
    print()
    print("2. FastAPI Server:")
    print("   python main.py --server")
    print("   or run: ./run_fastapi.sh (Linux/Mac) or run_fastapi.bat (Windows)")
    print()
    print("3. Command Line Processing:")
    print("   python main.py --file sample_data.csv")
    print()
    print("📁 IMPORTANT DIRECTORIES:")
    print("   • Input data: Place CSV files in root directory")
    print("   • Output reports: output/reports/")
    print("   • Individual profiles: output/individual_profiles/")
    print("   • Logs: logs/")
    print()
    print("🔗 ENDPOINTS:")
    print("   • Streamlit Dashboard: http://localhost:8501")
    print("   • FastAPI Server: http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/docs")
    print()
    print("📖 FEATURES:")
    print("   ✅ Raw CSV data processing")
    print("   ✅ RaschPy integration")
    print("   ✅ Interactive Streamlit dashboard")
    print("   ✅ Multi-format reports (HTML, PDF, CSV, JSON)")
    print("   ✅ Individual profile generation")
    print("   ✅ Group summary analysis")
    print("   ✅ Real-time data validation")
    print()
    print("📚 For more information, see README.md or the documentation.")
    print("=" * 60)

def main():
    """Main setup function."""
    print_header()
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install requirements
    if success and not install_requirements():
        success = False
    
    # Setup directories
    if success and not setup_directories():
        success = False
    
    # Install wkhtmltopdf
    if success:
        install_wkhtmltopdf()
    
    # Create sample data
    if success and not create_sample_data():
        success = False
    
    # Test installation
    if success and not test_installation():
        success = False
    
    # Create run scripts
    if success and not create_run_scripts():
        success = False
    
    if success:
        print_completion_message()
        return 0
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
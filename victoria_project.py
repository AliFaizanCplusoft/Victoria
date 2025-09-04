#!/usr/bin/env python3
"""
Victoria Project - Main Entry Point
Unified launcher for both Streamlit and API applications
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_streamlit():
    """Run Streamlit application"""
    print("🚀 Starting Victoria Project Streamlit Application...")
    
    import subprocess
    app_path = project_root / "app" / "streamlit" / "main.py"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(app_path),
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    
    print("🌐 Streamlit URL: http://localhost:8501")
    return subprocess.run(cmd).returncode

def run_api():
    """Run FastAPI application"""
    print("🚀 Starting Victoria Project API...")
    
    sys.path.insert(0, str(project_root / "app" / "api"))
    from main import main as api_main
    
    print("🌐 API URL: http://localhost:8000")
    print("📚 Docs URL: http://localhost:8000/docs")
    
    api_main()

def show_info():
    """Show project information"""
    print("""
🏢 Victoria Project - Psychometric Assessment Analysis System

📊 Features:
  • Individual psychometric analysis
  • Trait clustering with archetype mapping
  • Vertria's 5 entrepreneurial archetypes
  • Professional branded reports
  • REST API for integration

🚀 Usage:
  python victoria_project.py streamlit  # Run web interface
  python victoria_project.py api        # Run REST API  
  python victoria_project.py --help     # Show this help

🎯 Vertria Entrepreneurial Archetypes:
  • Strategic Innovation
  • Resilient Leadership  
  • Collaborative Responsibility
  • Ambitious Drive
  • Adaptive Intelligence

📁 Clean Architecture:
  victoria/           # Core business logic
  ├── config/         # Configuration management
  ├── core/           # Domain models & types
  ├── scoring/        # Psychometric scoring
  ├── clustering/     # Trait clustering & archetypes
  └── utils/          # Shared utilities
  
  app/                # Application layer
  ├── streamlit/      # Web interface
  └── api/            # REST API

📧 For support: Check project documentation
""")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Victoria Project - Psychometric Assessment Analysis"
    )
    
    parser.add_argument(
        "mode",
        choices=["streamlit", "api", "info"],
        nargs="?",
        default="info",
        help="Application mode to run"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "streamlit":
            return run_streamlit()
        elif args.mode == "api":
            run_api()
            return 0
        else:
            show_info()
            return 0
            
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
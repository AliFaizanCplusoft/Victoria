#!/usr/bin/env python3
"""
Simple script to run the Victoria API without file watching
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the API
from app.api.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting Victoria Assessment API...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable file watching to avoid the change detection issue
        log_level="info"
    )

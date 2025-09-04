#!/usr/bin/env python3
"""
API launcher script for Victoria Project - Psychometric Assessment API
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging(log_level: str = "INFO"):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'api.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    return logger

def check_dependencies():
    """
    Check if required dependencies are installed.
    
    Returns:
        bool: True if all dependencies are available
    """
    required_packages = [
        'fastapi',
        'uvicorn',
        'pandas',
        'numpy',
        'sklearn',
        'plotly',
        'matplotlib',
        'seaborn',
        'jinja2',
        'pydantic',
        'aiofiles',
        'python_multipart'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements_api.txt")
        return False
    
    return True

def create_directories():
    """Create necessary directories for the API."""
    directories = [
        "logs",
        "temp",
        "temp/uploads",
        "temp/processing",
        "output",
        "output/reports",
        "output/profiles"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Created necessary directories in: {project_root}")

def main():
    """Main function to start the API server."""
    parser = argparse.ArgumentParser(
        description="Victoria Project - Psychometric Assessment API Server"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
        default="INFO",
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--check-deps", 
        action="store_true", 
        help="Check dependencies and exit"
    )
    parser.add_argument(
        "--setup-only", 
        action="store_true", 
        help="Setup directories and exit"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_deps:
        print("All dependencies are installed!")
        sys.exit(0)
    
    # Create directories
    create_directories()
    
    if args.setup_only:
        print("Setup completed!")
        sys.exit(0)
    
    # Import and start the API
    try:
        import uvicorn
        from api.main import app
        
        logger.info(f"Starting Victoria Project API on {args.host}:{args.port}")
        logger.info(f"Documentation available at: http://{args.host}:{args.port}/docs")
        logger.info(f"Health check available at: http://{args.host}:{args.port}/api/v1/health")
        
        # Run the server
        if args.reload:
            # For reload mode, use string import
            uvicorn.run(
                "api.main:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                log_level=args.log_level.lower(),
                access_log=True,
                server_header=False,
                date_header=False
            )
        else:
            # For production mode, use app instance
            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                workers=args.workers,
                log_level=args.log_level.lower(),
                access_log=True,
                server_header=False,
                date_header=False
            )
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please ensure all dependencies are installed: pip install -r requirements_api.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
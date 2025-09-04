"""
Configuration module for Victoria Project
Centralizes all file paths and configuration settings
"""
import os
from pathlib import Path

# Base paths configuration
def get_base_data_path():
    """Get the base data path based on environment"""
    if os.environ.get("DOCKER_ENV") == "production":
        return "/app/data_writable"
    elif os.environ.get("DOCKER_ENV") == "development":
        return "/app/data"
    else:
        # Local development environment
        return str(Path(__file__).parent.absolute())

# File names configuration
class FileConfig:
    """Configuration for file names and paths"""
    
    # Base paths
    BASE_DATA_PATH = get_base_data_path()
    
    # Input file names (configurable via environment variables)
    TRAITS_FILE_NAME = os.environ.get(
        "TRAITS_FILE_NAME", 
        "Assessment Raw Data and Constructs - Original Assessment(in).csv"
    )
    
    # Default sample file name - can be overridden via environment variable
    RESPONSES_FILE_NAME = os.environ.get(
        "RESPONSES_FILE_NAME",
        "responses-J85CNaQX-01K07B9RGTVWE6VGT0BYFQW1V1-Z5IYIF9T2Z3HLZC5CAM5U0SX.csv"
    )
    
    # Output file names
    OUTPUT_FILE_NAME = os.environ.get("OUTPUT_FILE_NAME", "processed_output.txt")
    
    # Full paths
    @property
    def traits_file_path(self):
        return os.path.join(self.BASE_DATA_PATH, self.TRAITS_FILE_NAME)
    
    @property
    def responses_file_path(self):
        return os.path.join(self.BASE_DATA_PATH, self.RESPONSES_FILE_NAME)
    
    @property
    def output_file_path(self):
        return os.path.join(self.BASE_DATA_PATH, self.OUTPUT_FILE_NAME)
    
    def get_file_path(self, filename):
        """Get full path for any file in the data directory"""
        return os.path.join(self.BASE_DATA_PATH, filename)

# Global configuration instance
config = FileConfig()
"""
Configuration module for Victoria Project
Centralizes all file paths and configuration settings
"""
import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (override=True forces .env to take precedence)
load_dotenv(override=True)

# Setup logging
logger = logging.getLogger(__name__)

# Vertria Brand Configuration
class BrandConfig:
    """Vertria brand guidelines and styling configuration"""
    
    # Color Palette
    COLORS = {
        'primary_burgundy': '#570F27',
        'dark_blue': '#151A4A', 
        'accent_yellow': '#FFDC58',
        'deep_burgundy': '#240610',
        'white': '#FFFFFF',
        'light_gray': '#F8F9FA'
    }
    
    # Typography
    FONTS = {
        'header': 'Blair ITC, serif',
        'body': 'Outfit, sans-serif',
        'monospace': 'Monaco, monospace'
    }
    
    # Brand Voice
    BRAND_VOICE = {
        'tone': 'confident, purposeful, empowering',
        'focus': 'growth, mentorship, leadership',
        'style': 'professional yet approachable'
    }

# Base paths configuration
def get_base_data_path() -> str:
    """Get the base data path based on environment"""
    if os.environ.get("DOCKER_ENV") == "production":
        return "/app/data_writable"
    elif os.environ.get("DOCKER_ENV") == "development":
        return "/app/data"
    else:
        # Local development environment
        return str(Path(__file__).parent.parent.parent.absolute())

# Vertria Entrepreneurial Archetypes Configuration
class ArchetypeConfig:
    """Configuration for the 5 Entrepreneurial Archetypes"""
    
    ARCHETYPES = {
        'strategic_innovation': {
            'name': 'Strategic Innovation',
            'core_traits': ['Risk Taking', 'Innovation', 'Critical Thinking', 'Decision Making'],
            'description': 'Calculated risk-takers who use strategic thinking to guide innovation',
            'characteristics': ['Strategic planners', 'Calculated decision-makers', 'Innovation-focused'],
            'color': BrandConfig.COLORS['primary_burgundy']
        },
        'resilient_leadership': {
            'name': 'Resilient Leadership',
            'core_traits': ['Leadership', 'Resilience', 'Adaptability', 'Conflict Resolution'],
            'description': 'Leaders who navigate setbacks and interpersonal challenges',
            'characteristics': ['Team builders', 'Crisis managers', 'Adaptive leaders'],
            'color': BrandConfig.COLORS['dark_blue']
        },
        'collaborative_responsibility': {
            'name': 'Collaborative Responsibility', 
            'core_traits': ['Accountability', 'Team Building', 'Servant Leadership'],
            'description': 'Focus on team growth, ownership, and trust-building',
            'characteristics': ['Team-oriented', 'Responsible', 'Trust-builders'],
            'color': BrandConfig.COLORS['accent_yellow']
        },
        'ambitious_drive': {
            'name': 'Ambitious Drive',
            'core_traits': ['Passion/Drive', 'Resilience', 'Problem Solving', 'Ambition'],
            'description': 'Highly motivated individuals who persevere through challenges',
            'characteristics': ['Goal-driven', 'Persistent', 'Solution-oriented'],
            'color': BrandConfig.COLORS['deep_burgundy']
        },
        'adaptive_intelligence': {
            'name': 'Adaptive Intelligence',
            'core_traits': ['Critical Thinking', 'Problem Solving', 'Emotional Intelligence', 'Adaptability'],
            'description': 'Logical problem-solvers who understand team/customer needs',
            'characteristics': ['Analytical', 'Empathetic', 'Flexible', 'Customer-focused'],
            'color': BrandConfig.COLORS['primary_burgundy']
        }
    }

# Core trait definitions
class TraitConfig:
    """Configuration for the 11 core traits"""
    
    CORE_TRAITS = [
        'Risk Taking',
        'Innovation', 
        'Leadership',
        'Resilience',
        'Accountability',
        'Decision Making',
        'Adaptability',
        'Continuous Learning',
        'Passion/Drive',
        'Problem Solving',
        'Emotional Intelligence'
    ]

# File configuration
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
    
    # Report templates
    HTML_TEMPLATE_DIR = "templates"
    PDF_OUTPUT_DIR = "output"
    
    # Full paths
    @property
    def traits_file_path(self) -> str:
        return os.path.join(self.BASE_DATA_PATH, self.TRAITS_FILE_NAME)
    
    @property
    def responses_file_path(self) -> str:
        return os.path.join(self.BASE_DATA_PATH, self.RESPONSES_FILE_NAME)
    
    @property
    def output_file_path(self) -> str:
        return os.path.join(self.BASE_DATA_PATH, self.OUTPUT_FILE_NAME)
    
    def get_file_path(self, filename: str) -> str:
        """Get full path for any file in the data directory"""
        return os.path.join(self.BASE_DATA_PATH, filename)

# Application configuration
class AppConfig:
    """Application-wide configuration"""
    
    # Environment
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    
    # API Configuration
    API_HOST = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT = int(os.environ.get("API_PORT", "8000"))
    
    # Streamlit Configuration
    STREAMLIT_HOST = os.environ.get("STREAMLIT_HOST", "0.0.0.0")
    STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))
    
    # LLM Configuration
    ENABLE_LLM_REPORTS = os.environ.get("ENABLE_LLM_REPORTS", "true").lower() == "true"
    LLM_CACHE_ENABLED = os.environ.get("LLM_CACHE_ENABLED", "true").lower() == "true"
    LLM_RATE_LIMIT = int(os.environ.get("LLM_RATE_LIMIT", "60"))
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
    OPENAI_MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", "2000"))
    OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))

# Global configuration instances
config = FileConfig()
app_config = AppConfig()
brand_config = BrandConfig()
archetype_config = ArchetypeConfig()
trait_config = TraitConfig()
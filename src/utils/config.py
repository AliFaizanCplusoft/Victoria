"""Application configuration"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "Psychometric Reporting Pipeline"
    debug: bool = True
    database_url: str = "postgresql://user:pass@localhost:5432/psychometric_db"
    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = ""
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()

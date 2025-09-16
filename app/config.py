"""
Configuration management for the debate bot application.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str
    
    # Database
    database_url: str = "sqlite:///./conversations.db"
    
    # Service URLs
    openai_base_url: str = "https://api.openai.com/v1"
    postman_collection_url: Optional[str] = None
    swagger_docs_url: str = "http://localhost:8000/docs"
    base_url: str = "http://localhost:8000"
    api_base_url: str = "http://localhost:8000"
    
    # Performance & Limits
    max_response_time: int = 30
    max_message_length: int = 5000
    rate_limit_per_minute: int = 100
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay_seconds: int = 1
    openai_timeout_seconds: int = 25
    
    # Logging
    log_level: str = "INFO"
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_settings() -> Settings:
    """
    Load settings based on environment.
    Automatically loads .env.dev for development or .env.prod for production.
    """
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        load_dotenv(".env.prod")
    else:
        load_dotenv(".env.dev")
    
    return Settings()


# Global settings instance
settings = load_settings()
"""
Enterprise Configuration Management for the LLM Document Intelligence System.

This module provides a robust and secure way to manage application settings.
It uses Pydantic's BaseSettings to load configuration from environment variables
and a .env file, ensuring that the application is easy to configure and deploy
in different environments (development, staging, production).

Key Features:
- Environment-aware settings (development, staging, production).
- Validation of critical settings to prevent misconfiguration.
- Centralized access to all configuration parameters.
- Secure handling of secrets and credentials.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from functools import lru_cache

class ApplicationSettings(BaseSettings):
    """
    Defines the application's configuration settings, loaded from environment
    variables and a .env file. Provides validation and convenient access methods.
    """
    
    # --- General Application Settings ---
    APP_NAME: str = "LLM Document Intelligence System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # --- Server Settings ---
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # --- Security Settings ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a-secure-secret-key-that-you-must-change")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # --- CORS (Cross-Origin Resource Sharing) Settings ---
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-production-domain.com"
    ]
    
    # --- Database Settings ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/document_intelligence"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # --- Redis Settings ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # --- Azure OpenAI Settings ---
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-turbo")
    
    # --- Azure Document Intelligence Settings ---
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    
    # --- File Upload Settings ---
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_FILE_EXTENSIONS: List[str] = [".pdf", ".docx", ".jpg", ".png"]
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "/tmp/uploads")

    # --- Validators ---
    # Pydantic validators ensure that critical settings meet specific criteria.

    @validator("ENVIRONMENT")
    def validate_environment(cls, value):
        if value not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of 'development', 'staging', or 'production'")
        return value

    @validator("SECRET_KEY")
    def validate_secret_key(cls, value, values):
        if values.get("ENVIRONMENT") == "production" and value == "a-secure-secret-key-that-you-must-change":
            raise ValueError("SECRET_KEY must be changed in a production environment")
        return value

    # --- Helper Properties and Methods ---

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def get_database_config(self) -> dict:
        """Returns a dictionary of database connection pool settings."""
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
        }

    class Config:
        env_file = ".env"
        case_sensitive = True

# --- Environment-Specific Settings ---

class DevelopmentSettings(ApplicationSettings):
    """Settings for the development environment."""
    DEBUG: bool = True

class ProductionSettings(ApplicationSettings):
    """Settings for the production environment."""
    DEBUG: bool = False

@lru_cache()
def get_settings() -> ApplicationSettings:
    """
    Factory function to get the appropriate settings object based on the
    ENVIRONMENT variable. Uses lru_cache to ensure settings are loaded only once.
    """
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return ProductionSettings()
    return DevelopmentSettings()

# --- Global Settings Instance ---
# This instance is imported and used throughout the application.
settings = get_settings()

# --- Logging Configuration ---
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO" if settings.is_production else "DEBUG",
        },
    },
}
"""
Enterprise configuration management for LLM Document Intelligence System.
Environment-aware configuration with validation and security features.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    # Application settings
    APP_NAME: str = "LLM Document Intelligence System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-domain.com"
    ]
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "your-domain.com"
    ]
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/document_intelligence"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-turbo")
    AZURE_OPENAI_MODEL_NAME: str = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4-turbo")
    AZURE_OPENAI_MAX_TOKENS: int = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4000"))
    AZURE_OPENAI_TEMPERATURE: float = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.1"))
    
    # Azure Document Intelligence settings
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    AZURE_DOCUMENT_INTELLIGENCE_API_VERSION: str = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_VERSION", "2023-07-31")
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "50")) * 1024 * 1024  # 50MB in bytes
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".doc", ".txt", ".rtf",
        ".jpg", ".jpeg", ".png", ".tiff", ".bmp"
    ]
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "/tmp/uploads")
    
    # Processing settings
    DEFAULT_CONFIDENCE_THRESHOLD: float = float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.8"))
    MAX_CONCURRENT_PROCESSING: int = int(os.getenv("MAX_CONCURRENT_PROCESSING", "5"))
    PROCESSING_TIMEOUT_SECONDS: int = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "300"))
    
    # Cache settings
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # Monitoring and logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8001"))
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
    
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "200"))
    
    # Background task settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        if values.get("ENVIRONMENT") == "production" and v == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production environment")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("AZURE_OPENAI_API_KEY")
    def validate_azure_openai_key(cls, v, values):
        if values.get("ENVIRONMENT") != "development" and not v:
            raise ValueError("AZURE_OPENAI_API_KEY is required in non-development environments")
        return v
    
    @validator("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    def validate_azure_doc_intelligence_key(cls, v, values):
        if values.get("ENVIRONMENT") != "development" and not v:
            raise ValueError("AZURE_DOCUMENT_INTELLIGENCE_KEY is required in non-development environments")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must be a Redis URL")
        return v
    
    @validator("ALLOWED_ORIGINS")
    def validate_allowed_origins(cls, v, values):
        if values.get("ENVIRONMENT") == "production":
            # Remove localhost origins in production
            return [origin for origin in v if "localhost" not in origin and "127.0.0.1" not in origin]
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT == "staging"
    
    def get_database_config(self) -> dict:
        """Get database configuration for SQLAlchemy."""
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "pool_recycle": 3600,  # 1 hour
            "pool_pre_ping": True,
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis configuration."""
        return {
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "socket_timeout": self.REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": self.REDIS_SOCKET_TIMEOUT,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }
    
    def get_azure_openai_config(self) -> dict:
        """Get Azure OpenAI configuration."""
        return {
            "api_key": self.AZURE_OPENAI_API_KEY,
            "api_base": self.AZURE_OPENAI_ENDPOINT,
            "api_version": self.AZURE_OPENAI_API_VERSION,
            "deployment_name": self.AZURE_OPENAI_DEPLOYMENT_NAME,
            "model_name": self.AZURE_OPENAI_MODEL_NAME,
            "max_tokens": self.AZURE_OPENAI_MAX_TOKENS,
            "temperature": self.AZURE_OPENAI_TEMPERATURE,
        }
    
    def get_azure_document_intelligence_config(self) -> dict:
        """Get Azure Document Intelligence configuration."""
        return {
            "key": self.AZURE_DOCUMENT_INTELLIGENCE_KEY,
            "endpoint": self.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            "api_version": self.AZURE_DOCUMENT_INTELLIGENCE_API_VERSION,
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Development settings override
class DevelopmentSettings(Settings):
    """Development-specific settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    WORKERS: int = 1
    
    # Use SQLite for development if no PostgreSQL URL provided
    @validator("DATABASE_URL", pre=True)
    def dev_database_url(cls, v):
        if v == "postgresql+asyncpg://postgres:password@localhost:5432/document_intelligence":
            return "sqlite+aiosqlite:///./dev_database.db"
        return v


# Production settings override
class ProductionSettings(Settings):
    """Production-specific settings."""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    @validator("SECRET_KEY")
    def prod_secret_key(cls, v):
        if v == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production")
        return v


# Staging settings override
class StagingSettings(Settings):
    """Staging-specific settings."""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Get settings based on environment with caching."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "development":
        return DevelopmentSettings()
    elif env == "staging":
        return StagingSettings()
    elif env == "production":
        return ProductionSettings()
    else:
        return Settings()


# Global settings instance
settings = get_settings()

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "detailed": {
            "formatter": "detailed",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": settings.LOG_LEVEL,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["detailed"] if settings.is_development else ["default"],
            "level": "INFO" if settings.is_development else "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["default"],
    },
}
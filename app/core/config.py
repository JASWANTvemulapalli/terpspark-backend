"""
Core configuration settings for TerpSpark Backend API.
Loads environment variables and provides application-wide settings.
"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "TerpSpark"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Security
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Email Configuration
    EMAIL_MODE: str = "mock"  # "mock" or "smtp" - use mock for dev, smtp for production
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "terpspark.events@gmail.com"
    SMTP_FROM_NAME: str = "TerpSpark"
    SMTP_USE_TLS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/15minutes"
    RATE_LIMIT_REGISTRATION: str = "10/hour"
    RATE_LIMIT_ANNOUNCEMENTS: str = "10/day"
    RATE_LIMIT_API: str = "100/minute"
    RATE_LIMIT_EXPORT: str = "5/hour"
    
    # File Upload (for future phases)
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/jpg,image/webp"
    UPLOAD_DIR: str = "./uploads"
    CDN_URL: str = "https://cdn.terpspark.umd.edu"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/terpspark.log"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Parse allowed image types into a list."""
        return [img_type.strip() for img_type in self.ALLOWED_IMAGE_TYPES.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reading .env file multiple times.
    """
    return Settings()


# Export settings instance
settings = get_settings()

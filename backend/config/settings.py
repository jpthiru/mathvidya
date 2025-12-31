"""
Application Settings

Environment-based configuration using Pydantic Settings.
Reads from .env file or environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings and configuration"""

    # Application
    APP_NAME: str = "Mathvidya API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mathvidya_user:password@localhost:5432/mathvidya"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours - extended for exam sessions and bulk question entry
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",
        "http://localhost:8080",  # Frontend dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://ec2-13-202-49-76.ap-south-1.compute.amazonaws.com",
        "https://ec2-13-202-49-76.ap-south-1.compute.amazonaws.com",
        "http://mathvidya.com",
        "https://mathvidya.com",
        "http://www.mathvidya.com",
        "https://www.mathvidya.com",
    ]

    # AWS Configuration
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "mathvidya-media-prod"
    S3_PRESIGNED_URL_EXPIRY: int = 900  # 15 minutes
    S3_QUESTION_IMAGES_PREFIX: str = "question-images/"
    S3_ANSWER_SHEETS_PREFIX: str = "answer-sheets/"

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Email Configuration (for future use)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@mathvidya.com"
    EMAILS_FROM_NAME: str = "Mathvidya"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # SLA Configuration
    SLA_CENTUM_HOURS: int = 24
    SLA_PREMIUM_HOURS: int = 48
    WORKING_HOURS_START: int = 9  # 9 AM
    WORKING_HOURS_END: int = 18  # 6 PM

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()

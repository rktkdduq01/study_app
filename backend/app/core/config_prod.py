"""
Production configuration settings
"""
from typing import List, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
import secrets


class ProductionSettings(BaseSettings):
    """Production-specific settings"""
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    TESTING: bool = False
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Educational RPG Platform"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Shorter for production
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS - Restricted for production
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "https://educational-rpg.com",
        "https://www.educational-rpg.com",
        "https://api.educational-rpg.com"
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str
    REDIS_POOL_SIZE: int = 10
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS: dict = {
        1: 3,   # TCP_KEEPIDLE
        2: 3,   # TCP_KEEPINTVL
        3: 3,   # TCP_KEEPCNT
    }
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}
    UPLOAD_PATH: str = "/app/uploads"
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.sendgrid.net"
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "noreply@educational-rpg.com"
    EMAILS_FROM_NAME: str = "Educational RPG"
    
    # External Services
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: int = 30
    
    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_MONTHLY: str
    STRIPE_PRICE_ID_YEARLY: str
    
    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-west-2"
    S3_BUCKET_NAME: str
    S3_BUCKET_REGION: str = "us-west-2"
    S3_PRESIGNED_URL_EXPIRY: int = 3600
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = "/var/log/educational-rpg/app.log"
    LOG_FILE_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
    LOG_FILE_BACKUP_COUNT: int = 10
    
    # Performance
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600
    ENABLE_COMPRESSION: bool = True
    COMPRESSION_LEVEL: int = 6
    
    # Security Headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.educational-rpg.com wss://api.educational-rpg.com",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    # Session
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    
    # Feature Flags
    ENABLE_AI_TUTOR: bool = True
    ENABLE_MULTIPLAYER: bool = False
    ENABLE_PAYMENT: bool = True
    MAINTENANCE_MODE: bool = False
    
    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_S3_BUCKET: str = "educational-rpg-backups"
    
    class Config:
        case_sensitive = True
        env_file = ".env.production"
        env_file_encoding = "utf-8"


# Create settings instance
settings = ProductionSettings()
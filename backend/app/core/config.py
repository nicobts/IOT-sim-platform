"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

import secrets
from typing import List, Optional
from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application Settings
    PROJECT_NAME: str = "FastAPI IOT SIM Management Server"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Configuration
    DATABASE_URL: PostgresDsn
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # Redis Configuration
    REDIS_URL: RedisDsn
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50

    # 1NCE API Configuration
    ONCE_API_BASE_URL: AnyHttpUrl = "https://api.1nce.com"
    ONCE_CLIENT_ID: str
    ONCE_CLIENT_SECRET: str
    ONCE_API_TIMEOUT: int = 30
    ONCE_MAX_RETRIES: int = 3

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        """Parse CORS origins from JSON string or list"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    # Monitoring & Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True

    # Background Jobs
    ENABLE_SCHEDULER: bool = True
    SYNC_SIMS_INTERVAL_MINUTES: int = 15
    SYNC_USAGE_INTERVAL_MINUTES: int = 60
    CHECK_QUOTAS_INTERVAL_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Caching
    CACHE_TTL_SECONDS: int = 300
    ENABLE_CACHE: bool = True

    @property
    def database_url_str(self) -> str:
        """Get database URL as string"""
        return str(self.DATABASE_URL)

    @property
    def redis_url_str(self) -> str:
        """Get Redis URL as string"""
        return str(self.REDIS_URL)

    @property
    def once_api_base_url_str(self) -> str:
        """Get 1NCE API base URL as string"""
        return str(self.ONCE_API_BASE_URL)


# Global settings instance
settings = Settings()

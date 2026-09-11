from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from typing import Optional
import warnings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    # Database
    DATABASE_URL: str

    # Application
    APP_NAME: str = "CyberShield AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security — JWT (Phase 8)
    # JWT_SECRET_KEY must be overridden in production via environment variable.
    # The default is intentionally weak and will trigger a warning in production.
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Seeding — initial admin user (Phase 8)
    # Set these in Render/production to auto-create the first admin on deploy.
    # Neither value is ever logged — see seed.py for the security note.
    SEED_ADMIN_EMAIL: Optional[str] = None
    SEED_ADMIN_PASSWORD: Optional[str] = None

    # CORS (optional, can be expanded later)
    CORS_ORIGINS: Optional[str] = None
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: Optional[str] = None
    CORS_ALLOW_HEADERS: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()

    # Warn loudly if the default JWT secret is used in production.
    # This is logged as a WARNING (not ERROR) so it doesn't crash the app,
    # but it will appear prominently in Render's deploy log.
    # The secret value itself is NEVER logged.
    _default_secret = "dev-secret-key-change-in-production-use-openssl-rand-hex-32"
    if s.ENVIRONMENT == "production" and s.JWT_SECRET_KEY == _default_secret:
        import logging
        logging.getLogger("config").warning(
            "SECURITY WARNING: JWT_SECRET_KEY is using the default development value "
            "in a production environment. Set JWT_SECRET_KEY to a strong random value "
            "immediately. Generate one with: openssl rand -hex 32"
        )

    return s

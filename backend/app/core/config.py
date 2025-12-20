"""Application configuration."""


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # API Settings
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    # CORS origins: comma-separated list or "*" for all origins (dev only)
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-me-in-production-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./data/mintbean.db"

    # Beancount
    BEANCOUNT_FILE_PATH: str = ""
    BEANCOUNT_REPO_PATH: str = ""

    # Plaid
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_ENV: str = "sandbox"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        """Parse CORS origins from comma-separated string or wildcard."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()

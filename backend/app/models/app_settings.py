"""Application settings model for global configuration."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class AppSettings(Base):
    """Global application settings."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Plaid settings
    plaid_client_id = Column(String(255), nullable=True)
    plaid_secret = Column(String(255), nullable=True)
    plaid_environment = Column(
        String(20), nullable=False, default="sandbox"
    )  # sandbox or production

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of settings."""
        return f"<AppSettings env={self.plaid_environment}>"

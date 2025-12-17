"""Application settings model for global configuration."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class AppSettings(Base):
    """Global application settings."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Plaid settings - single client_id, separate secrets per environment
    plaid_client_id = Column(String(255), nullable=True)
    plaid_sandbox_secret = Column(String(255), nullable=True)
    plaid_production_secret = Column(String(255), nullable=True)
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

    def get_credentials_for_environment(self, environment: str) -> tuple[str | None, str | None]:
        """
        Get the client_id and secret for the specified environment.

        Args:
            environment: 'sandbox' or 'production'

        Returns:
            Tuple of (client_id, secret) for the environment
        """
        if environment == "production":
            return (self.plaid_client_id, self.plaid_production_secret)
        else:  # Default to sandbox
            return (self.plaid_client_id, self.plaid_sandbox_secret)

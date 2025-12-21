"""Application settings model for global configuration."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class AppSettings(Base):
    """Global application settings."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Database settings
    database_type = Column(String(20), nullable=False, default="sqlite")  # sqlite or mysql
    database_host = Column(String(255), nullable=True)  # MySQL only
    database_port = Column(Integer, nullable=True, default=3306)  # MySQL only
    database_name = Column(String(255), nullable=True)  # MySQL only
    database_user = Column(String(255), nullable=True)  # MySQL only
    database_password = Column(String(255), nullable=True)  # MySQL only
    sqlite_path = Column(String(500), nullable=True, default="./data/mintbean.db")

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

    def get_database_url(self) -> str:
        """
        Build the database URL from stored settings.

        Returns:
            SQLAlchemy database URL string
        """
        if self.database_type == "mysql":
            # MySQL connection string: mysql+pymysql://user:password@host:port/database
            return (
                f"mysql+pymysql://{self.database_user}:{self.database_password}"
                f"@{self.database_host}:{self.database_port}/{self.database_name}"
            )
        else:
            # SQLite connection string: sqlite:///path/to/db.db
            return f"sqlite:///{self.sqlite_path}"

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

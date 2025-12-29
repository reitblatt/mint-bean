"""Application settings model for global configuration."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.core.encryption import decrypt_value, encrypt_value


class AppSettings(Base):
    """
    Global application settings.

    Sensitive fields (passwords, API secrets) are automatically encrypted
    when stored in the database using hybrid properties.
    """

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Database settings
    database_type = Column(String(20), nullable=False, default="sqlite")  # sqlite or mysql
    database_host = Column(String(255), nullable=True)  # MySQL only
    database_port = Column(Integer, nullable=True, default=3306)  # MySQL only
    database_name = Column(String(255), nullable=True)  # MySQL only
    database_user = Column(String(255), nullable=True)  # MySQL only
    _database_password = Column(
        "database_password", String(500), nullable=True
    )  # MySQL only - encrypted
    sqlite_path = Column(String(500), nullable=True, default="./data/mintbean.db")

    # Plaid settings - single client_id, separate secrets per environment
    plaid_client_id = Column(String(255), nullable=True)
    _plaid_sandbox_secret = Column("plaid_sandbox_secret", String(500), nullable=True)  # Encrypted
    _plaid_production_secret = Column(
        "plaid_production_secret", String(500), nullable=True
    )  # Encrypted
    plaid_environment = Column(
        String(20), nullable=False, default="sandbox"
    )  # sandbox or production

    # Encrypted property: database_password
    @hybrid_property
    def database_password(self) -> str | None:
        """Get decrypted database password."""
        return decrypt_value(self._database_password)

    @database_password.setter
    def database_password(self, value: str | None):
        """Set database password (will be encrypted)."""
        self._database_password = encrypt_value(value)

    # Encrypted property: plaid_sandbox_secret
    @hybrid_property
    def plaid_sandbox_secret(self) -> str | None:
        """Get decrypted Plaid sandbox secret."""
        return decrypt_value(self._plaid_sandbox_secret)

    @plaid_sandbox_secret.setter
    def plaid_sandbox_secret(self, value: str | None):
        """Set Plaid sandbox secret (will be encrypted)."""
        self._plaid_sandbox_secret = encrypt_value(value)

    # Encrypted property: plaid_production_secret
    @hybrid_property
    def plaid_production_secret(self) -> str | None:
        """Get decrypted Plaid production secret."""
        return decrypt_value(self._plaid_production_secret)

    @plaid_production_secret.setter
    def plaid_production_secret(self, value: str | None):
        """Set Plaid production secret (will be encrypted)."""
        self._plaid_production_secret = encrypt_value(value)

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

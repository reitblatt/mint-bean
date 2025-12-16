"""Settings service for global application configuration."""

from sqlalchemy.orm import Session

from app.models.app_settings import AppSettings


def get_or_create_settings(db: Session) -> AppSettings:
    """
    Get or create the global settings object.

    There should only ever be one AppSettings row in the database.

    Args:
        db: Database session

    Returns:
        AppSettings object
    """
    settings = db.query(AppSettings).first()

    if not settings:
        # Create default settings
        settings = AppSettings(
            plaid_environment="sandbox",
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def update_plaid_settings(
    db: Session,
    client_id: str | None = None,
    secret: str | None = None,
    environment: str | None = None,
) -> AppSettings:
    """
    Update Plaid settings.

    Args:
        db: Database session
        client_id: Plaid client ID
        secret: Plaid secret
        environment: Plaid environment (sandbox or production)

    Returns:
        Updated AppSettings object
    """
    settings = get_or_create_settings(db)

    if client_id is not None:
        settings.plaid_client_id = client_id
    if secret is not None:
        settings.plaid_secret = secret
    if environment is not None:
        if environment not in ["sandbox", "production"]:
            raise ValueError("Environment must be 'sandbox' or 'production'")
        settings.plaid_environment = environment

    db.commit()
    db.refresh(settings)

    return settings

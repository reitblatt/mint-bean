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
    sandbox_secret: str | None = None,
    production_secret: str | None = None,
    environment: str | None = None,
) -> AppSettings:
    """
    Update Plaid settings with environment-specific secrets.

    Args:
        db: Database session
        client_id: Plaid client ID (same for all environments)
        sandbox_secret: Plaid secret for sandbox environment
        production_secret: Plaid secret for production environment
        environment: Current Plaid environment (sandbox or production)

    Returns:
        Updated AppSettings object
    """
    settings = get_or_create_settings(db)

    # Update client ID (same for all environments)
    if client_id is not None:
        settings.plaid_client_id = client_id

    # Update environment-specific secrets
    if sandbox_secret is not None:
        settings.plaid_sandbox_secret = sandbox_secret
    if production_secret is not None:
        settings.plaid_production_secret = production_secret

    # Update environment
    if environment is not None:
        if environment not in ["sandbox", "production"]:
            raise ValueError("Environment must be 'sandbox' or 'production'")
        settings.plaid_environment = environment

    db.commit()
    db.refresh(settings)

    return settings

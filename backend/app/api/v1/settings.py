"""Settings API endpoints (Admin only)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin_user
from app.core.database import get_db
from app.models.user import User
from app.services.settings_service import get_or_create_settings, update_plaid_settings

router = APIRouter()


class PlaidSettings(BaseModel):
    """Plaid API settings with environment-specific secrets."""

    client_id: str | None = None
    sandbox_secret: str | None = None
    production_secret: str | None = None
    environment: str | None = None


class PlaidSettingsResponse(BaseModel):
    """Plaid settings response (secrets are masked)."""

    client_id: str | None
    sandbox_secret_masked: str | None
    production_secret_masked: str | None
    environment: str


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    database_type: str
    database_host: str | None = None
    database_port: int | None = None
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
    sqlite_path: str | None = None


class DatabaseSettingsResponse(BaseModel):
    """Database settings response (password is masked)."""

    database_type: str
    database_host: str | None
    database_port: int | None
    database_name: str | None
    database_user: str | None
    database_password_masked: str | None
    sqlite_path: str | None


@router.get("/plaid", response_model=PlaidSettingsResponse)
def get_plaid_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> PlaidSettingsResponse:
    """
    Get current Plaid API settings from database (admin only).

    Args:
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Plaid settings with masked secrets
    """
    settings = get_or_create_settings(db)

    def mask_secret(secret: str | None) -> str | None:
        """Mask a secret for display."""
        if not secret:
            return None
        if len(secret) > 8:
            return f"{secret[:4]}...{secret[-4:]}"
        return "****"

    return PlaidSettingsResponse(
        client_id=settings.plaid_client_id,
        sandbox_secret_masked=mask_secret(settings.plaid_sandbox_secret),
        production_secret_masked=mask_secret(settings.plaid_production_secret),
        environment=settings.plaid_environment,
    )


@router.put("/plaid", response_model=PlaidSettingsResponse)
def update_plaid_settings_endpoint(
    settings: PlaidSettings,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> PlaidSettingsResponse:
    """
    Update Plaid API settings in database (admin only).

    Args:
        settings: New Plaid settings with environment-specific credentials
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated settings with masked secrets
    """
    # Validate environment if provided
    if settings.environment:
        valid_envs = ["sandbox", "production"]
        if settings.environment not in valid_envs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment. Must be one of: {', '.join(valid_envs)}",
            )

    try:
        # Update settings in database
        updated_settings = update_plaid_settings(
            db=db,
            client_id=settings.client_id,
            sandbox_secret=settings.sandbox_secret,
            production_secret=settings.production_secret,
            environment=settings.environment,
        )

        def mask_secret(secret: str | None) -> str | None:
            """Mask a secret for display."""
            if not secret:
                return None
            if len(secret) > 8:
                return f"{secret[:4]}...{secret[-4:]}"
            return "****"

        return PlaidSettingsResponse(
            client_id=updated_settings.plaid_client_id,
            sandbox_secret_masked=mask_secret(updated_settings.plaid_sandbox_secret),
            production_secret_masked=mask_secret(updated_settings.plaid_production_secret),
            environment=updated_settings.plaid_environment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/database", response_model=DatabaseSettingsResponse)
def get_database_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> DatabaseSettingsResponse:
    """
    Get current database configuration from app settings (admin only).

    Args:
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Database settings with masked password
    """
    settings = get_or_create_settings(db)

    def mask_password(password: str | None) -> str | None:
        """Mask a password for display."""
        if not password:
            return None
        if len(password) > 8:
            return f"{password[:2]}...{password[-2:]}"
        return "****"

    return DatabaseSettingsResponse(
        database_type=settings.database_type,
        database_host=settings.database_host,
        database_port=settings.database_port,
        database_name=settings.database_name,
        database_user=settings.database_user,
        database_password_masked=mask_password(settings.database_password),
        sqlite_path=settings.sqlite_path,
    )


@router.put("/database", response_model=DatabaseSettingsResponse)
def update_database_settings_endpoint(
    settings: DatabaseSettings,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> DatabaseSettingsResponse:
    """
    Update database configuration (admin only).

    WARNING: Changing database settings requires restarting the application
    to reconnect with the new database.

    Args:
        settings: New database configuration
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated database settings with masked password
    """
    # Validate database type
    if settings.database_type not in ["sqlite", "mysql"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid database type. Must be 'sqlite' or 'mysql'.",
        )

    # Validate MySQL settings if MySQL is selected
    if settings.database_type == "mysql":
        if not all(
            [
                settings.database_host,
                settings.database_name,
                settings.database_user,
                settings.database_password,
            ]
        ):
            raise HTTPException(
                status_code=400,
                detail="MySQL requires host, name, user, and password.",
            )

    try:
        # Get current settings
        app_settings = get_or_create_settings(db)

        # Update database configuration
        app_settings.database_type = settings.database_type
        if settings.database_type == "mysql":
            app_settings.database_host = settings.database_host
            app_settings.database_port = settings.database_port
            app_settings.database_name = settings.database_name
            app_settings.database_user = settings.database_user
            if settings.database_password:
                app_settings.database_password = settings.database_password
        else:
            if settings.sqlite_path:
                app_settings.sqlite_path = settings.sqlite_path

        db.commit()
        db.refresh(app_settings)

        def mask_password(password: str | None) -> str | None:
            """Mask a password for display."""
            if not password:
                return None
            if len(password) > 8:
                return f"{password[:2]}...{password[-2:]}"
            return "****"

        return DatabaseSettingsResponse(
            database_type=app_settings.database_type,
            database_host=app_settings.database_host,
            database_port=app_settings.database_port,
            database_name=app_settings.database_name,
            database_user=app_settings.database_user,
            database_password_masked=mask_password(app_settings.database_password),
            sqlite_path=app_settings.sqlite_path,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e

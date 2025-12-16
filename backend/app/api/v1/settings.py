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
    """Plaid API settings."""

    client_id: str | None = None
    secret: str | None = None
    environment: str | None = None


class PlaidSettingsResponse(BaseModel):
    """Plaid settings response (secret is masked)."""

    client_id: str | None
    secret_masked: str | None
    environment: str


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
        Plaid settings with masked secret
    """
    settings = get_or_create_settings(db)

    # Mask the secret for display
    secret_masked = None
    if settings.plaid_secret:
        if len(settings.plaid_secret) > 8:
            secret_masked = f"{settings.plaid_secret[:4]}...{settings.plaid_secret[-4:]}"
        else:
            secret_masked = "****"

    return PlaidSettingsResponse(
        client_id=settings.plaid_client_id,
        secret_masked=secret_masked,
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
        settings: New Plaid settings
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated settings with masked secret
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
            secret=settings.secret,
            environment=settings.environment,
        )

        # Mask the secret for display
        secret_masked = None
        if updated_settings.plaid_secret:
            if len(updated_settings.plaid_secret) > 8:
                secret_masked = (
                    f"{updated_settings.plaid_secret[:4]}...{updated_settings.plaid_secret[-4:]}"
                )
            else:
                secret_masked = "****"

        return PlaidSettingsResponse(
            client_id=updated_settings.plaid_client_id,
            secret_masked=secret_masked,
            environment=updated_settings.plaid_environment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

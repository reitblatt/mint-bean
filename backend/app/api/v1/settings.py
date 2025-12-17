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

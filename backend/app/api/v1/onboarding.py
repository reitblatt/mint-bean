"""Onboarding API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash
from app.core.database import get_db
from app.models.user import User
from app.services.settings_service import get_or_create_settings

router = APIRouter()


class OnboardingStatusResponse(BaseModel):
    """Response schema for onboarding status."""

    needs_onboarding: bool


class OnboardingRequest(BaseModel):
    """Request schema for initial onboarding."""

    # Admin user details
    admin_email: EmailStr = Field(..., description="Admin user email")
    admin_password: str = Field(..., min_length=8, description="Admin user password")

    # Plaid configuration
    plaid_client_id: str = Field(..., description="Plaid client ID")
    plaid_secret: str = Field(..., description="Plaid secret")
    plaid_environment: str = Field(
        "sandbox", description="Plaid environment (sandbox, development, production)"
    )


@router.get("/status", response_model=OnboardingStatusResponse)
def check_onboarding_status(db: Session = Depends(get_db)) -> OnboardingStatusResponse:
    """
    Check if the application needs initial onboarding.

    Returns true if no users exist in the database.
    """
    user_count = db.query(User).count()
    return OnboardingStatusResponse(needs_onboarding=user_count == 0)


@router.post("/complete")
def complete_onboarding(request: OnboardingRequest, db: Session = Depends(get_db)) -> dict:
    """
    Complete initial onboarding by creating admin user and configuring Plaid.

    This endpoint can only be called when no users exist.
    """
    # Check if onboarding is still needed
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Onboarding already complete. Users already exist.",
        )

    # Validate Plaid environment
    if request.plaid_environment not in ["sandbox", "development", "production"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid Plaid environment. Must be sandbox, development, or production.",
        )

    try:
        # Create admin user
        admin_user = User(
            email=request.admin_email,
            hashed_password=get_password_hash(request.admin_password),
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)

        # Update Plaid settings
        settings = get_or_create_settings(db)
        settings.plaid_client_id = request.plaid_client_id

        # Set the secret based on environment
        if request.plaid_environment == "sandbox":
            settings.plaid_sandbox_secret = request.plaid_secret
        elif request.plaid_environment == "production":
            settings.plaid_production_secret = request.plaid_secret

        settings.plaid_environment = request.plaid_environment

        db.commit()
        db.refresh(admin_user)

        return {
            "status": "success",
            "message": "Onboarding completed successfully",
            "admin_user_id": admin_user.id,
            "admin_email": admin_user.email,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to complete onboarding: {str(e)}"
        ) from e

"""Onboarding API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash
from app.core.database import get_db
from app.models.user import User
from app.services.category_service import seed_default_categories, seed_default_plaid_mappings
from app.services.dashboard_service import create_default_dashboard
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

    # Database configuration
    database_type: str = Field("sqlite", description="Database type (sqlite or mysql)")
    database_host: str | None = Field(None, description="MySQL host (MySQL only)")
    database_port: int = Field(3306, description="MySQL port (MySQL only)")
    database_name: str | None = Field(None, description="MySQL database name (MySQL only)")
    database_user: str | None = Field(None, description="MySQL username (MySQL only)")
    database_password: str | None = Field(None, description="MySQL password (MySQL only)")
    sqlite_path: str = Field("./data/mintbean.db", description="SQLite file path (SQLite only)")

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

    # Validate database type
    if request.database_type not in ["sqlite", "mysql"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid database type. Must be sqlite or mysql.",
        )

    # Validate MySQL configuration if MySQL is selected
    if request.database_type == "mysql":
        if not all(
            [
                request.database_host,
                request.database_name,
                request.database_user,
                request.database_password,
            ]
        ):
            raise HTTPException(
                status_code=400,
                detail="MySQL configuration requires host, name, user, and password.",
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

        # Update application settings
        settings = get_or_create_settings(db)

        # Database configuration
        settings.database_type = request.database_type
        if request.database_type == "mysql":
            settings.database_host = request.database_host
            settings.database_port = request.database_port
            settings.database_name = request.database_name
            settings.database_user = request.database_user
            settings.database_password = request.database_password
        else:
            settings.sqlite_path = request.sqlite_path

        # Plaid configuration
        settings.plaid_client_id = request.plaid_client_id

        # Set the secret based on environment
        if request.plaid_environment == "sandbox":
            settings.plaid_sandbox_secret = request.plaid_secret
        elif request.plaid_environment == "production":
            settings.plaid_production_secret = request.plaid_secret

        settings.plaid_environment = request.plaid_environment

        db.commit()
        db.refresh(admin_user)

        # Seed default categories for the new admin user
        seed_default_categories(db, admin_user.id)

        # Seed default Plaid category mappings
        seed_default_plaid_mappings(db, admin_user.id)

        # Create default dashboard for the new admin user
        create_default_dashboard(db, admin_user)

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

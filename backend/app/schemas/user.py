"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.input_validation import (
    sanitize_string,
    validate_email_format,
    validate_no_script_tags,
)


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, max_length=128)
    is_admin: bool = False

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Additional email validation beyond EmailStr."""
        # EmailStr already validates format, but we add extra checks
        validated = validate_email_format(v)
        validate_no_script_tags(validated)
        return sanitize_string(validated, max_length=254)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength and sanitize."""
        # Check for script tags (XSS prevention)
        validate_no_script_tags(v)

        # Validate password complexity
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)
    is_admin: bool | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    is_admin: bool
    is_active: bool
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""

    user_id: int | None = None


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str = Field(..., max_length=128)

    @field_validator("email")
    @classmethod
    def validate_login_email(cls, v: str) -> str:
        """Sanitize email for login."""
        validated = validate_email_format(v)
        validate_no_script_tags(validated)
        return sanitize_string(validated, max_length=254)

    @field_validator("password")
    @classmethod
    def validate_login_password(cls, v: str) -> str:
        """Sanitize password for login."""
        # Just check for XSS, don't enforce complexity on login
        validate_no_script_tags(v)
        return v


class UserDeleteRequest(BaseModel):
    """Schema for user deletion request."""

    hard_delete: bool = False  # If True, permanently delete; if False, archive


class UserRestoreRequest(BaseModel):
    """Schema for restoring archived user."""

    restore_data: bool = True  # If True, restore all user data; if False, start fresh

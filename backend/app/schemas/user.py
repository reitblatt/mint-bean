"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)
    is_admin: bool = False


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
    password: str


class UserDeleteRequest(BaseModel):
    """Schema for user deletion request."""

    hard_delete: bool = False  # If True, permanently delete; if False, archive


class UserRestoreRequest(BaseModel):
    """Schema for restoring archived user."""

    restore_data: bool = True  # If True, restore all user data; if False, start fresh

"""Plaid Item schemas."""

from datetime import datetime

from pydantic import BaseModel


class PlaidItemBase(BaseModel):
    """Base Plaid Item schema."""

    item_id: str
    institution_id: str | None = None
    institution_name: str | None = None


class PlaidItemCreate(PlaidItemBase):
    """Schema for creating a Plaid Item."""

    access_token: str


class PlaidItemUpdate(BaseModel):
    """Schema for updating a Plaid Item."""

    institution_name: str | None = None
    cursor: str | None = None
    is_active: bool | None = None
    needs_update: bool | None = None
    error_code: str | None = None
    last_synced_at: datetime | None = None


class PlaidItemResponse(PlaidItemBase):
    """Schema for Plaid Item response."""

    id: int
    is_active: bool
    needs_update: bool
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class LinkTokenCreateRequest(BaseModel):
    """Request schema for creating a link token."""

    user_id: str | None = "user-1"  # For now, hardcoded user


class LinkTokenCreateResponse(BaseModel):
    """Response schema for link token creation."""

    link_token: str
    expiration: str


class PublicTokenExchangeRequest(BaseModel):
    """Request schema for exchanging public token."""

    public_token: str


class PublicTokenExchangeResponse(BaseModel):
    """Response schema for public token exchange."""

    item_id: str
    institution_id: str | None = None
    institution_name: str | None = None


class TransactionsSyncResponse(BaseModel):
    """Response schema for transactions sync."""

    added: int
    modified: int
    removed: int
    cursor: str

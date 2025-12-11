"""Plaid Item schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlaidItemBase(BaseModel):
    """Base Plaid Item schema."""

    item_id: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None


class PlaidItemCreate(PlaidItemBase):
    """Schema for creating a Plaid Item."""

    access_token: str


class PlaidItemUpdate(BaseModel):
    """Schema for updating a Plaid Item."""

    institution_name: Optional[str] = None
    cursor: Optional[str] = None
    is_active: Optional[bool] = None
    needs_update: Optional[bool] = None
    error_code: Optional[str] = None
    last_synced_at: Optional[datetime] = None


class PlaidItemResponse(PlaidItemBase):
    """Schema for Plaid Item response."""

    id: int
    is_active: bool
    needs_update: bool
    error_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_synced_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LinkTokenCreateRequest(BaseModel):
    """Request schema for creating a link token."""

    user_id: Optional[str] = "user-1"  # For now, hardcoded user


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
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None


class TransactionsSyncResponse(BaseModel):
    """Response schema for transactions sync."""

    added: int
    modified: int
    removed: int
    cursor: str

"""Account schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    """Base account schema."""

    name: str
    official_name: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    beancount_account: str
    currency: str = "USD"
    active: bool = True


class AccountCreate(AccountBase):
    """Schema for creating an account."""

    plaid_account_id: Optional[str] = None
    plaid_item_id: Optional[str] = None
    institution_name: Optional[str] = None
    institution_id: Optional[str] = None


class AccountUpdate(BaseModel):
    """Schema for updating an account."""

    name: Optional[str] = None
    official_name: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    beancount_account: Optional[str] = None
    current_balance: Optional[float] = None
    available_balance: Optional[float] = None
    active: Optional[bool] = None
    needs_reconnection: Optional[bool] = None


class AccountResponse(AccountBase):
    """Schema for account response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: str
    plaid_account_id: Optional[str] = None
    institution_name: Optional[str] = None
    current_balance: Optional[float] = None
    available_balance: Optional[float] = None
    needs_reconnection: bool = False
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

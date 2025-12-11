"""Account schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    """Base account schema."""

    name: str
    official_name: str | None = None
    type: str
    subtype: str | None = None
    beancount_account: str
    currency: str = "USD"
    active: bool = True


class AccountCreate(AccountBase):
    """Schema for creating an account."""

    plaid_account_id: str | None = None
    plaid_item_id: str | None = None
    institution_name: str | None = None
    institution_id: str | None = None


class AccountUpdate(BaseModel):
    """Schema for updating an account."""

    name: str | None = None
    official_name: str | None = None
    type: str | None = None
    subtype: str | None = None
    beancount_account: str | None = None
    current_balance: float | None = None
    available_balance: float | None = None
    active: bool | None = None
    needs_reconnection: bool | None = None


class AccountResponse(AccountBase):
    """Schema for account response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: str
    plaid_account_id: str | None = None
    institution_name: str | None = None
    current_balance: float | None = None
    available_balance: float | None = None
    needs_reconnection: bool = False
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

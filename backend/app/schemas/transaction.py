"""Transaction schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.category import CategoryResponse


class TransactionBase(BaseModel):
    """Base transaction schema."""

    date: datetime
    amount: float
    description: str
    payee: str | None = None
    narration: str | None = None
    currency: str = "USD"
    pending: bool = False
    reviewed: bool = False


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""

    account_id: int
    category_id: int | None = None
    beancount_account: str | None = None
    plaid_transaction_id: str | None = None
    tags: list[str] | None = None
    links: list[str] | None = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    date: datetime | None = None
    amount: float | None = None
    description: str | None = None
    payee: str | None = None
    narration: str | None = None
    category_id: int | None = None
    beancount_account: str | None = None
    pending: bool | None = None
    reviewed: bool | None = None
    tags: list[str] | None = None
    links: list[str] | None = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    account_id: int
    category_id: int | None = None
    category: CategoryResponse | None = None
    beancount_account: str | None = None
    plaid_transaction_id: str | None = None
    plaid_primary_category: str | None = None
    plaid_detailed_category: str | None = None
    plaid_confidence_level: str | None = None
    merchant_name: str | None = None
    synced_to_beancount: bool = False
    beancount_flag: str
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list response."""

    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

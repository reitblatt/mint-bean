"""Transaction schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TransactionBase(BaseModel):
    """Base transaction schema."""

    date: datetime
    amount: float
    description: str
    payee: Optional[str] = None
    narration: Optional[str] = None
    currency: str = "USD"
    pending: bool = False
    reviewed: bool = False


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""

    account_id: int
    category_id: Optional[int] = None
    beancount_account: Optional[str] = None
    plaid_transaction_id: Optional[str] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    date: Optional[datetime] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    payee: Optional[str] = None
    narration: Optional[str] = None
    category_id: Optional[int] = None
    beancount_account: Optional[str] = None
    pending: Optional[bool] = None
    reviewed: Optional[bool] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    account_id: int
    category_id: Optional[int] = None
    beancount_account: Optional[str] = None
    plaid_transaction_id: Optional[str] = None
    synced_to_beancount: bool = False
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list response."""

    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

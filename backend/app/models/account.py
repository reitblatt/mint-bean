"""Account model."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Account(Base):
    """Account model representing financial accounts."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Account identification
    account_id = Column(String(255), unique=True, index=True, nullable=False)
    plaid_account_id = Column(String(255), unique=True, index=True, nullable=True)
    plaid_item_id = Column(String(255), index=True, nullable=True)

    # Account details
    name = Column(String(255), nullable=False)
    official_name = Column(String(255), nullable=True)
    type = Column(String(50), nullable=False)  # checking, savings, credit, investment
    subtype = Column(String(50), nullable=True)

    # Institution info
    institution_name = Column(String(255), nullable=True)
    institution_id = Column(String(255), nullable=True)

    # Beancount mapping
    beancount_account = Column(String(255), nullable=False, unique=True)

    # Balances
    current_balance = Column(Float, nullable=True)
    available_balance = Column(Float, nullable=True)
    currency = Column(String(10), default="USD", nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    needs_reconnection = Column(Boolean, default=False, nullable=False)

    # Timestamps
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )

    # Account metadata (JSON) - renamed from 'metadata' to avoid conflict with SQLAlchemy
    account_metadata = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation of account."""
        return f"<Account {self.beancount_account}: {self.name}>"

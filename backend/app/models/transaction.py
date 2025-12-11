"""Transaction model."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Transaction(Base):
    """Transaction model representing financial transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Transaction identification
    transaction_id = Column(String(255), unique=True, index=True, nullable=False)
    plaid_transaction_id = Column(String(255), unique=True, index=True, nullable=True)

    # Account reference
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    account = relationship("Account", back_populates="transactions")

    # Category reference
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="transactions")

    # Transaction details
    date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String(500), nullable=False)
    payee = Column(String(255), nullable=True)
    narration = Column(Text, nullable=True)

    # Beancount specific
    beancount_account = Column(String(255), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    tags = Column(Text, nullable=True)  # JSON string of tags
    links = Column(Text, nullable=True)  # JSON string of links

    # Metadata
    pending = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)
    synced_to_beancount = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Original data from Plaid (JSON)
    raw_data = Column(Text, nullable=True)

    @property
    def beancount_flag(self) -> str:
        """
        Get the appropriate beancount flag for this transaction.

        Returns:
            '!' for pending transactions (not yet cleared)
            '*' for completed/cleared transactions
        """
        return "!" if self.pending else "*"

    def __repr__(self) -> str:
        """String representation of transaction."""
        return f"<Transaction {self.transaction_id}: {self.description} - ${self.amount}>"

"""Plaid Item model for storing Plaid access tokens and metadata."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlaidItem(Base):
    """Represents a Plaid Item (a user's connection to a financial institution)."""

    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)

    # Institution information
    institution_id = Column(String, nullable=True)
    institution_name = Column(String, nullable=True)

    # Plaid environment (sandbox or production)
    environment = Column(String(20), nullable=False, default="sandbox", index=True)

    # Sync cursor for transactions
    cursor = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    needs_update = Column(Boolean, default=False)
    error_code = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    last_synced_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="plaid_items")

    def __repr__(self):
        return f"<PlaidItem(id={self.id}, institution={self.institution_name}, active={self.is_active})>"

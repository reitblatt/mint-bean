"""Plaid Item model for storing Plaid access tokens and metadata."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class PlaidItem(Base):
    """Represents a Plaid Item (a user's connection to a financial institution)."""

    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)

    # Institution information
    institution_id = Column(String, nullable=True)
    institution_name = Column(String, nullable=True)

    # Sync cursor for transactions
    cursor = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    needs_update = Column(Boolean, default=False)
    error_code = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<PlaidItem(id={self.id}, institution={self.institution_name}, active={self.is_active})>"

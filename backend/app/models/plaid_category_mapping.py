"""Plaid Category Mapping model for mapping Plaid categories to user categories."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class PlaidCategoryMapping(Base):
    """Maps Plaid categories to user's custom categories for auto-categorization."""

    __tablename__ = "plaid_category_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # Plaid category identifiers
    plaid_primary_category = Column(String(100), nullable=False, index=True)
    plaid_detailed_category = Column(String(100), nullable=True, index=True)

    # Mapping configuration
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category")

    # Settings
    confidence = Column(Float, default=1.0)  # How confident we are in this mapping (0.0-1.0)
    auto_apply = Column(Boolean, default=True)  # Auto-apply to new transactions

    # Statistics
    match_count = Column(Integer, default=0)  # How many times this mapping has been used
    last_matched_at = Column(DateTime, nullable=True)  # Last time this mapping was applied

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Unique constraint on plaid category combination
    __table_args__ = (
        UniqueConstraint(
            "plaid_primary_category",
            "plaid_detailed_category",
            name="uix_plaid_category",
        ),
    )

    def __repr__(self) -> str:
        """String representation of mapping."""
        detailed = f":{self.plaid_detailed_category}" if self.plaid_detailed_category else ""
        return f"<PlaidCategoryMapping {self.plaid_primary_category}{detailed} → {self.category_id}>"

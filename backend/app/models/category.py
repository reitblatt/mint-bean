"""Category model."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    """Category model for transaction categorization."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Category identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)

    # Hierarchy - FK relationship for true parent-child structure
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    parent = relationship("Category", remote_side=[id], backref="children")

    # Beancount mapping
    beancount_account = Column(String(255), nullable=False)

    # Category type
    category_type = Column(String(50), nullable=False)  # expense, income, transfer

    # Display settings
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    display_order = Column(Integer, default=0)  # For ordering categories in UI

    # Status
    is_active = Column(Boolean, default=True)  # Soft delete support
    is_system = Column(Boolean, default=False)  # System categories can't be deleted

    # Usage statistics
    transaction_count = Column(Integer, default=0)  # Cached count for performance
    last_used_at = Column(DateTime, nullable=True)  # Last time category was used

    # Description
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    def __repr__(self) -> str:
        """String representation of category."""
        return f"<Category {self.name}: {self.beancount_account}>"

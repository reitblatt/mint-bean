"""Category model."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    """Category model for transaction categorization."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    # Category identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)

    # Hierarchy
    parent_category = Column(String(255), nullable=True)

    # Beancount mapping
    beancount_account = Column(String(255), nullable=False)

    # Category type
    category_type = Column(String(50), nullable=False)  # expense, income, transfer

    # Display settings
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)

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
    transactions = relationship("Transaction", back_populates="category")

    def __repr__(self) -> str:
        """String representation of category."""
        return f"<Category {self.name}: {self.beancount_account}>"

"""Rule model for transaction categorization."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Rule(Base):
    """Rule model for automatic transaction categorization."""

    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)

    # Rule identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Rule conditions (JSON string containing match criteria)
    # Example: {"field": "description", "operator": "contains", "value": "amazon"}
    conditions = Column(Text, nullable=False)

    # Actions (JSON string containing actions to take)
    # Example: {"set_category": "Shopping:Online", "set_payee": "Amazon"}
    actions = Column(Text, nullable=False)

    # Target category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")

    # Rule settings
    priority = Column(Integer, default=0, nullable=False)  # Higher priority runs first
    active = Column(Boolean, default=True, nullable=False)

    # Statistics
    match_count = Column(Integer, default=0, nullable=False)
    last_matched_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation of rule."""
        return f"<Rule {self.name} (priority: {self.priority})>"

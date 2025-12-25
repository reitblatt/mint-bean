"""Dashboard tab model for custom dashboards."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class DashboardTab(Base):
    """Dashboard tab model.

    Represents a named tab in a user's custom dashboard.
    Each tab can contain multiple widgets in a grid layout.
    """

    __tablename__ = "dashboard_tabs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    icon = Column(String(50), nullable=True)  # Optional icon name (e.g., "home", "chart")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="dashboard_tabs")
    widgets = relationship("DashboardWidget", back_populates="tab", cascade="all, delete-orphan")

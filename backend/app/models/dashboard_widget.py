"""Dashboard widget model for custom dashboards."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DashboardWidget(Base):
    """Dashboard widget model.

    Represents a configurable widget within a dashboard tab.
    Widgets are positioned in a grid layout and have flexible JSON configuration.
    """

    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, index=True)
    tab_id = Column(Integer, ForeignKey("dashboard_tabs.id"), nullable=False, index=True)

    # Widget type determines which component renders it
    # Types: "summary_card", "line_chart", "bar_chart", "pie_chart", "table"
    widget_type = Column(String(50), nullable=False, index=True)

    title = Column(String(200), nullable=False)

    # Grid layout positioning (4-column grid)
    grid_row = Column(Integer, nullable=False, default=1)
    grid_col = Column(Integer, nullable=False, default=1)
    grid_width = Column(Integer, nullable=False, default=1)  # Spans 1-4 columns
    grid_height = Column(Integer, nullable=False, default=1)  # Spans N rows

    # Widget-specific configuration stored as JSON text
    # Examples:
    # - Summary card: {"metric": "total_balance"}
    # - Line chart: {"data_type": "spending_over_time", "granularity": "daily"}
    # - Bar chart: {"data_type": "spending_by_category", "limit": 10}
    # - Pie chart: {"data_type": "expense_breakdown", "limit": 8}
    # - Table: {"filters": {"limit": 10, "sort": "date_desc"}}
    config = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tab = relationship("DashboardTab", back_populates="widgets")

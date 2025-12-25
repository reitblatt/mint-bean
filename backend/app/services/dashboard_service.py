"""Dashboard service for managing dashboard creation and configuration."""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.dashboard_tab import DashboardTab
from app.models.dashboard_widget import DashboardWidget
from app.models.user import User


def create_default_dashboard(db: Session, user: User) -> DashboardTab:
    """Create a default dashboard for a new user.

    Creates an "Overview" tab with a standard set of widgets:
    - Row 1: 4 summary cards (balance, spending, income, uncategorized)
    - Row 2: Line chart (2 cols) + Pie chart (2 cols)
    - Row 3: Transaction table (4 cols)

    Args:
        db: Database session
        user: User to create dashboard for

    Returns:
        The created dashboard tab with widgets
    """
    # Create the Overview tab
    tab = DashboardTab(
        user_id=user.id,
        name="Overview",
        display_order=0,
        is_default=True,
        icon="home",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(tab)
    db.flush()  # Get the tab ID

    # Define default widgets
    widgets = [
        # Row 1: Summary cards
        DashboardWidget(
            tab_id=tab.id,
            widget_type="summary_card",
            title="Total Balance",
            grid_row=1,
            grid_col=1,
            grid_width=1,
            grid_height=1,
            config=json.dumps({"metric": "total_balance"}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        DashboardWidget(
            tab_id=tab.id,
            widget_type="summary_card",
            title="Total Spending",
            grid_row=1,
            grid_col=2,
            grid_width=1,
            grid_height=1,
            config=json.dumps({"metric": "total_spending"}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        DashboardWidget(
            tab_id=tab.id,
            widget_type="summary_card",
            title="Total Income",
            grid_row=1,
            grid_col=3,
            grid_width=1,
            grid_height=1,
            config=json.dumps({"metric": "total_income"}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        DashboardWidget(
            tab_id=tab.id,
            widget_type="summary_card",
            title="Uncategorized",
            grid_row=1,
            grid_col=4,
            grid_width=1,
            grid_height=1,
            config=json.dumps({"metric": "uncategorized_count"}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        # Row 2: Charts
        DashboardWidget(
            tab_id=tab.id,
            widget_type="line_chart",
            title="Spending Over Time",
            grid_row=2,
            grid_col=1,
            grid_width=2,
            grid_height=2,
            config=json.dumps({"data_type": "spending_over_time", "granularity": "daily"}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        DashboardWidget(
            tab_id=tab.id,
            widget_type="pie_chart",
            title="Spending by Category",
            grid_row=2,
            grid_col=3,
            grid_width=2,
            grid_height=2,
            config=json.dumps({"data_type": "spending_by_category", "limit": 8}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        # Row 3: Transaction table
        DashboardWidget(
            tab_id=tab.id,
            widget_type="table",
            title="Recent Transactions",
            grid_row=4,
            grid_col=1,
            grid_width=4,
            grid_height=2,
            config=json.dumps({"filters": {"limit": 10, "sort": "date_desc"}}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
    ]

    # Add all widgets
    for widget in widgets:
        db.add(widget)

    db.commit()
    db.refresh(tab)

    return tab

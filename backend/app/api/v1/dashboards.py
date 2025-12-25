"""Dashboard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.dashboard_tab import DashboardTab
from app.models.dashboard_widget import DashboardWidget
from app.models.user import User
from app.schemas.dashboard import (
    DashboardTabCreate,
    DashboardTabResponse,
    DashboardTabUpdate,
    DashboardTabWithWidgets,
    DashboardWidgetCreate,
    DashboardWidgetResponse,
    DashboardWidgetUpdate,
)

router = APIRouter()


@router.get("", response_model=list[DashboardTabResponse])
def list_tabs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DashboardTab]:
    """List all dashboard tabs for the current user."""
    tabs = (
        db.query(DashboardTab)
        .filter(DashboardTab.user_id == current_user.id)
        .order_by(DashboardTab.display_order, DashboardTab.id)
        .all()
    )
    return tabs


@router.get("/{tab_id}", response_model=DashboardTabWithWidgets)
def get_tab(
    tab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardTab:
    """Get a specific dashboard tab with its widgets."""
    tab = (
        db.query(DashboardTab)
        .filter(DashboardTab.id == tab_id, DashboardTab.user_id == current_user.id)
        .first()
    )

    if not tab:
        raise HTTPException(status_code=404, detail="Dashboard tab not found")

    return tab


@router.post("", response_model=DashboardTabResponse, status_code=201)
def create_tab(
    tab_data: DashboardTabCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardTab:
    """Create a new dashboard tab."""
    # If this is set as default, unset other defaults
    if tab_data.is_default:
        db.query(DashboardTab).filter(DashboardTab.user_id == current_user.id).update(
            {"is_default": False}
        )

    tab = DashboardTab(
        user_id=current_user.id,
        name=tab_data.name,
        display_order=tab_data.display_order,
        is_default=tab_data.is_default,
        icon=tab_data.icon,
    )

    db.add(tab)
    db.commit()
    db.refresh(tab)

    return tab


@router.patch("/{tab_id}", response_model=DashboardTabResponse)
def update_tab(
    tab_id: int,
    tab_data: DashboardTabUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardTab:
    """Update a dashboard tab."""
    tab = (
        db.query(DashboardTab)
        .filter(DashboardTab.id == tab_id, DashboardTab.user_id == current_user.id)
        .first()
    )

    if not tab:
        raise HTTPException(status_code=404, detail="Dashboard tab not found")

    # If setting this tab as default, unset other defaults
    if tab_data.is_default is True and not tab.is_default:
        db.query(DashboardTab).filter(
            DashboardTab.user_id == current_user.id, DashboardTab.id != tab_id
        ).update({"is_default": False})

    # Update fields
    update_data = tab_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tab, field, value)

    db.commit()
    db.refresh(tab)

    return tab


@router.delete("/{tab_id}", status_code=204)
def delete_tab(
    tab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a dashboard tab (and all its widgets)."""
    tab = (
        db.query(DashboardTab)
        .filter(DashboardTab.id == tab_id, DashboardTab.user_id == current_user.id)
        .first()
    )

    if not tab:
        raise HTTPException(status_code=404, detail="Dashboard tab not found")

    db.delete(tab)
    db.commit()


@router.post("/{tab_id}/widgets", response_model=DashboardWidgetResponse, status_code=201)
def create_widget(
    tab_id: int,
    widget_data: DashboardWidgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardWidget:
    """Create a new widget in a dashboard tab."""
    # Verify tab exists and belongs to user
    tab = (
        db.query(DashboardTab)
        .filter(DashboardTab.id == tab_id, DashboardTab.user_id == current_user.id)
        .first()
    )

    if not tab:
        raise HTTPException(status_code=404, detail="Dashboard tab not found")

    widget = DashboardWidget(
        tab_id=tab_id,
        widget_type=widget_data.widget_type,
        title=widget_data.title,
        grid_row=widget_data.grid_row,
        grid_col=widget_data.grid_col,
        grid_width=widget_data.grid_width,
        grid_height=widget_data.grid_height,
        config=widget_data.config,
    )

    db.add(widget)
    db.commit()
    db.refresh(widget)

    return widget


@router.patch("/{tab_id}/widgets/{widget_id}", response_model=DashboardWidgetResponse)
def update_widget(
    tab_id: int,
    widget_id: int,
    widget_data: DashboardWidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardWidget:
    """Update a widget."""
    # Verify tab exists and belongs to user
    tab = (
        db.query(DashboardTab)
        .filter(DashboardTab.id == tab_id, DashboardTab.user_id == current_user.id)
        .first()
    )

    if not tab:
        raise HTTPException(status_code=404, detail="Dashboard tab not found")

    # Get widget
    widget = (
        db.query(DashboardWidget)
        .filter(DashboardWidget.id == widget_id, DashboardWidget.tab_id == tab_id)
        .first()
    )

    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Update fields
    update_data = widget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(widget, field, value)

    db.commit()
    db.refresh(widget)

    return widget


@router.delete("/{tab_id}/widgets/{widget_id}", status_code=204)
def delete_widget(
    tab_id: int,
    widget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a widget."""
    # Verify tab exists and belongs to user
    tab = (
        db.query(DashboardTab)
        .filter(DashboardTab.id == tab_id, DashboardTab.user_id == current_user.id)
        .first()
    )

    if not tab:
        raise HTTPException(status_code=404, detail="Dashboard tab not found")

    # Get widget
    widget = (
        db.query(DashboardWidget)
        .filter(DashboardWidget.id == widget_id, DashboardWidget.tab_id == tab_id)
        .first()
    )

    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    db.delete(widget)
    db.commit()

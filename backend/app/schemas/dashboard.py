"""Dashboard and widget schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class DashboardWidgetBase(BaseModel):
    """Base dashboard widget schema."""

    widget_type: str = Field(
        ..., description="Widget type (summary_card, line_chart, bar_chart, pie_chart, table)"
    )
    title: str = Field(..., description="Widget title")
    grid_row: int = Field(1, description="Grid row position (1-based)")
    grid_col: int = Field(1, description="Grid column position (1-based)")
    grid_width: int = Field(1, ge=1, le=4, description="Widget width in grid columns (1-4)")
    grid_height: int = Field(1, ge=1, description="Widget height in grid rows")
    config: str | None = Field(None, description="Widget-specific JSON configuration")


class DashboardWidgetCreate(DashboardWidgetBase):
    """Schema for creating a new widget."""

    pass


class DashboardWidgetUpdate(BaseModel):
    """Schema for updating a widget (all fields optional)."""

    widget_type: str | None = None
    title: str | None = None
    grid_row: int | None = None
    grid_col: int | None = None
    grid_width: int | None = Field(None, ge=1, le=4)
    grid_height: int | None = Field(None, ge=1)
    config: str | None = None


class DashboardWidgetResponse(DashboardWidgetBase):
    """Schema for widget response."""

    id: int
    tab_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardTabBase(BaseModel):
    """Base dashboard tab schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Tab name")
    display_order: int = Field(0, description="Tab display order")
    is_default: bool = Field(False, description="Whether this is the default tab")
    icon: str | None = Field(None, max_length=50, description="Optional icon name")


class DashboardTabCreate(DashboardTabBase):
    """Schema for creating a new tab."""

    pass


class DashboardTabUpdate(BaseModel):
    """Schema for updating a tab (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    display_order: int | None = None
    is_default: bool | None = None
    icon: str | None = Field(None, max_length=50)


class DashboardTabResponse(DashboardTabBase):
    """Schema for tab response (without widgets)."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardTabWithWidgets(DashboardTabResponse):
    """Schema for tab response with nested widgets."""

    widgets: list[DashboardWidgetResponse] = []

    class Config:
        from_attributes = True

"""Category schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str
    display_name: str
    beancount_account: str
    category_type: str
    parent_category: str | None = None
    icon: str | None = None
    color: str | None = None
    description: str | None = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    display_name: str | None = None
    beancount_account: str | None = None
    parent_category: str | None = None
    icon: str | None = None
    color: str | None = None
    description: str | None = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

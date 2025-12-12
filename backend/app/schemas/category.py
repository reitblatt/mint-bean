"""Category schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str
    display_name: str
    beancount_account: str
    category_type: str
    parent_id: int | None = None
    icon: str | None = None
    color: str | None = None
    description: str | None = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    display_order: int = 0
    is_active: bool = True
    is_system: bool = False


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = None
    display_name: str | None = None
    beancount_account: str | None = None
    category_type: str | None = None
    parent_id: int | None = None
    icon: str | None = None
    color: str | None = None
    description: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    display_order: int
    is_active: bool
    is_system: bool
    transaction_count: int
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CategoryTreeNode(BaseModel):
    """Schema for category hierarchy tree node."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    category_type: str
    icon: str | None = None
    color: str | None = None
    parent_id: int | None = None
    transaction_count: int
    children: list["CategoryTreeNode"] = []


class CategoryMergeRequest(BaseModel):
    """Schema for merging categories."""

    source_category_ids: list[int]
    target_category_id: int
    delete_source_categories: bool = True

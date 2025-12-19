"""Plaid Category Mapping schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.category import CategoryResponse


class PlaidCategoryMappingBase(BaseModel):
    """Base Plaid category mapping schema."""

    plaid_primary_category: str
    plaid_detailed_category: str | None = None
    category_id: int
    confidence: float = 1.0
    auto_apply: bool = True


class PlaidCategoryMappingCreate(PlaidCategoryMappingBase):
    """Schema for creating a Plaid category mapping."""

    pass


class PlaidCategoryMappingUpdate(BaseModel):
    """Schema for updating a Plaid category mapping."""

    category_id: int | None = None
    confidence: float | None = None
    auto_apply: bool | None = None


class PlaidCategoryMappingResponse(PlaidCategoryMappingBase):
    """Schema for Plaid category mapping response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category: CategoryResponse  # Include full category object
    match_count: int
    last_matched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

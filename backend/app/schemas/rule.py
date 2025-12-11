"""Rule schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class RuleBase(BaseModel):
    """Base rule schema."""

    name: str
    description: str | None = None
    conditions: dict[str, Any]
    actions: dict[str, Any]
    priority: int = 0
    active: bool = True


class RuleCreate(RuleBase):
    """Schema for creating a rule."""

    category_id: int | None = None


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""

    name: str | None = None
    description: str | None = None
    conditions: dict[str, Any] | None = None
    actions: dict[str, Any] | None = None
    category_id: int | None = None
    priority: int | None = None
    active: bool | None = None


class RuleResponse(RuleBase):
    """Schema for rule response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int | None = None
    match_count: int = 0
    last_matched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

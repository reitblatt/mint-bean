"""Rule schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class RuleBase(BaseModel):
    """Base rule schema."""

    name: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 0
    active: bool = True


class RuleCreate(RuleBase):
    """Schema for creating a rule."""

    category_id: Optional[int] = None


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""

    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    category_id: Optional[int] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class RuleResponse(RuleBase):
    """Schema for rule response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: Optional[int] = None
    match_count: int = 0
    last_matched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

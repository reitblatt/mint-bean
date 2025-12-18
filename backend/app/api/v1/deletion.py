"""Deletion impact analysis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.deletion_service import compute_deletion_impact

router = APIRouter()


class DeletionImpactResponse(BaseModel):
    """Response model for deletion impact analysis."""

    entity_type: str
    entity_id: int
    cascades: dict[str, int]
    total_affected: int
    warnings: list[str]


@router.get("/impact/{entity_type}/{entity_id}", response_model=DeletionImpactResponse)
def get_deletion_impact(
    entity_type: str,
    entity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeletionImpactResponse:
    """
    Analyze the impact of deleting an entity.

    Returns information about:
    - How many dependent objects will be cascade deleted
    - Warnings about data loss or broken references
    - Total number of affected objects

    Args:
        entity_type: Type of entity (User, Account, Category, PlaidItem, Rule)
        entity_id: ID of the entity to analyze
        current_user: Current authenticated user
        db: Database session

    Returns:
        Deletion impact analysis

    Raises:
        HTTPException: If entity type is invalid or entity doesn't exist
    """
    # Validate entity type
    valid_types = ["User", "Account", "Category", "PlaidItem", "Rule"]
    if entity_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        # Compute deletion impact
        impact = compute_deletion_impact(
            db=db, entity_type=entity_type, entity_id=entity_id, user_id=current_user.id
        )

        return DeletionImpactResponse(**impact.to_dict())

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error computing deletion impact: {str(e)}"
        ) from e

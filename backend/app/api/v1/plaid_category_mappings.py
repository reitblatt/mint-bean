"""Plaid Category Mapping API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plaid_category_mapping import PlaidCategoryMapping
from app.schemas.plaid_category_mapping import (
    PlaidCategoryMappingCreate,
    PlaidCategoryMappingResponse,
    PlaidCategoryMappingUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[PlaidCategoryMappingResponse])
def list_mappings(
    plaid_primary_category: str | None = None,
    auto_apply_only: bool = False,
    db: Session = Depends(get_db),
) -> list[PlaidCategoryMapping]:
    """
    List all Plaid category mappings.

    Args:
        plaid_primary_category: Filter by Plaid primary category
        auto_apply_only: Only return mappings with auto_apply=True
        db: Database session

    Returns:
        List of Plaid category mappings
    """
    query = db.query(PlaidCategoryMapping)

    if plaid_primary_category:
        query = query.filter(PlaidCategoryMapping.plaid_primary_category == plaid_primary_category)

    if auto_apply_only:
        query = query.filter(PlaidCategoryMapping.auto_apply.is_(True))

    return query.order_by(
        PlaidCategoryMapping.plaid_primary_category,
        PlaidCategoryMapping.plaid_detailed_category,
    ).all()


@router.get("/{mapping_id}", response_model=PlaidCategoryMappingResponse)
def get_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
) -> PlaidCategoryMapping:
    """
    Get a specific Plaid category mapping by ID.

    Args:
        mapping_id: Mapping ID
        db: Database session

    Returns:
        Plaid category mapping details
    """
    mapping = db.query(PlaidCategoryMapping).filter(PlaidCategoryMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping


@router.post("/", response_model=PlaidCategoryMappingResponse, status_code=201)
def create_mapping(
    mapping: PlaidCategoryMappingCreate,
    db: Session = Depends(get_db),
) -> PlaidCategoryMapping:
    """
    Create a new Plaid category mapping.

    Args:
        mapping: Mapping data
        db: Database session

    Returns:
        Created mapping
    """
    # Check if mapping already exists
    existing = (
        db.query(PlaidCategoryMapping)
        .filter(
            PlaidCategoryMapping.plaid_primary_category == mapping.plaid_primary_category,
            PlaidCategoryMapping.plaid_detailed_category == mapping.plaid_detailed_category,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Mapping already exists for this Plaid category combination",
        )

    db_mapping = PlaidCategoryMapping(**mapping.model_dump())
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@router.patch("/{mapping_id}", response_model=PlaidCategoryMappingResponse)
def update_mapping(
    mapping_id: int,
    mapping: PlaidCategoryMappingUpdate,
    db: Session = Depends(get_db),
) -> PlaidCategoryMapping:
    """
    Update a Plaid category mapping.

    Args:
        mapping_id: Mapping ID
        mapping: Updated mapping data
        db: Database session

    Returns:
        Updated mapping
    """
    db_mapping = (
        db.query(PlaidCategoryMapping).filter(PlaidCategoryMapping.id == mapping_id).first()
    )
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    update_data = mapping.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_mapping, field, value)

    db.commit()
    db.refresh(db_mapping)
    return db_mapping


@router.delete("/{mapping_id}", status_code=204)
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a Plaid category mapping.

    Args:
        mapping_id: Mapping ID
        db: Database session
    """
    db_mapping = (
        db.query(PlaidCategoryMapping).filter(PlaidCategoryMapping.id == mapping_id).first()
    )
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    db.delete(db_mapping)
    db.commit()


@router.post("/bulk", response_model=list[PlaidCategoryMappingResponse], status_code=201)
def create_bulk_mappings(
    mappings: list[PlaidCategoryMappingCreate],
    skip_existing: bool = True,
    db: Session = Depends(get_db),
) -> list[PlaidCategoryMapping]:
    """
    Create multiple Plaid category mappings at once.

    Args:
        mappings: List of mapping data
        skip_existing: Skip mappings that already exist instead of erroring
        db: Database session

    Returns:
        List of created mappings
    """
    created_mappings = []

    for mapping_data in mappings:
        # Check if mapping already exists
        existing = (
            db.query(PlaidCategoryMapping)
            .filter(
                PlaidCategoryMapping.plaid_primary_category == mapping_data.plaid_primary_category,
                PlaidCategoryMapping.plaid_detailed_category
                == mapping_data.plaid_detailed_category,
            )
            .first()
        )

        if existing:
            if skip_existing:
                continue
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Mapping already exists for {mapping_data.plaid_primary_category}:{mapping_data.plaid_detailed_category}",
                )

        db_mapping = PlaidCategoryMapping(**mapping_data.model_dump())
        db.add(db_mapping)
        created_mappings.append(db_mapping)

    db.commit()

    # Refresh all created mappings
    for mapping in created_mappings:
        db.refresh(mapping)

    return created_mappings

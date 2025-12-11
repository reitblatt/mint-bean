"""Category API endpoints."""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter()


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    category_type: str = None,
    db: Session = Depends(get_db),
) -> list[Category]:
    """
    List all categories.

    Args:
        category_type: Filter by category type (expense, income, transfer)
        db: Database session

    Returns:
        List of categories
    """
    query = db.query(Category)
    if category_type:
        query = query.filter(Category.category_type == category_type)
    return query.order_by(Category.name).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
) -> Category:
    """
    Get a specific category by ID.

    Args:
        category_id: Category ID
        db: Database session

    Returns:
        Category details
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
) -> Category:
    """
    Create a new category.

    Args:
        category: Category data
        db: Database session

    Returns:
        Created category
    """
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
) -> Category:
    """
    Update a category.

    Args:
        category_id: Category ID
        category: Updated category data
        db: Database session

    Returns:
        Updated category
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a category.

    Args:
        category_id: Category ID
        db: Database session
    """
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(db_category)
    db.commit()

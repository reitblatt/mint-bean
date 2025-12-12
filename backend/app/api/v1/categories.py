"""Category API endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import (
    CategoryCreate,
    CategoryMergeRequest,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
)

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

    # Check if it's a system category
    if db_category.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system category")

    # Soft delete by marking as inactive
    db_category.is_active = False
    db.commit()


@router.get("/tree", response_model=list[CategoryTreeNode])
def get_category_tree(
    category_type: str | None = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
) -> list[CategoryTreeNode]:
    """
    Get category hierarchy as a tree structure.

    Args:
        category_type: Filter by category type (expense, income, transfer)
        include_inactive: Include inactive categories
        db: Database session

    Returns:
        List of root category nodes with nested children
    """
    # Query all categories
    query = db.query(Category)
    if category_type:
        query = query.filter(Category.category_type == category_type)
    if not include_inactive:
        query = query.filter(Category.is_active.is_(True))

    categories = query.order_by(Category.display_order, Category.name).all()

    # Helper function to build tree recursively
    def build_tree_node(category: Category) -> CategoryTreeNode:
        node = CategoryTreeNode(
            id=category.id,
            name=category.name,
            display_name=category.display_name,
            category_type=category.category_type,
            icon=category.icon,
            color=category.color,
            parent_id=category.parent_id,
            transaction_count=category.transaction_count,
            children=[],
        )

        # Find children
        for cat in categories:
            if cat.parent_id == category.id:
                node.children.append(build_tree_node(cat))

        return node

    # Build tree starting from root nodes (categories with no parent)
    tree = []
    for category in categories:
        if category.parent_id is None:
            tree.append(build_tree_node(category))

    return tree


@router.post("/merge", response_model=CategoryResponse)
def merge_categories(
    merge_request: CategoryMergeRequest,
    db: Session = Depends(get_db),
) -> Category:
    """
    Merge multiple categories into a target category.

    All transactions from source categories are moved to the target category.
    Optionally deletes source categories after merging.

    Args:
        merge_request: Merge request with source and target category IDs
        db: Database session

    Returns:
        Updated target category
    """
    # Validate target category exists
    target_category = (
        db.query(Category).filter(Category.id == merge_request.target_category_id).first()
    )
    if not target_category:
        raise HTTPException(status_code=404, detail="Target category not found")

    # Validate source categories exist
    source_categories = (
        db.query(Category).filter(Category.id.in_(merge_request.source_category_ids)).all()
    )
    if len(source_categories) != len(merge_request.source_category_ids):
        raise HTTPException(status_code=404, detail="One or more source categories not found")

    # Check for system categories
    for cat in source_categories:
        if cat.is_system:
            raise HTTPException(status_code=400, detail=f"Cannot merge system category: {cat.name}")

    # Update all transactions from source categories to target category
    for source_id in merge_request.source_category_ids:
        db.query(Transaction).filter(Transaction.category_id == source_id).update(
            {"category_id": target_category.id}, synchronize_session=False
        )

    # Update child categories to point to target or null
    for source_id in merge_request.source_category_ids:
        db.query(Category).filter(Category.parent_id == source_id).update(
            {"parent_id": target_category.id}, synchronize_session=False
        )

    # Delete or deactivate source categories
    if merge_request.delete_source_categories:
        for source_id in merge_request.source_category_ids:
            db.query(Category).filter(Category.id == source_id).update(
                {"is_active": False}, synchronize_session=False
            )

    db.commit()

    # Recalculate statistics for target category
    _update_category_statistics(target_category.id, db)

    db.refresh(target_category)
    return target_category


@router.post("/{category_id}/refresh-stats", response_model=CategoryResponse)
def refresh_category_statistics(
    category_id: int,
    db: Session = Depends(get_db),
) -> Category:
    """
    Refresh transaction statistics for a category.

    Recalculates transaction_count and last_used_at from actual transaction data.

    Args:
        category_id: Category ID
        db: Database session

    Returns:
        Updated category with refreshed statistics
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    _update_category_statistics(category_id, db)

    db.refresh(category)
    return category


def _update_category_statistics(category_id: int, db: Session) -> None:
    """
    Helper function to update category statistics.

    Args:
        category_id: Category ID
        db: Database session
    """
    # Count transactions
    transaction_count = db.query(Transaction).filter(Transaction.category_id == category_id).count()

    # Get last used timestamp
    last_transaction = (
        db.query(Transaction)
        .filter(Transaction.category_id == category_id)
        .order_by(Transaction.date.desc())
        .first()
    )

    last_used_at = last_transaction.date if last_transaction else None

    # Update category
    db.query(Category).filter(Category.id == category_id).update(
        {
            "transaction_count": transaction_count,
            "last_used_at": last_used_at,
            "updated_at": datetime.now(UTC),
        },
        synchronize_session=False,
    )
    db.commit()

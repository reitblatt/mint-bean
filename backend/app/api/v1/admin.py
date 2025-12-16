"""Admin API endpoints for user management."""

from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin_user, get_password_hash
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserDeleteRequest,
    UserResponse,
    UserRestoreRequest,
    UserUpdate,
)
from app.services.category_service import seed_default_categories

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    List all users (admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Create a new user (admin only).

    Args:
        user_data: User creation data
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If email already exists (active user) or archived user needs restoration
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        # If user is archived, prompt for restoration
        if existing_user.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "User with this email was previously archived",
                    "user_id": existing_user.id,
                    "archived_at": existing_user.archived_at.isoformat(),
                    "action_required": "Use POST /api/v1/admin/users/{user_id}/restore to restore this user",
                },
            )
        # If user is active, reject
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered with an active user",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin,
        is_active=True,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Seed default categories for the new user
    seed_default_categories(db, db_user.id)

    return db_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific user (admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Update a user (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found or email conflict
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields if provided
    update_data = user_data.model_dump(exclude_unset=True)

    # Check for email conflict if email is being updated
    if "email" in update_data and update_data["email"] != user.email:
        existing_user = db.query(User).filter(User.email == update_data["email"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Handle password update separately
    if "password" in update_data:
        user.hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]

    # Update other fields
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    delete_options: UserDeleteRequest = Body(default=UserDeleteRequest()),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Delete or archive a user (admin only).

    Args:
        user_id: User ID
        delete_options: Deletion options (hard_delete: True for permanent, False for archive)
        current_user: Current authenticated admin user
        db: Database session

    Raises:
        HTTPException: If user not found or trying to delete self
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if delete_options.hard_delete:
        # Hard delete - permanently remove user and all data
        db.delete(user)
    else:
        # Soft delete - archive user (keeps all data)
        user.archived_at = datetime.now(UTC)
        user.is_active = False

    db.commit()
    return None


@router.post("/users/{user_id}/restore", response_model=UserResponse)
def restore_user(
    user_id: int,
    restore_options: UserRestoreRequest = Body(default=UserRestoreRequest()),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Restore an archived user (admin only).

    Args:
        user_id: User ID
        restore_options: Restoration options (restore_data: True to keep data, False to reset)
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Restored user

    Raises:
        HTTPException: If user not found or not archived
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.archived_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not archived",
        )

    # Restore user
    user.archived_at = None
    user.is_active = True

    if not restore_options.restore_data:
        # Delete all user data and start fresh
        # The cascade deletes will handle related data
        for account in user.accounts:
            db.delete(account)
        for transaction in user.transactions:
            db.delete(transaction)
        for category in user.categories:
            db.delete(category)
        for rule in user.rules:
            db.delete(rule)
        for plaid_item in user.plaid_items:
            db.delete(plaid_item)
        for mapping in user.plaid_category_mappings:
            db.delete(mapping)

        db.commit()
        db.refresh(user)

        # Seed default categories for fresh start
        seed_default_categories(db, user.id)
    else:
        # Just restore the user, keeping all data
        db.commit()
        db.refresh(user)

    return user


@router.post("/users/{user_id}/reset-password", response_model=UserResponse)
def reset_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Reset a user's password (admin only).

    Args:
        user_id: User ID
        new_password: New password
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found or password too short
    """
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)

    return user

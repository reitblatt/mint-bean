"""Service for soft delete operations with audit trail support."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.plaid_item import PlaidItem
from app.models.rule import Rule
from app.models.transaction import Transaction
from app.models.user import User


def soft_delete_user(db: Session, user_id: int) -> User:
    """
    Soft delete a user by setting archived_at timestamp.

    Args:
        db: Database session
        user_id: ID of user to soft delete

    Returns:
        Updated user object

    Raises:
        ValueError: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    if user.archived_at:
        raise ValueError(f"User {user_id} is already archived")

    user.archived_at = datetime.now(UTC)
    user.is_active = False
    db.commit()
    db.refresh(user)

    return user


def restore_user(db: Session, user_id: int) -> User:
    """
    Restore a soft-deleted user.

    Args:
        db: Database session
        user_id: ID of user to restore

    Returns:
        Updated user object

    Raises:
        ValueError: If user not found or not archived
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    if not user.archived_at:
        raise ValueError(f"User {user_id} is not archived")

    user.archived_at = None
    user.is_active = True
    db.commit()
    db.refresh(user)

    return user


def soft_delete_category(db: Session, category_id: int, user_id: int) -> Category:
    """
    Soft delete a category by setting is_active to False.

    Args:
        db: Database session
        category_id: ID of category to soft delete
        user_id: ID of user (for permission check)

    Returns:
        Updated category object

    Raises:
        ValueError: If category not found or not owned by user
    """
    category = (
        db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    )
    if not category:
        raise ValueError(f"Category {category_id} not found or not owned by user {user_id}")

    if category.is_system:
        raise ValueError(f"Cannot delete system category '{category.name}'")

    if not category.is_active:
        raise ValueError(f"Category {category_id} is already inactive")

    category.is_active = False
    db.commit()
    db.refresh(category)

    return category


def restore_category(db: Session, category_id: int, user_id: int) -> Category:
    """
    Restore a soft-deleted category.

    Args:
        db: Database session
        category_id: ID of category to restore
        user_id: ID of user (for permission check)

    Returns:
        Updated category object

    Raises:
        ValueError: If category not found or not owned by user
    """
    category = (
        db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    )
    if not category:
        raise ValueError(f"Category {category_id} not found or not owned by user {user_id}")

    if category.is_active:
        raise ValueError(f"Category {category_id} is already active")

    category.is_active = True
    db.commit()
    db.refresh(category)

    return category


def hard_delete_with_cascades(
    db: Session, entity_type: str, entity_id: int, user_id: int
) -> dict[str, int]:
    """
    Perform a hard delete with cascades.

    This function actually deletes the entity and all its dependent objects from the database.

    Args:
        db: Database session
        entity_type: Type of entity (User, Account, Category, etc.)
        entity_id: ID of entity to delete
        user_id: ID of user (for permission check)

    Returns:
        Dictionary mapping entity types to counts of deleted objects

    Raises:
        ValueError: If entity type is unknown or entity doesn't exist
    """
    deleted_counts: dict[str, int] = {}

    if entity_type == "Account":
        account = (
            db.query(Account).filter(Account.id == entity_id, Account.user_id == user_id).first()
        )
        if not account:
            raise ValueError(f"Account {entity_id} not found or not owned by user {user_id}")

        # Count and delete transactions
        transaction_count = (
            db.query(Transaction)
            .filter(Transaction.account_id == entity_id, Transaction.user_id == user_id)
            .count()
        )
        db.query(Transaction).filter(
            Transaction.account_id == entity_id, Transaction.user_id == user_id
        ).delete()
        deleted_counts["Transaction"] = transaction_count

        # Delete the account
        db.delete(account)
        deleted_counts["Account"] = 1

        db.commit()

    elif entity_type == "Category":
        category = (
            db.query(Category).filter(Category.id == entity_id, Category.user_id == user_id).first()
        )
        if not category:
            raise ValueError(f"Category {entity_id} not found or not owned by user {user_id}")

        if category.is_system:
            raise ValueError(f"Cannot delete system category '{category.name}'")

        # Unlink transactions (they don't get deleted)
        transaction_count = (
            db.query(Transaction)
            .filter(Transaction.category_id == entity_id, Transaction.user_id == user_id)
            .count()
        )
        db.query(Transaction).filter(
            Transaction.category_id == entity_id, Transaction.user_id == user_id
        ).update({Transaction.category_id: None})

        # Update rules that reference this category
        db.query(Rule).filter(Rule.category_id == entity_id).update({Rule.category_id: None})

        # Update child categories to become top-level
        db.query(Category).filter(
            Category.parent_id == entity_id, Category.user_id == user_id
        ).update({Category.parent_id: None})

        # Delete the category
        db.delete(category)
        deleted_counts["Category"] = 1

        db.commit()

    elif entity_type == "PlaidItem":
        plaid_item = (
            db.query(PlaidItem)
            .filter(PlaidItem.id == entity_id, PlaidItem.user_id == user_id)
            .first()
        )
        if not plaid_item:
            raise ValueError(f"PlaidItem {entity_id} not found or not owned by user {user_id}")

        # Delete the Plaid item (accounts are not deleted, just unlinked)
        db.delete(plaid_item)
        deleted_counts["PlaidItem"] = 1

        db.commit()

    elif entity_type == "Rule":
        rule = db.query(Rule).filter(Rule.id == entity_id, Rule.user_id == user_id).first()
        if not rule:
            raise ValueError(f"Rule {entity_id} not found or not owned by user {user_id}")

        # Delete the rule
        db.delete(rule)
        deleted_counts["Rule"] = 1

        db.commit()

    else:
        raise ValueError(f"Unsupported entity type for deletion: {entity_type}")

    return deleted_counts

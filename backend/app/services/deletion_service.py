"""Service for managing data deletion and computing deletion impacts."""

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.deletion_policy import DELETION_REGISTRY, DeletionPolicy
from app.models.plaid_category_mapping import PlaidCategoryMapping
from app.models.plaid_item import PlaidItem
from app.models.rule import Rule
from app.models.transaction import Transaction


class DeletionImpact:
    """
    Represents the impact of deleting an object.

    Attributes:
        entity_type: The type of entity being deleted
        entity_id: The ID of the entity being deleted
        cascades: Dictionary mapping entity types to counts of objects that will be deleted
        warnings: List of warning messages about the deletion
    """

    def __init__(self, entity_type: str, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.cascades: dict[str, int] = {}
        self.warnings: list[str] = []

    def add_cascade(self, entity_type: str, count: int) -> None:
        """Add a cascade deletion count for an entity type."""
        if count > 0:
            self.cascades[entity_type] = count

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def total_affected(self) -> int:
        """Get total number of objects that will be affected (including the main object)."""
        return 1 + sum(self.cascades.values())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "cascades": self.cascades,
            "total_affected": self.total_affected(),
            "warnings": self.warnings,
        }


def compute_deletion_impact(
    db: Session, entity_type: str, entity_id: int, user_id: int
) -> DeletionImpact:
    """
    Compute the impact of deleting an entity.

    Args:
        db: Database session
        entity_type: Type of entity (User, Account, Category, etc.)
        entity_id: ID of the entity to delete
        user_id: ID of the current user (for permission checks)

    Returns:
        DeletionImpact object describing what will be deleted

    Raises:
        ValueError: If entity type is unknown or entity doesn't exist
    """
    impact = DeletionImpact(entity_type, entity_id)

    # Get deletion metadata for this entity type
    metadata = DELETION_REGISTRY.get(entity_type)
    if not metadata:
        raise ValueError(f"Unknown entity type: {entity_type}")

    # Check policy
    if metadata.policy == DeletionPolicy.MANUAL:
        impact.add_warning(f"{entity_type} can only be deleted manually via UI")

    # Compute cascades based on entity type
    if entity_type == "User":
        _compute_user_deletion_impact(db, entity_id, impact)
    elif entity_type == "Account":
        _compute_account_deletion_impact(db, entity_id, user_id, impact)
    elif entity_type == "Category":
        _compute_category_deletion_impact(db, entity_id, user_id, impact)
    elif entity_type == "PlaidItem":
        _compute_plaid_item_deletion_impact(db, entity_id, user_id, impact)
    elif entity_type == "Rule":
        _compute_rule_deletion_impact(db, entity_id, user_id, impact)

    return impact


def _compute_user_deletion_impact(db: Session, user_id: int, impact: DeletionImpact) -> None:
    """Compute impact of deleting a user."""
    # Count all user-owned entities
    plaid_item_count = (
        db.query(func.count(PlaidItem.id)).filter(PlaidItem.user_id == user_id).scalar()
    )
    account_count = db.query(func.count(Account.id)).filter(Account.user_id == user_id).scalar()
    transaction_count = (
        db.query(func.count(Transaction.id)).filter(Transaction.user_id == user_id).scalar()
    )
    category_count = db.query(func.count(Category.id)).filter(Category.user_id == user_id).scalar()
    rule_count = db.query(func.count(Rule.id)).filter(Rule.user_id == user_id).scalar()
    mapping_count = (
        db.query(func.count(PlaidCategoryMapping.id))
        .filter(PlaidCategoryMapping.user_id == user_id)
        .scalar()
    )

    impact.add_cascade("PlaidItem", plaid_item_count)
    impact.add_cascade("Account", account_count)
    impact.add_cascade("Transaction", transaction_count)
    impact.add_cascade("Category", category_count)
    impact.add_cascade("Rule", rule_count)
    impact.add_cascade("PlaidCategoryMapping", mapping_count)

    if transaction_count > 0:
        impact.add_warning(
            f"Deleting this user will permanently delete {transaction_count} transactions"
        )


def _compute_account_deletion_impact(
    db: Session, account_id: int, user_id: int, impact: DeletionImpact
) -> None:
    """Compute impact of deleting an account."""
    # Verify account ownership
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()
    if not account:
        raise ValueError(f"Account {account_id} not found or not owned by user {user_id}")

    # Count transactions for this account
    transaction_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.account_id == account_id, Transaction.user_id == user_id)
        .scalar()
    )

    impact.add_cascade("Transaction", transaction_count)

    if transaction_count > 0:
        impact.add_warning(
            f"Deleting account '{account.name}' will permanently delete {transaction_count} transactions"
        )

    # Check if any rules reference this account
    rule_count = (
        db.query(func.count(Rule.id))
        .filter(Rule.user_id == user_id)
        .filter(Rule.conditions.like(f'%"account_id": {account_id}%'))
        .scalar()
    )

    if rule_count > 0:
        impact.add_warning(
            f"{rule_count} rule(s) reference this account and may need to be updated"
        )


def _compute_category_deletion_impact(
    db: Session, category_id: int, user_id: int, impact: DeletionImpact
) -> None:
    """Compute impact of deleting a category."""
    # Verify category ownership
    category = (
        db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    )
    if not category:
        raise ValueError(f"Category {category_id} not found or not owned by user {user_id}")

    # Check if category is a system category
    if category.is_system:
        raise ValueError(f"Cannot delete system category '{category.name}'")

    # Count transactions using this category
    transaction_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.category_id == category_id, Transaction.user_id == user_id)
        .scalar()
    )

    if transaction_count > 0:
        impact.add_warning(
            f"{transaction_count} transaction(s) use this category and will become uncategorized"
        )

    # Check if any rules reference this category
    rule_count = db.query(func.count(Rule.id)).filter(Rule.category_id == category_id).scalar()

    if rule_count > 0:
        impact.add_warning(
            f"{rule_count} rule(s) reference this category and may need to be updated"
        )

    # Check for child categories
    child_count = (
        db.query(func.count(Category.id))
        .filter(Category.parent_id == category_id, Category.user_id == user_id)
        .scalar()
    )

    if child_count > 0:
        impact.add_warning(
            f"{child_count} child categor{'y' if child_count == 1 else 'ies'} will become top-level categories"
        )


def _compute_plaid_item_deletion_impact(
    db: Session, plaid_item_id: int, user_id: int, impact: DeletionImpact
) -> None:
    """Compute impact of deleting a Plaid item."""
    # Verify Plaid item ownership
    plaid_item = (
        db.query(PlaidItem)
        .filter(PlaidItem.id == plaid_item_id, PlaidItem.user_id == user_id)
        .first()
    )
    if not plaid_item:
        raise ValueError(f"PlaidItem {plaid_item_id} not found or not owned by user {user_id}")

    # Count accounts linked to this Plaid item
    account_count = (
        db.query(func.count(Account.id))
        .filter(Account.plaid_item_id == plaid_item.item_id, Account.user_id == user_id)
        .scalar()
    )

    if account_count > 0:
        impact.add_warning(
            f"Deleting this Plaid connection will affect {account_count} account(s). "
            "Accounts will not be deleted but will no longer sync."
        )


def _compute_rule_deletion_impact(
    db: Session, rule_id: int, user_id: int, impact: DeletionImpact
) -> None:
    """Compute impact of deleting a rule."""
    # Verify rule ownership
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.user_id == user_id).first()
    if not rule:
        raise ValueError(f"Rule {rule_id} not found or not owned by user {user_id}")

    # Rules don't cascade delete anything, but we can show statistics
    if rule.match_count > 0:
        impact.add_warning(
            f"This rule has been applied to {rule.match_count} transaction(s). "
            "Those transactions will keep their categorization."
        )

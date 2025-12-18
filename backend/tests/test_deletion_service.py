"""Tests for deletion service."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.plaid_item import PlaidItem
from app.models.rule import Rule
from app.models.transaction import Transaction
from app.models.user import User
from app.services.deletion_service import (
    compute_deletion_impact,
)
from app.services.soft_delete_service import (
    hard_delete_with_cascades,
    restore_category,
    restore_user,
    soft_delete_category,
    soft_delete_user,
)


@pytest.fixture
def user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashedpassword",
        is_admin=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def category(db: Session, user: User) -> Category:
    """Create a test category."""
    category = Category(
        user_id=user.id,
        name="Test:Category",
        display_name="Test Category",
        beancount_account="Expenses:Test",
        category_type="expense",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def account(db: Session, user: User) -> Account:
    """Create a test account."""
    account = Account(
        user_id=user.id,
        account_id="test_account_001",
        name="Test Account",
        type="checking",
        beancount_account="Assets:Bank:Checking",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def transaction(db: Session, user: User, account: Account, category: Category) -> Transaction:
    """Create a test transaction."""
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        transaction_id="test_txn_001",
        date=datetime.now(UTC),
        amount=100.00,
        description="Test Transaction",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@pytest.fixture
def plaid_item(db: Session, user: User) -> PlaidItem:
    """Create a test Plaid item."""
    plaid_item = PlaidItem(
        user_id=user.id,
        item_id="test_item_001",
        access_token="test_access_token",
        institution_name="Test Bank",
        environment="sandbox",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(plaid_item)
    db.commit()
    db.refresh(plaid_item)
    return plaid_item


@pytest.fixture
def rule(db: Session, user: User, category: Category) -> Rule:
    """Create a test rule."""
    rule = Rule(
        user_id=user.id,
        category_id=category.id,
        name="Test Rule",
        conditions='{"field": "description", "operator": "contains", "value": "test"}',
        actions='{"set_category": "Test:Category"}',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


class TestComputeDeletionImpact:
    """Tests for compute_deletion_impact function."""

    def test_compute_user_deletion_impact(
        self,
        db: Session,
        user: User,
        account: Account,
        transaction: Transaction,
        category: Category,
    ):
        """Test computing impact of deleting a user."""
        impact = compute_deletion_impact(
            db=db, entity_type="User", entity_id=user.id, user_id=user.id
        )

        assert impact.entity_type == "User"
        assert impact.entity_id == user.id
        assert impact.cascades["Account"] >= 1
        assert impact.cascades["Transaction"] >= 1
        assert impact.cascades["Category"] >= 1
        assert impact.total_affected() > 1
        assert len(impact.warnings) > 0

    def test_compute_account_deletion_impact(
        self, db: Session, user: User, account: Account, transaction: Transaction
    ):
        """Test computing impact of deleting an account."""
        impact = compute_deletion_impact(
            db=db, entity_type="Account", entity_id=account.id, user_id=user.id
        )

        assert impact.entity_type == "Account"
        assert impact.entity_id == account.id
        assert impact.cascades["Transaction"] >= 1
        assert impact.total_affected() >= 2  # Account + Transaction
        assert any("transaction" in w.lower() for w in impact.warnings)

    def test_compute_category_deletion_impact(
        self, db: Session, user: User, category: Category, transaction: Transaction, rule: Rule
    ):
        """Test computing impact of deleting a category."""
        impact = compute_deletion_impact(
            db=db, entity_type="Category", entity_id=category.id, user_id=user.id
        )

        assert impact.entity_type == "Category"
        assert impact.entity_id == category.id
        assert len(impact.warnings) > 0
        # Should warn about transactions and rules
        assert any("transaction" in w.lower() for w in impact.warnings)
        assert any("rule" in w.lower() for w in impact.warnings)

    def test_compute_plaid_item_deletion_impact(
        self, db: Session, user: User, plaid_item: PlaidItem
    ):
        """Test computing impact of deleting a Plaid item."""
        impact = compute_deletion_impact(
            db=db, entity_type="PlaidItem", entity_id=plaid_item.id, user_id=user.id
        )

        assert impact.entity_type == "PlaidItem"
        assert impact.entity_id == plaid_item.id

    def test_compute_rule_deletion_impact(self, db: Session, user: User, rule: Rule):
        """Test computing impact of deleting a rule."""
        impact = compute_deletion_impact(
            db=db, entity_type="Rule", entity_id=rule.id, user_id=user.id
        )

        assert impact.entity_type == "Rule"
        assert impact.entity_id == rule.id

    def test_compute_deletion_impact_invalid_entity_type(self, db: Session, user: User):
        """Test computing impact with invalid entity type."""
        with pytest.raises(ValueError, match="Unknown entity type"):
            compute_deletion_impact(
                db=db, entity_type="InvalidType", entity_id=999, user_id=user.id
            )

    def test_compute_deletion_impact_nonexistent_entity(self, db: Session, user: User):
        """Test computing impact for nonexistent entity."""
        with pytest.raises(ValueError, match="not found"):
            compute_deletion_impact(db=db, entity_type="Account", entity_id=99999, user_id=user.id)


class TestSoftDelete:
    """Tests for soft delete operations."""

    def test_soft_delete_user(self, db: Session, user: User):
        """Test soft deleting a user."""
        result = soft_delete_user(db=db, user_id=user.id)

        assert result.id == user.id
        assert result.archived_at is not None
        assert result.is_active is False

        # Verify in database
        db.refresh(user)
        assert user.archived_at is not None
        assert user.is_active is False

    def test_restore_user(self, db: Session, user: User):
        """Test restoring a soft-deleted user."""
        # First soft delete
        soft_delete_user(db=db, user_id=user.id)

        # Then restore
        result = restore_user(db=db, user_id=user.id)

        assert result.id == user.id
        assert result.archived_at is None
        assert result.is_active is True

    def test_soft_delete_category(self, db: Session, user: User, category: Category):
        """Test soft deleting a category."""
        result = soft_delete_category(db=db, category_id=category.id, user_id=user.id)

        assert result.id == category.id
        assert result.is_active is False

        # Verify in database
        db.refresh(category)
        assert category.is_active is False

    def test_restore_category(self, db: Session, user: User, category: Category):
        """Test restoring a soft-deleted category."""
        # First soft delete
        soft_delete_category(db=db, category_id=category.id, user_id=user.id)

        # Then restore
        result = restore_category(db=db, category_id=category.id, user_id=user.id)

        assert result.id == category.id
        assert result.is_active is True

    def test_soft_delete_system_category_fails(self, db: Session, user: User):
        """Test that soft deleting a system category fails."""
        system_category = Category(
            user_id=user.id,
            name="System:Category",
            display_name="System Category",
            beancount_account="Expenses:System",
            category_type="expense",
            is_system=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(system_category)
        db.commit()
        db.refresh(system_category)

        with pytest.raises(ValueError, match="Cannot delete system category"):
            soft_delete_category(db=db, category_id=system_category.id, user_id=user.id)


class TestHardDelete:
    """Tests for hard delete operations."""

    def test_hard_delete_account_with_transactions(
        self, db: Session, user: User, account: Account, transaction: Transaction
    ):
        """Test hard deleting an account cascades to transactions."""
        account_id = account.id
        transaction_id = transaction.id

        # Delete the account
        deleted_counts = hard_delete_with_cascades(
            db=db, entity_type="Account", entity_id=account_id, user_id=user.id
        )

        assert deleted_counts["Account"] == 1
        assert deleted_counts["Transaction"] >= 1

        # Verify account and transaction are gone
        assert db.query(Account).filter(Account.id == account_id).first() is None
        assert db.query(Transaction).filter(Transaction.id == transaction_id).first() is None

    def test_hard_delete_category_unlinks_transactions(
        self, db: Session, user: User, category: Category, transaction: Transaction
    ):
        """Test hard deleting a category unlinks but doesn't delete transactions."""
        category_id = category.id
        transaction_id = transaction.id

        # Delete the category
        deleted_counts = hard_delete_with_cascades(
            db=db, entity_type="Category", entity_id=category_id, user_id=user.id
        )

        assert deleted_counts["Category"] == 1

        # Verify category is gone
        assert db.query(Category).filter(Category.id == category_id).first() is None

        # Verify transaction still exists but has no category
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        assert transaction is not None
        assert transaction.category_id is None

    def test_hard_delete_rule(self, db: Session, user: User, rule: Rule):
        """Test hard deleting a rule."""
        rule_id = rule.id

        # Delete the rule
        deleted_counts = hard_delete_with_cascades(
            db=db, entity_type="Rule", entity_id=rule_id, user_id=user.id
        )

        assert deleted_counts["Rule"] == 1

        # Verify rule is gone
        assert db.query(Rule).filter(Rule.id == rule_id).first() is None

    def test_hard_delete_nonexistent_entity_fails(self, db: Session, user: User):
        """Test hard deleting nonexistent entity fails."""
        with pytest.raises(ValueError, match="not found"):
            hard_delete_with_cascades(
                db=db, entity_type="Account", entity_id=99999, user_id=user.id
            )

    def test_hard_delete_system_category_fails(self, db: Session, user: User):
        """Test hard deleting system category fails."""
        system_category = Category(
            user_id=user.id,
            name="System:Category",
            display_name="System Category",
            beancount_account="Expenses:System",
            category_type="expense",
            is_system=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(system_category)
        db.commit()
        db.refresh(system_category)

        with pytest.raises(ValueError, match="Cannot delete system category"):
            hard_delete_with_cascades(
                db=db, entity_type="Category", entity_id=system_category.id, user_id=user.id
            )

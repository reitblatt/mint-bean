"""Integration tests for data isolation between users.

These tests verify that users cannot access each other's data through the API.
"""

from datetime import datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_password_hash
from app.models.account import Account
from app.models.category import Category
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.models.user import User


@pytest.fixture
def user1(db: Session) -> User:
    """Create first test user."""
    user = User(
        email="user1@example.com",
        hashed_password=get_password_hash("password1"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user2(db: Session) -> User:
    """Create second test user."""
    user = User(
        email="user2@example.com",
        hashed_password=get_password_hash("password2"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers_user1(user1: User) -> dict:
    """Create authentication headers for user1."""
    token = create_access_token(data={"sub": str(user1.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(user2: User) -> dict:
    """Create authentication headers for user2."""
    token = create_access_token(data={"sub": str(user2.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user1_transaction(db: Session, user1: User) -> Transaction:
    """Create a transaction owned by user1."""
    # Create account first
    account = Account(
        user_id=user1.id,
        account_id="user1_acc_1",
        name="User1 Checking",
        type="depository",
        beancount_account="Assets:Checking:User1",
        currency="USD",
        environment="sandbox",
        is_active=True,
    )
    db.add(account)
    db.commit()

    transaction = Transaction(
        user_id=user1.id,
        transaction_id="user1_txn_1",
        account_id=account.id,
        date=datetime(2024, 3, 15),
        amount=-100.00,
        description="User1's private transaction",
        payee="Private Store",
        currency="USD",
        environment="sandbox",
        pending=False,
        reviewed=False,
        synced_to_beancount=False,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@pytest.fixture
def user1_account(db: Session, user1: User) -> Account:
    """Create an account owned by user1."""
    account = Account(
        user_id=user1.id,
        account_id="user1_acc_2",
        name="User1 Savings",
        type="depository",
        beancount_account="Assets:Savings:User1",
        currency="USD",
        environment="sandbox",
        is_active=True,
        current_balance=5000.00,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def user1_category(db: Session, user1: User) -> Category:
    """Create a category owned by user1."""
    category = Category(
        user_id=user1.id,
        name="user1_category",
        display_name="User1 Private Category",
        beancount_account="Expenses:User1:Private",
        category_type="expense",
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def user1_plaid_item(db: Session, user1: User) -> PlaidItem:
    """Create a Plaid item owned by user1."""
    item = PlaidItem(
        user_id=user1.id,
        item_id="user1_item_123",
        access_token="user1-access-token",
        institution_id="ins_user1",
        institution_name="User1 Bank",
        environment="sandbox",
        is_active=True,
        needs_update=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ============================================================================
# Transaction Isolation Tests
# ============================================================================


def test_user_cannot_list_other_users_transactions(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that user2 cannot see user1's transactions in list endpoint."""
    response = client.get("/api/v1/transactions", headers=auth_headers_user2)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total"] == 0
    assert len(data["transactions"]) == 0


def test_user_cannot_get_other_users_transaction_by_id(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that user2 cannot access user1's transaction by ID."""
    response = client.get(
        f"/api/v1/transactions/{user1_transaction.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_user_cannot_update_other_users_transaction(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that user2 cannot update user1's transaction."""
    response = client.patch(
        f"/api/v1/transactions/{user1_transaction.id}",
        headers=auth_headers_user2,
        json={"amount": -999.99},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_delete_other_users_transaction(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that user2 cannot delete user1's transaction."""
    response = client.delete(
        f"/api/v1/transactions/{user1_transaction.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Account Isolation Tests
# ============================================================================


def test_user_cannot_list_other_users_accounts(
    client: TestClient,
    user1_account: Account,
    auth_headers_user2: dict,
):
    """Test that user2 cannot see user1's accounts."""
    response = client.get("/api/v1/accounts", headers=auth_headers_user2)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 0


def test_user_cannot_get_other_users_account_by_id(
    client: TestClient,
    user1_account: Account,
    auth_headers_user2: dict,
):
    """Test that user2 cannot access user1's account by ID."""
    response = client.get(
        f"/api/v1/accounts/{user1_account.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_update_other_users_account(
    client: TestClient,
    user1_account: Account,
    auth_headers_user2: dict,
):
    """Test that user2 cannot update user1's account."""
    response = client.patch(
        f"/api/v1/accounts/{user1_account.id}",
        headers=auth_headers_user2,
        json={"name": "Hacked Account"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Category Isolation Tests
# ============================================================================


def test_user_cannot_list_other_users_categories(
    client: TestClient,
    user1_category: Category,
    auth_headers_user2: dict,
):
    """Test that user2 cannot see user1's categories."""
    response = client.get("/api/v1/categories", headers=auth_headers_user2)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Should only contain default categories, not user1's custom category
    category_names = [cat["name"] for cat in data]
    assert user1_category.name not in category_names


def test_user_cannot_get_other_users_category_by_id(
    client: TestClient,
    user1_category: Category,
    auth_headers_user2: dict,
):
    """Test that user2 cannot access user1's category by ID."""
    response = client.get(
        f"/api/v1/categories/{user1_category.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_update_other_users_category(
    client: TestClient,
    user1_category: Category,
    auth_headers_user2: dict,
):
    """Test that user2 cannot update user1's category."""
    response = client.patch(
        f"/api/v1/categories/{user1_category.id}",
        headers=auth_headers_user2,
        json={"display_name": "Hacked Category"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_delete_other_users_category(
    client: TestClient,
    user1_category: Category,
    auth_headers_user2: dict,
):
    """Test that user2 cannot delete user1's category."""
    response = client.delete(
        f"/api/v1/categories/{user1_category.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Plaid Item Isolation Tests
# ============================================================================


def test_user_cannot_list_other_users_plaid_items(
    client: TestClient,
    user1_plaid_item: PlaidItem,
    auth_headers_user2: dict,
):
    """Test that user2 cannot see user1's Plaid items."""
    response = client.get("/api/v1/plaid/items", headers=auth_headers_user2)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 0


def test_user_cannot_get_other_users_plaid_item_by_id(
    client: TestClient,
    user1_plaid_item: PlaidItem,
    auth_headers_user2: dict,
):
    """Test that user2 cannot access user1's Plaid item by ID."""
    response = client.get(
        f"/api/v1/plaid/items/{user1_plaid_item.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_sync_other_users_plaid_item(
    client: TestClient,
    user1_plaid_item: PlaidItem,
    auth_headers_user2: dict,
):
    """Test that user2 cannot sync user1's Plaid item."""
    response = client.post(
        f"/api/v1/plaid/items/{user1_plaid_item.id}/sync",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_delete_other_users_plaid_item(
    client: TestClient,
    user1_plaid_item: PlaidItem,
    auth_headers_user2: dict,
):
    """Test that user2 cannot delete user1's Plaid item."""
    response = client.delete(
        f"/api/v1/plaid/items/{user1_plaid_item.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Analytics/Dashboard Isolation Tests
# ============================================================================


def test_analytics_summary_metrics_isolated(
    client: TestClient,
    user1_transaction: Transaction,
    user1_account: Account,
    auth_headers_user2: dict,
):
    """Test that analytics endpoints don't include other users' data."""
    response = client.get(
        "/api/v1/analytics/summary-metrics",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # User2 should see zero values, not user1's data
    assert data["total_balance"] == 0.0
    assert data["total_spending"] == 0.0
    assert data["transaction_count"] == 0
    assert data["account_count"] == 0


def test_analytics_spending_over_time_isolated(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that time series analytics don't include other users' data."""
    response = client.get(
        "/api/v1/analytics/spending-over-time",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # User2 should see no data points from user1
    assert len(data["data"]) == 0


def test_analytics_spending_by_category_isolated(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that category breakdown doesn't include other users' data."""
    response = client.get(
        "/api/v1/analytics/spending-by-category",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # User2 should see no spending data from user1
    assert len(data["data"]) == 0
    assert data["total_amount"] == 0.0


def test_flexible_widget_query_isolated(
    client: TestClient,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that flexible widget queries don't leak data between users."""
    response = client.post(
        "/api/v1/analytics/query/metric",
        headers=auth_headers_user2,
        json={
            "metric": "total_spending",
            "filters": [],
        },
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # User2 should see 0, not user1's spending
    assert data["value"] == 0.0


# ============================================================================
# Cross-User Data Leakage Edge Cases
# ============================================================================


def test_user_owns_created_transaction(
    client: TestClient,
    user1_account: Account,
    auth_headers_user1: dict,
    user2: User,
    db: Session,
):
    """Test that created transactions are owned by the authenticated user."""
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers_user1,
        json={
            "account_id": user1_account.id,
            "date": "2024-03-15",
            "amount": -50.00,
            "description": "Test transaction",
            "currency": "USD",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    transaction_id = response.json()["id"]
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    # Verify the transaction is owned by user1, not user2
    assert transaction.user_id == user1_account.user_id
    assert transaction.user_id != user2.id


def test_user_cannot_create_account_for_other_user(
    client: TestClient,
    auth_headers_user2: dict,
    user1: User,
    db: Session,
):
    """Test that users cannot create resources for other users."""
    response = client.post(
        "/api/v1/accounts",
        headers=auth_headers_user2,
        json={
            "account_id": "malicious_acc",
            "name": "Hacked Account",
            "type": "depository",
            "beancount_account": "Assets:Hacked",
            "currency": "USD",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    account_id = response.json()["id"]
    account = db.query(Account).filter(Account.id == account_id).first()

    # Verify the account is owned by user2, not user1
    assert account.user_id != user1.id


def test_filter_by_account_id_respects_ownership(
    client: TestClient,
    user1_account: Account,
    user1_transaction: Transaction,
    auth_headers_user2: dict,
):
    """Test that filtering by account_id still respects user ownership."""
    # User2 tries to filter by user1's account_id
    response = client.get(
        f"/api/v1/transactions?account_id={user1_account.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Should return 0 results, not user1's transactions
    assert data["total"] == 0
    assert len(data["transactions"]) == 0


def test_filter_by_category_id_respects_ownership(
    client: TestClient,
    user1_category: Category,
    auth_headers_user2: dict,
):
    """Test that filtering by category_id still respects user ownership."""
    # User2 tries to filter by user1's category_id
    response = client.get(
        f"/api/v1/transactions?category_id={user1_category.id}",
        headers=auth_headers_user2,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Should return 0 results
    assert data["total"] == 0

"""Pytest configuration and fixtures."""

import os
from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.app_settings import AppSettings
from app.models.category import Category
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.models.user import User

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Create default app settings for tests
    settings = AppSettings(
        plaid_client_id="test_client_id",
        plaid_secret="test_secret",
        plaid_environment="sandbox",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(settings)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    from app.core.auth import get_password_hash

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    from app.core.auth import create_access_token

    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_account(db: Session, test_user: User) -> Account:
    """Create a sample account for testing."""
    account = Account(
        user_id=test_user.id,
        account_id="test_acc_1",
        name="Test Checking",
        type="depository",
        beancount_account="Assets:Checking:Test",
        currency="USD",
        environment="sandbox",
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def sample_category(db: Session, test_user: User) -> Category:
    """Create a sample category for testing."""
    category = Category(
        user_id=test_user.id,
        name="groceries",
        display_name="Groceries",
        beancount_account="Expenses:Food:Groceries",
        category_type="expense",
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def sample_transaction(
    db: Session, test_user: User, sample_account: Account, sample_category: Category
) -> Transaction:
    """Create a sample transaction for testing."""
    transaction = Transaction(
        user_id=test_user.id,
        transaction_id="test_txn_1",
        account_id=sample_account.id,
        category_id=sample_category.id,
        date=datetime(2024, 3, 15),
        amount=-25.50,
        description="Test grocery purchase",
        payee="Whole Foods",
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
def sample_plaid_item(db: Session, test_user: User) -> PlaidItem:
    """Create a sample Plaid item for testing."""
    item = PlaidItem(
        user_id=test_user.id,
        item_id="test_item_123",
        access_token="access-sandbox-test-token",
        institution_id="ins_test",
        institution_name="Test Bank",
        environment="sandbox",
        is_active=True,
        needs_update=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def mock_plaid_account():
    """Mock Plaid account data."""

    class MockBalance:
        iso_currency_code = "USD"
        current = 1000.00
        available = 950.00

    class MockAccount:
        account_id = "plaid_acc_123"
        name = "Plaid Checking"
        official_name = "Plaid Gold Checking"
        type = type("Type", (), {"value": "depository"})()
        subtype = "checking"
        balances = MockBalance()

    return MockAccount()


@pytest.fixture
def mock_plaid_transaction():
    """Mock Plaid transaction data."""

    class MockTransaction:
        transaction_id = "plaid_txn_123"
        account_id = "plaid_acc_123"
        amount = 25.50
        iso_currency_code = "USD"
        date = datetime(2024, 3, 15).date()
        name = "Starbucks"
        merchant_name = "Starbucks"
        pending = False

    return MockTransaction()


@pytest.fixture
def mock_plaid_transaction_pending():
    """Mock pending Plaid transaction data."""

    class MockTransaction:
        transaction_id = "plaid_txn_pending_456"
        account_id = "plaid_acc_123"
        amount = 15.00
        iso_currency_code = "USD"
        date = datetime(2024, 3, 16).date()
        name = "McDonald's"
        merchant_name = "McDonald's"
        pending = True

    return MockTransaction()


@pytest.fixture(autouse=True)
def reset_plaid_env():
    """Reset Plaid environment variables for testing."""
    original_values = {}
    test_values = {
        "PLAID_CLIENT_ID": "test_client_id",
        "PLAID_SECRET": "test_secret",
        "PLAID_ENV": "sandbox",
    }

    for key, value in test_values.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original values
    for key, value in original_values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

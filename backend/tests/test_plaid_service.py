"""Tests for Plaid service."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.models.user import User
from app.services.plaid_service import PlaidService


class TestPlaidServiceInit:
    """Test PlaidService initialization."""

    def test_init_with_credentials(self):
        """Test service initializes with credentials."""
        service = PlaidService()
        assert service.client is not None

    def test_init_without_credentials(self):
        """Test service handles missing credentials."""
        with patch("app.services.plaid_service.settings") as mock_settings:
            mock_settings.PLAID_CLIENT_ID = None
            mock_settings.PLAID_SECRET = None
            service = PlaidService()
            assert service.client is None


class TestCreateLinkToken:
    """Test create_link_token method."""

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_create_link_token_success(self, mock_plaid_api):
        """Test successful link token creation."""
        mock_response = Mock()
        mock_response.link_token = "link-sandbox-test-token"
        mock_response.expiration = datetime(2024, 12, 31, 23, 59, 59)

        mock_client = Mock()
        mock_client.link_token_create.return_value = mock_response

        service = PlaidService()
        service.client = mock_client

        result = service.create_link_token("user-123")

        assert result["link_token"] == "link-sandbox-test-token"
        assert "expiration" in result
        mock_client.link_token_create.assert_called_once()

    def test_create_link_token_no_client(self):
        """Test link token creation fails without client."""
        service = PlaidService()
        service.client = None

        with pytest.raises(ValueError, match="not initialized"):
            service.create_link_token("user-123")


class TestExchangePublicToken:
    """Test exchange_public_token method."""

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_exchange_token_creates_new_item(self, mock_plaid_api, db: Session, test_user: User):
        """Test exchanging token creates new PlaidItem."""
        # Mock exchange response
        mock_exchange_response = Mock()
        mock_exchange_response.access_token = "access-sandbox-token"
        mock_exchange_response.item_id = "item-123"

        # Mock item get response
        mock_item_response = Mock()
        mock_item_response.item.institution_id = "ins_test"

        # Mock institution response
        mock_inst_response = Mock()
        mock_inst_response.institution.name = "Test Bank"

        mock_client = Mock()
        mock_client.item_public_token_exchange.return_value = mock_exchange_response
        mock_client.item_get.return_value = mock_item_response
        mock_client.institutions_get_by_id.return_value = mock_inst_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        plaid_item = service.exchange_public_token("public-token-test", db, user_id=test_user.id)

        assert plaid_item.item_id == "item-123"
        assert plaid_item.access_token == "access-sandbox-token"
        assert plaid_item.institution_name == "Test Bank"
        assert plaid_item.is_active is True
        assert plaid_item.user_id == test_user.id
        assert plaid_item.environment == "sandbox"

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_exchange_token_updates_existing_item(
        self, mock_plaid_api, db: Session, sample_plaid_item: PlaidItem, test_user: User
    ):
        """Test exchanging token updates existing PlaidItem."""
        # Mock exchange response
        mock_exchange_response = Mock()
        mock_exchange_response.access_token = "new-access-token"
        mock_exchange_response.item_id = sample_plaid_item.item_id

        # Mock item get response
        mock_item_response = Mock()
        mock_item_response.item.institution_id = "ins_test"

        # Mock institution response
        mock_inst_response = Mock()
        mock_inst_response.institution.name = "Updated Bank"

        mock_client = Mock()
        mock_client.item_public_token_exchange.return_value = mock_exchange_response
        mock_client.item_get.return_value = mock_item_response
        mock_client.institutions_get_by_id.return_value = mock_inst_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        plaid_item = service.exchange_public_token("public-token-test", db, user_id=test_user.id)

        assert plaid_item.id == sample_plaid_item.id
        assert plaid_item.access_token == "new-access-token"
        assert plaid_item.institution_name == "Updated Bank"


class TestGetAccounts:
    """Test get_accounts method."""

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_get_accounts_creates_new(
        self, mock_plaid_api, db: Session, sample_plaid_item: PlaidItem, mock_plaid_account
    ):
        """Test getting accounts creates new records."""
        mock_response = Mock()
        mock_response.accounts = [mock_plaid_account]

        mock_client = Mock()
        mock_client.accounts_get.return_value = mock_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        accounts = service.get_accounts(sample_plaid_item, db)

        assert len(accounts) == 1
        assert accounts[0].name == "Plaid Checking"
        assert accounts[0].plaid_account_id == "plaid_acc_123"
        assert accounts[0].is_active is True
        assert accounts[0].user_id == sample_plaid_item.user_id
        assert accounts[0].environment == "sandbox"

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_get_accounts_updates_existing(
        self,
        mock_plaid_api,
        db: Session,
        sample_plaid_item: PlaidItem,
        mock_plaid_account,
        test_user: User,
    ):
        """Test getting accounts updates existing records."""
        # Create existing account
        existing = Account(
            user_id=test_user.id,
            account_id="existing_1",
            plaid_account_id="plaid_acc_123",
            name="Old Name",
            type="depository",
            beancount_account="Assets:Checking:Old",
            currency="USD",
            environment="sandbox",
            is_active=False,
        )
        db.add(existing)
        db.commit()

        mock_response = Mock()
        mock_response.accounts = [mock_plaid_account]

        mock_client = Mock()
        mock_client.accounts_get.return_value = mock_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        accounts = service.get_accounts(sample_plaid_item, db)

        assert len(accounts) == 1
        assert accounts[0].id == existing.id
        assert accounts[0].name == "Plaid Checking"
        assert accounts[0].is_active is True


class TestSyncTransactions:
    """Test sync_transactions method."""

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_sync_adds_new_transactions(
        self,
        mock_plaid_api,
        db: Session,
        sample_plaid_item: PlaidItem,
        mock_plaid_account,
        mock_plaid_transaction,
        test_user: User,
    ):
        """Test sync adds new transactions."""
        # Create account first
        account = Account(
            user_id=test_user.id,
            account_id="test_acc",
            plaid_account_id="plaid_acc_123",
            name="Test Account",
            type="depository",
            beancount_account="Assets:Checking:Test",
            currency="USD",
            environment="sandbox",
            is_active=True,
        )
        db.add(account)
        db.commit()

        # Mock accounts response
        mock_accounts_response = Mock()
        mock_accounts_response.accounts = [mock_plaid_account]

        # Mock sync response
        mock_sync_response = Mock()
        mock_sync_response.added = [mock_plaid_transaction]
        mock_sync_response.modified = []
        mock_sync_response.removed = []
        mock_sync_response.next_cursor = "cursor_123"
        mock_sync_response.has_more = False

        mock_client = Mock()
        mock_client.accounts_get.return_value = mock_accounts_response
        mock_client.transactions_sync.return_value = mock_sync_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        added, modified, removed, cursor = service.sync_transactions(sample_plaid_item, db)

        assert added == 1
        assert modified == 0
        assert removed == 0
        assert cursor == "cursor_123"

        # Verify transaction was created
        txn = (
            db.query(Transaction)
            .filter(Transaction.plaid_transaction_id == "plaid_txn_123")
            .first()
        )
        assert txn is not None
        assert txn.amount == -25.50  # Plaid uses positive for debits
        assert txn.pending is False
        assert txn.user_id == test_user.id
        assert txn.environment == "sandbox"

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_sync_updates_pending_to_completed(
        self,
        mock_plaid_api,
        db: Session,
        sample_plaid_item: PlaidItem,
        mock_plaid_account,
        mock_plaid_transaction_pending,
        test_user: User,
    ):
        """Test sync correctly handles pending → completed transition."""
        # Create account
        account = Account(
            user_id=test_user.id,
            account_id="test_acc",
            plaid_account_id="plaid_acc_123",
            name="Test Account",
            type="depository",
            beancount_account="Assets:Checking:Test",
            currency="USD",
            environment="sandbox",
            is_active=True,
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # Create existing pending transaction
        pending_txn = Transaction(
            user_id=test_user.id,
            transaction_id="plaid_plaid_txn_pending_456",
            plaid_transaction_id="plaid_txn_pending_456",
            account_id=account.id,
            date=datetime(2024, 3, 16),
            amount=-15.00,
            description="McDonald's",
            payee="McDonald's",
            currency="USD",
            environment="sandbox",
            pending=True,
            reviewed=False,
            synced_to_beancount=False,
        )
        db.add(pending_txn)
        db.commit()

        # Mock transaction now completed
        completed_txn = Mock()
        completed_txn.transaction_id = "plaid_txn_pending_456"
        completed_txn.account_id = "plaid_acc_123"
        completed_txn.amount = 15.00
        completed_txn.iso_currency_code = "USD"
        completed_txn.date = datetime(2024, 3, 17).date()
        completed_txn.name = "McDonald's"
        completed_txn.merchant_name = "McDonald's"
        completed_txn.pending = False

        # Mock accounts response
        mock_accounts_response = Mock()
        mock_accounts_response.accounts = [mock_plaid_account]

        # Mock sync response
        mock_sync_response = Mock()
        mock_sync_response.added = []
        mock_sync_response.modified = [completed_txn]
        mock_sync_response.removed = []
        mock_sync_response.next_cursor = "cursor_456"
        mock_sync_response.has_more = False

        mock_client = Mock()
        mock_client.accounts_get.return_value = mock_accounts_response
        mock_client.transactions_sync.return_value = mock_sync_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        added, modified, removed, cursor = service.sync_transactions(sample_plaid_item, db)

        assert added == 0
        assert modified == 1
        assert removed == 0

        # Verify transaction was updated, not duplicated
        txns = (
            db.query(Transaction)
            .filter(Transaction.plaid_transaction_id == "plaid_txn_pending_456")
            .all()
        )
        assert len(txns) == 1
        assert txns[0].pending is False
        assert txns[0].date == datetime(2024, 3, 17)

    @patch("app.services.plaid_service.plaid_api.PlaidApi")
    def test_sync_removes_transactions(
        self,
        mock_plaid_api,
        db: Session,
        sample_plaid_item: PlaidItem,
        mock_plaid_account,
        sample_transaction: Transaction,
    ):
        """Test sync removes deleted transactions."""
        sample_transaction.plaid_transaction_id = "plaid_txn_to_remove"
        db.commit()

        # Mock removed transaction
        mock_removed = Mock()
        mock_removed.transaction_id = "plaid_txn_to_remove"

        # Mock accounts response
        mock_accounts_response = Mock()
        mock_accounts_response.accounts = [mock_plaid_account]

        # Mock sync response
        mock_sync_response = Mock()
        mock_sync_response.added = []
        mock_sync_response.modified = []
        mock_sync_response.removed = [mock_removed]
        mock_sync_response.next_cursor = "cursor_789"
        mock_sync_response.has_more = False

        mock_client = Mock()
        mock_client.accounts_get.return_value = mock_accounts_response
        mock_client.transactions_sync.return_value = mock_sync_response

        service = PlaidService()
        service.client = mock_client
        service.environment = "sandbox"

        added, modified, removed, cursor = service.sync_transactions(sample_plaid_item, db)

        assert added == 0
        assert modified == 0
        assert removed == 1

        # Verify transaction was deleted
        txn = (
            db.query(Transaction)
            .filter(Transaction.plaid_transaction_id == "plaid_txn_to_remove")
            .first()
        )
        assert txn is None

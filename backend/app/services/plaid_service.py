"""Plaid integration service."""

import logging
from datetime import datetime

import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.account import Account
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class PlaidService:
    """Service for interacting with Plaid API."""

    def __init__(self):
        """Initialize Plaid client."""
        # Map environment string to Plaid environment
        env_map = {
            "sandbox": plaid.Environment.Sandbox,
            "development": plaid.Environment.Development,
            "production": plaid.Environment.Production,
        }

        if not settings.PLAID_CLIENT_ID or not settings.PLAID_SECRET:
            logger.warning("Plaid credentials not configured. Plaid integration disabled.")
            self.client = None
            return

        configuration = plaid.Configuration(
            host=env_map.get(settings.PLAID_ENV, plaid.Environment.Sandbox),
            api_key={
                "clientId": settings.PLAID_CLIENT_ID,
                "secret": settings.PLAID_SECRET,
            },
        )

        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        logger.info(f"Plaid client initialized for environment: {settings.PLAID_ENV}")

    def create_link_token(self, user_id: str = "user-1") -> dict:
        """
        Create a link token for Plaid Link.

        Args:
            user_id: User identifier

        Returns:
            Dict with link_token and expiration
        """
        if not self.client:
            raise ValueError("Plaid client not initialized. Check credentials.")

        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
                client_name="MintBean",
                products=[Products("transactions")],
                country_codes=[CountryCode("US")],
                language="en",
            )

            response = self.client.link_token_create(request)
            return {
                "link_token": response.link_token,
                "expiration": response.expiration.isoformat(),
            }
        except plaid.ApiException as e:
            logger.error(f"Error creating link token: {e}")
            raise

    def exchange_public_token(self, public_token: str, db: Session) -> PlaidItem:
        """
        Exchange public token for access token and create PlaidItem.

        Args:
            public_token: Public token from Plaid Link
            db: Database session

        Returns:
            Created PlaidItem
        """
        if not self.client:
            raise ValueError("Plaid client not initialized. Check credentials.")

        try:
            # Exchange public token for access token
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)

            access_token = response.access_token
            item_id = response.item_id

            # Get institution information
            institution_id = None
            institution_name = None
            try:
                item_response = self.client.item_get(
                    plaid.model.item_get_request.ItemGetRequest(access_token=access_token)
                )
                institution_id = item_response.item.institution_id

                if institution_id:
                    inst_request = InstitutionsGetByIdRequest(
                        institution_id=institution_id,
                        country_codes=[CountryCode("US")],
                    )
                    inst_response = self.client.institutions_get_by_id(inst_request)
                    institution_name = inst_response.institution.name
            except Exception as e:
                logger.warning(f"Could not fetch institution details: {e}")

            # Create or update PlaidItem
            plaid_item = db.query(PlaidItem).filter(PlaidItem.item_id == item_id).first()

            if plaid_item:
                plaid_item.access_token = access_token
                plaid_item.institution_id = institution_id
                plaid_item.institution_name = institution_name
                plaid_item.is_active = True
                plaid_item.needs_update = False
                plaid_item.error_code = None
                plaid_item.updated_at = datetime.utcnow()
            else:
                plaid_item = PlaidItem(
                    item_id=item_id,
                    access_token=access_token,
                    institution_id=institution_id,
                    institution_name=institution_name,
                    is_active=True,
                )
                db.add(plaid_item)

            db.commit()
            db.refresh(plaid_item)

            logger.info(f"Successfully exchanged token for item: {item_id}")
            return plaid_item

        except plaid.ApiException as e:
            logger.error(f"Error exchanging public token: {e}")
            raise

    def get_accounts(self, plaid_item: PlaidItem, db: Session) -> list[Account]:
        """
        Fetch accounts from Plaid and sync to database.

        Args:
            plaid_item: PlaidItem with access token
            db: Database session

        Returns:
            List of Account objects
        """
        if not self.client:
            raise ValueError("Plaid client not initialized.")

        try:
            request = plaid.model.accounts_get_request.AccountsGetRequest(
                access_token=plaid_item.access_token
            )
            response = self.client.accounts_get(request)

            accounts = []
            for plaid_account in response.accounts:
                # Check if account already exists
                account = (
                    db.query(Account)
                    .filter(Account.plaid_account_id == plaid_account.account_id)
                    .first()
                )

                if not account:
                    # Generate a beancount account name
                    safe_name = plaid_account.name.replace(" ", "")
                    beancount_account = (
                        f"Assets:{plaid_item.institution_name or 'Bank'}:{safe_name}"
                    )

                    account = Account(
                        name=plaid_account.name,
                        account_id=f"plaid_{plaid_account.account_id}",
                        plaid_account_id=plaid_account.account_id,
                        type=plaid_account.type.value,
                        beancount_account=beancount_account,
                        currency=plaid_account.balances.iso_currency_code or "USD",
                        is_active=True,
                    )
                    db.add(account)
                else:
                    # Update account name if changed
                    account.name = plaid_account.name
                    account.is_active = True

                accounts.append(account)

            db.commit()
            logger.info(f"Synced {len(accounts)} accounts for item {plaid_item.item_id}")
            return accounts

        except plaid.ApiException as e:
            logger.error(f"Error fetching accounts: {e}")
            plaid_item.needs_update = True
            plaid_item.error_code = str(e.status)
            db.commit()
            raise

    def sync_transactions(self, plaid_item: PlaidItem, db: Session) -> tuple[int, int, int, str]:
        """
        Sync transactions from Plaid using the transactions/sync endpoint.

        Args:
            plaid_item: PlaidItem with access token
            db: Database session

        Returns:
            Tuple of (added_count, modified_count, removed_count, new_cursor)
        """
        if not self.client:
            raise ValueError("Plaid client not initialized.")

        added_count = 0
        modified_count = 0
        removed_count = 0
        cursor = plaid_item.cursor or ""

        try:
            # Make sure accounts are synced first
            accounts = self.get_accounts(plaid_item, db)
            account_map = {acc.plaid_account_id: acc for acc in accounts}

            # Sync transactions
            has_more = True
            while has_more:
                request = TransactionsSyncRequest(
                    access_token=plaid_item.access_token, cursor=cursor
                )
                response = self.client.transactions_sync(request)

                # Process added transactions
                for plaid_txn in response.added:
                    account = account_map.get(plaid_txn.account_id)
                    if not account:
                        logger.warning(f"Account {plaid_txn.account_id} not found for transaction")
                        continue

                    # Check if transaction already exists
                    existing = (
                        db.query(Transaction)
                        .filter(Transaction.plaid_transaction_id == plaid_txn.transaction_id)
                        .first()
                    )

                    if not existing:
                        transaction = Transaction(
                            transaction_id=f"plaid_{plaid_txn.transaction_id}",
                            plaid_transaction_id=plaid_txn.transaction_id,
                            account_id=account.id,
                            date=plaid_txn.date,
                            description=plaid_txn.name,
                            payee=plaid_txn.merchant_name or plaid_txn.name,
                            amount=-plaid_txn.amount,  # Plaid uses positive for debits
                            currency=plaid_txn.iso_currency_code or "USD",
                            pending=plaid_txn.pending,
                            reviewed=False,
                            synced_to_beancount=False,
                        )
                        db.add(transaction)
                        added_count += 1

                # Process modified transactions
                for plaid_txn in response.modified:
                    existing = (
                        db.query(Transaction)
                        .filter(Transaction.plaid_transaction_id == plaid_txn.transaction_id)
                        .first()
                    )

                    if existing:
                        # Track pending → completed transitions
                        was_pending = existing.pending
                        is_now_pending = plaid_txn.pending

                        if was_pending and not is_now_pending:
                            logger.info(
                                f"Transaction {plaid_txn.transaction_id} cleared: "
                                f"pending → completed"
                            )

                        existing.date = plaid_txn.date
                        existing.description = plaid_txn.name
                        existing.payee = plaid_txn.merchant_name or plaid_txn.name
                        existing.amount = -plaid_txn.amount
                        existing.pending = plaid_txn.pending
                        existing.updated_at = datetime.utcnow()
                        modified_count += 1

                # Process removed transactions
                for removed_id in response.removed:
                    existing = (
                        db.query(Transaction)
                        .filter(Transaction.plaid_transaction_id == removed_id.transaction_id)
                        .first()
                    )
                    if existing:
                        db.delete(existing)
                        removed_count += 1

                # Update cursor
                cursor = response.next_cursor
                has_more = response.has_more

                db.commit()

            # Update plaid_item with new cursor and sync time
            plaid_item.cursor = cursor
            plaid_item.last_synced_at = datetime.utcnow()
            plaid_item.needs_update = False
            plaid_item.error_code = None
            db.commit()

            logger.info(
                f"Sync complete for item {plaid_item.item_id}: "
                f"+{added_count} ~{modified_count} -{removed_count}"
            )

            return added_count, modified_count, removed_count, cursor

        except plaid.ApiException as e:
            logger.error(f"Error syncing transactions: {e}")
            plaid_item.needs_update = True
            plaid_item.error_code = str(e.status)
            db.commit()
            raise


# Singleton instance
plaid_service = PlaidService()

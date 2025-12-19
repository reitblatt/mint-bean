"""Plaid integration service."""

import json
import logging
from datetime import UTC, datetime

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
from app.models.plaid_category_mapping import PlaidCategoryMapping
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.services.rule_engine import RuleEngine

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

    def exchange_public_token(self, public_token: str, db: Session, user_id: int) -> PlaidItem:
        """
        Exchange public token for access token and create PlaidItem.

        Args:
            public_token: Public token from Plaid Link
            db: Database session
            user_id: User ID to associate with the PlaidItem

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

            # Get the environment from the service instance
            environment = getattr(self, "environment", "sandbox")

            if plaid_item:
                plaid_item.access_token = access_token
                plaid_item.institution_id = institution_id
                plaid_item.institution_name = institution_name
                plaid_item.environment = environment
                plaid_item.user_id = user_id
                plaid_item.is_active = True
                plaid_item.needs_update = False
                plaid_item.error_code = None
                plaid_item.updated_at = datetime.now(UTC)
            else:
                plaid_item = PlaidItem(
                    user_id=user_id,
                    item_id=item_id,
                    access_token=access_token,
                    institution_id=institution_id,
                    institution_name=institution_name,
                    environment=environment,
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

            # Get the environment from plaid_item
            environment = plaid_item.environment

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

                    # Extract subtype as string (handle both enum and string)
                    subtype_str = None
                    if plaid_account.subtype:
                        subtype_str = (
                            plaid_account.subtype.value
                            if hasattr(plaid_account.subtype, "value")
                            else plaid_account.subtype
                        )

                    account = Account(
                        user_id=plaid_item.user_id,
                        name=plaid_account.name,
                        official_name=plaid_account.official_name,
                        account_id=f"plaid_{plaid_account.account_id}",
                        plaid_account_id=plaid_account.account_id,
                        plaid_item_id=plaid_item.item_id,
                        type=plaid_account.type.value,
                        subtype=subtype_str,
                        institution_name=plaid_item.institution_name,
                        institution_id=plaid_item.institution_id,
                        environment=environment,
                        beancount_account=beancount_account,
                        currency=plaid_account.balances.iso_currency_code or "USD",
                        current_balance=plaid_account.balances.current,
                        available_balance=plaid_account.balances.available,
                        is_active=True,
                        last_synced_at=datetime.now(UTC),
                    )
                    db.add(account)
                else:
                    # Extract subtype as string (handle both enum and string)
                    subtype_str = None
                    if plaid_account.subtype:
                        subtype_str = (
                            plaid_account.subtype.value
                            if hasattr(plaid_account.subtype, "value")
                            else plaid_account.subtype
                        )

                    # Update account details
                    account.name = plaid_account.name
                    account.official_name = plaid_account.official_name
                    account.subtype = subtype_str
                    account.plaid_item_id = plaid_item.item_id  # Ensure this is set
                    account.institution_name = plaid_item.institution_name
                    account.institution_id = plaid_item.institution_id
                    account.environment = environment
                    account.current_balance = plaid_account.balances.current
                    account.available_balance = plaid_account.balances.available
                    account.is_active = True
                    account.last_synced_at = datetime.now(UTC)

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

            # Get the environment from plaid_item
            environment = plaid_item.environment

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
                        # Extract Plaid category information
                        plaid_category_json = None
                        plaid_primary = None
                        plaid_detailed = None
                        plaid_confidence = None

                        if (
                            hasattr(plaid_txn, "personal_finance_category")
                            and plaid_txn.personal_finance_category
                        ):
                            try:
                                pfc = plaid_txn.personal_finance_category
                                plaid_primary = pfc.primary if hasattr(pfc, "primary") else None
                                plaid_detailed = pfc.detailed if hasattr(pfc, "detailed") else None
                                plaid_confidence = (
                                    pfc.confidence_level
                                    if hasattr(pfc, "confidence_level")
                                    else None
                                )
                                # Validate we got actual strings, not Mock objects
                                if not isinstance(plaid_primary, str | type(None)):
                                    plaid_primary = None
                                if not isinstance(plaid_detailed, str | type(None)):
                                    plaid_detailed = None
                                if not isinstance(plaid_confidence, str | type(None)):
                                    plaid_confidence = None
                            except (AttributeError, TypeError):
                                # Skip if not accessible (e.g., Mock object)
                                pass

                        # Also store legacy category array if available
                        if hasattr(plaid_txn, "category") and plaid_txn.category:
                            try:
                                plaid_category_json = json.dumps(plaid_txn.category)
                            except (TypeError, ValueError):
                                # Skip if not JSON serializable (e.g., Mock object)
                                pass

                        transaction = Transaction(
                            user_id=plaid_item.user_id,
                            transaction_id=f"plaid_{plaid_txn.transaction_id}",
                            plaid_transaction_id=plaid_txn.transaction_id,
                            account_id=account.id,
                            date=plaid_txn.date,
                            description=plaid_txn.name,
                            payee=plaid_txn.merchant_name or plaid_txn.name,
                            amount=-plaid_txn.amount,  # Plaid uses positive for debits
                            currency=plaid_txn.iso_currency_code or "USD",
                            environment=environment,
                            pending=plaid_txn.pending,
                            reviewed=False,
                            synced_to_beancount=False,
                            # Plaid categorization data
                            plaid_category=plaid_category_json,
                            plaid_primary_category=plaid_primary,
                            plaid_detailed_category=plaid_detailed,
                            plaid_confidence_level=plaid_confidence,
                            merchant_name=plaid_txn.merchant_name,
                        )
                        db.add(transaction)
                        db.flush()  # Flush to get transaction ID for auto-categorization

                        # Apply auto-categorization
                        self.apply_auto_categorization(transaction, db)

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

                        # Extract Plaid category information
                        plaid_category_json = None
                        plaid_primary = None
                        plaid_detailed = None
                        plaid_confidence = None

                        if (
                            hasattr(plaid_txn, "personal_finance_category")
                            and plaid_txn.personal_finance_category
                        ):
                            try:
                                pfc = plaid_txn.personal_finance_category
                                plaid_primary = pfc.primary if hasattr(pfc, "primary") else None
                                plaid_detailed = pfc.detailed if hasattr(pfc, "detailed") else None
                                plaid_confidence = (
                                    pfc.confidence_level
                                    if hasattr(pfc, "confidence_level")
                                    else None
                                )
                                # Validate we got actual strings, not Mock objects
                                if not isinstance(plaid_primary, str | type(None)):
                                    plaid_primary = None
                                if not isinstance(plaid_detailed, str | type(None)):
                                    plaid_detailed = None
                                if not isinstance(plaid_confidence, str | type(None)):
                                    plaid_confidence = None
                            except (AttributeError, TypeError):
                                # Skip if not accessible (e.g., Mock object)
                                pass

                        # Also store legacy category array if available
                        if hasattr(plaid_txn, "category") and plaid_txn.category:
                            try:
                                plaid_category_json = json.dumps(plaid_txn.category)
                            except (TypeError, ValueError):
                                # Skip if not JSON serializable (e.g., Mock object)
                                pass

                        existing.date = plaid_txn.date
                        existing.description = plaid_txn.name
                        existing.payee = plaid_txn.merchant_name or plaid_txn.name
                        existing.amount = -plaid_txn.amount
                        existing.environment = environment
                        existing.pending = plaid_txn.pending
                        existing.updated_at = datetime.now(UTC)
                        # Update Plaid category fields
                        existing.plaid_category = plaid_category_json
                        existing.plaid_primary_category = plaid_primary
                        existing.plaid_detailed_category = plaid_detailed
                        existing.plaid_confidence_level = plaid_confidence
                        existing.merchant_name = plaid_txn.merchant_name

                        # Re-apply auto-categorization if transaction cleared from pending
                        # or if it was never categorized
                        if (was_pending and not is_now_pending) or not existing.category_id:
                            self.apply_auto_categorization(existing, db)

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
            plaid_item.last_synced_at = datetime.now(UTC)
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

    def apply_auto_categorization(
        self, transaction: Transaction, db: Session
    ) -> dict[str, str | None]:
        """
        Apply auto-categorization to a transaction.

        Auto-categorization happens in this order:
        1. Plaid category mapping (if available)
        2. Rule engine (if no mapping or mapping failed)

        Args:
            transaction: Transaction to categorize
            db: Database session

        Returns:
            Dictionary with categorization result:
            {
                "method": "plaid_mapping" | "rule" | None,
                "category_id": int | None,
                "confidence": float | None
            }
        """
        # Skip if already categorized manually
        if transaction.category_id and not transaction.auto_categorized:
            logger.debug(
                f"Transaction {transaction.transaction_id} already manually categorized, skipping"
            )
            return {"method": None, "category_id": transaction.category_id, "confidence": None}

        # Try Plaid category mapping first
        if transaction.plaid_primary_category:
            mapping = (
                db.query(PlaidCategoryMapping)
                .filter(
                    PlaidCategoryMapping.plaid_primary_category
                    == transaction.plaid_primary_category,
                    PlaidCategoryMapping.auto_apply.is_(True),
                )
                .filter(
                    (PlaidCategoryMapping.plaid_detailed_category.is_(None))
                    | (
                        PlaidCategoryMapping.plaid_detailed_category
                        == transaction.plaid_detailed_category
                    )
                )
                .order_by(
                    # Prefer detailed mappings over primary-only mappings
                    PlaidCategoryMapping.plaid_detailed_category.isnot(None).desc(),
                    PlaidCategoryMapping.confidence.desc(),
                )
                .first()
            )

            if mapping:
                transaction.category_id = mapping.category_id
                transaction.auto_categorized = True
                transaction.categorization_method = "plaid_mapping"

                # Update mapping statistics
                mapping.match_count += 1
                mapping.last_matched_at = datetime.now(UTC)

                logger.info(
                    f"Applied Plaid mapping to transaction {transaction.transaction_id}: "
                    f"{mapping.plaid_primary_category} → category {mapping.category_id}"
                )

                return {
                    "method": "plaid_mapping",
                    "category_id": mapping.category_id,
                    "confidence": mapping.confidence,
                }

        # Try rule engine if no Plaid mapping applied
        rule_engine = RuleEngine(db)
        actions = rule_engine.apply_rules(transaction, apply_changes=True)

        if actions and "set_category" in actions:
            logger.info(
                f"Applied rule to transaction {transaction.transaction_id}: "
                f"category {transaction.category_id}"
            )
            return {
                "method": "rule",
                "category_id": transaction.category_id,
                "confidence": None,
            }

        # No categorization applied
        return {"method": None, "category_id": None, "confidence": None}


# Singleton instance - kept for backward compatibility but deprecated
# Use create_plaid_service() instead
plaid_service = PlaidService()


def create_plaid_service(
    client_id: str | None = None, secret: str | None = None, environment: str = "sandbox"
) -> PlaidService:
    """
    Create a PlaidService instance with specific credentials.

    Args:
        client_id: Plaid client ID
        secret: Plaid secret
        environment: Plaid environment (sandbox or production)

    Returns:
        PlaidService instance
    """
    # Create a new instance with custom credentials
    service = object.__new__(PlaidService)

    # Map environment string to Plaid environment
    env_map = {
        "sandbox": plaid.Environment.Sandbox,
        "development": plaid.Environment.Development,
        "production": plaid.Environment.Production,
    }

    # Store the environment for later use
    service.environment = environment

    if not client_id or not secret:
        logger.warning("Plaid credentials not configured. Plaid integration disabled.")
        service.client = None
        return service

    configuration = plaid.Configuration(
        host=env_map.get(environment, plaid.Environment.Sandbox),
        api_key={
            "clientId": client_id,
            "secret": secret,
        },
    )

    api_client = plaid.ApiClient(configuration)
    service.client = plaid_api.PlaidApi(api_client)
    logger.info(f"Plaid client initialized for environment: {environment}")

    return service

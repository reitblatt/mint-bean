"""Beancount file parsing and writing service."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from beancount import loader
    from beancount.core import data
except ImportError:
    loader = None
    data = None

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BeancountService:
    """Service for reading and writing beancount files."""

    def __init__(self, file_path: str | None = None):
        """
        Initialize beancount service.

        Args:
            file_path: Path to beancount file (defaults to settings)
        """
        self.file_path = file_path or settings.BEANCOUNT_FILE_PATH
        self.repo_path = settings.BEANCOUNT_REPO_PATH

    def parse_transactions(self) -> list[dict[str, Any]]:
        """
        Parse transactions from beancount file.

        Returns:
            List of transaction dictionaries
        """
        if loader is None or data is None:
            logger.error("Beancount library not installed")
            return []

        logger.info(f"Parsing beancount file: {self.file_path}")

        # Check if file exists
        if not Path(self.file_path).exists():
            logger.error(f"Beancount file not found: {self.file_path}")
            return []

        try:
            # Load the beancount file
            entries, errors, options = loader.load_file(self.file_path)

            if errors:
                logger.warning(f"Beancount file has {len(errors)} errors")
                for error in errors[:5]:  # Log first 5 errors
                    logger.warning(f"  {error}")

            transactions = []

            for entry in entries:
                if not isinstance(entry, data.Transaction):
                    continue

                # Extract basic transaction info
                txn_data = {
                    "date": entry.date.isoformat(),
                    "payee": entry.payee or "",
                    "narration": entry.narration or "",
                    "tags": list(entry.tags) if entry.tags else [],
                    "links": list(entry.links) if entry.links else [],
                    "postings": [],
                }

                # Extract postings (account movements)
                for posting in entry.postings:
                    if posting.units:
                        posting_data = {
                            "account": posting.account,
                            "amount": float(posting.units.number),
                            "currency": posting.units.currency,
                        }
                        txn_data["postings"].append(posting_data)

                # Determine the main account and category
                # Find asset/liability accounts (where money came from/went to)
                asset_postings = [
                    p for p in txn_data["postings"] if p["account"].startswith("Assets:")
                ]
                liability_postings = [
                    p for p in txn_data["postings"] if p["account"].startswith("Liabilities:")
                ]
                expense_postings = [
                    p for p in txn_data["postings"] if p["account"].startswith("Expenses:")
                ]
                income_postings = [
                    p for p in txn_data["postings"] if p["account"].startswith("Income:")
                ]

                # Main account (where the money moved)
                if asset_postings:
                    txn_data["main_account"] = asset_postings[0]["account"]
                    txn_data["amount"] = asset_postings[0]["amount"]
                elif liability_postings:
                    txn_data["main_account"] = liability_postings[0]["account"]
                    txn_data["amount"] = liability_postings[0]["amount"]
                else:
                    # Fallback to first posting
                    if txn_data["postings"]:
                        txn_data["main_account"] = txn_data["postings"][0]["account"]
                        txn_data["amount"] = txn_data["postings"][0]["amount"]

                # Category account (expense or income)
                if expense_postings:
                    txn_data["category_account"] = expense_postings[0]["account"]
                    txn_data["category_type"] = "expense"
                elif income_postings:
                    txn_data["category_account"] = income_postings[0]["account"]
                    txn_data["category_type"] = "income"

                # Generate a transaction ID based on content hash
                id_string = f"{txn_data['date']}|{txn_data['payee']}|{txn_data['narration']}|{txn_data.get('amount', 0)}"
                txn_data["transaction_id"] = hashlib.sha256(id_string.encode()).hexdigest()[:32]

                transactions.append(txn_data)

            logger.info(f"Parsed {len(transactions)} transactions from beancount file")
            return transactions

        except Exception as e:
            logger.error(f"Error parsing beancount file: {e}")
            return []

    def parse_accounts(self) -> list[dict[str, Any]]:
        """
        Parse account declarations from beancount file.

        Returns:
            List of account dictionaries
        """
        if loader is None or data is None:
            logger.error("Beancount library not installed")
            return []

        logger.info(f"Parsing accounts from: {self.file_path}")

        # Check if file exists
        if not Path(self.file_path).exists():
            logger.error(f"Beancount file not found: {self.file_path}")
            return []

        try:
            # Load the beancount file
            entries, errors, options = loader.load_file(self.file_path)

            if errors:
                logger.warning(f"Beancount file has {len(errors)} errors")

            accounts = []

            for entry in entries:
                if not isinstance(entry, data.Open):
                    continue

                # Generate account ID from account name
                account_id = hashlib.sha256(entry.account.encode()).hexdigest()[:32]

                # Determine account type based on account name prefix
                account_type = "other"
                if entry.account.startswith("Assets:"):
                    if "Bank" in entry.account or "Cash" in entry.account:
                        account_type = "depository"
                    elif "Investment" in entry.account:
                        account_type = "investment"
                    elif "CreditCard" in entry.account:
                        account_type = "credit"
                    else:
                        account_type = "other"
                elif entry.account.startswith("Liabilities:"):
                    account_type = "credit"

                account_data = {
                    "account_id": account_id,
                    "name": entry.account.split(":")[-1],  # Last part of account name
                    "beancount_account": entry.account,  # Full account name
                    "type": account_type,
                    "subtype": None,
                    "currencies": list(entry.currencies) if entry.currencies else ["USD"],
                    "official_name": entry.account,
                    "is_active": True,
                }

                accounts.append(account_data)

            logger.info(f"Parsed {len(accounts)} accounts from beancount file")
            return accounts

        except Exception as e:
            logger.error(f"Error parsing accounts from beancount file: {e}")
            return []

    def write_transaction(
        self,
        date: datetime,
        payee: str,
        narration: str,
        postings: list[dict[str, Any]],
        flag: str = "*",
        tags: list[str] | None = None,
        links: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Write a transaction to the beancount file.

        Args:
            date: Transaction date
            payee: Payee name
            narration: Transaction description
            postings: List of posting dictionaries with 'account', 'amount', and 'currency'
            flag: Transaction flag ('*' for cleared, '!' for pending)
            tags: Optional list of tags
            links: Optional list of links
            metadata: Optional metadata dictionary

        Returns:
            True if successful
        """
        logger.info(f"Writing transaction: {date.date()} - {narration}")

        try:
            # Check if file exists
            file_path = Path(self.file_path)
            if not file_path.exists():
                logger.error(f"Beancount file not found: {self.file_path}")
                return False

            # Format transaction
            lines = []
            lines.append("")  # Blank line before transaction

            # Transaction header
            date_str = date.strftime("%Y-%m-%d")
            txn_line = f'{date_str} {flag} "{payee}" "{narration}"'

            # Add tags
            if tags:
                tag_str = " ".join(f"#{tag}" for tag in tags)
                txn_line += f" {tag_str}"

            # Add links
            if links:
                link_str = " ".join(f"^{link}" for link in links)
                txn_line += f" {link_str}"

            lines.append(txn_line)

            # Add metadata
            if metadata:
                for key, value in metadata.items():
                    lines.append(f"  {key}: {value}")

            # Add postings
            for posting in postings:
                account = posting["account"]
                amount = posting["amount"]
                currency = posting.get("currency", "USD")

                # Format amount with 2 decimal places
                amount_str = f"{amount:.2f}"
                lines.append(f"  {account:<50} {amount_str:>12} {currency}")

            # Append to file
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines))
                f.write("\n")

            logger.info(f"Successfully wrote transaction to {self.file_path}")
            return True

        except Exception as e:
            logger.error(f"Error writing transaction: {e}")
            return False

    def update_transaction(self, transaction_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an existing transaction in the beancount file.

        Args:
            transaction_id: Unique transaction identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful

        TODO: Implement transaction updating
        - Parse beancount file
        - Find transaction by metadata or link
        - Update the transaction
        - Rewrite the file or section
        - Optionally commit to git repo
        """
        logger.info(f"Updating transaction: {transaction_id}")
        # TODO: Implement actual updating
        return True

    def sync_from_file(self) -> dict[str, int]:
        """
        Sync transactions from beancount file to database.

        Returns:
            Dictionary with sync statistics

        TODO: Implement syncing logic
        - Parse all transactions from beancount file
        - Compare with database transactions
        - Insert new transactions
        - Update modified transactions
        - Return counts of added/updated/unchanged
        """
        logger.info("Syncing from beancount file to database")
        # TODO: Implement actual syncing
        return {"added": 0, "updated": 0, "unchanged": 0}

    def sync_to_file(self, db) -> dict[str, int]:
        """
        Sync transactions from database to beancount file.

        Args:
            db: Database session

        Returns:
            Dictionary with sync statistics
        """
        from app.models.account import Account
        from app.models.category import Category
        from app.models.transaction import Transaction

        logger.info("Syncing from database to beancount file")

        synced_count = 0
        failed_count = 0

        try:
            # Query unsynced, reviewed, non-pending transactions
            transactions = (
                db.query(Transaction)
                .filter(
                    Transaction.synced_to_beancount.is_(False),
                    Transaction.reviewed.is_(True),
                    Transaction.pending.is_(False),
                )
                .all()
            )

            logger.info(f"Found {len(transactions)} transactions to sync")

            for txn in transactions:
                try:
                    # Get account info
                    account = db.query(Account).filter(Account.id == txn.account_id).first()
                    if not account:
                        logger.warning(f"Account not found for transaction {txn.id}")
                        failed_count += 1
                        continue

                    # Get category info
                    category = None
                    if txn.category_id:
                        category = db.query(Category).filter(Category.id == txn.category_id).first()

                    # Build postings
                    postings = []

                    # Posting 1: Account (where money moved from/to)
                    postings.append(
                        {
                            "account": account.beancount_account,
                            "amount": txn.amount,
                            "currency": txn.currency,
                        }
                    )

                    # Posting 2: Category (expense/income) or default
                    if category:
                        category_amount = -txn.amount  # Opposite sign for double-entry
                        postings.append(
                            {
                                "account": category.beancount_account,
                                "amount": category_amount,
                                "currency": txn.currency,
                            }
                        )
                    else:
                        # Use a default "Uncategorized" account
                        category_amount = -txn.amount
                        default_account = (
                            "Expenses:Uncategorized" if txn.amount < 0 else "Income:Uncategorized"
                        )
                        postings.append(
                            {
                                "account": default_account,
                                "amount": category_amount,
                                "currency": txn.currency,
                            }
                        )

                    # Prepare tags and metadata
                    tags = []
                    if txn.tags:
                        try:
                            import json

                            tags = json.loads(txn.tags) if isinstance(txn.tags, str) else txn.tags
                        except Exception:
                            pass

                    links = []
                    if txn.links:
                        try:
                            import json

                            links = (
                                json.loads(txn.links) if isinstance(txn.links, str) else txn.links
                            )
                        except Exception:
                            pass

                    metadata = {"mintbean_id": txn.transaction_id}
                    if txn.plaid_transaction_id:
                        metadata["plaid_id"] = txn.plaid_transaction_id

                    # Write transaction
                    success = self.write_transaction(
                        date=txn.date,
                        payee=txn.payee or "",
                        narration=txn.description,
                        postings=postings,
                        flag=txn.beancount_flag,
                        tags=tags,
                        links=links,
                        metadata=metadata,
                    )

                    if success:
                        # Mark as synced
                        txn.synced_to_beancount = True
                        synced_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error syncing transaction {txn.id}: {e}")
                    failed_count += 1

            # Commit the synced flags
            db.commit()

            logger.info(f"Sync complete: {synced_count} synced, {failed_count} failed")
            return {"synced": synced_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            db.rollback()
            return {"synced": synced_count, "failed": failed_count}

    def validate_file(self) -> dict[str, Any]:
        """
        Validate beancount file syntax and balance.

        Returns:
            Validation results

        TODO: Implement validation
        - Use beancount.loader.load_file() with error capture
        - Check for syntax errors
        - Check for balance assertions
        - Return errors and warnings
        """
        logger.info(f"Validating beancount file: {self.file_path}")
        # TODO: Implement actual validation
        return {"valid": True, "errors": [], "warnings": []}

    def commit_to_git(self, message: str) -> bool:
        """
        Commit beancount file changes to git.

        Args:
            message: Commit message

        Returns:
            True if successful

        TODO: Implement git integration
        - Check if repo_path is a git repository
        - Stage beancount file changes
        - Commit with provided message
        - Handle git errors gracefully
        """
        logger.info(f"Committing to git: {message}")
        # TODO: Implement actual git commit
        return True

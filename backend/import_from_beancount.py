#!/usr/bin/env python3
"""
Script to import transactions from beancount file into the database.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.core.config import settings
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.services.beancount_service import BeancountService


def create_or_get_account(db: Session, account_data: dict) -> Account:
    """Create account if it doesn't exist, or return existing one."""
    # Check if account exists by beancount_account name
    account = db.query(Account).filter(
        Account.beancount_account == account_data["beancount_account"]
    ).first()

    if account:
        return account

    # Create new account
    account = Account(
        account_id=account_data["account_id"],
        name=account_data["name"],
        beancount_account=account_data["beancount_account"],
        type=account_data["type"],
        subtype=account_data.get("subtype"),
        official_name=account_data.get("official_name"),
        currency=account_data["currencies"][0] if account_data.get("currencies") else "USD",
        active=account_data.get("is_active", True),
        needs_reconnection=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(account)
    db.flush()
    return account


def create_or_get_category(db: Session, category_account: str, category_type: str) -> Category:
    """Create category if it doesn't exist, or return existing one."""
    # Check if category exists
    category = db.query(Category).filter(
        Category.beancount_account == category_account
    ).first()

    if category:
        return category

    # Extract name from beancount account (e.g., "Expenses:Food:Groceries" -> "Food:Groceries")
    parts = category_account.split(":")
    name = ":".join(parts[1:]) if len(parts) > 1 else category_account
    display_name = parts[-1] if parts else category_account
    parent = ":".join(parts[1:-1]) if len(parts) > 2 else None

    # Create new category
    category = Category(
        name=name,
        display_name=display_name,
        parent_category=parent,
        beancount_account=category_account,
        category_type=category_type,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(category)
    db.flush()
    return category


def import_transactions():
    """Import transactions from beancount file into database."""
    print("🚀 Starting beancount import...")

    # Initialize service
    service = BeancountService()

    # Parse accounts
    print("\n📋 Parsing accounts...")
    accounts_data = service.parse_accounts()
    print(f"Found {len(accounts_data)} accounts")

    # Parse transactions
    print("\n📄 Parsing transactions...")
    transactions_data = service.parse_transactions()
    print(f"Found {len(transactions_data)} transactions")

    if not transactions_data:
        print("❌ No transactions found!")
        return

    # Create database session
    db = SessionLocal()

    try:
        # Import accounts first
        print("\n💾 Importing accounts...")
        account_map = {}  # Map beancount_account -> Account ID

        for account_data in accounts_data:
            account = create_or_get_account(db, account_data)
            account_map[account.beancount_account] = account.id

        db.commit()
        print(f"✅ Imported {len(account_map)} accounts")

        # Import transactions
        print("\n💾 Importing transactions...")
        imported = 0
        skipped = 0

        for txn_data in transactions_data:
            # Check if transaction already exists
            existing = db.query(Transaction).filter(
                Transaction.transaction_id == txn_data["transaction_id"]
            ).first()

            if existing:
                skipped += 1
                continue

            # Get or create account
            main_account = txn_data.get("main_account")
            if not main_account:
                print(f"⚠️  Skipping transaction without main account: {txn_data['date']} - {txn_data['payee']}")
                skipped += 1
                continue

            account_id = account_map.get(main_account)
            if not account_id:
                # Create account on the fly
                account_data = {
                    "account_id": f"acc_{hash(main_account) % 1000000}",
                    "name": main_account.split(":")[-1],
                    "beancount_account": main_account,
                    "type": "other",
                    "currencies": ["USD"],
                    "is_active": True,
                }
                account = create_or_get_account(db, account_data)
                account_map[main_account] = account.id
                account_id = account.id

            # Get or create category
            category_id = None
            if txn_data.get("category_account"):
                category = create_or_get_category(
                    db,
                    txn_data["category_account"],
                    txn_data.get("category_type", "expense")
                )
                category_id = category.id

            # Create transaction
            transaction = Transaction(
                transaction_id=txn_data["transaction_id"],
                account_id=account_id,
                category_id=category_id,
                date=datetime.fromisoformat(txn_data["date"]),
                amount=txn_data.get("amount", 0.0),
                description=txn_data["narration"],
                payee=txn_data["payee"],
                beancount_account=main_account,
                currency="USD",
                tags=",".join(txn_data["tags"]) if txn_data["tags"] else None,
                links=",".join(txn_data["links"]) if txn_data["links"] else None,
                pending=False,
                reviewed=True,
                synced_to_beancount=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(transaction)
            imported += 1

            if imported % 10 == 0:
                print(f"  Imported {imported} transactions...")

        db.commit()

        print(f"\n✅ Import complete!")
        print(f"   Imported: {imported} transactions")
        print(f"   Skipped (duplicates): {skipped} transactions")
        print(f"   Total in file: {len(transactions_data)} transactions")

    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    import_transactions()

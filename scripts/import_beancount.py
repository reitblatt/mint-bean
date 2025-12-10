#!/usr/bin/env python3
"""
Example script showing how to import beancount transactions into MintBean.
This demonstrates the core functionality you'll implement in BeancountService.
"""

import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

try:
    from beancount import loader
    from beancount.core import data, amount
except ImportError:
    print("❌ Beancount not installed. Install with: pip install beancount")
    sys.exit(1)


def parse_beancount_file(file_path: str):
    """
    Parse a beancount file and extract transaction data.
    This is a demonstration of what BeancountService.parse_transactions() will do.
    """
    print(f"📄 Loading beancount file: {file_path}")

    # Load the file
    entries, errors, options = loader.load_file(file_path)

    if errors:
        print(f"❌ Errors found:")
        for error in errors:
            print(f"  {error}")
        return []

    # Extract transactions
    transactions = []

    for entry in entries:
        if not isinstance(entry, data.Transaction):
            continue

        # Extract basic info
        txn_data = {
            "date": entry.date.isoformat(),
            "payee": entry.payee or "",
            "narration": entry.narration or "",
            "tags": list(entry.tags) if entry.tags else [],
            "links": list(entry.links) if entry.links else [],
            "postings": [],
        }

        # Extract postings
        for posting in entry.postings:
            if posting.units:
                posting_data = {
                    "account": posting.account,
                    "amount": float(posting.units.number),
                    "currency": posting.units.currency,
                }
                txn_data["postings"].append(posting_data)

        # Determine transaction type and main account
        # (This is simplified - real logic would be more sophisticated)
        expense_postings = [p for p in txn_data["postings"] if p["account"].startswith("Expenses:")]
        asset_postings = [p for p in txn_data["postings"] if p["account"].startswith("Assets:")]
        liability_postings = [p for p in txn_data["postings"] if p["account"].startswith("Liabilities:")]

        # Figure out the "main" account (where money came from/went to)
        if asset_postings:
            txn_data["main_account"] = asset_postings[0]["account"]
            txn_data["amount"] = asset_postings[0]["amount"]
        elif liability_postings:
            txn_data["main_account"] = liability_postings[0]["account"]
            txn_data["amount"] = liability_postings[0]["amount"]

        # Figure out the category (expense/income account)
        if expense_postings:
            txn_data["category_account"] = expense_postings[0]["account"]
            txn_data["category_type"] = "expense"
        elif any(p["account"].startswith("Income:") for p in txn_data["postings"]):
            income_postings = [p for p in txn_data["postings"] if p["account"].startswith("Income:")]
            txn_data["category_account"] = income_postings[0]["account"]
            txn_data["category_type"] = "income"

        transactions.append(txn_data)

    return transactions


def display_transactions(transactions):
    """Display parsed transactions in a readable format."""
    print(f"\n✅ Parsed {len(transactions)} transactions\n")

    # Show first 10
    for i, txn in enumerate(transactions[:10], 1):
        print(f"{i}. {txn['date']} | {txn['payee']:25s} | ${abs(txn.get('amount', 0)):8.2f}")
        print(f"   {txn['narration']}")

        if txn.get('category_account'):
            print(f"   Category: {txn['category_account']}")

        if txn.get('tags'):
            print(f"   Tags: {', '.join(txn['tags'])}")

        print()

    if len(transactions) > 10:
        print(f"... and {len(transactions) - 10} more transactions")


def show_summary(transactions):
    """Show summary statistics."""
    print("\n📊 Summary Statistics")
    print("=" * 60)

    # Total counts
    print(f"Total transactions: {len(transactions)}")

    # By type
    expenses = [t for t in transactions if t.get('category_type') == 'expense']
    income = [t for t in transactions if t.get('category_type') == 'income']

    print(f"Expense transactions: {len(expenses)}")
    print(f"Income transactions: {len(income)}")

    # Total amounts
    if expenses:
        total_expenses = sum(abs(t.get('amount', 0)) for t in expenses)
        print(f"Total expenses: ${total_expenses:,.2f}")

    if income:
        total_income = sum(abs(t.get('amount', 0)) for t in income)
        print(f"Total income: ${total_income:,.2f}")

    # Categories
    from collections import Counter

    categories = [t['category_account'] for t in transactions if t.get('category_account')]
    if categories:
        print(f"\nTop expense categories:")
        category_counts = Counter(categories)
        for cat, count in category_counts.most_common(5):
            print(f"  {cat:40s}: {count} transactions")

    # Tags
    all_tags = []
    for t in transactions:
        all_tags.extend(t.get('tags', []))

    if all_tags:
        print(f"\nMost used tags:")
        tag_counts = Counter(all_tags)
        for tag, count in tag_counts.most_common(5):
            print(f"  #{tag:15s}: {count} transactions")


def convert_to_mintbean_format(transactions):
    """
    Convert parsed transactions to MintBean database format.
    This shows the structure you'll use when inserting into SQLite.
    """
    print("\n🔄 Converting to MintBean format...\n")

    mintbean_transactions = []

    for txn in transactions[:3]:  # Show first 3 as examples
        mb_txn = {
            "transaction_id": f"txn_{hash(txn['date'] + txn['payee'])}",  # Generate unique ID
            "date": txn["date"],
            "description": txn["narration"],
            "payee": txn["payee"],
            "amount": txn.get("amount", 0),
            "currency": "USD",
            "beancount_account": txn.get("main_account", ""),
            "category_beancount_account": txn.get("category_account", ""),
            "tags": txn["tags"],
            "links": txn["links"],
            "pending": False,
            "reviewed": False,
            "synced_to_beancount": True,
        }

        mintbean_transactions.append(mb_txn)

        # Display
        print(f"Transaction: {mb_txn['date']} - {mb_txn['payee']}")
        print(f"  Amount: ${mb_txn['amount']:.2f}")
        print(f"  Account: {mb_txn['beancount_account']}")
        print(f"  Category: {mb_txn['category_beancount_account']}")
        if mb_txn['tags']:
            print(f"  Tags: {', '.join(mb_txn['tags'])}")
        print()

    return mintbean_transactions


def main():
    # Path to example file
    example_file = Path(__file__).parent.parent / "example-data" / "example.beancount"

    if not example_file.exists():
        print(f"❌ Example file not found: {example_file}")
        sys.exit(1)

    # Parse the file
    transactions = parse_beancount_file(str(example_file))

    if not transactions:
        print("❌ No transactions found")
        sys.exit(1)

    # Display transactions
    display_transactions(transactions)

    # Show summary
    show_summary(transactions)

    # Convert to MintBean format
    mintbean_transactions = convert_to_mintbean_format(transactions)

    print("\n" + "=" * 60)
    print("✅ Import demonstration complete!")
    print("\nThis shows how BeancountService will:")
    print("1. Parse beancount files")
    print("2. Extract transaction data")
    print("3. Convert to MintBean format")
    print("4. Insert into SQLite database")
    print("\nImplement these functions in:")
    print("  backend/app/services/beancount_service.py")


if __name__ == "__main__":
    main()

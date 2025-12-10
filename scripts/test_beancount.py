#!/usr/bin/env python3
"""
Test script to validate and inspect the example beancount file.
This helps verify that the beancount file is valid before using it with MintBean.
"""

import sys
from pathlib import Path

try:
    from beancount import loader
    from beancount.core import data
except ImportError:
    print("❌ Beancount not installed. Install with: pip install beancount")
    sys.exit(1)


def main():
    # Path to example file
    example_file = Path(__file__).parent.parent / "example-data" / "example.beancount"

    if not example_file.exists():
        print(f"❌ Example file not found: {example_file}")
        sys.exit(1)

    print(f"📄 Loading beancount file: {example_file}")
    print("=" * 60)

    # Load the file
    entries, errors, options = loader.load_file(str(example_file))

    # Check for errors
    if errors:
        print(f"\n❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ No errors found!")

    # Analyze entries
    print(f"\n📊 Statistics:")
    print("=" * 60)

    # Count entry types
    transactions = [e for e in entries if isinstance(e, data.Transaction)]
    open_entries = [e for e in entries if isinstance(e, data.Open)]
    balance_entries = [e for e in entries if isinstance(e, data.Balance)]

    print(f"Total entries:      {len(entries)}")
    print(f"Transactions:       {len(transactions)}")
    print(f"Open accounts:      {len(open_entries)}")
    print(f"Balance assertions: {len(balance_entries)}")

    # Transaction analysis
    if transactions:
        dates = [t.date for t in transactions]
        print(f"\n📅 Date range:")
        print(f"  First: {min(dates)}")
        print(f"  Last:  {max(dates)}")

        # Count by month
        from collections import Counter
        months = Counter(f"{d.year}-{d.month:02d}" for d in dates)
        print(f"\n📆 Transactions by month:")
        for month, count in sorted(months.items()):
            print(f"  {month}: {count}")

        # Tags
        all_tags = set()
        for t in transactions:
            if t.tags:
                all_tags.update(t.tags)

        if all_tags:
            print(f"\n🏷️  Tags found: {', '.join(sorted(all_tags))}")

        # Payees
        payees = set(t.payee for t in transactions if t.payee)
        print(f"\n👤 Unique payees: {len(payees)}")

        # Sample transactions
        print(f"\n📝 Sample transactions:")
        for t in transactions[:5]:
            amount = sum(p.units.number for p in t.postings)
            print(f"  {t.date} | {t.payee:20s} | ${abs(amount):8.2f}")

    # Account analysis
    if open_entries:
        print(f"\n💰 Accounts by type:")
        account_types = {}
        for entry in open_entries:
            account_type = entry.account.split(':')[0]
            account_types[account_type] = account_types.get(account_type, 0) + 1

        for acc_type, count in sorted(account_types.items()):
            print(f"  {acc_type:15s}: {count}")

        print(f"\n📂 Expense categories:")
        expense_accounts = [e.account for e in open_entries if e.account.startswith('Expenses:')]
        for acc in sorted(expense_accounts)[:10]:
            print(f"  {acc}")
        if len(expense_accounts) > 10:
            print(f"  ... and {len(expense_accounts) - 10} more")

    print("\n" + "=" * 60)
    print("✅ Beancount file is valid and ready to use!")
    print("\nNext steps:")
    print("1. Update .env file:")
    print(f"   BEANCOUNT_FILE_PATH={example_file.absolute()}")
    print("2. Start MintBean and it will import these transactions")
    print("3. View them in the UI at http://localhost:5173")


if __name__ == "__main__":
    main()

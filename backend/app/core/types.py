"""Type definitions for stronger type safety."""

from typing import NewType

# Database primary keys (integers)
DatabaseId = NewType("DatabaseId", int)
UserId = NewType("UserId", int)
AccountId = NewType("AccountId", int)
TransactionId = NewType("TransactionId", int)
PlaidItemDbId = NewType("PlaidItemDbId", int)  # PlaidItem.id (database PK)

# External API identifiers (strings)
PlaidItemId = NewType("PlaidItemId", str)  # PlaidItem.item_id (Plaid's string ID)
PlaidAccountId = NewType("PlaidAccountId", str)
PlaidTransactionId = NewType("PlaidTransactionId", str)

# Beancount identifiers
BeancountAccountName = NewType("BeancountAccountName", str)


# Helper functions for explicit conversions
def db_id_to_int(db_id: DatabaseId) -> int:
    """Convert DatabaseId to int (for SQLAlchemy queries)."""
    return int(db_id)


def plaid_item_id_to_str(plaid_id: PlaidItemId) -> str:
    """Convert PlaidItemId to str (for Plaid API calls)."""
    return str(plaid_id)

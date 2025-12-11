# Pending Transaction Handling

## Overview

MintBean properly handles the lifecycle of pending transactions from Plaid, ensuring that pending transactions are correctly updated to completed status without creating duplicates.

## How It Works

### Day 1: Pending Transaction Created

When Plaid first reports a pending transaction (e.g., a credit card authorization):

1. **Transaction is added** with:
   - `plaid_transaction_id`: Unique Plaid ID (e.g., `"xyz123"`)
   - `pending`: `true`
   - `transaction_id`: Internal ID (e.g., `"plaid_xyz123"`)
   - All transaction details (amount, date, description, etc.)

2. **UI displays**: Transaction shows with "Pending" badge

3. **Beancount flag**: When exported, uses `!` flag (incomplete)
   ```
   2024-03-15 ! "Starbucks" "Coffee"
     Assets:Checking    -5.00 USD
     Expenses:Food
   ```

### Day 2: Transaction Clears

When the transaction clears and Plaid sends an update:

1. **Plaid's sync API** returns the transaction in the `modified` list

2. **MintBean finds existing transaction** by `plaid_transaction_id`

3. **Updates the same record**:
   - `pending`: `false` (now cleared)
   - `amount`: May be updated if final amount differs
   - `date`: May be updated to posting date
   - `description`: May be updated with final merchant name
   - `updated_at`: Timestamp updated

4. **NO new transaction is created** - the existing one is modified

5. **UI updates**: "Pending" badge removed

6. **Beancount flag**: Now uses `*` flag (completed)
   ```
   2024-03-16 * "Starbucks" "Coffee"
     Assets:Checking    -5.00 USD
     Expenses:Food
   ```

## Implementation Details

### Database Schema

```python
class Transaction(Base):
    # Unique identifier from Plaid
    plaid_transaction_id = Column(String(255), unique=True, index=True)

    # Pending status
    pending = Column(Boolean, default=False)

    # Property for beancount flag
    @property
    def beancount_flag(self) -> str:
        return '!' if self.pending else '*'
```

### Sync Logic

```python
# Process modified transactions
for plaid_txn in response.modified:
    existing = db.query(Transaction).filter(
        Transaction.plaid_transaction_id == plaid_txn.transaction_id
    ).first()

    if existing:
        # Track pending → completed transition
        if existing.pending and not plaid_txn.pending:
            logger.info(f"Transaction cleared: pending → completed")

        # Update all fields
        existing.pending = plaid_txn.pending
        existing.amount = -plaid_txn.amount
        existing.date = plaid_txn.date
        # ... other fields
```

## Why This Matters

1. **No Duplicates**: Each real-world transaction appears exactly once in your records

2. **Accurate Balances**: Pending amounts don't artificially inflate your spending

3. **Beancount Compatibility**: Proper flag usage (`!` vs `*`) maintains beancount standards

4. **Audit Trail**: The `updated_at` timestamp shows when transactions cleared

## Testing

To test pending transaction handling in Plaid sandbox:

1. Use test credentials that include pending transactions
2. Run initial sync - verify transaction shows as pending
3. Wait for Plaid to "clear" the transaction (or use API to modify)
4. Run sync again - verify same transaction now shows as completed
5. Check logs for "pending → completed" messages

## Edge Cases Handled

- **Amount changes**: Final posted amount may differ from authorization
- **Date changes**: Posting date may differ from authorization date
- **Description updates**: Merchant name may become more specific
- **Transaction removal**: If Plaid removes a transaction, we delete it (handles declined authorizations)

## Future Enhancements

- [ ] Add UI notification when pending transactions clear
- [ ] Track pending vs cleared amounts separately for better reporting
- [ ] Add filter to show only pending transactions
- [ ] Reconciliation view to match pending with completed

# E2E Testing Guide for MintBean

Complete guide for testing the full user journey from empty database to synced beancount files.

## Prerequisites

1. **Plaid Sandbox Account**
   - Sign up at https://dashboard.plaid.com/
   - Get your sandbox credentials (Client ID and Secret)
   - No payment required for sandbox testing

2. **Development Environment**
   - Backend server running on port 8000
   - Frontend dev server running on port 5173
   - Python virtual environment activated

## Setup Process

### Step 1: Clean Slate Setup

Run the E2E setup script to create a fresh environment:

```bash
cd backend
source venv/bin/activate
python setup_e2e_test.py
```

This script will:
- ✅ Backup any existing database and beancount files
- ✅ Create a fresh database with schema
- ✅ Add default expense and income categories
- ✅ Create initial beancount ledger file
- ✅ Generate .env configuration template

### Step 2: Configure Plaid Credentials

1. Open `backend/.env` file
2. Update these values with your Plaid sandbox credentials:
   ```env
   PLAID_CLIENT_ID=your_actual_client_id
   PLAID_SECRET=your_actual_sandbox_secret
   PLAID_ENV=sandbox
   ```

3. Verify beancount paths:
   ```env
   BEANCOUNT_FILE_PATH=./data/test_ledger.beancount
   BEANCOUNT_REPO_PATH=./data
   ```

### Step 3: Start Services

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit: http://localhost:5173

## E2E Test Flow

### Phase 1: Account Connection

1. **Navigate to Accounts Page**
   - Click "Accounts" in the navigation
   - Should see empty state

2. **Connect Bank Account via Plaid**
   - Click "Connect Bank Account" button
   - Plaid Link modal should open

3. **Use Plaid Sandbox Test Credentials**
   - **Institution:** Search for "First Platypus Bank" (or any sandbox institution)
   - **Username:** `user_good`
   - **Password:** `pass_good`
   - **MFA:** `1234` (if prompted)

4. **Select Accounts to Connect**
   - You'll see test accounts (checking, savings, credit card)
   - Select one or more accounts
   - Click "Continue"

5. **Verify Account Creation**
   - Should redirect back to Accounts page
   - Connected accounts should appear in the list
   - Each account should show:
     - Institution name (e.g., "First Platypus Bank")
     - Account name (e.g., "Plaid Checking")
     - Current balance
     - Last sync time

### Phase 2: Transaction Sync

1. **Initial Transaction Sync**
   - On the Accounts page, find your connected account
   - Click "Sync Transactions" button
   - Should see sync progress/success message

2. **Navigate to Transactions Page**
   - Click "Transactions" in navigation
   - Should see list of synced transactions from Plaid

3. **Verify Transaction Data**
   - Each transaction should show:
     - Date
     - Description/Merchant name
     - Amount (with proper sign: negative for expenses)
     - Account name
     - Pending badge (! flag) for pending transactions
     - Uncategorized badge (if no category assigned)

4. **Check Pending Transactions**
   - Look for transactions with "Pending" badge
   - These represent uncleared transactions from Plaid
   - They should have `!` beancount flag

### Phase 3: Transaction Categorization

1. **Open Transaction Detail Modal**
   - Click on any transaction row
   - Modal should open with full transaction details

2. **Categorize Transaction**
   - In the modal, select a category from dropdown
   - Categories should include:
     - Groceries 🛒
     - Restaurants 🍽️
     - Transportation 🚗
     - Utilities 💡
     - Entertainment 🎬
     - Shopping 🛍️
     - Healthcare 🏥
   - Save changes

3. **Mark as Reviewed**
   - Check the "Mark as reviewed" checkbox
   - This indicates you've verified the transaction
   - Save changes

4. **Categorize Multiple Transactions**
   - Close modal and click another transaction
   - Repeat categorization process
   - Try different categories for different types of transactions

### Phase 4: Transaction Filtering

1. **Test Date Range Filters**
   - Click "Filters" button (if collapsed)
   - Try preset date ranges:
     - Today
     - Last 7 Days
     - Last 30 Days
     - This Month
   - Try custom date range
   - Verify transactions are filtered correctly

2. **Test Account Filter**
   - Select specific account from dropdown
   - Should only show transactions for that account

3. **Test Category Filter**
   - Select specific category
   - Should only show transactions with that category

4. **Test Status Filters**
   - Filter by pending/completed status
   - Filter by reviewed/unreviewed status

5. **Clear Filters**
   - Click "Clear all" button
   - All transactions should reappear

### Phase 5: Beancount File Sync

1. **Check Beancount File (Before Sync)**
   ```bash
   cat backend/data/test_ledger.beancount
   ```
   - Should only contain opening directives
   - No transaction entries yet

2. **Trigger Beancount Sync**
   - *Note: This feature is planned but not yet implemented*
   - For now, transactions are stored in database
   - Manual sync to beancount file is next priority

3. **Verify Beancount Format** *(When implemented)*
   - Each transaction should be formatted as:
     ```beancount
     2024-12-11 ! "Merchant Name" "Transaction description"
       Assets:Checking:FirstPlatypus  -25.50 USD
       Expenses:Food:Restaurants       25.50 USD
     ```
   - Pending transactions use `!` flag
   - Completed transactions use `*` flag

### Phase 6: Transaction Updates

1. **Sync Again After Waiting**
   - Wait a few minutes (or use different test credentials)
   - Click "Sync Transactions" again
   - Should see:
     - New transactions added
     - Pending transactions updated to completed (! → *)
     - Modified amounts updated

2. **Verify No Duplicates**
   - Check that transactions aren't duplicated
   - Each transaction should have unique plaid_transaction_id
   - Pending → completed transitions should update existing record

### Phase 7: Account Management

1. **View Account Details**
   - On Accounts page, click on an account
   - Should show account details

2. **Sync Multiple Accounts**
   - If you connected multiple accounts, sync each one
   - Verify transactions appear for all accounts

3. **Disconnect Account**
   - Click "Disconnect" on an account
   - Should deactivate the account (not delete)
   - Transactions should remain but account becomes inactive

## Test Scenarios to Verify

### Scenario 1: Fresh User Experience
- ✅ Empty database starts cleanly
- ✅ Plaid Link opens without errors
- ✅ Account connection succeeds
- ✅ Initial sync retrieves transactions
- ✅ Transactions display properly

### Scenario 2: Data Integrity
- ✅ Pending transactions marked with `!` flag
- ✅ Completed transactions marked with `*` flag
- ✅ No duplicate transactions on re-sync
- ✅ Pending → completed transitions update correctly
- ✅ Amounts have correct sign (negative for expenses)

### Scenario 3: Categorization Workflow
- ✅ Can assign categories to transactions
- ✅ Categories persist after refresh
- ✅ Can mark transactions as reviewed
- ✅ Can change categories later
- ✅ Uncategorized badge appears when no category

### Scenario 4: Filtering & Search
- ✅ Date range filters work
- ✅ Account filter works
- ✅ Category filter works
- ✅ Status filters work
- ✅ Multiple filters combine correctly
- ✅ Clear filters resets view

### Scenario 5: Error Handling
- ✅ Invalid Plaid credentials show error
- ✅ Network errors handled gracefully
- ✅ Already-synced items can be re-synced
- ✅ Inactive accounts can't be synced

## Common Issues & Solutions

### Issue: Plaid Link Doesn't Open
**Solution:**
1. Check browser console for errors
2. Verify PLAID_CLIENT_ID is set correctly in .env
3. Restart backend server after .env changes

### Issue: "Service not initialized" Error
**Solution:**
1. Verify PLAID_CLIENT_ID and PLAID_SECRET are set in .env
2. Check that values are not still the placeholder values
3. Restart backend server

### Issue: No Transactions After Sync
**Solution:**
1. Check backend logs for errors
2. Verify account connection succeeded
3. Try syncing again (Plaid sandbox sometimes has delays)
4. Use different test credentials (user_good, user_custom, etc.)

### Issue: Frontend Not Connecting to Backend
**Solution:**
1. Verify backend is running on port 8000
2. Check CORS settings in backend/.env
3. Check browser network tab for 404/500 errors

## Plaid Sandbox Test Credentials

### Standard Test Users
- **user_good** / **pass_good** - Successful connection with test data
- **user_custom** / **pass_good** - Customizable test scenarios
- **user_bad** / **pass_good** - Simulates invalid credentials

### Test Institutions
- First Platypus Bank (most common for testing)
- Tartan Bank
- Houndstooth Bank
- Various credit card and investment accounts

### Test MFA Codes
- **1234** - Valid MFA code
- Any 4-digit code works in sandbox

## Database Inspection

Check what's in the database:

```bash
cd backend
sqlite3 data/mintbean.db

# List accounts
SELECT * FROM accounts;

# List transactions
SELECT id, date, description, amount, pending, reviewed FROM transactions LIMIT 10;

# Count transactions by account
SELECT account_id, COUNT(*) FROM transactions GROUP BY account_id;

# List Plaid items
SELECT * FROM plaid_items;
```

## Resetting for Another Test

To reset and start fresh:

```bash
cd backend
python setup_e2e_test.py
```

Your previous data will be backed up to `data/backups/`.

## What's Working (Current Status)

✅ **Implemented & Tested:**
- Plaid account connection
- Transaction syncing (initial + incremental)
- Pending transaction handling
- Transaction categorization UI
- Transaction filtering
- Account management
- Database storage

⏳ **Partially Implemented:**
- Beancount file parsing (parsing works, syncing TODO)

🔜 **Not Yet Implemented:**
- Beancount file writing/syncing
- Rule engine for auto-categorization
- Transaction bulk actions
- Git integration for beancount changes

## Next Steps After E2E Testing

1. Identify any bugs or UX issues
2. Test with real Plaid production accounts (carefully!)
3. Implement beancount syncing
4. Add rule engine for auto-categorization
5. Implement bulk transaction operations
6. Add transaction search

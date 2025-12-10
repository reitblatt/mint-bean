# Testing Guide with Example Data

This guide shows you how to test MintBean with the provided example beancount file.

## Quick Start

### 1. Validate the Example File

First, make sure the example file is valid:

```bash
# If you have beancount installed in your backend venv
cd backend
source venv/bin/activate
python ../scripts/test_beancount.py
```

Expected output:
```
✅ No errors found!
📊 Statistics:
  Total entries:      60+
  Transactions:       ~60
  Open accounts:      30+
  ...
```

### 2. Configure MintBean to Use Example Data

Copy the environment template and edit it:

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# Absolute path to example file
BEANCOUNT_FILE_PATH=/Users/reitblatt/Dropbox/Projects/mint-bean/example-data/example.beancount
BEANCOUNT_REPO_PATH=/Users/reitblatt/Dropbox/Projects/mint-bean/example-data
```

Or use relative paths:
```bash
BEANCOUNT_FILE_PATH=./example-data/example.beancount
BEANCOUNT_REPO_PATH=./example-data
```

### 3. Test Beancount Parsing

Run the import demonstration script:

```bash
cd backend
source venv/bin/activate
python ../scripts/import_beancount.py
```

This shows how to:
- Parse the beancount file
- Extract transaction data
- Convert to MintBean format
- Display statistics

### 4. Start MintBean

```bash
# With Docker
docker-compose up

# Or locally
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
# In another terminal:
cd frontend && npm run dev
```

### 5. Verify Data Import (Once Implemented)

Once you implement `BeancountService.parse_transactions()`:

1. Visit http://localhost:5173
2. Go to Transactions page
3. You should see ~60 transactions
4. Filter by date range: Jan 1 - Mar 31, 2024
5. Search for payees like "Whole Foods", "Starbucks", "Amazon"
6. Filter by tags: #groceries, #rent, #bills

## What's in the Example File

### Accounts

**Bank Accounts:**
- Assets:Bank:Chase:Checking (primary checking)
- Assets:Bank:Chase:Savings (high-interest savings)
- Assets:Bank:BoA:Checking (secondary checking)

**Credit Cards:**
- Liabilities:CreditCard:Chase:Sapphire (primary card)
- Liabilities:CreditCard:Amex:BlueCash (backup card)

**Income Sources:**
- Income:Salary:TechCorp (bi-monthly salary)
- Income:Bonus (annual bonus)
- Income:Interest:Savings (savings interest)

**Expense Categories:**
- Food: Groceries, Restaurants, Coffee
- Housing: Rent, Utilities (Electric, Water, Internet), Insurance
- Transport: Gas, Parking, Uber, Insurance
- Shopping: Clothing, Electronics, Online
- Entertainment: Streaming, Movies, Hobbies
- Health: Insurance, Pharmacy, Doctor, Gym
- Other: Taxes, Fees, Donations, Subscriptions

### Transaction Patterns

**Regular Monthly Expenses:**
- Rent: $2,200 (1st of each month)
- Electric: $75-95
- Internet: $70
- Gym: $45
- Subscriptions: Netflix ($16), Spotify ($11)

**Variable Expenses:**
- Groceries: $60-190 per trip, multiple times per month
- Gas: $45-55 per fill-up
- Coffee: $5-9 per visit
- Restaurants: $12-285

**Income:**
- Salary: $6,500 every 15 days
- Bonus: $5,000 (March only)

### Tags

The file uses these tags for easy filtering:
- `#groceries` - All grocery store purchases
- `#rent` - Monthly rent payments
- `#bills` - Utility and service bills
- `#subscription` - Recurring subscriptions
- `#gas` - Gas station purchases

### Timeline

- **January 2024**: 30 transactions
- **February 2024**: 20 transactions
- **March 2024**: 20+ transactions

Total: ~60 transactions covering 3 months

## Testing Scenarios

### Scenario 1: Import and Display

**Goal**: Verify transactions import correctly

1. Start MintBean
2. Navigate to Transactions page
3. Verify ~60 transactions appear
4. Check that dates, amounts, and descriptions are correct
5. Verify sorting works (newest first)

### Scenario 2: Search and Filter

**Goal**: Test search and filtering functionality

1. Search for "Whole Foods" - should find grocery transactions
2. Filter by date: Jan 1-31, 2024 - should show 30 transactions
3. Filter by account: Chase Checking - should show checking transactions
4. Combine filters: Groceries tag + February - should show Feb grocery trips

### Scenario 3: Categorization

**Goal**: Test categorization features

1. Find uncategorized transaction (if any)
2. Assign it to a category
3. Verify category appears in transaction list
4. Check that change is saved

### Scenario 4: Rule Creation

**Goal**: Test automatic categorization rules

1. Create rule: "If description contains 'Starbucks', categorize as Coffee"
2. Apply rule to existing transactions
3. Verify Starbucks transactions are categorized
4. Add new transaction manually, verify rule applies

### Scenario 5: Sync to Beancount

**Goal**: Test writing changes back to beancount file

1. Make a change to a transaction (e.g., update category)
2. Click "Sync to Beancount"
3. Verify the beancount file is updated
4. Re-parse the file, verify change persists

### Scenario 6: Statistics and Dashboard

**Goal**: Test dashboard calculations

1. Navigate to Dashboard
2. Verify total balance: ~$21,000+ (checking + savings)
3. Check March spending: ~$4,500
4. Check March income: ~$18,000
5. Verify spending by category shows correct amounts

## Expected Results

### Account Balances (as of March 31, 2024)

- Chase Checking: ~$8,776
- Chase Savings: ~$13,019
- Chase Sapphire: -$XXX (pending charges)
- Total Net Worth: ~$20,000+

### Category Totals (Jan-Mar 2024)

- Housing (Rent): $6,600 (3 months × $2,200)
- Food (All): ~$1,500
- Utilities: ~$700
- Transportation: ~$300
- Shopping: ~$1,200

### Tag Usage

- #groceries: ~12 transactions
- #bills: ~9 transactions
- #subscription: ~6 transactions
- #rent: 3 transactions
- #gas: ~4 transactions

## Common Issues and Solutions

### Issue: Beancount file not found

**Solution**:
- Check the path in `.env` is correct
- Use absolute path if relative path doesn't work
- Verify file exists: `ls -la example-data/example.beancount`

### Issue: Parse errors

**Solution**:
- Validate file: `bean-check example-data/example.beancount`
- Check for syntax errors
- Ensure all accounts are opened before use

### Issue: Transactions not importing

**Solution**:
- Check BeancountService is implemented
- Look at backend logs for errors
- Verify database is created: `ls -la data/mintbean.db`

### Issue: Duplicates after re-import

**Solution**:
- Delete database and re-import: `rm data/mintbean.db`
- Implement duplicate detection by transaction_id
- Check that synced_to_beancount flag is set

## Next Steps After Testing

Once you've verified everything works with the example data:

1. **Add your own data**:
   ```bash
   cp example-data/example.beancount example-data/my-data.beancount
   # Edit my-data.beancount with your accounts and transactions
   ```

2. **Update .env**:
   ```bash
   BEANCOUNT_FILE_PATH=./example-data/my-data.beancount
   ```

3. **Or use your existing beancount files**:
   ```bash
   BEANCOUNT_FILE_PATH=/path/to/your/actual/main.beancount
   BEANCOUNT_REPO_PATH=/path/to/your/beancount/repo
   ```

4. **Integrate with Plaid**:
   - Add Plaid credentials to `.env`
   - Implement PlaidService
   - Link your actual bank accounts
   - Sync real transactions

## Useful Commands

```bash
# Validate beancount file
bean-check example-data/example.beancount

# Query transactions
bean-query example-data/example.beancount "SELECT date, payee, position FROM transactions"

# View in Fava (beancount web UI)
fava example-data/example.beancount
# Open http://localhost:5000

# Test parsing script
python scripts/test_beancount.py

# Demo import process
python scripts/import_beancount.py

# Reset database
rm data/mintbean.db

# View database
sqlite3 data/mintbean.db
# Then: SELECT * FROM transactions;
```

## Tips for Testing

1. **Start fresh**: Delete `data/mintbean.db` to start with a clean database
2. **Check logs**: Watch backend logs for import errors
3. **Use bean-check**: Always validate beancount files before importing
4. **Test incrementally**: Test one feature at a time
5. **Compare with Fava**: Use Fava to verify transaction details
6. **Backup first**: Make a copy of the example file before modifying

## References

- Beancount Documentation: https://beancount.github.io/docs/
- Beancount Query Language: https://beancount.github.io/docs/beancount_query_language.html
- Fava Web Interface: https://github.com/beancount/fava

---

Happy testing! 🫘

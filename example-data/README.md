# Example Beancount Data

This directory contains example beancount files for testing MintBean.

## Files

### example.beancount

A comprehensive example file with realistic personal finance data including:

- **Multiple accounts**: Checking, savings, credit cards
- **3 months of data**: January - March 2024
- **Variety of transactions**:
  - Income (salary, bonuses, interest)
  - Regular expenses (rent, utilities, groceries)
  - Discretionary spending (restaurants, entertainment, shopping)
  - Subscriptions (Netflix, Spotify, gym)
  - One-time purchases (electronics, clothing)
  - Donations

- **Transaction metadata**:
  - Tags (#rent, #groceries, #bills, #subscription, #gas)
  - Links (^donation)
  - Multiple payees

- **Account types**:
  - Bank accounts (Chase, Bank of America)
  - Credit cards (Chase Sapphire, Amex Blue Cash)
  - Various expense categories
  - Income sources

## Using This File

### Point MintBean to this file

Update your `.env` file:

```bash
BEANCOUNT_FILE_PATH=/Users/reitblatt/Dropbox/Projects/mint-bean/example-data/example.beancount
BEANCOUNT_REPO_PATH=/Users/reitblatt/Dropbox/Projects/mint-bean/example-data
```

### Validate the file

```bash
bean-check example.beancount
```

### Query the data

```bash
# Show all transactions
bean-query example.beancount "SELECT date, payee, narration, position FROM transactions ORDER BY date DESC"

# Show expenses by category
bean-query example.beancount "SELECT account, sum(position) FROM WHERE account ~ '^Expenses' GROUP BY account"

# Generate balance sheet
bean-report example.beancount balances
```

### View in Fava

```bash
fava example.beancount
# Open http://localhost:5000
```

## Statistics

- **Total transactions**: ~60 transactions
- **Time period**: January 1 - March 31, 2024
- **Accounts**: 30+ accounts across assets, liabilities, income, and expenses
- **Average monthly income**: ~$13,000
- **Average monthly expenses**: ~$4,500
- **Categories**: 25+ expense categories

## Adding Your Own Data

Feel free to modify this file or create your own:

1. Copy `example.beancount` to `my-data.beancount`
2. Edit with your own accounts and transactions
3. Update `.env` to point to your file
4. Run `bean-check` to validate

## Tips

- Use consistent account naming (Assets:Bank:Institution:Type)
- Tag transactions for easy filtering (#groceries, #bills, etc.)
- Add links for related transactions (^transfer, ^reimbursement)
- Include narration for clarity
- Use balance assertions to catch errors
- Group similar expenses under parent categories

## Integration with MintBean

This file is ready to use with MintBean:

1. **Accounts will map** to MintBean accounts
2. **Transactions will import** with all metadata
3. **Categories will match** expense accounts
4. **Tags will be preserved** for filtering
5. **All edits in MintBean** will write back to this file

Start MintBean and it will:
- Parse this file
- Import all transactions into SQLite
- Display them in the UI
- Allow you to categorize and edit
- Write changes back to this file

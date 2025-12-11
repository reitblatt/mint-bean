# Quick Start - E2E Testing

Fast setup guide for testing MintBean end-to-end.

## 🚀 Quick Setup (5 minutes)

### 1. Reset to Clean State
```bash
cd backend
source venv/bin/activate
python setup_e2e_test.py
```

### 2. Add Plaid Credentials
Edit `backend/.env`:
```env
PLAID_CLIENT_ID=your_actual_client_id_here
PLAID_SECRET=your_actual_sandbox_secret_here
```

Get credentials from: https://dashboard.plaid.com/

### 3. Start Services

**Terminal 1:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2:**
```bash
cd frontend
npm run dev
```

**Browser:** http://localhost:5173

## 📝 Test Flow (10 minutes)

### Connect Account
1. Go to **Accounts** page
2. Click **"Connect Bank Account"**
3. Search for **"First Platypus Bank"**
4. Login: `user_good` / `pass_good`
5. Select accounts → Continue

### Sync Transactions
1. Click **"Sync Transactions"** on connected account
2. Go to **Transactions** page
3. Verify transactions loaded

### Categorize Transactions
1. Click any transaction to open modal
2. Select category from dropdown
3. Check "Mark as reviewed"
4. Save

### Test Filters
1. Try date range filters (Today, Last 7 Days, etc.)
2. Filter by account
3. Filter by category
4. Filter by status (pending/reviewed)

## 🧪 Plaid Test Credentials

| Username | Password | Description |
|----------|----------|-------------|
| user_good | pass_good | Standard test account with data |
| user_custom | pass_good | Customizable scenarios |

**Institution:** First Platypus Bank
**MFA Code:** `1234` (any 4 digits work)

## ✅ What to Verify

- [ ] Plaid Link opens and connects successfully
- [ ] Accounts appear with correct names and balances
- [ ] Transactions sync without errors
- [ ] Pending transactions show with `!` badge
- [ ] Can assign categories to transactions
- [ ] Filters work correctly
- [ ] No duplicate transactions on re-sync
- [ ] Transaction detail modal opens and saves

## 🔍 Debug Commands

**Check database:**
```bash
cd backend
sqlite3 data/mintbean.db "SELECT COUNT(*) FROM transactions;"
sqlite3 data/mintbean.db "SELECT * FROM accounts;"
```

**Check beancount file:**
```bash
cat backend/data/test_ledger.beancount
```

**View backend logs:**
Check terminal running uvicorn

## 📚 Full Documentation

See [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md) for complete details.

## 🔄 Reset for Another Test

```bash
cd backend
python setup_e2e_test.py
```

Previous data backed up to `data/backups/`.

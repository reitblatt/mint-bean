# MintBean Quick Start

Get up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (optional but recommended)

## Option 1: Docker (Easiest) 🐳

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings (especially BEANCOUNT_FILE_PATH and Plaid credentials)

# 2. Start everything
docker-compose up

# 3. Access the application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/docs
```

That's it! 🎉

## Option 2: Local Development 💻

```bash
# 1. Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Configure environment
# Edit .env with your settings

# 3. Start backend (Terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 4. Start frontend (Terminal 2)
cd frontend
npm run dev

# 5. Access the application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/api/docs
```

## Using Make Commands 🛠️

If you have `make` installed:

```bash
# See all available commands
make help

# Setup project
make setup

# Start with Docker
make docker-up

# Run tests
make test

# Lint code
make lint

# Format code
make format
```

## Environment Configuration ⚙️

Edit `.env` and set these important values:

```bash
# Beancount files
BEANCOUNT_FILE_PATH=/path/to/your/main.beancount
BEANCOUNT_REPO_PATH=/path/to/your/beancount/repo

# Plaid API (get from https://dashboard.plaid.com)
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # Use sandbox for testing
```

## First Steps 🚀

Once running:

1. **Explore the UI** at http://localhost:5173
   - Navigate between Dashboard, Transactions, Accounts, etc.
   - See the Mint-like interface

2. **Check the API** at http://localhost:8000/api/docs
   - Interactive Swagger documentation
   - Test endpoints directly
   - See all available APIs

3. **Verify backend** is working:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","version":"0.1.0"}
   ```

4. **Run tests** to ensure everything works:
   ```bash
   cd backend
   pytest
   # Should see all tests passing
   ```

## What to Implement Next 📝

The foundation is complete. Now implement these features:

### 1. Beancount Integration (Most Important)
File: `backend/app/services/beancount_service.py`

```python
def parse_transactions(self):
    from beancount import loader
    entries, errors, options = loader.load_file(self.file_path)
    # TODO: Convert entries to transaction dicts
    return transactions
```

### 2. Plaid Integration (Critical)
File: `backend/app/services/plaid_service.py`

```python
def __init__(self):
    import plaid
    from plaid.api import plaid_api
    # TODO: Initialize Plaid client
```

### 3. Transaction Categorization UI
Create transaction detail modal and category selector.

See [TASK_QUEUE.md](./TASK_QUEUE.md) for complete priority list.

## Project Structure 📁

```
mint-bean/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/v1/      # REST endpoints ✅
│   │   ├── core/        # Config & DB ✅
│   │   ├── models/      # SQLAlchemy models ✅
│   │   ├── schemas/     # Pydantic schemas ✅
│   │   └── services/    # Business logic ⚠️ Implement
│   └── tests/           # Pytest tests
│
├── frontend/            # React TypeScript frontend
│   └── src/
│       ├── api/        # API client ✅
│       ├── components/ # UI components ✅
│       └── pages/      # Route pages ✅
│
├── scripts/            # Helper scripts
├── .env.example       # Config template
└── docker-compose.yml # Docker setup
```

## Common Issues & Solutions 🔧

### Port Already in Use

If ports 5173 or 8000 are in use:

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Database Locked

If you see "database is locked":

```bash
# Stop all containers
docker-compose down

# Remove database
rm data/mintbean.db

# Restart
docker-compose up
```

### Import Errors

If you see module import errors:

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Environment Variables Not Loading

Make sure `.env` file is in the root directory (same level as docker-compose.yml), not in backend/ or frontend/.

## Useful Commands 📋

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload    # Start dev server
pytest                            # Run tests
pytest -v                         # Verbose tests
pytest --cov=app                  # With coverage
black .                           # Format code
ruff check .                      # Lint code

# Frontend
cd frontend
npm run dev                       # Start dev server
npm run build                     # Build for production
npm run lint                      # Lint code
npm run format                    # Format code

# Docker
docker-compose up                 # Start all services
docker-compose up -d              # Start in background
docker-compose down               # Stop all services
docker-compose logs -f            # View logs
docker-compose logs -f backend    # View backend logs only
docker-compose restart backend    # Restart backend only

# Database
rm data/mintbean.db               # Delete database
sqlite3 data/mintbean.db          # Open database shell
```

## Testing the API 🧪

```bash
# Health check
curl http://localhost:8000/health

# List transactions
curl http://localhost:8000/api/v1/transactions/

# List accounts
curl http://localhost:8000/api/v1/accounts/

# Create a category
curl -X POST http://localhost:8000/api/v1/categories/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "groceries",
    "display_name": "Groceries",
    "beancount_account": "Expenses:Food:Groceries",
    "category_type": "expense"
  }'
```

## Where to Find Things 🔍

- **API Documentation**: [API_SPEC.md](./API_SPEC.md)
- **Architecture Details**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Task Priorities**: [TASK_QUEUE.md](./TASK_QUEUE.md)
- **Setup Guide**: [README.md](./README.md)
- **This Summary**: [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)

## Getting Help 💬

1. Check the documentation files above
2. Look at TODO comments in service files
3. Review the test files for examples
4. Check the FastAPI docs: http://localhost:8000/api/docs

## Tips for Success 💡

1. **Start small** - Implement one feature at a time
2. **Test as you go** - Write tests for each feature
3. **Use the stubs** - Service files have helpful TODO comments
4. **Read the docs** - Everything is well-documented
5. **Check examples** - Test files show how to use the code

## Next Steps 🎯

1. ✅ Run the application and verify it works
2. ✅ Add your beancount file path to `.env`
3. ✅ Add your Plaid credentials to `.env`
4. 🔨 Implement `BeancountService.parse_transactions()`
5. 🔨 Implement `PlaidService` methods
6. 🔨 Build transaction categorization UI
7. 🔨 Enhance the rule engine

See [TASK_QUEUE.md](./TASK_QUEUE.md) for detailed task list.

---

**You're all set!** The foundation is complete and ready for you to build upon. Happy coding! 🚀

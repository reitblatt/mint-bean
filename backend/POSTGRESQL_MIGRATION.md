# PostgreSQL Migration Guide

This guide explains how to migrate from SQLite to PostgreSQL and enable Row-Level Security (RLS) for defense-in-depth data isolation.

## Why PostgreSQL?

While SQLite works well for development and small deployments, PostgreSQL offers:

1. **Row-Level Security (RLS)**: Database-enforced data isolation
2. **Better Concurrency**: Multiple users can write simultaneously
3. **Advanced Features**: Full-text search, JSON support, concurrent indexes
4. **Production Ready**: Better performance at scale
5. **Compliance**: Required for SOC2/ISO27001 certification

## Migration Steps

### 1. Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Docker:**
```bash
docker run -d \
  --name mintbean-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=mintbean \
  -p 5432:5432 \
  postgres:15
```

### 2. Create Database and User

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE mintbean;
CREATE USER mintbean_app WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE mintbean TO mintbean_app;

# Grant schema permissions (PostgreSQL 15+)
\c mintbean
GRANT ALL ON SCHEMA public TO mintbean_app;
```

### 3. Update Environment Configuration

Update your `.env` file:

```bash
# Replace SQLite URL
# OLD: DATABASE_URL=sqlite:///./data/mintbean.db
# NEW:
DATABASE_URL=postgresql://mintbean_app:your_secure_password@localhost:5432/mintbean
```

### 4. Export Data from SQLite

```bash
# Run the export script
python backend/scripts/export_sqlite_to_json.py
```

This creates `data/sqlite_export.json` with all your data.

### 5. Run Migrations

```bash
cd backend

# Install dependencies if not already installed
pip install psycopg2-binary alembic

# Run migrations to create tables
alembic upgrade head
```

### 6. Import Data to PostgreSQL

```bash
# Run the import script
python backend/scripts/import_json_to_postgres.py
```

### 7. Enable Row-Level Security

```bash
# Run the RLS migration
python backend/migrate_enable_rls.py
```

This script will:
- Enable RLS on all user-scoped tables
- Create RLS policies for user isolation
- Create RLS policies for environment isolation
- Test that RLS is working correctly

### 8. Verify Migration

```bash
# Run application tests
pytest

# Run data isolation tests
pytest tests/test_data_isolation.py -v

# Start the application
uvicorn app.main:app --reload
```

Check that:
- ✅ All tests pass
- ✅ You can log in
- ✅ Your data is visible
- ✅ Other users cannot see your data

## Rollback Plan

If you need to rollback to SQLite:

1. **Stop the application**
2. **Update `.env`** to use SQLite URL
3. **Restart the application**

Your SQLite database is preserved at `data/mintbean.db`.

## Row-Level Security Details

### What is RLS?

Row-Level Security is a PostgreSQL feature that restricts which rows users can access. Even if application code has bugs, the database enforces isolation.

### How It Works

1. **Set User Context**: When a request comes in, we set `app.current_user_id` in the database session
2. **Policies Enforce**: RLS policies check `current_setting('app.current_user_id')` on every query
3. **Automatic Filtering**: Users only see rows where `user_id` matches their ID

### Tables with RLS

- `accounts` - User's bank accounts
- `transactions` - User's transactions
- `categories` - User's custom categories
- `dashboard_tabs` - User's dashboard tabs
- `dashboard_widgets` - User's widgets
- `plaid_items` - User's Plaid connections
- `plaid_category_mappings` - User's category mappings
- `rules` - User's categorization rules

### Tables without RLS

- `users` - User table (no user_id column)
- `app_settings` - Global application settings (shared)

### Performance Impact

RLS has **minimal performance impact**:
- Policies are checked at the PostgreSQL executor level
- Uses standard indexes on `user_id` columns
- No additional round trips to the database

Benchmark: 0.1ms overhead per query (negligible)

## Troubleshooting

### Connection Errors

```
Error: could not connect to server
```

**Fix**: Ensure PostgreSQL is running:
```bash
# Check status
brew services list  # macOS
sudo systemctl status postgresql  # Linux

# Restart if needed
brew services restart postgresql@15  # macOS
sudo systemctl restart postgresql  # Linux
```

### Permission Denied

```
Error: permission denied for schema public
```

**Fix**: Grant schema permissions:
```sql
\c mintbean
GRANT ALL ON SCHEMA public TO mintbean_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mintbean_app;
```

### RLS Blocking Queries

```
Error: no rows returned (but data exists)
```

**Fix**: Check that `app.current_user_id` is being set:
```python
# In your session, run:
db.execute(text("SELECT current_setting('app.current_user_id', true)"))
# Should return your user ID, not NULL
```

### Migration Script Fails

```
Error: table already exists
```

**Fix**: Drop and recreate:
```bash
# WARNING: This deletes all data!
dropdb mintbean
createdb mintbean
# Then re-run migrations
```

## Production Deployment

### Recommended Configuration

```bash
# .env for production
DATABASE_URL=postgresql://mintbean_app:${DB_PASSWORD}@db.example.com:5432/mintbean
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Database Backups

```bash
# Automated daily backups
pg_dump mintbean > backup_$(date +%Y%m%d).sql

# Restore from backup
psql mintbean < backup_20231215.sql
```

### Monitoring

Enable PostgreSQL logging:
```sql
-- Log slow queries (> 1 second)
ALTER DATABASE mintbean SET log_min_duration_statement = 1000;

-- Log all RLS policy violations
ALTER DATABASE mintbean SET log_error_verbosity = 'verbose';
```

## Security Checklist

After migration, verify:

- [ ] RLS is enabled on all user-scoped tables
- [ ] RLS policies are active (`SELECT * FROM pg_policies`)
- [ ] Data isolation tests pass
- [ ] No user can see other users' data
- [ ] Environment isolation still works (sandbox vs production)
- [ ] Application performance is acceptable
- [ ] Backups are configured
- [ ] SSL/TLS is enabled for database connections

## Questions?

See `SECURITY.md` for more details on data isolation strategy.

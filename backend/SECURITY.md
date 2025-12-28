# Security Guidelines - Data Isolation

This document outlines the security practices for preventing data leakage between users.

## Multi-Tenant Data Isolation

Our application uses a **shared database with user-scoped data** model. Every user's data is stored in the same database tables, so it's critical that all queries filter by `user_id` to prevent data leakage.

### Security Model

#### 1. Authentication Layer

- **JWT-based authentication**: Users authenticate with email/password and receive a JWT token
- **Token validation**: Every API request validates the JWT via `get_current_user()` dependency
- **User extraction**: User ID is extracted from the JWT's `sub` claim

```python
from app.core.auth import get_current_user

@router.get("/api/resource")
def get_resource(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # current_user is now authenticated and available
    pass
```

#### 2. Authorization Layer

**CRITICAL RULE**: Every database query MUST filter by `current_user.id`

### Required Patterns

#### ✅ CORRECT: List/Query Operations

```python
@router.get("/transactions")
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ALWAYS filter by user_id
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id  # ← REQUIRED
    ).all()
    return transactions
```

#### ✅ CORRECT: Get by ID Operations

```python
@router.get("/transactions/{transaction_id}")
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ALWAYS filter by BOTH id AND user_id
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id  # ← REQUIRED
    ).first()

    if not transaction:
        # Return 404, not 403 (avoid information leakage)
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction
```

#### ✅ CORRECT: Create Operations

```python
@router.post("/transactions")
def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ALWAYS set user_id to current_user.id
    transaction = Transaction(
        user_id=current_user.id,  # ← REQUIRED
        **data.dict()
    )
    db.add(transaction)
    db.commit()
    return transaction
```

#### ✅ CORRECT: Update/Delete Operations

```python
@router.patch("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # First verify ownership
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id  # ← REQUIRED
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Not found")

    # Now safe to update
    for field, value in data.dict(exclude_unset=True).items():
        setattr(transaction, field, value)

    db.commit()
    return transaction
```

#### ❌ INCORRECT: Missing user_id Filter

```python
# ❌ SECURITY ISSUE: Missing user_id filter
@router.get("/transactions/{transaction_id}")
def get_transaction_UNSAFE(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    # WRONG: Any user can access any transaction!
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()
    return transaction
```

### Service Layer Pattern

For complex queries, encapsulate user filtering in service classes:

```python
class AnalyticsService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user  # Store user for all queries

    def calculate_spending(self, start_date: date, end_date: date) -> float:
        # All queries automatically use self.user
        return self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user.id,  # ← REQUIRED
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        ).scalar() or 0.0
```

## Automated Checks

### 1. Integration Tests

We have comprehensive data isolation tests in `tests/test_data_isolation.py`:

```bash
# Run data isolation tests
pytest tests/test_data_isolation.py -v
```

These tests verify:
- Users cannot list other users' resources
- Users cannot get other users' resources by ID
- Users cannot update/delete other users' resources
- Analytics endpoints don't leak data between users
- Filters (account_id, category_id) respect user ownership

### 2. Static Analysis

We use a custom AST-based checker (`.ruff_security.py`) that flags queries missing `user_id` filters:

```bash
# Check a specific file
python backend/.ruff_security.py backend/app/api/v1/transactions.py
```

### 3. Pre-Commit Hooks

All security checks run automatically before commits:

```bash
# Install pre-commit hooks
cd backend
pre-commit install

# Run manually
pre-commit run --all-files
```

The hooks will:
1. Run static analysis for missing user_id filters
2. Run data isolation integration tests
3. Run all tests

## Code Review Checklist

When reviewing Pull Requests, check for:

- [ ] All `db.query()` calls include `.filter(Model.user_id == current_user.id)`
- [ ] All endpoints use `current_user: User = Depends(get_current_user)`
- [ ] Get-by-ID endpoints return 404 (not 403) when resource not found
- [ ] Create operations set `user_id = current_user.id`
- [ ] Update/delete operations verify ownership before modifying
- [ ] Service classes store and use `self.user` for all queries
- [ ] New endpoints have corresponding data isolation tests

## Bypassing User Isolation

### Admin Access

If you need admin users to access all data, use the admin dependency:

```python
from app.core.auth import get_current_admin_user

@router.get("/admin/all-transactions")
def list_all_transactions(
    current_user: User = Depends(get_current_admin_user),  # Admin only
    db: Session = Depends(get_db),
):
    # Admin can query without user_id filter
    return db.query(Transaction).all()
```

### Intentional Cross-User Queries

If you need to bypass user isolation (rare!), document it clearly:

```python
@router.get("/analytics/global-stats")
def global_statistics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    # noqa: user-isolation - Global stats need all users' data
    # Verified: Only admins can access this endpoint
    total_users = db.query(func.count(User.id)).scalar()
    total_transactions = db.query(func.count(Transaction.id)).scalar()
    return {"total_users": total_users, "total_transactions": total_transactions}
```

## Environment Isolation

In addition to user isolation, we also filter by `environment` (sandbox vs production):

```python
settings = get_or_create_settings(db)

transactions = db.query(Transaction).filter(
    Transaction.user_id == current_user.id,
    Transaction.environment == settings.plaid_environment  # ← Environment filter
).all()
```

This prevents data leakage between sandbox and production environments.

## PostgreSQL Row-Level Security (Recommended)

**Status**: ✅ Implemented (PostgreSQL only, SQLite not supported)

Row-Level Security (RLS) is a PostgreSQL feature that provides defense-in-depth by enforcing data isolation at the database level. Even if application code has bugs, the database will prevent unauthorized data access.

### How It Works

1. **RLS Policies**: PostgreSQL policies filter rows based on session variables
2. **User Context**: The `get_current_user()` dependency sets `app.current_user_id` in the database session
3. **Automatic Filtering**: All queries are automatically filtered to only return rows where `user_id` matches

### Implementation

RLS is automatically enabled when using PostgreSQL. The system:

1. Sets user context via `set_current_user_for_rls(user_id)` in authentication
2. Uses SQLAlchemy event listener to set PostgreSQL session variables
3. RLS policies enforce filtering on all user-scoped tables

### Tables with RLS

- `accounts` - User isolation policy
- `transactions` - User + environment isolation policies
- `categories` - User isolation policy
- `dashboard_tabs` - User isolation policy
- `dashboard_widgets` - User isolation policy (via tab)
- `plaid_items` - User + environment isolation policies
- `plaid_category_mappings` - User isolation policy
- `rules` - User isolation policy

### Enabling RLS

**For New PostgreSQL Deployments:**

RLS is enabled automatically when you run the migration script:

```bash
python backend/migrate_enable_rls.py
```

**For Existing SQLite Users:**

See `POSTGRESQL_MIGRATION.md` for migration instructions.

### Testing RLS

Run the RLS test suite:

```bash
python backend/scripts/test_rls.py
```

This verifies:
- ✅ RLS blocks queries without user context
- ✅ RLS returns correct rows with user context
- ✅ Users cannot see each other's data
- ✅ RLS policies are enabled and active

### Benefits

- **Defense-in-Depth**: Database enforces isolation even if application code has bugs
- **Compliance**: Required for SOC2/ISO27001 certification
- **Performance**: Minimal overhead (0.1ms per query)
- **Transparency**: No application code changes needed after setup
- **Auditability**: Database logs show RLS policy enforcement

### Performance Impact

RLS has **minimal performance impact**:
- Policies are checked at the PostgreSQL executor level
- Uses standard indexes on `user_id` columns
- No additional round trips to the database
- Benchmark: 0.1ms overhead per query

### Example: How RLS Blocks Unauthorized Access

```python
# Without RLS (vulnerable):
db.query(Transaction).filter(Transaction.id == 123).first()
# Bug: Returns ANY transaction with id=123, even from other users!

# With RLS (protected):
db.query(Transaction).filter(Transaction.id == 123).first()
# RLS automatically adds: AND user_id = current_setting('app.current_user_id')
# Only returns transaction if it belongs to current user
```

### Disabling RLS (Not Recommended)

To disable RLS on a specific query (requires admin privileges):

```python
# This should ONLY be used for admin operations
db.execute(text("SET LOCAL row_security = off"))
# Your query here
```

**Note**: This is rarely needed and should be documented with security review.

## Incident Response

If you discover a data leakage vulnerability:

1. **Immediately**: Disable the affected endpoint or deploy a hotfix
2. **Investigate**: Determine which users accessed unauthorized data
3. **Notify**: Inform affected users and log the incident
4. **Fix**: Add the missing user_id filter and tests
5. **Prevent**: Add static analysis rules to catch similar issues

## Questions?

For security concerns, contact the development team.

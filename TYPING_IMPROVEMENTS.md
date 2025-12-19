# Type Safety Improvements to Prevent ID Confusion Bugs

## The Problem

We had a bug where `Account.plaid_item_id` (a Plaid string ID) was never being set, causing the disconnect impact query to return 0 accounts. The type system didn't catch this because both IDs are just `int` and `str`.

## Proposed Solutions

### 1. NewType for ID Disambiguation (Implemented)

We've created `app/core/types.py` with branded types:

```python
from typing import NewType

# Database primary keys
PlaidItemDbId = NewType("PlaidItemDbId", int)  # PlaidItem.id

# External API identifiers
PlaidItemId = NewType("PlaidItemId", str)  # PlaidItem.item_id
```

### 2. How to Use These Types

**Before (error-prone):**
```python
def get_disconnect_impact(item_id: int, db: Session):
    plaid_item = db.query(PlaidItem).filter(PlaidItem.id == item_id).first()

    # BUG: Using item_id (int) where we need plaid_item.item_id (str)
    accounts = db.query(Account).filter(
        Account.plaid_item_id == plaid_item.id  # WRONG!
    ).all()
```

**After (type-safe):**
```python
from app.core.types import PlaidItemDbId, PlaidItemId

def get_disconnect_impact(item_db_id: PlaidItemDbId, db: Session):
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.id == item_db_id
    ).first()

    # Type error if we try to use the wrong ID type
    accounts = db.query(Account).filter(
        Account.plaid_item_id == plaid_item.item_id  # Correct!
    ).all()
```

With mypy strict mode, this would catch the error:
```
error: Argument of type "PlaidItemDbId" cannot be assigned to parameter
"plaid_item_id" of type "PlaidItemId"
```

### 3. Pydantic Models with Validators

For API schemas, use Pydantic with custom validators:

```python
from pydantic import BaseModel, validator
from app.core.types import PlaidItemId

class AccountCreate(BaseModel):
    plaid_item_id: PlaidItemId

    @validator('plaid_item_id')
    def validate_plaid_item_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('plaid_item_id must be a non-empty string')
        if not v.startswith('item_'):
            raise ValueError('plaid_item_id must start with "item_"')
        return PlaidItemId(v)
```

### 4. SQLAlchemy Model Type Hints

Add type hints to SQLAlchemy models (Python 3.10+):

```python
from app.core.types import PlaidItemId, PlaidItemDbId

class PlaidItem(Base):
    __tablename__ = "plaid_items"

    id: Mapped[PlaidItemDbId] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[PlaidItemId] = mapped_column(String, unique=True)

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plaid_item_id: Mapped[PlaidItemId | None] = mapped_column(String, nullable=True)
```

### 5. Runtime Validation

Add runtime assertions in development:

```python
def set_plaid_item_id(account: Account, item_id: PlaidItemId) -> None:
    """Set plaid_item_id with runtime validation."""
    assert isinstance(item_id, str), f"Expected str, got {type(item_id)}"
    assert item_id.startswith('item_'), f"Invalid Plaid item_id: {item_id}"
    account.plaid_item_id = item_id
```

### 6. Enable mypy Strict Mode

Add to `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
```

## Migration Path

1. ✅ Create `app/core/types.py` with NewType definitions
2. Update PlaidService to use typed IDs
3. Update API endpoints to use typed IDs
4. Add type hints to SQLAlchemy models
5. Enable mypy in CI with `--strict` mode
6. Add pre-commit hook for mypy

## Benefits

- **Compile-time safety**: mypy catches ID type mismatches
- **Self-documenting**: Code is clearer about which ID type is needed
- **Refactoring safety**: Changing ID types becomes safer
- **Runtime validation**: Pydantic ensures data integrity at API boundaries

## Limitations

- NewTypes are erased at runtime (no runtime overhead, but no runtime checking)
- Requires discipline to use the types consistently
- May need explicit casts when interfacing with third-party libraries
- Retrofitting existing code takes time

## Alternative: Rust-style Type System

For even stronger guarantees, consider:
- Using a language with a stronger type system (Rust, TypeScript)
- Code generation from database schema to ensure type alignment
- Protocol buffers or GraphQL for API type safety

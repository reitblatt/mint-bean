# Deletion Framework Usage Guide

The deletion framework provides a comprehensive system for managing data lifecycle with impact analysis and user warnings.

## Backend Components

### 1. Deletion Policy Registry

Located in `backend/app/models/deletion_policy.py`:

```python
from app.models.deletion_policy import DELETION_REGISTRY, DeletionPolicy

# Each entity has a deletion policy
DELETION_REGISTRY = {
    "User": DeletionMetadata(
        policy=DeletionPolicy.MANUAL,
        cascade_to=["PlaidItem", "Account", "Transaction", "Category", "Rule"],
    ),
    "Account": DeletionMetadata(
        policy=DeletionPolicy.CASCADE,
        cascade_from=["User"],
        cascade_to=["Transaction"],
    ),
    # ... etc
}
```

### 2. Deletion Impact Analysis API

**Endpoint:** `GET /api/v1/deletion/impact/{entity_type}/{entity_id}`

**Example Request:**
```bash
GET /api/v1/deletion/impact/Account/123
Authorization: Bearer <token>
```

**Example Response:**
```json
{
  "entity_type": "Account",
  "entity_id": 123,
  "cascades": {
    "Transaction": 145
  },
  "total_affected": 146,
  "warnings": [
    "Deleting account 'Chase Checking' will permanently delete 145 transactions"
  ]
}
```

### 3. Deletion Services

**Soft Delete (Audit Trail):**
```python
from app.services.soft_delete_service import soft_delete_category, restore_category

# Soft delete - sets is_active=False, keeps data
soft_delete_category(db, category_id=123, user_id=1)

# Restore
restore_category(db, category_id=123, user_id=1)
```

**Hard Delete (Permanent):**
```python
from app.services.soft_delete_service import hard_delete_with_cascades

# Permanently delete with cascades
deleted_counts = hard_delete_with_cascades(
    db,
    entity_type="Account",
    entity_id=123,
    user_id=1
)
# Returns: {"Account": 1, "Transaction": 145}
```

## Frontend Integration

### Using the Deletion Confirmation Modal

The `DeletionConfirmationModal` component automatically fetches and displays deletion impact.

**Example Integration:**

```tsx
import { useState } from 'react'
import { DeletionConfirmationModal } from '../components/DeletionConfirmationModal'
import { api } from '../api/api'

function MyPage() {
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [entityToDelete, setEntityToDelete] = useState<{
    type: string
    id: number
    name: string
  } | null>(null)

  const handleDeleteClick = (entityType: string, id: number, name: string) => {
    setEntityToDelete({ type: entityType, id, name })
    setShowDeleteModal(true)
  }

  const handleConfirmDelete = async () => {
    if (!entityToDelete) return

    try {
      // Perform the actual deletion
      await api.delete(`/${entityToDelete.type.toLowerCase()}s/${entityToDelete.id}`)

      // Refresh your data
      fetchData()

      // Close modal
      setShowDeleteModal(false)
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  return (
    <div>
      {/* Your page content */}
      <button onClick={() => handleDeleteClick('Account', 123, 'Chase Checking')}>
        Delete Account
      </button>

      {/* Deletion Modal */}
      {entityToDelete && (
        <DeletionConfirmationModal
          isOpen={showDeleteModal}
          entityType={entityToDelete.type}
          entityId={entityToDelete.id}
          entityName={entityToDelete.name}
          onConfirm={handleConfirmDelete}
          onCancel={() => setShowDeleteModal(false)}
        />
      )}
    </div>
  )
}
```

## Deletion Policies by Entity

| Entity | Policy | Cascades To | Notes |
|--------|--------|-------------|-------|
| User | Manual | PlaidItem, Account, Transaction, Category, Rule | Full cascade deletion |
| Account | Cascade | Transaction | Deletes all transactions |
| Transaction | Cascade | - | No cascades |
| Category | Cascade | - | Unlinks transactions (doesn't delete them) |
| PlaidItem | Cascade | - | Accounts remain but stop syncing |
| Rule | Cascade | - | Transactions keep their categorization |

## Impact Analysis Examples

### Deleting an Account with Transactions
```json
{
  "entity_type": "Account",
  "entity_id": 123,
  "cascades": {
    "Transaction": 145
  },
  "total_affected": 146,
  "warnings": [
    "Deleting account 'Chase Checking' will permanently delete 145 transactions",
    "3 rule(s) reference this account and may need to be updated"
  ]
}
```

### Deleting a Category
```json
{
  "entity_type": "Category",
  "entity_id": 456,
  "cascades": {},
  "total_affected": 1,
  "warnings": [
    "87 transaction(s) use this category and will become uncategorized",
    "2 rule(s) reference this category and may need to be updated",
    "1 child category will become a top-level category"
  ]
}
```

### Deleting a User
```json
{
  "entity_type": "User",
  "entity_id": 1,
  "cascades": {
    "PlaidItem": 2,
    "Account": 5,
    "Transaction": 1247,
    "Category": 32,
    "Rule": 8,
    "PlaidCategoryMapping": 15
  },
  "total_affected": 1310,
  "warnings": [
    "Deleting this user will permanently delete 1247 transactions"
  ]
}
```

## Best Practices

1. **Always show deletion impact** before confirming destructive operations
2. **Use soft delete** for user-facing entities where possible (User, Category)
3. **Log hard deletes** for audit trail
4. **Test cascade behavior** thoroughly when adding new relationships
5. **Update DELETION_REGISTRY** when adding new models or relationships

## Testing

Tests are located in `backend/tests/test_deletion_service.py`:

```bash
# Run deletion framework tests
pytest tests/test_deletion_service.py -v

# Run all tests
pytest tests/ -v
```

All 17 deletion framework tests pass:
- Deletion impact computation (7 tests)
- Soft delete operations (5 tests)
- Hard delete operations (5 tests)

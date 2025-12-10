# API Specification

Complete API documentation for MintBean v1.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

Currently, the API does not require authentication. This will be added in a future version.

## Common Patterns

### Pagination

List endpoints support pagination via query parameters:

```
GET /transactions?page=1&page_size=50
```

Response format:
```json
{
  "transactions": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

### Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Status codes:
- `400` - Bad Request (validation error)
- `404` - Not Found
- `422` - Unprocessable Entity (Pydantic validation)
- `500` - Internal Server Error

### Date Formats

All dates use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`

Example: `2024-01-15T14:30:00`

## Endpoints

### Health Check

#### `GET /health`

Check API health status.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Transactions

### List Transactions

#### `GET /api/v1/transactions/`

List all transactions with optional filtering and pagination.

**Query Parameters**:
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 50): Items per page (max: 200)
- `account_id` (integer, optional): Filter by account
- `category_id` (integer, optional): Filter by category
- `start_date` (string, optional): Filter by start date (ISO format)
- `end_date` (string, optional): Filter by end date (ISO format)
- `search` (string, optional): Search in description and payee

**Response**: `200 OK`
```json
{
  "transactions": [
    {
      "id": 1,
      "transaction_id": "txn_abc123",
      "account_id": 1,
      "category_id": 5,
      "date": "2024-01-15T00:00:00",
      "amount": -42.50,
      "description": "Grocery Store",
      "payee": "Whole Foods",
      "narration": "Weekly groceries",
      "currency": "USD",
      "pending": false,
      "reviewed": true,
      "beancount_account": "Expenses:Food:Groceries",
      "plaid_transaction_id": "plaid_xyz789",
      "synced_to_beancount": true,
      "created_at": "2024-01-16T10:00:00",
      "updated_at": "2024-01-16T10:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

### Get Transaction

#### `GET /api/v1/transactions/{transaction_id}`

Get a specific transaction by ID.

**Path Parameters**:
- `transaction_id` (integer): Transaction ID

**Response**: `200 OK`
```json
{
  "id": 1,
  "transaction_id": "txn_abc123",
  "account_id": 1,
  "category_id": 5,
  "date": "2024-01-15T00:00:00",
  "amount": -42.50,
  "description": "Grocery Store",
  "payee": "Whole Foods",
  "narration": "Weekly groceries",
  "currency": "USD",
  "pending": false,
  "reviewed": true,
  "beancount_account": "Expenses:Food:Groceries",
  "plaid_transaction_id": "plaid_xyz789",
  "synced_to_beancount": true,
  "created_at": "2024-01-16T10:00:00",
  "updated_at": "2024-01-16T10:00:00"
}
```

**Error Response**: `404 Not Found`

### Create Transaction

#### `POST /api/v1/transactions/`

Create a new transaction.

**Request Body**:
```json
{
  "account_id": 1,
  "category_id": 5,
  "date": "2024-01-15T00:00:00",
  "amount": -42.50,
  "description": "Grocery Store",
  "payee": "Whole Foods",
  "narration": "Weekly groceries",
  "currency": "USD",
  "pending": false,
  "reviewed": false
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "transaction_id": "txn_abc123",
  ...
}
```

### Update Transaction

#### `PATCH /api/v1/transactions/{transaction_id}`

Update a transaction. Only provided fields are updated.

**Path Parameters**:
- `transaction_id` (integer): Transaction ID

**Request Body** (all fields optional):
```json
{
  "category_id": 6,
  "payee": "Updated Payee",
  "reviewed": true
}
```

**Response**: `200 OK`
```json
{
  "id": 1,
  "transaction_id": "txn_abc123",
  ...
}
```

### Delete Transaction

#### `DELETE /api/v1/transactions/{transaction_id}`

Delete a transaction.

**Path Parameters**:
- `transaction_id` (integer): Transaction ID

**Response**: `204 No Content`

---

## Accounts

### List Accounts

#### `GET /api/v1/accounts/`

List all accounts.

**Query Parameters**:
- `active_only` (boolean, default: true): Only return active accounts

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "account_id": "acc_xyz123",
    "name": "Checking Account",
    "official_name": "Chase Total Checking",
    "type": "checking",
    "subtype": "checking",
    "beancount_account": "Assets:Bank:Chase:Checking",
    "plaid_account_id": "plaid_abc789",
    "institution_name": "Chase",
    "current_balance": 1500.00,
    "available_balance": 1450.00,
    "currency": "USD",
    "active": true,
    "needs_reconnection": false,
    "last_synced_at": "2024-01-16T10:00:00",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-16T10:00:00"
  }
]
```

### Get Account

#### `GET /api/v1/accounts/{account_id}`

Get a specific account by ID.

**Response**: `200 OK` (same structure as list item)

### Create Account

#### `POST /api/v1/accounts/`

Create a new account.

**Request Body**:
```json
{
  "name": "Checking Account",
  "official_name": "Chase Total Checking",
  "type": "checking",
  "subtype": "checking",
  "beancount_account": "Assets:Bank:Chase:Checking",
  "plaid_account_id": "plaid_abc789",
  "institution_name": "Chase",
  "currency": "USD"
}
```

**Response**: `201 Created`

### Update Account

#### `PATCH /api/v1/accounts/{account_id}`

Update an account.

**Request Body** (all fields optional):
```json
{
  "current_balance": 1600.00,
  "needs_reconnection": true
}
```

**Response**: `200 OK`

### Delete Account

#### `DELETE /api/v1/accounts/{account_id}`

Delete an account and all its transactions.

**Response**: `204 No Content`

---

## Categories

### List Categories

#### `GET /api/v1/categories/`

List all categories.

**Query Parameters**:
- `category_type` (string, optional): Filter by type (`expense`, `income`, `transfer`)

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "groceries",
    "display_name": "Groceries",
    "beancount_account": "Expenses:Food:Groceries",
    "category_type": "expense",
    "parent_category": "food",
    "icon": "shopping-cart",
    "color": "#4CAF50",
    "description": "Grocery shopping",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### Get Category

#### `GET /api/v1/categories/{category_id}`

Get a specific category by ID.

**Response**: `200 OK`

### Create Category

#### `POST /api/v1/categories/`

Create a new category.

**Request Body**:
```json
{
  "name": "groceries",
  "display_name": "Groceries",
  "beancount_account": "Expenses:Food:Groceries",
  "category_type": "expense",
  "parent_category": "food",
  "icon": "shopping-cart",
  "color": "#4CAF50",
  "description": "Grocery shopping"
}
```

**Response**: `201 Created`

### Update Category

#### `PATCH /api/v1/categories/{category_id}`

Update a category.

**Response**: `200 OK`

### Delete Category

#### `DELETE /api/v1/categories/{category_id}`

Delete a category.

**Response**: `204 No Content`

---

## Rules

### List Rules

#### `GET /api/v1/rules/`

List all rules, ordered by priority.

**Query Parameters**:
- `active_only` (boolean, default: true): Only return active rules

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Amazon Purchases",
    "description": "Categorize Amazon purchases",
    "conditions": {
      "field": "description",
      "operator": "contains",
      "value": "amazon"
    },
    "actions": {
      "set_category": "shopping_online",
      "set_payee": "Amazon"
    },
    "category_id": 5,
    "priority": 10,
    "active": true,
    "match_count": 42,
    "last_matched_at": "2024-01-15T14:30:00",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-15T14:30:00"
  }
]
```

### Get Rule

#### `GET /api/v1/rules/{rule_id}`

Get a specific rule by ID.

**Response**: `200 OK`

### Create Rule

#### `POST /api/v1/rules/`

Create a new rule.

**Request Body**:
```json
{
  "name": "Amazon Purchases",
  "description": "Categorize Amazon purchases",
  "conditions": {
    "field": "description",
    "operator": "contains",
    "value": "amazon"
  },
  "actions": {
    "set_category": "shopping_online",
    "set_payee": "Amazon"
  },
  "category_id": 5,
  "priority": 10,
  "active": true
}
```

**Response**: `201 Created`

### Update Rule

#### `PATCH /api/v1/rules/{rule_id}`

Update a rule.

**Response**: `200 OK`

### Delete Rule

#### `DELETE /api/v1/rules/{rule_id}`

Delete a rule.

**Response**: `204 No Content`

---

## Rule Conditions

Rules support flexible condition matching:

### Operators

- `equals`: Exact match
- `contains`: Substring match (case-insensitive)
- `regex`: Regular expression match
- `greater_than`: Numeric comparison
- `less_than`: Numeric comparison

### Fields

- `description`: Transaction description
- `payee`: Payee name
- `amount`: Transaction amount
- `account`: Account name

### Example Conditions

**Simple match**:
```json
{
  "field": "description",
  "operator": "contains",
  "value": "starbucks"
}
```

**Regex match**:
```json
{
  "field": "description",
  "operator": "regex",
  "value": "^(amazon|amzn)"
}
```

**Amount threshold**:
```json
{
  "field": "amount",
  "operator": "greater_than",
  "value": 100
}
```

**Multiple conditions** (future):
```json
{
  "operator": "AND",
  "conditions": [
    {
      "field": "description",
      "operator": "contains",
      "value": "restaurant"
    },
    {
      "field": "amount",
      "operator": "less_than",
      "value": 50
    }
  ]
}
```

## Rule Actions

Rules can perform multiple actions:

### Available Actions

- `set_category`: Set the category (by name)
- `set_payee`: Set the payee name
- `set_tags`: Add tags (array of strings)
- `set_account`: Set beancount account

### Example Actions

**Simple categorization**:
```json
{
  "set_category": "shopping_online"
}
```

**Multiple actions**:
```json
{
  "set_category": "dining_out",
  "set_payee": "Chipotle",
  "set_tags": ["lunch", "fast-food"]
}
```

---

## Data Types

### Transaction

```typescript
{
  id: number
  transaction_id: string
  account_id: number
  category_id?: number
  date: string  // ISO 8601
  amount: number  // Negative for expenses
  description: string
  payee?: string
  narration?: string
  currency: string
  pending: boolean
  reviewed: boolean
  beancount_account?: string
  plaid_transaction_id?: string
  synced_to_beancount: boolean
  created_at: string
  updated_at: string
}
```

### Account

```typescript
{
  id: number
  account_id: string
  name: string
  official_name?: string
  type: string  // checking, savings, credit, investment
  subtype?: string
  beancount_account: string
  plaid_account_id?: string
  institution_name?: string
  current_balance?: number
  available_balance?: number
  currency: string
  active: boolean
  needs_reconnection: boolean
  last_synced_at?: string
  created_at: string
  updated_at: string
}
```

### Category

```typescript
{
  id: number
  name: string
  display_name: string
  beancount_account: string
  category_type: string  // expense, income, transfer
  parent_category?: string
  icon?: string
  color?: string
  description?: string
  created_at: string
  updated_at: string
}
```

### Rule

```typescript
{
  id: number
  name: string
  description?: string
  conditions: object
  actions: object
  category_id?: number
  priority: number
  active: boolean
  match_count: number
  last_matched_at?: string
  created_at: string
  updated_at: string
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. This will be added in production.

## Versioning

API version is included in the URL: `/api/v1/`

Breaking changes will result in a new version: `/api/v2/`

## Interactive Documentation

Access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

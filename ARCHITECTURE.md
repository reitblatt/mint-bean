# Architecture

This document describes the system design and architecture of MintBean.

## Overview

MintBean follows a clean architecture with clear separation between layers:

```
┌─────────────────────────────────────────────┐
│           Frontend (React/TS)               │
│  ┌────────────────────────────────────┐    │
│  │  Components → API Client → Pages   │    │
│  └────────────────────────────────────┘    │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────┐
│           Backend (FastAPI)                 │
│  ┌────────────────────────────────────┐    │
│  │  API → Services → Models → DB      │    │
│  └────────────────────────────────────┘    │
└─────────────────┬───────────────┬───────────┘
                  │               │
        ┌─────────▼─────┐  ┌─────▼──────────┐
        │ SQLite Cache  │  │  Beancount     │
        │  (Fast Read)  │  │  Files (SoT)   │
        └───────────────┘  └────────────────┘
```

## Core Principles

### 1. Beancount as Source of Truth

- Beancount files are the single source of truth for all financial data
- SQLite database acts as a read cache for fast queries
- All modifications must sync back to beancount files
- The system can be rebuilt from beancount files at any time

### 2. API-First Design

- Clear REST API between frontend and backend
- All business logic in the backend
- Frontend is a stateless UI layer
- APIs are versioned (`/api/v1/`)

### 3. Service Layer Pattern

Business logic is isolated in service modules:
- `beancount_service.py`: Read/write beancount files
- `plaid_service.py`: Integrate with Plaid API
- `rule_engine.py`: Apply categorization rules

### 4. Type Safety

- Python: Type hints everywhere, validated by MyPy
- TypeScript: Strict mode, shared types for API models
- Pydantic: Runtime validation for API requests/responses

## Data Flow

### Transaction Sync Flow

```
Plaid API
   │
   ▼
PlaidService.sync_transactions()
   │
   ▼
Transaction Models (SQLAlchemy)
   │
   ▼
SQLite Database
   │
   ▼
RuleEngine.apply_rules()
   │
   ▼
BeancountService.write_transaction()
   │
   ▼
Beancount Files (Git)
```

### User Categorization Flow

```
User Action (Frontend)
   │
   ▼
PATCH /api/v1/transactions/{id}
   │
   ▼
Update SQLite Database
   │
   ▼
BeancountService.update_transaction()
   │
   ▼
Beancount Files (Git)
   │
   ▼
Optional: Git Commit
```

## Backend Architecture

### Directory Structure

```
backend/app/
├── api/                    # API endpoints
│   └── v1/
│       ├── transactions.py  # Transaction endpoints
│       ├── accounts.py      # Account endpoints
│       ├── categories.py    # Category endpoints
│       └── rules.py         # Rule endpoints
│
├── core/                   # Core configuration
│   ├── config.py           # Settings management
│   ├── database.py         # DB session management
│   └── logging.py          # Logging setup
│
├── models/                 # SQLAlchemy ORM models
│   ├── transaction.py      # Transaction model
│   ├── account.py          # Account model
│   ├── category.py         # Category model
│   └── rule.py             # Rule model
│
├── schemas/                # Pydantic validation schemas
│   ├── transaction.py      # Transaction schemas
│   ├── account.py          # Account schemas
│   ├── category.py         # Category schemas
│   └── rule.py             # Rule schemas
│
├── services/               # Business logic
│   ├── beancount_service.py # Beancount I/O
│   ├── plaid_service.py     # Plaid integration
│   └── rule_engine.py       # Rule matching
│
└── main.py                 # FastAPI app entry
```

### Database Schema

**transactions**
- Primary cache for transaction data
- Maps 1:1 with Plaid transactions
- Tracks sync state with beancount
- Full-text search on description/payee

**accounts**
- Financial accounts (checking, savings, credit)
- Linked to Plaid items
- Maps to beancount account names

**categories**
- Expense/income categories
- Hierarchical structure
- Maps to beancount account names

**rules**
- Pattern-based categorization rules
- JSON storage for conditions/actions
- Priority ordering

### API Design

RESTful conventions:
- `GET /api/v1/transactions/` - List with filters
- `GET /api/v1/transactions/{id}` - Get specific
- `POST /api/v1/transactions/` - Create new
- `PATCH /api/v1/transactions/{id}` - Update
- `DELETE /api/v1/transactions/{id}` - Delete

Pagination:
- Query params: `page`, `page_size`
- Response includes: `total`, `total_pages`

Filtering:
- Query params for common filters
- Example: `?account_id=1&start_date=2024-01-01`

Error responses:
```json
{
  "detail": "Error message",
  "status_code": 404
}
```

## Frontend Architecture

### Directory Structure

```
frontend/src/
├── api/                    # API client layer
│   ├── client.ts           # Axios setup
│   ├── types.ts            # Shared TypeScript types
│   ├── transactions.ts     # Transaction API
│   ├── accounts.ts         # Account API
│   ├── categories.ts       # Category API
│   └── rules.ts            # Rule API
│
├── components/             # Reusable components
│   ├── Layout.tsx          # Main layout with nav
│   └── TransactionList.tsx # Transaction table
│
├── pages/                  # Route pages
│   ├── Dashboard.tsx       # Overview page
│   ├── Transactions.tsx    # Transaction list
│   ├── Accounts.tsx        # Account management
│   ├── Categories.tsx      # Category management
│   ├── Rules.tsx           # Rule management
│   └── Settings.tsx        # App settings
│
├── App.tsx                 # Route definitions
├── main.tsx                # React entry point
└── index.css               # Global styles
```

### State Management

- **React Query**: Server state (API data)
  - Automatic caching and refetching
  - Loading/error states
  - Optimistic updates

- **URL State**: Filters and pagination
  - Shareable URLs
  - Browser back/forward support

- **Component State**: UI state (modals, forms)

### Component Patterns

**Pages**: Route-level components
- Handle data fetching with React Query
- Pass data to presentational components
- Manage page-level state

**Components**: Reusable UI
- Pure/presentational when possible
- Receive data via props
- Emit events via callbacks

### Styling Strategy

- **Tailwind CSS**: Utility-first styling
- **Component classes**: Reusable patterns in `index.css`
- **Responsive**: Mobile-first breakpoints
- **Theme**: CSS variables for colors

## Integration Points

### Beancount Integration

The `BeancountService` abstracts all beancount operations:

1. **Reading**: Parse beancount files using `beancount.loader`
2. **Writing**: Generate valid beancount syntax
3. **Validation**: Check for errors before writing
4. **Git**: Optional commit after changes

Challenges:
- Preserving comments and formatting
- Handling includes and imports
- Transaction deduplication
- Account name validation

### Plaid Integration

The `PlaidService` handles all Plaid API calls:

1. **Link**: Create link tokens for frontend
2. **Exchange**: Convert public token to access token
3. **Sync**: Fetch transactions incrementally
4. **Refresh**: Update account balances

Best practices:
- Store access tokens securely (encrypted)
- Handle webhook notifications
- Graceful error handling for expired items
- Rate limiting and retries

### Rule Engine

The `RuleEngine` applies categorization rules:

1. **Matching**: Check if transaction matches conditions
2. **Priority**: Apply highest priority rule first
3. **Actions**: Set category, payee, tags
4. **Statistics**: Track rule match counts

Rule conditions support:
- Field matching (description, payee, amount, account)
- Operators (equals, contains, regex, gt, lt)
- Logical operators (AND, OR)

## Security Considerations

### Authentication (Future)

- OAuth2 with JWT tokens
- Secure token storage
- CORS configuration
- CSRF protection

### Data Protection

- Plaid access tokens encrypted at rest
- Database file permissions
- Environment variable secrets
- HTTPS in production

### Input Validation

- Pydantic schemas validate all inputs
- SQL injection prevention via ORM
- XSS prevention in React
- File path validation

## Performance Considerations

### Backend

- SQLite for fast local queries
- Database indexes on common filters
- Lazy loading of relationships
- Response pagination

### Frontend

- Code splitting by route
- React Query caching
- Debounced search inputs
- Virtual scrolling for large lists

### Caching Strategy

- React Query: 5-minute stale time
- SQLite: Read cache, not authoritative
- Beancount: Read on sync, write on change

## Deployment

### Development

- Docker Compose for local development
- Hot reload for both frontend and backend
- Shared volumes for live code updates

### Production (Future)

- Docker containers
- Reverse proxy (nginx)
- SSL/TLS termination
- Persistent volume for SQLite
- Read-only mount for beancount files

## Testing Strategy

### Backend Tests

- `pytest` for unit and integration tests
- FastAPI `TestClient` for API tests
- Mock external services (Plaid)
- Test database fixtures

### Frontend Tests

- Vitest for unit tests (future)
- React Testing Library (future)
- E2E tests with Playwright (future)

### Test Coverage Goals

- Backend: >80% coverage
- Frontend: >70% coverage
- Critical paths: 100% coverage

## Future Enhancements

### Architecture Evolution

1. **Multi-user support**: Add authentication and user isolation
2. **PostgreSQL**: Replace SQLite for production
3. **Background jobs**: Celery for async tasks
4. **WebSockets**: Real-time sync updates
5. **Microservices**: Split beancount/plaid services

### Scalability

- Horizontal scaling with load balancer
- Database connection pooling
- Redis for session/cache
- CDN for frontend assets

## Design Decisions

### Why SQLite?

- Fast local development
- No server setup required
- Good enough for single-user
- Easy to backup/restore
- Can migrate to PostgreSQL later

### Why FastAPI?

- Modern Python async framework
- Automatic API documentation
- Type safety with Pydantic
- Excellent performance
- Great developer experience

### Why React Query?

- Simplifies data fetching
- Built-in caching strategy
- Optimistic updates
- Handles loading/error states
- Reduces boilerplate

### Why Not Redux?

- React Query handles server state
- Local state is simple enough
- Reduces complexity
- Easier to learn
- Can add later if needed

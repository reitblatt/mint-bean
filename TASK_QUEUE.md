# Task Queue

Prioritized list of tasks for MintBean development.

## Priority 1: Core Functionality (Implement First)

### 1.0 Recent Improvements & New Tasks

#### Code Quality & Linting
- [ ] Address ruff linting warnings (101 remaining)
  - [ ] Update type annotations to use Python 3.10+ syntax (`X | Y` instead of `Optional[X]`)
  - [ ] Add proper exception chaining (`raise ... from err`)
  - [ ] Fix comparison operators (`cond` instead of `cond == True`)
  - [ ] Reorganize imports in scripts
  - [ ] Remove unused variables

#### Database Migrations
- [ ] Set up Alembic for database migrations
  - [ ] Initialize Alembic
  - [ ] Create initial migration
  - [ ] Add migration for Account.is_active rename
  - [ ] Document migration process

#### Additional Testing
- [ ] Add BeancountService tests
  - [ ] Unit tests for parsing methods
  - [ ] Unit tests for writing methods
  - [ ] Integration tests with sample beancount files
  - [ ] Error handling tests
- [ ] Add frontend tests
  - [ ] Component tests for PlaidLink
  - [ ] Component tests for TransactionDetailModal
  - [ ] Component tests for TransactionFilters
  - [ ] Integration tests for transaction workflows

#### Documentation
- [ ] Expand PENDING_TRANSACTIONS.md with edge cases
- [ ] Add API documentation with examples
- [ ] Create setup guide for Plaid sandbox
- [ ] Document test data and fixtures

### 1.1 Beancount Integration

- [ ] Implement `BeancountService.parse_transactions()`
  - Parse beancount files using `beancount.loader`
  - Extract transaction details
  - Handle multiple currencies
  - Parse tags and links
  - Handle metadata

- [ ] Implement `BeancountService.parse_accounts()`
  - Parse Open directives
  - Extract account metadata
  - Build account hierarchy

- [ ] Implement `BeancountService.write_transaction()`
  - Generate valid beancount syntax
  - Preserve formatting and comments
  - Handle posting balancing
  - Support tags and links

- [ ] Implement `BeancountService.update_transaction()`
  - Find transaction by ID/metadata
  - Update in place
  - Preserve surrounding content

- [ ] Implement `BeancountService.sync_from_file()`
  - Parse all transactions
  - Compare with database
  - Insert/update transactions
  - Return sync statistics

- [ ] Implement `BeancountService.sync_to_file()`
  - Query unsynced transactions
  - Write to beancount file
  - Mark as synced
  - Handle errors gracefully

- [ ] Add beancount validation
  - Check syntax errors
  - Verify balance assertions
  - Return meaningful errors

- [ ] Add git integration
  - Commit changes automatically
  - Generate commit messages
  - Handle git errors

### 1.2 Plaid Integration ✅ COMPLETED

- [x] Implement `PlaidService.__init__()`
  - Initialize Plaid client
  - Load credentials from settings
  - Handle different environments

- [x] Implement `PlaidService.create_link_token()`
  - Generate link tokens for frontend
  - Configure products
  - Set redirect URIs

- [x] Implement `PlaidService.exchange_public_token()`
  - Exchange public token for access token
  - Store access token securely
  - Create item record

- [x] Implement `PlaidService.get_accounts()`
  - Fetch account details
  - Extract balances
  - Map to internal models

- [x] Implement `PlaidService.sync_transactions()`
  - Use transactions sync endpoint
  - Handle added/modified/removed
  - Update cursor
  - Store in database
  - Handle pending → completed transitions

- [x] Implement `PlaidService.get_institution()`
  - Fetch institution details
  - Cache institution data
  - Extract logo and name

- [x] Add Plaid Link UI component
  - Integrate Plaid Link in frontend
  - Handle success/exit callbacks
  - Store access token

- [x] Add error handling
  - Handle item errors (needs reconnection)
  - Handle rate limits
  - Retry logic

- [x] Add pending transaction handling
  - Track pending transactions with `!` flag
  - Update to completed with `*` flag
  - Prevent duplicates using plaid_transaction_id

### 1.3 Transaction Categorization UI (Partially Completed)

- [x] Create transaction detail modal
  - Display full transaction details
  - Show/edit category
  - Show/edit tags and links
  - Show original Plaid data
  - Quick "mark as reviewed" checkbox

- [x] Add category selector component
  - Dropdown with all categories
  - Search/filter categories
  - Show hierarchy
  - Quick access to recent categories

- [ ] Implement transaction bulk actions
  - Select multiple transactions
  - Bulk categorize
  - Bulk mark as reviewed
  - Bulk delete

- [x] Add transaction filters UI
  - Date range picker with presets
  - Account filter
  - Category filter
  - Amount range
  - Pending/reviewed status
  - Inline collapsible filter panel

- [ ] Add transaction search
  - Full-text search in description/payee
  - Search suggestions
  - Highlight matches

### 1.4 Rule Engine

- [ ] Enhance rule condition matching
  - Support all operators
  - Support all fields
  - Add AND/OR logic
  - Add NOT operator

- [ ] Implement rule testing
  - Test rule against sample transactions
  - Show match/no-match
  - Explain why matched

- [ ] Add rule management UI
  - List all rules
  - Create/edit/delete rules
  - Drag to reorder priority
  - Toggle active/inactive

- [ ] Create rule builder component
  - Visual rule builder
  - Add/remove conditions
  - Add/remove actions
  - Preview rule JSON

- [ ] Add automatic rule suggestions
  - Analyze categorized transactions
  - Suggest new rules
  - Show confidence scores

## Priority 2: Essential Features (Implement Soon)

### 2.1 Dashboard & Analytics

- [ ] Implement spending by category chart
  - Pie chart or bar chart
  - Configurable time period
  - Click to drill down

- [ ] Add spending trends over time
  - Line chart
  - Compare to previous period
  - Show average

- [ ] Create account balance history
  - Track balance over time
  - Show all accounts
  - Projection based on trends

- [ ] Add budget tracking
  - Set monthly budgets by category
  - Progress bars
  - Alerts when approaching limit

- [ ] Implement income vs expenses
  - Monthly comparison
  - Year-to-date totals
  - Visual representation

### 2.2 Account Management

- [ ] Add Plaid account linking flow
  - Integrate Plaid Link
  - Exchange token
  - Create account records
  - Initial sync

- [ ] Implement account reconnection
  - Detect expired items
  - Show reconnection button
  - Update link flow
  - Resume syncing

- [ ] Add account balance updates
  - Fetch latest balances
  - Display prominently
  - Show change from last sync

- [ ] Create account settings
  - Rename accounts
  - Set beancount mapping
  - Hide/show accounts
  - Delete accounts

### 2.3 Category Management

- [ ] Build category list UI
  - Show all categories
  - Group by parent
  - Show transaction count
  - Show total amount

- [ ] Create category CRUD forms
  - Add new category
  - Edit existing
  - Set icon and color
  - Map to beancount account

- [ ] Implement category hierarchy
  - Parent/child relationships
  - Expand/collapse tree
  - Drag to reorganize

- [ ] Add category icon picker
  - Icon library
  - Search icons
  - Custom colors

- [ ] Import categories from beancount
  - Parse expense/income accounts
  - Auto-create categories
  - Preserve hierarchy

### 2.4 Settings & Configuration

- [ ] Create settings UI
  - Beancount file path
  - Repository path
  - Plaid credentials
  - Sync preferences

- [ ] Add sync preferences
  - Auto-sync interval
  - Auto-categorize on sync
  - Git auto-commit
  - Notification settings

- [ ] Implement backup/restore
  - Export database
  - Import database
  - Restore from beancount

- [ ] Add data validation
  - Check beancount file exists
  - Verify git repository
  - Test Plaid credentials

## Priority 3: Polish & UX (Implement Later)

### 3.1 UI Improvements

- [ ] Add loading states
  - Skeleton screens
  - Progress indicators
  - Optimistic updates

- [ ] Improve error handling
  - User-friendly error messages
  - Retry buttons
  - Error boundaries

- [ ] Add keyboard shortcuts
  - Navigate transactions
  - Quick categorize
  - Search
  - Create rules

- [ ] Implement dark mode
  - Toggle in settings
  - Persist preference
  - Update all components

- [ ] Add responsive mobile layout
  - Mobile-friendly navigation
  - Touch-optimized interactions
  - Swipe gestures

### 3.2 Transaction Features

- [ ] Add transaction notes
  - Attach notes to transactions
  - Show in detail view
  - Search in notes

- [ ] Implement transaction splits
  - Split into multiple categories
  - Specify amounts per category
  - Generate multiple postings

- [ ] Add recurring transaction detection
  - Identify patterns
  - Suggest rules
  - Mark as recurring

- [ ] Implement transaction merging
  - Merge duplicates
  - Resolve conflicts
  - Undo merge

### 3.3 Reports & Export

- [ ] Add spending reports
  - Monthly/yearly reports
  - Category breakdown
  - Export to PDF

- [ ] Create tax reports
  - Categorize deductions
  - Generate tax summaries
  - Export for accountant

- [ ] Implement data export
  - Export to CSV
  - Export to QIF
  - Export to OFX

- [ ] Add custom report builder
  - Select fields
  - Add filters
  - Save report templates

### 3.4 Notifications

- [ ] Add sync notifications
  - Notify on successful sync
  - Alert on sync errors
  - Show new transaction count

- [ ] Implement budget alerts
  - Notify when over budget
  - Weekly spending summary
  - Unusual spending alerts

- [ ] Add email notifications
  - Configure email settings
  - Weekly summaries
  - Alert emails

## Priority 4: Advanced Features (Future)

### 4.1 Multi-User Support

- [ ] Implement authentication
  - User registration/login
  - Password hashing
  - JWT tokens

- [ ] Add user isolation
  - Separate data per user
  - User-specific settings
  - Shared household accounts

- [ ] Create user management
  - Admin panel
  - User roles
  - Permissions

### 4.2 Bank Reconciliation

- [ ] Add reconciliation mode
  - Mark transactions as cleared
  - Compare to bank statements
  - Identify discrepancies

- [ ] Implement balance checking
  - Assert balances
  - Flag mismatches
  - Suggest corrections

### 4.3 Investment Tracking

- [ ] Add investment account support
  - Stock transactions
  - Dividends
  - Capital gains

- [ ] Implement portfolio tracking
  - Current holdings
  - Performance metrics
  - Asset allocation

### 4.4 Bill Management

- [ ] Add bill tracking
  - Create bill records
  - Set due dates
  - Link to transactions

- [ ] Implement reminders
  - Upcoming bills
  - Overdue bills
  - Payment confirmations

### 4.5 Mobile App

- [ ] React Native mobile app
  - iOS and Android
  - Camera receipt capture
  - Push notifications
  - Biometric auth

## Technical Debt & Improvements

### Testing ✅ COMPLETED (Backend)

- [x] Write backend unit tests
  - PlaidService unit tests (49 tests total)
  - API endpoint tests with mocking
  - Transaction workflow tests
  - Database tests with in-memory SQLite
  - Pending transaction lifecycle tests

- [x] Set up pre-commit hooks
  - Black code formatting
  - Ruff linting
  - Pytest test execution
  - Automatic code quality checks

- [x] Set up CI/CD
  - GitHub Actions workflow
  - Automated testing on push/PR
  - Code coverage reports (codecov)
  - Python 3.13 support
  - Frontend build tests

- [ ] Add frontend tests
  - Component tests with React Testing Library
  - Integration tests
  - E2E tests with Playwright

- [ ] Add BeancountService tests
  - Unit tests for all methods
  - Integration tests with sample files
  - Error handling tests

### Performance

- [ ] Optimize database queries
  - Add indexes
  - Optimize N+1 queries
  - Query profiling

- [ ] Implement caching
  - Redis for session data
  - Cache API responses
  - Cache computed aggregates

- [ ] Add background jobs
  - Async Plaid sync
  - Scheduled tasks
  - Email sending

### Security

- [ ] Implement authentication
  - OAuth2 flow
  - Secure token storage
  - CSRF protection

- [ ] Add audit logging
  - Log all changes
  - Track user actions
  - Export audit logs

- [ ] Security hardening
  - Rate limiting
  - Input sanitization
  - SQL injection prevention

### Documentation

- [ ] Add API documentation
  - Update endpoint docs
  - Add examples
  - Document error codes

- [ ] Create user documentation
  - Getting started guide
  - Feature tutorials
  - FAQ

- [ ] Write developer docs
  - Setup guide
  - Architecture overview
  - Contributing guide

### Infrastructure

- [ ] Production deployment
  - Docker containers
  - Nginx reverse proxy
  - SSL certificates

- [ ] Database migration
  - Alembic migrations
  - Migration scripts
  - Backup strategy

- [ ] Monitoring & logging
  - Application metrics
  - Error tracking (Sentry)
  - Log aggregation

## Completed Tasks

### Foundation
- [x] Project structure setup
- [x] FastAPI application foundation
- [x] SQLAlchemy models (Account, Transaction, Category, Rule, PlaidItem)
- [x] Pydantic schemas with validation
- [x] Basic CRUD endpoints for all models
- [x] React + TypeScript setup with Vite
- [x] Tailwind CSS configuration
- [x] React Router setup
- [x] API client with React Query
- [x] Layout component with navigation
- [x] Docker setup for development
- [x] Development tooling (black, ruff, eslint, prettier)
- [x] Initial documentation (README, TASK_QUEUE)

### Plaid Integration (Complete)
- [x] PlaidService implementation
  - [x] Link token creation
  - [x] Public token exchange
  - [x] Account fetching and syncing
  - [x] Transaction syncing with cursor-based pagination
  - [x] Institution details fetching
  - [x] Pending transaction handling
- [x] PlaidItem model and database schema
- [x] Plaid API endpoints (all 5 endpoints)
- [x] PlaidLink React component with OAuth flow
- [x] PlaidAccountsManager component
- [x] Integration with Accounts page
- [x] Error handling and reconnection flow
- [x] Comprehensive documentation (PENDING_TRANSACTIONS.md)

### Transaction UI
- [x] Transaction list page with pagination
- [x] Transaction detail modal
  - [x] View/edit mode toggle
  - [x] Category selector
  - [x] Mark as reviewed
  - [x] Show technical details
  - [x] Display pending status with badge
- [x] Transaction filters component
  - [x] Date range presets (Today, Last 7 Days, etc.)
  - [x] Custom date pickers
  - [x] Account and category filters
  - [x] Active filter display
  - [x] Inline collapsible panel
- [x] Transaction API with filtering and pagination
- [x] Beancount flag display (! for pending, * for completed)

### Testing & CI/CD
- [x] Pytest configuration with fixtures
- [x] In-memory SQLite test database
- [x] Mock Plaid API responses
- [x] 49 comprehensive backend tests
  - [x] PlaidService unit tests
  - [x] Plaid API endpoint tests
  - [x] Transaction API tests
  - [x] Transaction model tests
  - [x] E2E Plaid integration tests
  - [x] Pending transaction workflow tests
- [x] Pre-commit hooks (black, ruff, pytest)
- [x] GitHub Actions CI workflow
  - [x] Python 3.13 support
  - [x] Test coverage reporting
  - [x] Linting and type checking
  - [x] Frontend build verification

### Database
- [x] SQLite database setup
- [x] Database migration for Account.is_active field
- [x] Foreign key relationships
- [x] Unique constraints for Plaid IDs
- [x] Pending transaction tracking

---

## How to Use This Queue

1. **Start with Priority 1**: These are the core features needed for the app to be useful
2. **Pick tasks that build on each other**: Some tasks depend on others being completed first
3. **Test as you go**: Write tests for each feature as you implement it
4. **Update this doc**: Check off completed tasks and add new ones as needed
5. **Balance features**: Don't spend too long on any single feature before moving to the next

## Contributing

When working on tasks:
1. Create a feature branch: `feat/task-description`
2. Implement the task with tests
3. Update this doc to check off the task
4. Submit a PR with clear description
5. Reference this task in the commit message

## Task Estimation

- Small tasks: 1-4 hours
- Medium tasks: 4-8 hours
- Large tasks: 1-3 days
- Very large tasks: 3-7 days

Break down large tasks into smaller subtasks when possible.

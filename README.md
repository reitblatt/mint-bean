# MintBean

A modern web application that provides a Mint.com-like UI for managing beancount accounting data.

## Overview

MintBean bridges the gap between the power of [beancount](https://github.com/beancount/beancount) plain-text accounting and the convenience of modern financial management UIs like Mint.com. It provides:

- **Transaction Management**: View, search, and categorize transactions with a beautiful UI
- **Plaid Integration**: Automatically sync transactions from your financial institutions
- **Rule Engine**: Create rules to automatically categorize transactions
- **Beancount Compatibility**: All changes sync back to your beancount files
- **Dashboard**: Visualize spending trends and budgets

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **SQLite**: Fast local database for caching
- **Beancount**: Python library for parsing/writing beancount files
- **Plaid**: Financial data aggregation

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Data fetching and caching
- **React Router**: Client-side routing

## Project Structure

```
mint-bean/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   │   └── v1/
│   │   ├── core/           # Core configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   └── main.tsx       # Entry point
│   ├── package.json       # Node dependencies
│   └── Dockerfile
│
├── docker-compose.yml     # Docker orchestration
├── .env.example          # Environment template
└── README.md             # This file
```

## Getting Started

### Quick Start: AWS Deployment (Recommended for Production)

#### Option A: One-Click Terraform Deployment (Fastest)

Deploy complete infrastructure with a single command:

```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your domain and AWS region
terraform init
terraform apply
```

See [terraform/aws/README.md](./terraform/aws/README.md) for complete instructions.

**Estimated time**: 15-20 minutes
**Monthly cost**: ~$99-108 (optimizable to $50-70)

#### Option B: Manual AWS Setup (Step-by-Step)

For a turn-key production deployment with manual AWS CLI commands:

1. **Follow the AWS deployment guide**: See [DEPLOYMENT_AWS.md](./DEPLOYMENT_AWS.md)
2. **One-time setup**: The guide walks you through creating AWS resources (RDS, ECS, ALB, etc.)
3. **Interactive configuration**: When you first access the application, a setup wizard guides you through:
   - Database connection verification
   - Encryption key generation
   - Admin account creation
   - Plaid credentials configuration

**Estimated time**: 30-45 minutes
**Monthly cost**: ~$67-76 (can be reduced to $22-55 with AWS Lightsail)

### Prerequisites (For Local Development)

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (optional)

### Option 1: Docker Setup (Recommended)

1. **Clone and configure**:
   ```bash
   git clone <your-repo>
   cd mint-bean
   cp .env.example .env
   ```

2. **Edit `.env`** with your configuration:
   ```bash
   # Set your beancount file paths
   BEANCOUNT_FILE_PATH=/path/to/your/main.beancount
   BEANCOUNT_REPO_PATH=/path/to/your/beancount/repo

   # Set your Plaid credentials
   PLAID_CLIENT_ID=your_client_id
   PLAID_SECRET=your_secret
   PLAID_ENV=sandbox
   ```

3. **Update docker-compose.yml** to mount your beancount files:
   ```yaml
   services:
     backend:
       volumes:
         - /path/to/your/beancount:/beancount:ro
   ```

4. **Start the application**:
   ```bash
   docker-compose up -d
   ```

5. **Access the application**:
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/api/docs

### Option 2: Local Development Setup

#### Backend Setup

1. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp ../.env.example ../.env
   # Edit .env with your settings
   ```

4. **Create data directory**:
   ```bash
   mkdir -p data
   ```

5. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run the development server**:
   ```bash
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:5173
   - API: http://localhost:8000

## Development

### Code Style

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

**Backend**:
- Black for formatting
- Ruff for linting
- MyPy for type checking
- Type hints required for all functions

**Frontend**:
- ESLint for linting
- Prettier for formatting
- TypeScript strict mode

### Running Tests

**Backend**:
```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

**Frontend**:
```bash
cd frontend
npm run lint
npm run build  # Type checking
```

### Git Workflow

Use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build/tooling changes

## Configuration

### Environment Variables

See [.env.example](.env.example) for all available configuration options.

Key settings:
- `BEANCOUNT_FILE_PATH`: Path to your main beancount file
- `BEANCOUNT_REPO_PATH`: Path to your beancount git repository
- `PLAID_CLIENT_ID`, `PLAID_SECRET`: Your Plaid API credentials
- `DATABASE_URL`: Database connection string (default: SQLite)

### Beancount Integration

MintBean uses your beancount files as the source of truth. The SQLite database acts as a cache for fast queries. Changes made in the UI are written back to your beancount files.

**Important**: Back up your beancount files before making changes through the UI.

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

See [API_SPEC.md](./API_SPEC.md) for detailed endpoint documentation.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design and architecture decisions.

## Roadmap

See [TASK_QUEUE.md](./TASK_QUEUE.md) for the prioritized list of upcoming features and tasks.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes using conventional commits
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Beancount](https://github.com/beancount/beancount) - Plain text accounting
- [Plaid](https://plaid.com) - Financial data aggregation
- Inspired by [Mint.com](https://mint.com) (RIP)

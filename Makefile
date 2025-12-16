.PHONY: help setup dev dev-backend dev-frontend test lint format clean
.PHONY: docker-dev docker-dev-build docker-dev-down docker-dev-logs docker-dev-restart
.PHONY: docker-prod docker-prod-build docker-prod-down docker-prod-logs docker-prod-restart
.PHONY: docker-clean docker-prune

help:
	@echo "MintBean Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup              - Initial project setup"
	@echo ""
	@echo "Development (Local):"
	@echo "  make dev                - Start both backend and frontend (requires 2 terminals)"
	@echo "  make dev-backend        - Start backend only"
	@echo "  make dev-frontend       - Start frontend only"
	@echo ""
	@echo "Docker Development:"
	@echo "  make docker-dev         - Start development environment with Docker"
	@echo "  make docker-dev-build   - Rebuild and start development environment"
	@echo "  make docker-dev-down    - Stop development environment"
	@echo "  make docker-dev-logs    - View development logs"
	@echo "  make docker-dev-restart - Restart development services"
	@echo ""
	@echo "Docker Production:"
	@echo "  make docker-prod        - Start production environment"
	@echo "  make docker-prod-build  - Build production images"
	@echo "  make docker-prod-down   - Stop production environment"
	@echo "  make docker-prod-logs   - View production logs"
	@echo "  make docker-prod-restart- Restart production services"
	@echo ""
	@echo "Docker Maintenance:"
	@echo "  make docker-clean       - Remove containers and volumes"
	@echo "  make docker-prune       - Clean up all unused Docker resources"
	@echo ""
	@echo "Testing:"
	@echo "  make test               - Run all tests"
	@echo "  make test-backend       - Run backend tests"
	@echo "  make test-docker        - Run tests in Docker"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint               - Run all linters"
	@echo "  make format             - Format all code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean              - Remove generated files"
	@echo "  make clean-db           - Delete database (fresh start)"

setup:
	@echo "Running setup script..."
	@bash scripts/setup.sh

dev-backend:
	@echo "Starting backend..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend..."
	cd frontend && npm run dev

# Docker Development Commands
docker-dev:
	@echo "Starting development environment with Docker..."
	docker compose up -d

docker-dev-build:
	@echo "Building and starting development environment..."
	docker compose up --build -d

docker-dev-down:
	@echo "Stopping development environment..."
	docker compose down

docker-dev-logs:
	@echo "Viewing development logs (Ctrl+C to exit)..."
	docker compose logs -f

docker-dev-restart:
	@echo "Restarting development services..."
	docker compose restart

# Docker Production Commands
docker-prod:
	@echo "Starting production environment..."
	docker compose -f docker-compose.prod.yml up -d

docker-prod-build:
	@echo "Building production images..."
	docker compose -f docker-compose.prod.yml build

docker-prod-down:
	@echo "Stopping production environment..."
	docker compose -f docker-compose.prod.yml down

docker-prod-logs:
	@echo "Viewing production logs (Ctrl+C to exit)..."
	docker compose -f docker-compose.prod.yml logs -f

docker-prod-restart:
	@echo "Restarting production services..."
	docker compose -f docker-compose.prod.yml restart

# Docker Maintenance
docker-clean:
	@echo "Removing containers and volumes..."
	docker compose down -v
	docker compose -f docker-compose.prod.yml down -v

docker-prune:
	@echo "Cleaning up unused Docker resources..."
	docker system prune -f
	docker volume prune -f

# Legacy aliases
docker-up: docker-dev
docker-down: docker-dev-down

test: test-backend
	@echo "All tests complete!"

test-backend:
	@echo "Running backend tests..."
	cd backend && source venv/bin/activate && pytest

test-docker:
	@echo "Running tests in Docker..."
	docker compose exec backend pytest

lint: lint-backend lint-frontend
	@echo "Linting complete!"

lint-backend:
	@echo "Linting backend..."
	cd backend && source venv/bin/activate && ruff check . && mypy app/

lint-frontend:
	@echo "Linting frontend..."
	cd frontend && npm run lint

format: format-backend format-frontend
	@echo "Formatting complete!"

format-backend:
	@echo "Formatting backend..."
	cd backend && source venv/bin/activate && black . && ruff check --fix .

format-frontend:
	@echo "Formatting frontend..."
	cd frontend && npm run format

clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist frontend/node_modules/.vite
	@echo "Cleanup complete!"

clean-db:
	@echo "Deleting database..."
	rm -f data/mintbean.db
	@echo "Database deleted. Run 'make dev-backend' to recreate."

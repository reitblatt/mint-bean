.PHONY: help setup dev dev-backend dev-frontend test lint format clean docker-up docker-down

help:
	@echo "MintBean Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup        - Initial project setup"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start both backend and frontend (requires 2 terminals)"
	@echo "  make dev-backend  - Start backend only"
	@echo "  make dev-frontend - Start frontend only"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start with Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run all linters"
	@echo "  make format       - Format all code"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove generated files"
	@echo "  make clean-db     - Delete database (fresh start)"

setup:
	@echo "Running setup script..."
	@bash scripts/setup.sh

dev-backend:
	@echo "Starting backend..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend..."
	cd frontend && npm run dev

docker-up:
	@echo "Starting with Docker Compose..."
	docker-compose up

docker-down:
	@echo "Stopping Docker Compose..."
	docker-compose down

test: test-backend
	@echo "All tests complete!"

test-backend:
	@echo "Running backend tests..."
	cd backend && source venv/bin/activate && pytest

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

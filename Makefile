# TerpSpark Backend Makefile

.PHONY: help install dev test lint format clean docker-up docker-down migrate init-db

# Default target
help:
	@echo "TerpSpark Backend - Available Commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Run development server"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean temporary files"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make migrate     - Run database migrations"
	@echo "  make init-db     - Initialize database with sample data"

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest -v --cov=app --cov-report=html

# Run linters
lint:
	flake8 app/ --max-line-length=100
	mypy app/

# Format code
format:
	black app/ tests/
	isort app/ tests/

# Clean temporary files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -f test.db

# Start Docker containers
docker-up:
	docker-compose up -d

# Stop Docker containers
docker-down:
	docker-compose down

# Run database migrations
migrate:
	alembic upgrade head

# Create new migration
migration:
	alembic revision --autogenerate -m "$(msg)"

# Initialize database with sample data
init-db:
	python app/utils/init_db.py

# Full setup for new developers
setup: install migrate init-db
	@echo "✅ Setup complete! Run 'make dev' to start the server."

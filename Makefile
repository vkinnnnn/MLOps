.PHONY: help install dev-install test clean docker-build docker-up docker-down docker-logs format lint

help:
	@echo "Student Loan Document Extractor Platform - Available Commands:"
	@echo ""
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make test           - Run test suite"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start all services with Docker Compose"
	@echo "  make docker-down    - Stop all services"
	@echo "  make docker-logs    - View Docker logs"
	@echo "  make format         - Format code with Black"
	@echo "  make lint           - Run linting checks"
	@echo "  make clean          - Remove build artifacts and cache"
	@echo ""

install:
	pip install --upgrade pip
	pip install -r requirements.txt

dev-install:
	pip install --upgrade pip
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

format:
	black .

lint:
	flake8 .
	mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build dist htmlcov .coverage

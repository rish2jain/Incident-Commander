# Incident Commander Development Makefile

.PHONY: help install install-dev test test-unit test-integration lint format type-check security-check clean setup-dev run-local

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install production dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  setup-dev     - Complete development environment setup"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint          - Run linting (ruff)"
	@echo "  format        - Format code (black + isort)"
	@echo "  type-check    - Run type checking (mypy)"
	@echo "  security-check - Run security scanning (bandit)"
	@echo "  quality-check - Run all quality checks"
	@echo "  clean         - Clean build artifacts"
	@echo "  run-local     - Start local development environment"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test,docs]"

setup-dev: install-dev
	pre-commit install
	@echo "Development environment setup complete!"

# Testing targets
test:
	pytest

test-unit:
	pytest -m "unit or not (integration or e2e)" --maxfail=1

test-integration:
	pytest -m integration --maxfail=1

test-e2e:
	pytest -m e2e --maxfail=1

test-agents:
	pytest -m agent --maxfail=1

# Code quality targets
lint:
	ruff check .

format:
	black .
	isort .

type-check:
	mypy src/ agents/

security-check:
	bandit -r . -f json -o bandit-report.json || true
	@echo "Security scan complete. Check bandit-report.json for details."

quality-check: lint type-check security-check
	@echo "All quality checks completed!"

# Development targets
run-local:
	docker-compose up -d
	@echo "Local services started. Run 'uvicorn src.main:app --reload' to start the API server."

run-dashboard:
	python scripts/start_refined_dashboard.py

build-dashboard:
	cd dashboard && ./build.sh

install-dashboard:
	cd dashboard && npm install

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

# Pre-commit hooks
pre-commit-all:
	pre-commit run --all-files

# Docker targets
docker-build:
	docker build -t incident-commander .

docker-run:
	docker run -p 8000:8000 incident-commander

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build
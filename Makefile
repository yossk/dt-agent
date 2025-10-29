.PHONY: help install test clean build run docker-build docker-run docker-test setup-dev

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup-dev: ## Set up development environment with uv
	@echo "Setting up development environment with uv..."
	@which uv > /dev/null || (echo "uv not installed. Install from https://github.com/astral-sh/uv" && exit 1)
	uv venv
	uv pip install -e ".[dev]"
	@echo "Development environment ready!"

install: ## Install dependencies with uv
	@which uv > /dev/null || (echo "uv not installed. Install from https://github.com/astral-sh/uv" && exit 1)
	uv pip install -e .

test: ## Run tests
	pytest tests/ -v

test-example: ## Test with example data files
	python src/main.py example-data/"RE_ quote for server.msg" --config config/config.yaml

docker-build: ## Build Docker image
	docker build -t dt-agent:local .

docker-run: docker-build ## Build and run in Docker container
	docker-compose up -d dt-agent
	docker-compose logs -f dt-agent

docker-test: docker-build ## Test with example data in Docker
	@echo "Testing with example email file..."
	docker-compose run --rm dt-agent example-data/"RE_ quote for server.msg" --config config/config.yaml

docker-shell: docker-build ## Open interactive shell in Docker container
	docker-compose run --rm dt-agent /bin/bash

clean: ## Clean temporary files and caches
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/
	rm -rf data/quotes/* data/logs/* data/incoming/* 2>/dev/null || true

setup-config: ## Copy example config if it doesn't exist
	@if [ ! -f config/config.yaml ]; then \
		cp config/config.yaml.example config/config.yaml; \
		echo "Created config/config.yaml from example"; \
	else \
		echo "config/config.yaml already exists"; \
	fi

init: setup-config setup-dev ## Initialize project (config + dev environment)
	@echo "Project initialized!"


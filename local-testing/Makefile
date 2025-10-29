# Local Testing Makefile
# Wrapper for local testing - runs commands from project root but uses local-testing configs

.PHONY: help setup test test-docker clean

ROOT_DIR := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST)))/..)
CURRENT_DIR := $(shell pwd)

help: ## Show this help message
	@echo 'Local Testing Commands:'
	@echo '  make setup      - Set up local testing environment with uv'
	@echo '  make test       - Run local test with example data'
	@echo '  make test-docker - Run test in Docker'
	@echo '  make clean      - Clean local test data'

setup: ## Set up local testing environment (runs setup.sh)
	@./scripts/setup.sh

test: ## Run local test
	@cd $(ROOT_DIR) && ./local-testing/scripts/test-local.sh

test-docker: ## Run Docker test
	@cd $(ROOT_DIR) && ./local-testing/scripts/test-docker.sh

clean: ## Clean local test data
	@rm -rf data/quotes/* data/logs/* data/incoming/*
	@echo "Local test data cleaned!"


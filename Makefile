# Makefile for fuzzy-logic-search

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_PYTHON) -m pip
PYTEST := $(VENV_BIN)/pytest
BLACK := $(VENV_BIN)/black
RUFF := $(VENV_BIN)/ruff
MYPY := $(VENV_BIN)/mypy
COVERAGE := $(VENV_BIN)/coverage
SPHINX := $(VENV_BIN)/sphinx-build

# Package info
PACKAGE_NAME := fuzzy-logic-search
SRC_DIR := fuzzy_logic_search
TEST_DIR := tests
DOCS_DIR := docs

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Available targets:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick start:$(NC)"
	@echo "  make install-dev    # Set up complete development environment"
	@echo "  make test          # Run tests"
	@echo "  make lint          # Check code style"
	@echo "  make format        # Auto-format code"

# === Environment Setup ===

.PHONY: venv
venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	@$(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip setuptools wheel
	@echo "$(GREEN)Virtual environment created successfully!$(NC)"

.PHONY: install
install: venv ## Install package in production mode
	@echo "$(BLUE)Installing $(PACKAGE_NAME)...$(NC)"
	@$(VENV_PIP) install -e .
	@echo "$(GREEN)Package installed successfully!$(NC)"

.PHONY: install-dev
install-dev: venv ## Install package with all development dependencies
	@echo "$(BLUE)Installing $(PACKAGE_NAME) with development dependencies...$(NC)"
	@$(VENV_PIP) install -e ".[dev,docs]"
	@echo "$(GREEN)Development environment ready!$(NC)"

.PHONY: deps
deps: ## Install/update dependencies from pyproject.toml
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@$(VENV_PIP) install --upgrade -e ".[dev,docs]"
	@echo "$(GREEN)Dependencies updated!$(NC)"

# === Testing ===

.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(PYTEST) $(TEST_DIR) -xvs

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

.PHONY: test-watch
test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@$(VENV_BIN)/ptw $(TEST_DIR) -- -xvs

.PHONY: test-fast
test-fast: ## Run tests in parallel (requires pytest-xdist)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	@$(PYTEST) $(TEST_DIR) -n auto

.PHONY: coverage
coverage: test-cov ## Generate HTML coverage report
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "$(YELLOW)Please open htmlcov/index.html manually$(NC)"

# === Code Quality ===

.PHONY: lint
lint: ## Run code linters (ruff)
	@echo "$(BLUE)Running linters...$(NC)"
	@$(RUFF) check $(SRC_DIR) $(TEST_DIR)

.PHONY: format
format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(BLACK) $(SRC_DIR) $(TEST_DIR)
	@$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Code formatted!$(NC)"

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	@$(MYPY) $(SRC_DIR)

.PHONY: check
check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)All checks passed!$(NC)"

.PHONY: pre-commit
pre-commit: format lint type-check test ## Run all pre-commit checks
	@echo "$(GREEN)Ready to commit!$(NC)"

# === Documentation ===

.PHONY: docs
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	@mkdir -p $(DOCS_DIR)/_build
	@$(SPHINX) -b html $(DOCS_DIR) $(DOCS_DIR)/_build/html
	@echo "$(GREEN)Documentation built in $(DOCS_DIR)/_build/html$(NC)"

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000...$(NC)"
	@cd $(DOCS_DIR)/_build/html && $(VENV_PYTHON) -m http.server

.PHONY: docs-clean
docs-clean: ## Clean documentation build
	@echo "$(BLUE)Cleaning documentation...$(NC)"
	@rm -rf $(DOCS_DIR)/_build

# === Building & Distribution ===

.PHONY: build
build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	@$(VENV_PYTHON) -m build
	@echo "$(GREEN)Packages built in dist/$(NC)"

.PHONY: publish-test
publish-test: build ## Publish to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	@$(VENV_PYTHON) -m twine upload --repository testpypi dist/*

.PHONY: publish
publish: build ## Publish to PyPI
	@echo "$(RED)Publishing to PyPI...$(NC)"
	@echo "$(YELLOW)Are you sure? Press Ctrl+C to cancel.$(NC)"
	@sleep 3
	@$(VENV_PYTHON) -m twine upload dist/*

# === Cleaning ===

.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf build dist *.egg-info
	@rm -rf .pytest_cache .mypy_cache .ruff_cache
	@rm -rf htmlcov .coverage coverage.xml
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*~" -delete
	@echo "$(GREEN)Clean!$(NC)"

.PHONY: clean-all
clean-all: clean docs-clean ## Clean everything including virtual environment
	@echo "$(BLUE)Cleaning everything...$(NC)"
	@rm -rf $(VENV)
	@echo "$(GREEN)All clean!$(NC)"

# === Development Utilities ===

.PHONY: shell
shell: ## Launch Python shell with package imported
	@echo "$(BLUE)Launching Python shell...$(NC)"
	@$(VENV_PYTHON) -c "import sys; sys.path.insert(0, '.'); from fuzzy_logic_search import *" -i

.PHONY: jupyter
jupyter: ## Launch Jupyter notebook
	@echo "$(BLUE)Launching Jupyter notebook...$(NC)"
	@$(VENV_BIN)/jupyter notebook

.PHONY: update-deps
update-deps: ## Update all dependencies to latest versions
	@echo "$(BLUE)Updating dependencies to latest versions...$(NC)"
	@$(VENV_PIP) list --outdated
	@$(VENV_PIP) install --upgrade pip setuptools wheel
	@$(VENV_PIP) install --upgrade -e ".[dev,docs]"
	@echo "$(GREEN)Dependencies updated!$(NC)"

.PHONY: freeze
freeze: ## Freeze current dependencies to requirements.txt
	@echo "$(BLUE)Freezing dependencies...$(NC)"
	@$(VENV_PIP) freeze > requirements-frozen.txt
	@echo "$(GREEN)Dependencies frozen to requirements-frozen.txt$(NC)"

# === Version Management ===

.PHONY: version
version: ## Show current version
	@echo "$(BLUE)Current version:$(NC)"
	@grep "^version" pyproject.toml | cut -d'"' -f2

.PHONY: bump-patch
bump-patch: ## Bump patch version (0.0.X)
	@echo "$(BLUE)Bumping patch version...$(NC)"
	@$(VENV_PYTHON) -c "import toml; \
		config = toml.load('pyproject.toml'); \
		version = config['project']['version'].split('.'); \
		version[2] = str(int(version[2]) + 1); \
		config['project']['version'] = '.'.join(version); \
		toml.dump(config, open('pyproject.toml', 'w'))"
	@echo "$(GREEN)Version bumped to $$(make version)$(NC)"

.PHONY: bump-minor
bump-minor: ## Bump minor version (0.X.0)
	@echo "$(BLUE)Bumping minor version...$(NC)"
	@$(VENV_PYTHON) -c "import toml; \
		config = toml.load('pyproject.toml'); \
		version = config['project']['version'].split('.'); \
		version[1] = str(int(version[1]) + 1); \
		version[2] = '0'; \
		config['project']['version'] = '.'.join(version); \
		toml.dump(config, open('pyproject.toml', 'w'))"
	@echo "$(GREEN)Version bumped to $$(make version)$(NC)"

.PHONY: bump-major
bump-major: ## Bump major version (X.0.0)
	@echo "$(BLUE)Bumping major version...$(NC)"
	@$(VENV_PYTHON) -c "import toml; \
		config = toml.load('pyproject.toml'); \
		version = config['project']['version'].split('.'); \
		version[0] = str(int(version[0]) + 1); \
		version[1] = '0'; \
		version[2] = '0'; \
		config['project']['version'] = '.'.join(version); \
		toml.dump(config, open('pyproject.toml', 'w'))"
	@echo "$(GREEN)Version bumped to $$(make version)$(NC)"

# === Git Helpers ===

.PHONY: git-status
git-status: ## Show git status
	@git status

.PHONY: git-diff
git-diff: ## Show git diff
	@git diff

.PHONY: git-log
git-log: ## Show recent commits
	@git log --oneline -10

# === Default target ===
.DEFAULT_GOAL := help
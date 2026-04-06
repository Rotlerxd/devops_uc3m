.PHONY: help lint format typecheck test test-unit test-integration test-e2e \
        coverage security build deploy docs up down ci clean check

PYTHON      ?= $(CURDIR)/.venv/bin/python
PIP         ?= pip
NPM         ?= npm
DOCKER      ?= docker

BACKEND_DIR  = Backend
FRONTEND_DIR = Frontend
E2E_DIR      = e2e

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- Quality ----------

lint: ## Run Ruff linter
	$(PYTHON) -m ruff check Backend/

format: ## Run Ruff formatter
	$(PYTHON) -m ruff format Backend/

format-check: ## Check Ruff formatting (CI mode)
	$(PYTHON) -m ruff format --check Backend/

typecheck: ## Run Ty type checker
	$(PYTHON) -m ty check Backend/app/

check: lint typecheck test-unit ## Quick check: lint + typecheck + unit tests

# ---------- Testing ----------

test: test-unit test-integration ## Run all backend tests

test-unit: ## Run backend unit tests
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/unit -v --tb=short -m unit

test-integration: ## Run backend integration tests (needs PostgreSQL + Elasticsearch)
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/integration -v --tb=short -m integration

test-frontend: ## Run frontend unit tests
	cd $(FRONTEND_DIR) && $(NPM) run test:run

test-e2e: ## Run end-to-end tests
	cd $(E2E_DIR) && $(NPM) install --silent && npx playwright install --with-deps chromium 2>/dev/null; $(NPM) test

coverage: ## Run backend tests with coverage report
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/unit tests/integration \
		--cov=app --cov-report=term-missing --cov-report=html:htmlcov

# ---------- Security ----------

security: ## Run dependency vulnerability scans
	$(PYTHON) -m pip_audit -r $(BACKEND_DIR)/requirements.txt || true
	cd $(FRONTEND_DIR) && $(NPM) audit --production || true

# ---------- Build ----------

build: ## Build Docker images
	$(DOCKER) build -t newsradar-backend:latest $(BACKEND_DIR)

# ---------- Infra ----------

up: ## Start PostgreSQL + Elasticsearch
	cd $(BACKEND_DIR) && $(DOCKER) compose up -d

down: ## Stop PostgreSQL + Elasticsearch
	cd $(BACKEND_DIR) && $(DOCKER) compose down

# ---------- Docs ----------

docs: ## Generate API documentation
	bash scripts/gen-docs.sh

# ---------- CI ----------

ci: ## Run full CI pipeline locally
	bash scripts/ci-local.sh

clean: ## Remove build/test artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf Backend/htmlcov Backend/.coverage .ruff_cache .ty/
	rm -rf e2e/test-results e2e/playwright-report
	rm -rf Frontend/dist

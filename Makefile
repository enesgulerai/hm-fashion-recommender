# --- H&M Recommendation System Makefile (Windows/Linux/Mac Compatible) ---

.PHONY: help install start stop clean test test-v logs prune

# Default goal
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python

# =============================================================================
# 🆘 HELP
# =============================================================================
help: ## Shows the list of available commands.
	@$(PYTHON) -c "import re, sys; lines = [l.strip() for l in open('Makefile', encoding='utf-8')]; [print(f'\033[36m{m.group(1):<20}\033[0m {m.group(2)}') for l in lines if (m := re.search(r'^([a-zA-Z_-]+):.*?## (.*)$$', l))]"

# =============================================================================
# 🐳 DOCKER OPERATIONS
# =============================================================================
start: ## Starts all services (API, UI, Redis, Qdrant) in background.
	@echo "🚀 Starting all services..."
	docker-compose up -d --build
	@echo "✅ System is up! Access UI at: http://localhost:8502"

stop: ## Stops all containers (Preserves data).
	@echo "🛑 Stopping services..."
	docker-compose down

down: ## Stops containers and removes networks.
	docker-compose down

logs: ## Follows the logs.
	docker-compose logs -f

prune: ## Safe cleanup of dangling images.
	docker image prune -f

# =============================================================================
# 🧪 DEVELOPMENT
# =============================================================================
install: ## Installs dependencies.
	pip install -r src/api/requirements.txt -r src/ui/requirements.txt -r requirements.txt

test: ## Runs tests using Pytest.
	pytest tests/

test-v: ## Runs tests in verbose mode.
	pytest tests/ -vv

format: ## Formats code (Black/Isort).
	black .
	isort .

lint: ## Checks code style.
	black --check .
	isort --check-only .

# =============================================================================
# 🧹 CLEAN (Python-based)
# =============================================================================
clean: ## Removes __pycache__, .pyc, .pytest_cache files.
	@echo "🧹 Cleaning up bytecode and cache..."
	@$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache') if p.exists()]"
	@echo "✨ Clean complete."
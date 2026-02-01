# --- H&M Recommendation System - Bulletproof Makefile ---

.PHONY: help run stop logs clean prune

.DEFAULT_GOAL := help

# =============================================================================
# HELP
# =============================================================================
help:
	@echo "======================================================================"
	@echo " H&M FASHION RECOMMENDER - COMMAND CENTER"
	@echo "======================================================================"
	@echo "  make run    : Initializes the entire system (Infra + ETL + App)."
	@echo "  make stop   : It stops everything and cleans it up."
	@echo "  make logs   : It monitors the logs live."
	@echo "  make prune  : It deletes any leftover Docker images."
	@echo "  make clean  : Clears cache files."
	@echo "======================================================================"

# =============================================================================
# MAIN COMMANDS
# =============================================================================
run:
	@echo "System is building and starting..."
	docker-compose up -d --build
	@echo "====================================================="
	@echo "SYSTEM IS UP AND RUNNING!"
	@echo "====================================================="
	@echo "UI is running at: http://localhost:8501"
	@echo "API is running at: http://localhost:8000"
	@echo "Monitoring at:    http://localhost:3000"
	@echo "Tip: To track logs, type 'make logs'."

stop:
	@echo "Stopping all services..."
	docker-compose down --remove-orphans

logs:
	docker-compose logs -f

# =============================================================================
# UTILITIES
# =============================================================================
prune:
	docker image prune -f

clean:
	@echo "Cleaning up bytecode and cache..."
	@python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache') if p.exists()]"
	@echo "Clean complete."
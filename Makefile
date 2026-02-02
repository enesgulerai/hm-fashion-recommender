# --- H&M Recommendation System - Bulletproof Makefile ---

.PHONY: help run stop logs clean prune

.DEFAULT_GOAL := help
K8S_DIR := k8s

# =============================================================================
# HELP
# =============================================================================
help:
	@echo "======================================================================"
	@echo " H&M FASHION RECOMMENDER - COMMAND CENTER"
	@echo "======================================================================"
	@echo " ===== MAIN COMMANDS ====="
	@echo "  make run    : Initializes the entire system (Infra + ETL + App)."
	@echo "  make stop   : It stops everything and cleans it up."
	@echo "  make logs   : It monitors the logs live."
	@echo " ===== UTILITIES ====="
	@echo "  make prune  : It deletes any leftover Docker images."
	@echo "  make clean  : Clears cache files."
	@echo "  make test   : It runs unit tests."
	@echo " ===== Kubernetes ====="
	@echo "  make k8s-deploy : Installs the entire system on K8s (Build + Apply)."
	@echo "  make k8s-ingest : Starts the ETL job (Data Loading) on the K8s."
	@echo "  make k8s-stop   : It deletes all K8s resources."
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

test:
	@echo "Running unit tests..."
	pytest tests/

# =============================================================================
# KUBERNETES COMMANDS
# =============================================================================
k8s-build:
	@echo "Building Docker images for Kubernetes..."
	docker build -t hm-backend:latest -f Dockerfile.api .
	docker build -t hm-frontend:latest -f Dockerfile.frontend .
	docker build -t hm-etl:latest -f Dockerfile.api .

k8s-deploy: k8s-build
	@echo "Deploying to Kubernetes..."
	# 1. Infrastructure and Discs
	kubectl apply -f $(K8S_DIR)/infrastructure/
	# 2. Databases
	kubectl apply -f $(K8S_DIR)/databases/
	@echo "Waiting for databases to be ready..."
	sleep 10
	# 3. Applications
	kubectl apply -f $(K8S_DIR)/apps/
	@echo "Deployment complete! Frontend: http://localhost:30001"

k8s-ingest:
	@echo "Starting ETL Job..."
	-kubectl delete job etl-ingestion 2>nul || true
	kubectl apply -f $(K8S_DIR)/jobs/ingestion.yaml
	@echo "Logs for ETL (Press Ctrl+C to exit):"
	sleep 2
	@kubectl get pods -l job-name=etl-ingestion -o name | xargs kubectl logs -f

k8s-stop:
	@echo "Stopping Kubernetes resources..."
	kubectl delete -f $(K8S_DIR)/apps/ --ignore-not-found
	kubectl delete -f $(K8S_DIR)/databases/ --ignore-not-found
	kubectl delete -f $(K8S_DIR)/infrastructure/ --ignore-not-found
	kubectl delete -f $(K8S_DIR)/jobs/ --ignore-not-found
# --- H&M Recommendation System ---

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
	@echo "  make k8s-build : Builds the entire system on K8s (Build)."
	@echo "  make k8s-deploy : Installs the entire system on K8s (Build + Apply)."
	@echo "  make k8s-logs-etl : Starts the ETL job (Data Loading) on the K8s."
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
	@echo "UI is running at: http://localhost:8502"
	@echo "API is running at: http://localhost:8001"
	@echo "Monitoring at:    http://localhost:3001"
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
	docker build -t hm-backend:latest -f docker/backend/Dockerfile .
	docker build -t hm-frontend:latest -f docker/frontend/Dockerfile .
	docker build -t hm-etl:latest -f docker/backend/Dockerfile .

k8s-deploy: k8s-build
	@echo "Deploying Full System & Auto-Running ETL via Helm..."
	helm upgrade --install hm-recommender ./hm-chart
	@echo "Deployment triggered! Helm will handle DB warmups and start the ETL Job."
	@echo "Frontend will be available at: http://localhost:30001"

k8s-logs-etl:
	@echo "Tailing ETL Ingestion Logs (Press Ctrl+C to exit)..."
	kubectl logs -l job-name=etl-ingestion -f --pod-running-timeout=60s

k8s-stop:
	@echo "Stopping and destroying all Kubernetes resources..."
	helm uninstall hm-recommender
	-kubectl delete job etl-ingestion --ignore-not-found=true
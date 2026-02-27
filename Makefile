# --- H&M Recommendation System ---

.PHONY: help build-model run stop logs clean prune test k8s-build k8s-deploy k8s-logs-etl k8s-stop argocd-ui

.DEFAULT_GOAL := help
K8S_DIR := k8s

# =============================================================================
# COMMAND CENTER (HELP)
# =============================================================================
help:
	@echo "======================================================================"
	@echo " H&M FASHION RECOMMENDER - COMMAND CENTER (ONNX + K8S + GITOPS)"
	@echo "======================================================================"
	@echo " ===== MLOPS ====="
	@echo "  make build-model  : Generates the ONNX model into onnx_model/ dir."
	@echo " ===== DOCKER COMPOSE ====="
	@echo "  make run          : Initializes the system via Docker Compose."
	@echo "  make stop         : Stops Docker Compose services."
	@echo "  make logs         : Monitors the Docker Compose logs live."
	@echo " ===== KUBERNETES & HELM ====="
	@echo "  make k8s-build    : Builds Backend and Frontend Docker images."
	@echo "  make k8s-deploy   : Deploys the Full System & Auto-Runs ETL via Helm."
	@echo "  make k8s-logs-etl : Tails the ETL Ingestion logs on K8s."
	@echo "  make k8s-stop     : Destroys all K8s resources & Helm releases."
	@echo " ===== GITOPS (ARGOCD) ====="
	@echo "  make argocd-ui    : Port-forwards ArgoCD UI to https://localhost:8080"
	@echo " ===== UTILITIES ====="
	@echo "  make clean        : Clears cache and bytecode files."
	@echo "  make prune        : Deletes leftover dangling Docker images."
	@echo "  make test         : Runs unit tests."
	@echo "======================================================================"

# =============================================================================
# MLOPS (MODEL PREPARATION)
# =============================================================================
build-model:
	@echo "Exporting/Downloading ONNX Model..."
	@python -m src.models.export_onnx # <--- DİKKAT: BURAYA KENDİ PYTHON SCRİPT YOLUNU YAZ
	@echo "Model successfully generated in onnx_model/ directory!"

# =============================================================================
# DOCKER COMPOSE COMMANDS
# =============================================================================
run: build-model
	@echo "System is building and starting..."
	docker-compose up -d --build
	@echo "====================================================="
	@echo "SYSTEM IS UP AND RUNNING!"
	@echo "UI:  http://localhost:8501"
	@echo "API: http://localhost:8001"
	@echo "Tip: To track logs, type 'make logs'."

stop:
	@echo "Stopping all services..."
	docker-compose down --remove-orphans

logs:
	docker-compose logs -f

# =============================================================================
# KUBERNETES COMMANDS (INNER LOOP)
# =============================================================================
k8s-build: build-model
	@echo "Building Backend (API + ETL) image..."
	docker build -t hm-backend:latest -f docker/backend/Dockerfile .
	@echo "Building Frontend image..."
	docker build -t hm-frontend:latest -f docker/frontend/Dockerfile .

k8s-deploy: k8s-build
	@echo "Deploying Full System via Helm..."
	helm upgrade --install hm-recommender ./hm-chart
	@echo "Deployment triggered! Frontend will be available at: http://localhost:30001"

k8s-logs-etl:
	@echo "Tailing ETL Ingestion Logs (Press Ctrl+C to exit)..."
	kubectl logs -l job-name=etl-ingestion -f --pod-running-timeout=60s

k8s-stop:
	@echo "Stopping and destroying all Kubernetes resources..."
	helm uninstall hm-recommender || true
	-kubectl delete job -l app=etl-ingestion --ignore-not-found=true

# =============================================================================
# GITOPS COMMANDS (OUTER LOOP)
# =============================================================================
argocd-ui:
	@echo "Port-forwarding ArgoCD UI..."
	@echo "Go to: https://localhost:8080"
	@echo "Username: admin"
	@echo "Password fetch command (Windows/PS): kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
	kubectl port-forward svc/argocd-server -n argocd 8080:443

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

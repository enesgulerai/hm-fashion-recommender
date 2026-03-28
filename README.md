# AI Fashion Stylist: Personalized Recommendation System

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-d50000?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![Redis](https://img.shields.io/badge/Redis-Caching-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Prometheus](https://img.shields.io/badge/Monitoring-Prometheus-E6522C?style=for-the-badge&logo=prometheus)
![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)
[![Helm](https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white)](https://helm.sh/)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white)](https://argo-cd.readthedocs.io/)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)

> **"I need a red dress for a summer wedding."** -> *Retrieves visually and semantically similar items in milliseconds.*

This project implements an **End-to-End MLOps pipeline** for a real-time fashion recommendation system. It leverages **Semantic Search** using tailored BERT embeddings and a **Vector Database (Qdrant)** to understand user intent beyond keyword matching.

<p align="center">
  <img src="docs/images/streamlit_usage.gif" alt="Project Demo" width="700">
</p>

# Session: Architecture, Impact & Proof
*This section highlights the system design, performance benchmarks, and deployment strategies.*

## 🏗️ Microservices Architecture
The system is designed with scalability in mind, fully decoupled into independent microservices.

```mermaid
graph LR
    U[👤 User / Locust Test]
    Git[🐙 GitHub Repository]

    subgraph "Kubernetes Cluster (Minikube / AWS)"

        Argo[⚙️ ArgoCD]

        F["🖥️ Frontend (Streamlit)"]
        B["⚡ Async Backend (FastAPI)"]

        R[("🔥 Redis Cache")]
        Q[("🧠 Qdrant Vector DB")]

        M[📈 Prometheus]
        G[📊 Grafana]
    end

    Git -.->|Reads Helm & Configs| Argo
    Argo -.->|Syncs Cluster State| F
    Argo -.->|Syncs Cluster State| B

    U -->|Natural Language Query| F
    F -->|REST API Request| B

    B -->|1. Check Cache| R
    R -.->|Cache Hit <2ms| B
    B -->|2. Vector Search| Q
    Q -->|Top-K Candidates| B

    B -->|JSON Response| F
    F -->|Product Cards| U

    M -.->|Scrapes Async Metrics| B
    G -.->|Visualizes| M

    classDef cluster fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef gitops fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    class Argo,Git gitops;
```

## ⚡ High-Performance API & Reliability
The backend was completely refactored to an asynchronous architecture to prevent blocking during AI model inference and database operations.

* **Redis Caching:** Slashes inference latency to <2ms on cache hits.

![Redis Test Results](docs/grafana/grafana.png)

* **Extreme Stress Tested:** Validated via Locust on a local Kubernetes cluster.

* **Results:** Sustained 805 RPS (~2.9M requests/hour) under 2,000 concurrent users with a 0% error rate.

![Load Test Results](docs/load_test/locust.png)

## 🔄 GitOps & Continuous Deployment (ArgoCD)
To eliminate manual deployment bottlenecks, this project fully embraces the GitOps philosophy. The cluster state is entirely declarative and managed via Helm charts.

* **Single Source of Truth:** Any changes to the GitHub repository automatically trigger a synchronization.

![ArgoCD Topology Tree](docs/gitops/argocd_topology.png)

* **Zero-Downtime:** ArgoCD reconciles the cluster state without manual kubectl interventions.

## 📊 Observability & Drift Monitoring
Comprehensive monitoring stacks are integrated to track both system health and machine learning metrics.

* **Prometheus & Grafana:** Real-time API throughput, latency, and memory tracking.

* **Evidently AI:** Real-time Data Drift monitoring for the embedding model.

![Evidentyl AI](docs/evidently/evidently_drift_dashboard.png)

## ☁️ Cloud Deployment (AWS)
The project is not just local; it is fully capable of running in the cloud. It was successfully deployed on an AWS EC2 (t3.small) instance utilizing K3s (Lightweight Kubernetes).

![AWS](docs/aws/hm-aws-inbound-rules.png)

![AWS](docs/aws/hm-aws-instance.png)

![AWS](docs/aws/aws_streamlit_usage.gif)

# Session: Developer Guide
Instructions for reproducing the environment, running tests, and deploying the system locally.

## 🚀 Quick Start (Docker Compose)
The easiest way to run the project. You don't need Python installed locally, just Docker and Make.

```bash
    # 1. Clone the Repository
    git clone https://github.com/enesgulerai/hm-fashion-recommender.git
    cd hm-fashion-recommender

    # 2. Run the System (Automates Data Ingestion -> Embedding -> DB Indexing)
    make run
    # Note: If you don't have make installed (e.g., standard Windows CMD), you can use the raw command:
    docker-compose up -d --build

    # 3. Stop the System
    make stop
```

## ☸️ Kubernetes Deployment (Local)
For testing the production-ready Helm charts and Kubernetes manifests locally (requires Docker Desktop K8s or Minikube).

```bash
    # Deploy the entire stack
    make k8s-deploy

    # Watch Logs
    make k8s-logs

    # Teardown all K8s resources
    make k8s-stop
```

## 🔗 Service Access Points
Once the system is up, you can access the microservices here:

| Service          | URL | Default Credentials | Description |
|:-----------------| :--- | :--- | :--- |
| **Frontend App** | [**http://localhost:8502**](http://localhost:8502) | - | The main User Interface (Streamlit). Start here! |
| **API Docs**     | [**http://localhost:8001/docs**](http://localhost:8001/docs) | - | Interactive Swagger UI to test API endpoints. |
| **Grafana**      | [**http://localhost:3001**](http://localhost:3001) | `admin` / `admin` | Real-time dashboards for metrics visualization. |
| **Prometheus** | [**http://localhost:9091**](http://localhost:9091) | - | Raw metrics scraping and querying interface. |
| **Kubernetes UI** | [**http://localhost:30001**](http://localhost:30001) | - | Main Streamlit interface exposed via K8s NodePort. Use this for cluster deployments. |


## 🧪 Local Development & Testing
If you want to run the tests or develop locally outside of Docker:
```bash
    # 1. Setup Virtual Environment
    python -m venv .venv
    source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

    # 2. Install Dependencies
    make install

    # 3. Run the Pytest Suite
    make test
```

# 🛠️ Troubleshooting & Common Issues

**1. `make: command not found` (Windows Users)**
* **Symptom:** PowerShell or CMD throws an error that `make` is not recognized.
* **Solution:** Windows does not come with `make` pre-installed. You have two options:
  * **Option A (Bypass):** Run the raw Docker command instead: `docker compose up -d --build`
  * **Option B (Install):** Install `make` via Windows package managers:
    * `winget install ezwinports.make` OR `choco install make`

**2. Docker Daemon is Not Running**
* **Symptom:** `error during connect: This error may indicate that the docker daemon is not running.`
* **Solution:** Ensure Docker Desktop is launched and the Docker engine is running in the background before executing the Makefile.

**3. Port is Already Allocated**
* **Symptom:** `Bind for 0.0.0.0:8001 failed: port is already allocated.`
* **Solution:** Another service on your machine is using one of the required ports (8001, 8502, 6333, etc.). You can either stop that service or modify the port mappings in the `docker-compose.yml` file.

**4. Out of Memory (OOM) Errors (Qdrant or Embeddings)**
* **Symptom:** The `etl-worker` or `qdrant` container crashes unexpectedly during startup.
* **Solution:** Processing 100K+ embeddings can be memory-intensive. Ensure your Docker Desktop is allocated at least **4GB to 6GB of RAM** in its settings.


## 👨‍💻 Author
**Enes Guler** - MLOps Engineer

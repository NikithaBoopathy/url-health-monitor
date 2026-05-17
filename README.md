# URL Health Monitor

A production-grade URL health monitoring service that continuously checks whether websites are **UP** or **DOWN**, records response times, and exposes results via a REST API.

Built to demonstrate a full DevOps pipeline — Docker → Kubernetes → Terraform → CI/CD.

---

## Architecture

```
Developer
    │
    │  git push
    ▼
GitHub Actions (CI/CD Pipeline)
    │
    ├── Stage 1: pytest tests
    ├── Stage 2: docker build + push → Docker Hub
    └── Stage 3: update deployment.yaml (GitOps)
                        │
                        ▼
            Kubernetes Cluster (k3s)
            ┌─────────────────────────────┐
            │  namespace: monitoring      │
            │                             │
            │  Deployment (2 replicas)    │
            │  ┌──────────┐ ┌──────────┐ │
            │  │  Pod 1   │ │  Pod 2   │ │
            │  │ Flask app│ │ Flask app│ │
            │  └──────────┘ └──────────┘ │
            │                             │
            │  ConfigMap  →  URLs to check│
            │  Secret     →  Webhook key  │
            │  Service    →  NodePort 30800│
            └─────────────────────────────┘
                        │
                        ▼
            Terraform (Infrastructure as Code)
            Provisions namespace + ConfigMap
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **Python + Flask** | REST API serving health check results |
| **Docker** | Containerise the app into a portable image |
| **Kubernetes (k3s)** | Orchestrate containers with self-healing and scaling |
| **Terraform** | Provision K8s namespace and ConfigMap as code |
| **GitHub Actions** | CI/CD pipeline — test, build, push, deploy |
| **Docker Hub** | Store and version Docker images |

---

## Project Structure

```
url-health-monitor/
├── app/
│   ├── app.py                  # Flask app — health checker + REST API
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Container image blueprint
│   └── tests/
│       ├── __init__.py
│       └── test_app.py         # pytest tests
├── k8s/
│   ├── namespace.yaml          # monitoring namespace
│   ├── configmap.yaml          # URLs to monitor
│   ├── secret.yaml             # sensitive config
│   ├── deployment.yaml         # 2-replica deployment with probes
│   └── service.yaml            # NodePort service on 30800
├── terraform/
│   └── main.tf                 # Provisions namespace + ConfigMap
├── .github/
│   └── workflows/
│       └── cicd.yml            # 3-stage GitHub Actions pipeline
└── README.md
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Service info and version |
| `/health` | GET | Liveness check — returns `{"status": "healthy"}` |
| `/status` | GET | All monitored URLs with UP/DOWN status |
| `/status/<url>` | GET | Status of a single URL |

### Example response — `/status`

```json
{
  "https://google.com": {
    "status": "UP",
    "status_code": 200,
    "response_time_ms": 124,
    "checked_at": "2025-03-13T10:00:00Z"
  },
  "https://github.com": {
    "status": "UP",
    "status_code": 200,
    "response_time_ms": 89,
    "checked_at": "2025-03-13T10:00:00Z"
  }
}
```

---

## Getting Started

### Prerequisites

| Tool | Install |
|---|---|
| Docker | `sudo apt install -y docker.io` |
| k3s | `curl -sfL https://get.k3s.io \| sh -` |
| Terraform | See [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads) |
| kubectl | Included with k3s — `alias kubectl="k3s kubectl"` |
| Git | `sudo apt install -y git` |

---

### Phase 1 — Run with Docker

```bash
# Clone the repo
git clone https://github.com/NikithaBoopathy/url-health-monitor.git
cd url-health-monitor

# Build the image
docker build -t url-health-monitor:v1 ./app

# Run the container
docker run -d -p 5000:5000 \
  -e URLS_TO_MONITOR="https://google.com,https://github.com" \
  --name url-health-monitor \
  url-health-monitor:v1

# Test it
curl http://localhost:5000/health
curl http://localhost:5000/status
```

---

### Phase 2 — Deploy to Kubernetes

```bash
# Step 1 — Provision infrastructure with Terraform
cd terraform
terraform init
terraform apply -auto-approve
cd ..

# Step 2 — Import Docker image into k3s
sudo k3s ctr images import - < <(docker save url-health-monitor:v1)

# Step 3 — Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Step 4 — Watch pods come up
kubectl get pods -n monitoring -w

# Step 5 — Test the live API
curl http://localhost:30800/health
curl http://localhost:30800/status
```

---

### Phase 3 — CI/CD Pipeline

Every `git push` to `main` triggers the 3-stage pipeline automatically:

```
push to main
     │
     ▼
┌─────────────────────────────────────────────────────┐
│ Stage 1 — test                                      │
│   pytest tests/ -v                                  │
│    passes → continue    fails → pipeline stops  │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│ Stage 2 — build-and-push                           │
│   docker build -t username/url-health-monitor:SHA  │
│   docker push → Docker Hub                         │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│ Stage 3 — deploy                                    │
│   Update deployment.yaml with new image SHA        │
│   Commit back to repo (GitOps pattern)             │
└─────────────────────────────────────────────────────┘
```

#### Required GitHub Secrets

Go to `Settings → Secrets and variables → Actions` and add:

| Secret | Value |
|---|---|
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_PASSWORD` | Your Docker Hub access token (Read & Write) |

---

## Kubernetes Features Demonstrated

### Self-healing
```bash
# Delete a pod — Deployment immediately recreates it
kubectl delete pod <pod-name> -n monitoring
kubectl get pods -n monitoring -w
```

### Scaling
```bash
# Scale up to 5 replicas
kubectl scale deployment url-health-monitor --replicas=5 -n monitoring

# Scale back down
kubectl scale deployment url-health-monitor --replicas=2 -n monitoring
```

### Rolling update — zero downtime
```bash
# Update to a new image version
kubectl set image deployment/url-health-monitor \
  monitor=nikithaboopathy/url-health-monitor:new-sha \
  -n monitoring

# Check rollout status
kubectl rollout status deployment/url-health-monitor -n monitoring

# Rollback if needed
kubectl rollout undo deployment/url-health-monitor -n monitoring
```

### View logs
```bash
kubectl logs -l app=url-health-monitor -n monitoring --follow
```

---

## Kubernetes Manifest Highlights

### Liveness and Readiness Probes
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 15
  periodSeconds: 20
```

**Readiness probe** — pod only receives traffic after `/health` returns 200.  
**Liveness probe** — pod is restarted if `/health` stops responding.

### Resource Limits
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

Prevents the app from consuming the entire cluster's resources.

### Configuration via ConfigMap
```yaml
envFrom:
  - configMapRef:
      name: monitor-config
  - secretRef:
      name: monitor-secret
```

URLs to monitor are injected at runtime — no rebuild needed to change them.

---

## Terraform

Infrastructure is provisioned as code — not created by hand.

```bash
cd terraform
terraform init      # download providers
terraform plan      # preview changes
terraform apply     # create namespace + ConfigMap
terraform show      # view current state
terraform destroy   # tear everything down
```

---

## Running Tests

```bash
cd app
PYTHONPATH=. pytest tests/ -v

# Expected output:
# tests/test_app.py::test_health  PASSED  ✅
# tests/test_app.py::test_index   PASSED  ✅
# tests/test_app.py::test_status  PASSED  ✅
# 3 passed
```

---

## What I Would Add in Production

- **Persistent storage** — PostgreSQL or InfluxDB to store historical uptime data across pod restarts
- **Alerting** — PagerDuty or Slack webhook when a URL goes DOWN
- **Horizontal Pod Autoscaler** — auto-scale replicas based on CPU/memory
- **Helm charts** — parameterise K8s manifests for dev/staging/production environments
- **ArgoCD** — full GitOps — auto-sync cluster when deployment YAML changes in Git
- **Ingress controller** — domain-based routing instead of NodePort
- **Structured logging** — JSON logs + Loki/ELK for log aggregation

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `URLS_TO_MONITOR` | `https://google.com,https://github.com` | Comma-separated list of URLs to check |
| `CHECK_INTERVAL` | `30` | How often to check in seconds |
| `ALERT_WEBHOOK` | — | Webhook URL for DOWN alerts |

---

## Author

**Nikitha Boopathy**  
DevOps project — Docker · Kubernetes · Terraform · GitHub Actions


# PractiCode — Local Practical Coding Assessment Platform

## Project Specification v1.0

---

## 1. Vision & Problem Statement

Modern coding assessments (CodeSignal, HackerRank) have shifted from pure algorithmic puzzles to **practical engineering challenges**: wiring up OAuth flows, calling REST APIs, transforming data between services, doing image processing pipelines, etc. These are impossible to practice on LeetCode because they require **live backend services** to interact with.

**PractiCode** is a fully local, self-contained platform that:

- Provides a LeetCode/CodeSignal-style browser UI (problem description, code editor, test runner, results panel).
- Runs **real backend services** inside the cluster that problems can reference (OAuth servers, data APIs, image endpoints, databases, etc.).
- Executes user-submitted code **server-side** in isolated containers.
- Is entirely orchestrated via a local **Kind** (Kubernetes in Docker) cluster, bootstrapped with a single `make setup`.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kind Cluster                            │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────────┐  │
│  │   Frontend    │    │  API Server  │   │  PostgreSQL   │  │
│  │  (React SPA)  │◄──►│   (FastAPI)  │◄─►│  (problems,   │  │
│  │  served by    │    │              │   │   submissions) │  │
│  │  nginx        │    └──────┬───────┘   └───────────────┘  │
│  └──────────────┘           │                               │
│                              │                               │
│                    ┌─────────▼──────────┐                    │
│                    │  Code Executor     │                    │
│                    │  (Job Spawner)     │                    │
│                    │  Spawns K8s Jobs   │                    │
│                    │  per submission    │                    │
│                    └─────────┬──────────┘                    │
│                              │                               │
│                    ┌─────────▼──────────┐                    │
│                    │  Execution Job     │                    │
│                    │  (ephemeral pod)   │                    │
│                    │  - python:3.12     │                    │
│                    │  - resource limits │                    │
│                    │  - network: cluster│                    │
│                    └─────────┬──────────┘                    │
│                              │                               │
│              ┌───────────────┼───────────────┐               │
│              ▼               ▼               ▼               │
│  ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ Challenge Svc: │ │ Challenge    │ │ Challenge Svc:   │   │
│  │ OAuth Mock     │ │ Svc: Data API│ │ Image Pipeline   │   │
│  └────────────────┘ └──────────────┘ └──────────────────┘   │
│                                                             │
│  (Challenge services are deployed per-problem or shared)    │
└─────────────────────────────────────────────────────────────┘
```

**Key insight**: User code runs in ephemeral K8s Jobs that have **cluster-internal network access**. This means the user's Python code can make HTTP requests to challenge services (e.g., `http://oauth-mock.challenges.svc.cluster.local`) just like in a real CodeSignal assessment.

---

## 3. Component Breakdown

### 3.1 Frontend — `frontend/`

**Tech Stack**: React 18+, TypeScript, Vite, Monaco Editor, TailwindCSS

**Pages/Views**:

| View | Description |
|---|---|
| **Problem List** | Grid/list of available challenges. Shows title, difficulty, tags (API, Image Processing, OAuth, etc.), completion status. |
| **Problem Workspace** | Split-pane layout: left panel = problem description (markdown rendered) with tabs for Description, Hints, API Docs; right panel = Monaco code editor (Python syntax, autocomplete) with tabs for Code, Test Results, Submission History. |
| **Submission Results** | Real-time status (queued → running → passed/failed). Shows per-test-case results: input, expected output, actual output, diff. Shows stdout/stderr. Shows execution time & memory. |

**Key UI Components**:

- `<ProblemDescription />` — Renders markdown problem statement. Supports embedded API documentation blocks (endpoint URLs, request/response schemas), diagrams, and example walkthroughs.
- `<CodeEditor />` — Monaco editor instance. Language selector (Python initially, extensible). Boilerplate/starter code pre-loaded per problem. Local autosave to `localStorage`.
- `<TestRunner />` — "Run Tests" (runs visible test cases only) and "Submit" (runs all test cases including hidden). Shows real-time streaming status via WebSocket or polling.
- `<ResultsPanel />` — Tabbed: Test Output | Stdout/Stderr | Submission History.

**Container**: Served by an nginx container. The nginx config reverse-proxies `/api/*` to the API server service.

**Kubernetes**:
```yaml
# Deployment: frontend
# Service: frontend-svc (ClusterIP)
# Port: 80
# NodePort or port-forward for local browser access
```

---

### 3.2 API Server — `api-server/`

**Tech Stack**: Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2, uvicorn

This is the central orchestrator. It does NOT execute user code itself.

**REST API Endpoints**:

```
# Problems
GET    /api/problems                  — List all problems (with filters: difficulty, tags)
GET    /api/problems/{id}             — Get problem detail (description, starter code, visible tests)
GET    /api/problems/{id}/api-docs    — Get challenge-specific API documentation

# Submissions
POST   /api/problems/{id}/run         — Run code against visible test cases only
POST   /api/problems/{id}/submit      — Submit code against all test cases (including hidden)
GET    /api/submissions/{id}          — Get submission status & results
GET    /api/submissions/{id}/stream   — SSE stream for real-time status updates

# Admin / Problem Management
POST   /api/admin/problems            — Create a new problem
PUT    /api/admin/problems/{id}       — Update a problem
POST   /api/admin/problems/{id}/tests — Add/update test cases
```

**Database Schema** (PostgreSQL):

```sql
-- Core tables
CREATE TABLE problems (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug          VARCHAR(255) UNIQUE NOT NULL,
    title         VARCHAR(500) NOT NULL,
    difficulty    VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    tags          TEXT[] DEFAULT '{}',
    description   TEXT NOT NULL,                      -- Markdown
    starter_code  JSONB NOT NULL DEFAULT '{}',        -- {"python": "def solve():..."}
    api_docs      TEXT,                               -- Markdown for challenge API docs
    challenge_services JSONB DEFAULT '[]',            -- Services this problem needs
    time_limit_seconds INTEGER DEFAULT 30,
    memory_limit_mb    INTEGER DEFAULT 256,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE test_cases (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id  UUID REFERENCES problems(id) ON DELETE CASCADE,
    input       JSONB NOT NULL,                       -- Structured input data
    expected    JSONB NOT NULL,                       -- Expected output or validation rules
    is_hidden   BOOLEAN DEFAULT FALSE,                -- Hidden tests only run on submit
    is_sample   BOOLEAN DEFAULT FALSE,                -- Shown in problem description
    ordinal     INTEGER NOT NULL,
    validation_type VARCHAR(50) DEFAULT 'exact_match' -- exact_match | http_validation | custom_script
);

CREATE TABLE submissions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_id   UUID REFERENCES problems(id),
    code         TEXT NOT NULL,
    language     VARCHAR(20) NOT NULL DEFAULT 'python',
    status       VARCHAR(30) NOT NULL DEFAULT 'queued',
    -- status: queued | running | passed | failed | error | timeout
    results      JSONB,                               -- Per-test-case results
    stdout       TEXT,
    stderr       TEXT,
    duration_ms  INTEGER,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

**Submission Flow**:

1. Frontend POSTs code to `/api/problems/{id}/submit`.
2. API Server inserts a `submission` row (status=queued).
3. API Server calls the Code Executor service to create a K8s Job.
4. API Server returns submission ID immediately.
5. Frontend polls `/api/submissions/{id}` or connects to SSE stream.
6. Code Executor updates submission status via callback to API Server.

**Kubernetes**:
```yaml
# Deployment: api-server
# Service: api-server-svc (ClusterIP)
# Port: 8000
# ServiceAccount: api-server-sa (needs RBAC to create Jobs in executor namespace)
```

---

### 3.3 Code Executor — `code-executor/`

**Tech Stack**: Python 3.12, FastAPI (lightweight), `kubernetes` Python client

This service is responsible for **spawning and monitoring ephemeral K8s Jobs** that run user code. It does NOT run user code in its own process.

**Execution Model**:

```
API Server  ──POST /execute──►  Code Executor  ──creates──►  K8s Job (ephemeral pod)
                                                              │
                                                              ├─ Runs user code
                                                              ├─ Has cluster network access
                                                              ├─ Can reach challenge services
                                                              ├─ Resource-limited (CPU/mem)
                                                              └─ Auto-cleaned after completion
```

**API**:

```
POST /execute
  Body: {
    submission_id: str,
    problem_id: str,
    code: str,
    language: "python",
    test_cases: [...],
    time_limit_seconds: int,
    memory_limit_mb: int,
    challenge_services: {       # Injected as env vars in the Job pod
      "OAUTH_SERVER_URL": "http://oauth-mock.challenges.svc.cluster.local",
      "DATA_API_URL": "http://data-api.challenges.svc.cluster.local"
    }
  }

GET /execute/{submission_id}/status
  Returns: { status, results, stdout, stderr }
```

**Job Spec Template** (what gets created per submission):

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: exec-{submission_id_short}
  namespace: executor
  labels:
    app: code-execution
    submission-id: "{submission_id}"
spec:
  ttlSecondsAfterFinished: 120       # Auto-cleanup
  activeDeadlineSeconds: 60           # Hard timeout
  backoffLimit: 0                     # No retries
  template:
    spec:
      restartPolicy: Never
      serviceAccountName: executor-sa  # Minimal permissions
      containers:
        - name: runner
          image: practicode-runner-python:latest  # Pre-built, loaded into Kind
          resources:
            limits:
              cpu: "1"
              memory: "256Mi"
            requests:
              cpu: "250m"
              memory: "128Mi"
          env:
            - name: SUBMISSION_ID
              value: "{submission_id}"
            - name: CALLBACK_URL
              value: "http://api-server-svc.practicode.svc.cluster.local:8000/api/internal/results"
            # Challenge-specific env vars injected here
            - name: OAUTH_SERVER_URL
              value: "http://oauth-mock.challenges.svc.cluster.local"
          volumeMounts:
            - name: code-volume
              mountPath: /workspace
      volumes:
        - name: code-volume
          configMap:
            name: exec-{submission_id_short}-code
```

**Runner Image** — `runner-python/`:

A Docker image pre-loaded into Kind that:
1. Reads user code from `/workspace/solution.py` and test cases from `/workspace/tests.json`.
2. Executes a **harness** (`/app/harness.py`) that imports and runs the user's solution against each test case.
3. Captures stdout, stderr, execution time, and pass/fail per test case.
4. POSTs results back to the API Server's internal callback endpoint.
5. Supports multiple **validation modes**:
   - `exact_match` — Compare function return value to expected output.
   - `http_validation` — After running user code, the harness calls a validation endpoint on a challenge service to verify side effects (e.g., "did the user POST the correct transformed data?").
   - `custom_script` — Run a separate validation script provided by the problem definition.

**Pre-installed Python Packages in Runner** (common for practical challenges):
```
requests
httpx
Pillow
numpy
pandas
pydantic
cryptography
PyJWT
```

**Kubernetes**:
```yaml
# Deployment: code-executor
# Service: code-executor-svc (ClusterIP)
# Namespace: practicode
# Port: 8080
# ServiceAccount: code-executor-sa
#   - Needs RBAC: create/get/list/delete Jobs and ConfigMaps in "executor" namespace
```

---

### 3.4 Challenge Services — `challenges/`

These are the **mock backend services** that problems reference. User code running in execution Jobs talks to these over the cluster network.

**Architecture**: Each challenge service is a small, independent HTTP server. They can be shared across problems or problem-specific.

**Directory Structure**:
```
challenges/
├── oauth-mock/              # Generic OAuth2 server
│   ├── Dockerfile
│   ├── main.py              # FastAPI app
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
├── data-api/                # Generic CRUD data API
│   ├── Dockerfile
│   ├── main.py
│   └── k8s/
├── image-service/           # Image upload/download/validate service
│   ├── Dockerfile
│   ├── main.py
│   └── k8s/
└── _base/                   # Shared base image/utilities
    └── Dockerfile
```

**Example Challenge Services**:

#### 3.4.1 OAuth Mock — `challenges/oauth-mock/`

A configurable OAuth2 authorization server.

```
POST /oauth/token            — Issue access token (client_credentials or authorization_code)
GET  /oauth/.well-known      — OpenID configuration
GET  /oauth/validate          — Validate a token

Configuration via env vars:
  CLIENT_ID, CLIENT_SECRET   — Expected credentials
  TOKEN_TTL_SECONDS          — Token expiry
  SCOPES                     — Valid scopes
```

Per-problem configuration is achieved by deploying this service with different env vars per problem (or a single shared instance with multi-tenant config).

#### 3.4.2 Data API — `challenges/data-api/`

A generic REST API that serves/accepts structured data.

```
GET    /data/items            — Returns a list of items (JSON)
GET    /data/items/{id}       — Returns a single item
POST   /data/results          — Accepts transformed data from user code
GET    /data/results/validate — Validates what was posted (used by harness)

Configuration via env vars or mounted config files:
  DATASET_FILE               — Path to JSON dataset to serve
  EXPECTED_RESULTS_FILE      — Path to expected transformation results
```

#### 3.4.3 Image Service — `challenges/image-service/`

Serves source images and validates processed results.

```
GET    /images/list           — List available images
GET    /images/{id}           — Download an image
POST   /images/{id}/upload    — Upload processed image
GET    /images/{id}/validate  — Compare uploaded image against expected output

Configuration:
  SOURCE_IMAGES_DIR          — Directory of source images to serve
  EXPECTED_IMAGES_DIR        — Directory of expected output images
  TOLERANCE                  — Pixel diff tolerance for validation
```

**Kubernetes** (per challenge service):
```yaml
# Namespace: challenges
# Each service gets:
#   - Deployment (1 replica, minimal resources)
#   - Service (ClusterIP)
#   - ConfigMap or Secret for per-problem configuration
```

---

### 3.5 PostgreSQL — `infra/postgres/`

Standard PostgreSQL 16 deployment for persistent storage of problems, test cases, submissions, and results.

```yaml
# Deployment: postgres
# Service: postgres-svc (ClusterIP)
# Namespace: practicode
# Port: 5432
# PersistentVolumeClaim: postgres-pvc (1Gi, using Kind's local storage)
# Init: SQL migration scripts run via init container or Job
```

Data should be seeded with a starter set of problems (see Section 5).

---

## 4. Kubernetes Layout

### 4.1 Namespaces

| Namespace | Purpose |
|---|---|
| `practicode` | Core services: frontend, api-server, code-executor, postgres |
| `executor` | Ephemeral execution Jobs only. Isolated RBAC. |
| `challenges` | Challenge/mock services. Execution Jobs have network access to this namespace. |

### 4.2 RBAC

```yaml
# code-executor ServiceAccount needs:
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: executor
rules:
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["create", "get", "list", "watch", "delete"]
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["create", "get", "delete"]
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
```

### 4.3 Network Policies (optional, security hardening)

- Execution Jobs in `executor` namespace CAN reach services in `challenges` namespace.
- Execution Jobs in `executor` namespace CAN reach `api-server-svc` in `practicode` namespace (for result callbacks).
- Execution Jobs in `executor` namespace CANNOT reach the internet (no egress to 0.0.0.0/0).
- Execution Jobs CANNOT reach `postgres-svc` directly.

### 4.4 Resource Quotas

```yaml
# Namespace: executor
apiVersion: v1
kind: ResourceQuota
metadata:
  name: executor-quota
  namespace: executor
spec:
  hard:
    pods: "10"                  # Max 10 concurrent executions
    requests.cpu: "4"
    requests.memory: "2Gi"
    limits.cpu: "8"
    limits.memory: "4Gi"
```

---

## 5. Problem Definition Format

Problems are defined as YAML files that seed the database and configure associated challenge services.

```
problems/
├── 001-oauth-token-fetch/
│   ├── problem.yaml            # Problem metadata & description
│   ├── description.md          # Full problem description (markdown)
│   ├── api-docs.md             # API documentation shown to the user
│   ├── starter.py              # Starter code template
│   ├── solution.py             # Reference solution (not shown to user)
│   ├── tests.json              # Test case definitions
│   └── services.yaml           # Challenge services config for this problem
├── 002-data-transform-pipeline/
│   ├── ...
└── 003-image-resize-pipeline/
    ├── ...
```

**problem.yaml**:

```yaml
id: "001-oauth-token-fetch"
title: "OAuth Token Fetch & Data Retrieval"
difficulty: "medium"
tags: ["api", "oauth", "http", "json"]
time_limit_seconds: 30
memory_limit_mb: 256
description_file: "description.md"
api_docs_file: "api-docs.md"
starter_code:
  python: "starter.py"
test_cases_file: "tests.json"
services_file: "services.yaml"
```

**tests.json**:

```json
[
  {
    "id": "test-1",
    "name": "Basic token fetch and data retrieval",
    "input": {},
    "expected": {
      "status": "success",
      "data_count": 5
    },
    "is_hidden": false,
    "is_sample": true,
    "validation_type": "http_validation",
    "validation_endpoint": "http://data-api.challenges.svc.cluster.local/data/results/validate"
  },
  {
    "id": "test-2",
    "name": "Handles expired token gracefully",
    "input": {
      "token_ttl_override": 0
    },
    "expected": {
      "status": "success",
      "retried": true
    },
    "is_hidden": true,
    "validation_type": "http_validation",
    "validation_endpoint": "http://data-api.challenges.svc.cluster.local/data/results/validate"
  }
]
```

**services.yaml** (per-problem challenge service configuration):

```yaml
services:
  - name: oauth-mock
    namespace: challenges
    image: practicode-oauth-mock:latest
    env:
      CLIENT_ID: "test-client"
      CLIENT_SECRET: "test-secret"
      TOKEN_TTL_SECONDS: "300"
    # If the service is shared/already running, just reference it:
    # existing: true
    # service_url: "http://oauth-mock.challenges.svc.cluster.local"

  - name: data-api
    namespace: challenges
    image: practicode-data-api:latest
    env:
      DATASET_FILE: "/data/items.json"
    config_files:
      - source: "./data/items.json"
        mount: "/data/items.json"
```

---

## 6. Execution Harness Detail — `runner-python/`

The runner image is the most critical component. It bridges user code with the test framework.

```
runner-python/
├── Dockerfile
├── requirements.txt          # Pre-installed packages
├── app/
│   ├── harness.py            # Main entry point
│   ├── validators/
│   │   ├── exact_match.py    # Direct output comparison
│   │   ├── http_validator.py # Calls challenge service to validate
│   │   └── custom_script.py  # Runs a custom validation script
│   └── utils.py              # Timeout handling, output capture, etc.
```

**harness.py pseudocode**:

```python
import json, sys, time, traceback, requests

def main():
    # 1. Read inputs
    code = open("/workspace/solution.py").read()
    tests = json.load(open("/workspace/tests.json"))
    config = json.load(open("/workspace/config.json"))  # env vars, URLs, etc.

    # 2. Set environment variables (challenge service URLs, etc.)
    for key, val in config.get("env", {}).items():
        os.environ[key] = val

    results = []

    for test in tests:
        result = {"test_id": test["id"], "name": test["name"]}
        start = time.time()

        try:
            # 3. Execute user code in a subprocess with timeout
            #    Run as: python /workspace/solution.py
            #    Pass test input via stdin or env vars
            proc = subprocess.run(
                ["python", "/workspace/solution.py"],
                input=json.dumps(test.get("input", {})),
                capture_output=True, text=True,
                timeout=config["time_limit_seconds"],
                env={**os.environ, "TEST_INPUT": json.dumps(test.get("input", {}))}
            )

            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["exit_code"] = proc.returncode
            result["duration_ms"] = int((time.time() - start) * 1000)

            # 4. Validate based on validation_type
            if test["validation_type"] == "exact_match":
                actual = json.loads(proc.stdout.strip())
                result["passed"] = actual == test["expected"]
            elif test["validation_type"] == "http_validation":
                resp = requests.get(test["validation_endpoint"], params={"test_id": test["id"]})
                validation = resp.json()
                result["passed"] = validation["passed"]
                result["message"] = validation.get("message", "")
            elif test["validation_type"] == "custom_script":
                # Run validation script
                ...

        except subprocess.TimeoutExpired:
            result["passed"] = False
            result["error"] = "Time Limit Exceeded"
        except Exception as e:
            result["passed"] = False
            result["error"] = str(e)

        results.append(result)

    # 5. POST results back to API server
    callback_url = os.environ["CALLBACK_URL"]
    requests.post(callback_url, json={
        "submission_id": os.environ["SUBMISSION_ID"],
        "status": "passed" if all(r["passed"] for r in results) else "failed",
        "results": results
    })

if __name__ == "__main__":
    main()
```

---

## 7. Repository Structure

```
practicode/
├── Makefile                        # Primary entry point
├── README.md
├── SPEC.md                         # This document
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── ProblemList.tsx
│   │   │   └── ProblemWorkspace.tsx
│   │   ├── components/
│   │   │   ├── CodeEditor.tsx       # Monaco wrapper
│   │   │   ├── ProblemDescription.tsx
│   │   │   ├── TestRunner.tsx
│   │   │   └── ResultsPanel.tsx
│   │   ├── api/
│   │   │   └── client.ts            # API client (fetch wrapper)
│   │   └── types/
│   │       └── index.ts
│   └── public/
│
├── api-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                     # DB migrations
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                  # FastAPI app
│   │   ├── config.py
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── schemas.py               # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── problems.py
│   │   │   ├── submissions.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── executor_client.py   # Calls code-executor service
│   │   │   └── problem_loader.py    # Loads problems from YAML into DB
│   │   └── db.py                    # Database connection
│   └── tests/
│
├── code-executor/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  # FastAPI app
│   │   ├── job_manager.py           # K8s Job creation/monitoring
│   │   └── templates.py             # Job YAML templates
│   └── tests/
│
├── runner-python/
│   ├── Dockerfile
│   ├── requirements.txt             # requests, Pillow, numpy, pandas, etc.
│   └── app/
│       ├── harness.py
│       ├── validators/
│       │   ├── exact_match.py
│       │   ├── http_validator.py
│       │   └── custom_script.py
│       └── utils.py
│
├── challenges/
│   ├── oauth-mock/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── k8s/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   ├── data-api/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── k8s/
│   └── image-service/
│       ├── Dockerfile
│       ├── main.py
│       └── k8s/
│
├── problems/                        # Problem definitions (seed data)
│   ├── 001-oauth-token-fetch/
│   │   ├── problem.yaml
│   │   ├── description.md
│   │   ├── api-docs.md
│   │   ├── starter.py
│   │   ├── solution.py
│   │   └── tests.json
│   ├── 002-data-transform-pipeline/
│   └── 003-image-resize-pipeline/
│
├── k8s/                             # Cluster-level Kubernetes manifests
│   ├── namespaces.yaml
│   ├── rbac.yaml
│   ├── network-policies.yaml        # Optional
│   ├── resource-quotas.yaml
│   ├── postgres/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── init-job.yaml            # Runs migrations + seeds problems
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── api-server/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── serviceaccount.yaml
│   └── code-executor/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── serviceaccount.yaml
│
├── scripts/
│   ├── setup-kind.sh                # Create Kind cluster with config
│   ├── build-images.sh              # Build all Docker images
│   ├── load-images.sh               # Load images into Kind
│   ├── deploy.sh                    # Apply all K8s manifests
│   ├── seed-problems.sh             # Load problems into DB
│   ├── port-forward.sh              # Port-forward frontend to localhost
│   └── teardown.sh                  # Delete Kind cluster
│
└── kind-config.yaml                 # Kind cluster configuration
```

---

## 8. Makefile Targets

```makefile
.PHONY: setup teardown build deploy seed status logs port-forward clean

# One-command full setup
setup: cluster build load deploy seed port-forward
	@echo "PractiCode is running at http://localhost:3000"

# Individual targets
cluster:                             # Create Kind cluster
	kind create cluster --name practicode --config kind-config.yaml

build:                               # Build all Docker images
	docker build -t practicode-frontend:latest ./frontend
	docker build -t practicode-api-server:latest ./api-server
	docker build -t practicode-code-executor:latest ./code-executor
	docker build -t practicode-runner-python:latest ./runner-python
	docker build -t practicode-oauth-mock:latest ./challenges/oauth-mock
	docker build -t practicode-data-api:latest ./challenges/data-api
	docker build -t practicode-image-service:latest ./challenges/image-service

load:                                # Load images into Kind
	kind load docker-image --name practicode \
		practicode-frontend:latest \
		practicode-api-server:latest \
		practicode-code-executor:latest \
		practicode-runner-python:latest \
		practicode-oauth-mock:latest \
		practicode-data-api:latest \
		practicode-image-service:latest

deploy:                              # Apply K8s manifests
	kubectl apply -f k8s/namespaces.yaml
	kubectl apply -f k8s/rbac.yaml
	kubectl apply -f k8s/resource-quotas.yaml
	kubectl apply -f k8s/postgres/
	kubectl wait --for=condition=ready pod -l app=postgres -n practicode --timeout=120s
	kubectl apply -f k8s/api-server/
	kubectl apply -f k8s/code-executor/
	kubectl apply -f k8s/frontend/
	kubectl apply -f challenges/oauth-mock/k8s/
	kubectl apply -f challenges/data-api/k8s/
	kubectl apply -f challenges/image-service/k8s/

seed:                                # Load problems into database
	kubectl wait --for=condition=ready pod -l app=api-server -n practicode --timeout=120s
	./scripts/seed-problems.sh

port-forward:                        # Expose frontend to localhost
	@echo "Starting port-forward..."
	kubectl port-forward svc/frontend-svc -n practicode 3000:80 &

status:                              # Show cluster status
	kubectl get pods -A
	kubectl get svc -A

logs:                                # Tail logs for a specific service
	kubectl logs -f deployment/$(SVC) -n practicode

teardown:                            # Destroy everything
	kind delete cluster --name practicode

clean: teardown                      # Alias
```

---

## 9. Kind Cluster Configuration

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: practicode
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080          # NodePort for frontend (fallback)
        hostPort: 30080
        protocol: TCP
  - role: worker                      # Worker node for execution Jobs
    labels:
      node-role: executor
```

---

## 10. Starter Problem Set

Implement these three problems to validate the platform:

### Problem 001: OAuth Token Fetch & Data Retrieval

**Difficulty**: Medium

**Description**: An OAuth2 server is running. You need to: (1) obtain an access token using client credentials, (2) use that token to fetch a list of items from a data API, (3) transform the items (filter, map, aggregate), and (4) POST the results back to the data API.

**Services Used**: `oauth-mock`, `data-api`

**Skills Tested**: HTTP requests, OAuth2 client credentials flow, JSON manipulation, error handling.

### Problem 002: Data Transform Pipeline

**Difficulty**: Easy

**Description**: A REST API serves a paginated list of records. You need to: (1) fetch all pages, (2) clean and normalize the data (handle nulls, standardize dates, deduplicate), and (3) POST a summary report to the API.

**Services Used**: `data-api`

**Skills Tested**: Pagination handling, data cleaning, aggregation.

### Problem 003: Image Processing Pipeline

**Difficulty**: Hard

**Description**: An image service serves a list of source images. For each image: (1) download it, (2) resize to 256x256, (3) convert to grayscale, (4) add a 2px red border, and (5) upload the result back. The service validates pixel-level correctness.

**Services Used**: `image-service`

**Skills Tested**: Image I/O, Pillow library, batch processing, binary data handling.

---

## 11. Development Workflow for Adding New Problems

1. Create a new directory under `problems/` with the standard file structure.
2. Write `problem.yaml`, `description.md`, `api-docs.md`, `starter.py`, `solution.py`, and `tests.json`.
3. If the problem needs a new challenge service, create it under `challenges/`, build its image, and add K8s manifests.
4. If the problem reuses existing challenge services with different config, define the config overrides in `services.yaml`.
5. Run `make seed` to reload problems into the database.
6. Test by solving the problem yourself with the reference solution.

---

## 12. Future Extensibility

These are NOT in scope for v1 but the architecture should not preclude them:

- **Go execution environment**: Add `runner-golang/` image with Go toolchain. The Code Executor spawns Jobs with the Go runner image when `language: "go"`. The harness pattern is the same.
- **Additional languages**: Same pattern — new runner image per language.
- **Timer / Contest mode**: Frontend timer, submission locking after time expires.
- **Difficulty progression**: Track solve rate per user, suggest next problems.
- **WebSocket for real-time updates**: Replace SSE polling with WebSocket connections.
- **Problem versioning**: Support multiple versions of a problem with different test suites.
- **Custom Kubernetes resources**: If problems require databases (Redis, MySQL), define them as additional challenge services.
- **Multi-file submissions**: Support submissions with multiple files (e.g., `main.py` + `utils.py`).

---

## 13. Prerequisites & Dependencies

The user's machine needs:

| Tool | Version | Purpose |
|---|---|---|
| Docker | 24+ | Container runtime |
| Kind | 0.20+ | Local K8s cluster |
| kubectl | 1.28+ | K8s CLI |
| make | any | Build orchestration |
| Node.js | 20+ | Frontend build (during `docker build`) |
| Python | 3.12+ | Only needed for local development outside cluster |

---

## 14. Key Design Decisions & Rationale

**Why Kind over Docker Compose?**
Docker Compose could work for a simpler version, but Kind gives us: real K8s Jobs for isolated code execution, RBAC and network policies for security, namespace isolation, resource quotas, and a realistic environment that mirrors how CodeSignal actually works. It also makes adding new challenge services trivial (just another Deployment+Service).

**Why spawn K8s Jobs instead of running code in the executor process?**
Isolation. Each submission runs in its own pod with resource limits, its own network identity, and automatic cleanup. A misbehaving submission can't crash the executor or affect other submissions. It also makes multi-language support trivial — just swap the runner image.

**Why FastAPI for backend services?**
Lightweight, async-native, auto-generates OpenAPI docs (useful for challenge service documentation), excellent Pydantic integration for data validation. Well-suited for all the small HTTP services in this architecture.

**Why PostgreSQL over SQLite?**
Running in K8s, we want a proper database service. PostgreSQL also gives us JSONB columns (excellent for flexible test case and result storage), array types for tags, and is the standard choice for production-like environments.

**Why pre-load runner images into Kind?**
Kind clusters can't pull from Docker Hub by default (they run in their own Docker network). Pre-loading with `kind load docker-image` ensures images are available instantly without configuring a registry. For a local development tool, this is the simplest approach.

---

## 15. Security Considerations

Even though this is local-only, good isolation practices prevent accidental damage:

- **Execution Jobs run with `runAsNonRoot: true`** and a non-root user in the runner image.
- **No privileged containers** anywhere in the cluster.
- **Resource limits on every pod** to prevent fork bombs or memory exhaustion from killing the host machine.
- **`activeDeadlineSeconds` on Jobs** as a hard timeout backstop.
- **Network policies** (optional but recommended) prevent execution Jobs from reaching the internet or the database.
- **No `hostPath` mounts** in execution Jobs.
- **RBAC**: The code-executor ServiceAccount can only manage resources in the `executor` namespace. Execution Jobs use a minimal ServiceAccount with no K8s API permissions.
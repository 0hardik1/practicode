# AGENTS.md

## Purpose

This repository is a local-first coding assessment platform. Agents working here should optimize for a fast local loop, keep the Kind deployment flow working, and preserve the existing problem bundle format.

## Repo Map

- `frontend/`: React + Vite UI with Monaco, file explorer, run/test/submit UX, and Python IntelliSense/hover support.
- `api-server/`: FastAPI app for problem catalog, file APIs, submissions, and Python editor assistance.
- `code-executor/`: execution service that prepares jobs for the runner.
- `runner-python/`: Python harness and validators that execute user code.
- `challenges/`: mock external services used by practical problems.
- `problems/`: source-of-truth problem bundles.
- `k8s/`: cluster manifests for the core stack.
- `scripts/`: build, load, deploy, seed, and port-forward helpers used by `make`.

## Default Workflow

- Use `make setup` for the complete setup. It runs `make clean` first, then installs dependencies, rebuilds Kind, deploys the stack, seeds problems, and starts port-forwards.
- Use `make help` to discover supported commands.
- Use `make verify` for quick syntax-only verification of the Python services.
- If you change frontend code, a reliable verification path is:
  - `docker build -f frontend/Dockerfile -t practicode-frontend:latest ./frontend`
- If you change API server packaging or dependencies, verify with:
  - `docker build -f api-server/Dockerfile -t practicode-api-server:latest .`

## Runtime Assumptions

- The primary UI is `http://localhost:3000`.
- API docs are at `http://localhost:8000/docs`.
- Problems are seeded from `problems/`.
- The cluster version uses files baked into the API server image, so new or edited problem bundles on disk do not reach Kind until the API image is rebuilt, loaded, redeployed, and reseeded.
- The local API server also seeds problems on startup.

## Coding Notes

- Python is the only supported runnable language today.
- If you add a new Python runtime dependency for user solutions, add it to `runner-python/requirements.txt`.
- The API server image installs `runner-python/requirements.txt` too, so editor IntelliSense/hover can see the same installed Python packages as the runner.
- Challenge services are not auto-discovered. If you add a new one, you must wire it into the build/deploy/load scripts.

## Supported Test Validation Types

- `exact_match`: compares stdout to `expected`, with a fallback that allows debug logs before the final output line.
- `program_output`: used for ad-hoc `Run`; always passes and returns raw/coerced stdout.
- `http_validation`: calls a validation endpoint with `test_id`.
- `custom_script`: runs a validator script inside the problem workspace.

## How To Add A New Problem

### 1. Create a new problem directory

Follow the existing convention:

- `problems/004-my-problem/`

Keep these aligned when possible:

- directory name
- `id` in `problem.yaml`
- `slug` in `problem.yaml`

### 2. Add the required files

At minimum, add:

- `problem.yaml`
- `description.md`
- `starter.py`
- `solution.py`
- `tests.json`

Optional, but commonly used:

- `api-docs.md`
- `services.yaml`
- `fixtures/`
- `assets/`
- validator scripts referenced by `custom_script`

### 3. Use the expected `problem.yaml` shape

The loader in `api-server/app/services/problem_loader.py` expects this structure:

```yaml
id: "004-my-problem"
slug: "my-problem"
title: "My Problem"
difficulty: "medium"
tags: ["api", "json"]
time_limit_seconds: 30
memory_limit_mb: 256
description_file: "description.md"
api_docs_file: "api-docs.md"
starter_code:
  python: "starter.py"
test_cases_file: "tests.json"
services_file: "services.yaml"
```

Notes:

- `starter_code.python` is what the UI/editor runs today.
- `api_docs_file` and `services_file` are optional.
- The loader reads tests from `test_cases_file` and stores extra test fields as validation config.

### 4. Add `tests.json`

Tests are JSON objects with fields like:

```json
[
  {
    "id": "my-problem-visible",
    "name": "Visible sample",
    "input": {},
    "expected": {"status": "ok"},
    "is_hidden": false,
    "is_sample": true,
    "validation_type": "exact_match"
  }
]
```

Guidance:

- Include at least one visible sample test so `Run Tests` and the problem description have something to show.
- Add hidden tests for `Submit`.
- Use `exact_match` for plain stdout/JSON results.
- Use `http_validation` when the user code interacts with a mock service and the real assertion should happen via that service.
- Use `custom_script` when the validation logic is too specific for the built-in validators.

### 5. Add `services.yaml` if the problem needs external services

Use the existing shape:

```yaml
services:
  - name: my-service
    local_url_env: MY_SERVICE_URL
    local_url: "http://localhost:9004"
    service_url_env: MY_SERVICE_URL
    service_url: "http://my-service.challenges.svc.cluster.local:8000"
    env:
      SOME_SETTING: "value"
```

What this does:

- local runs get `local_url`
- cluster runs get `service_url`
- shared `env` entries are injected in both environments

### 6. If the problem needs a new challenge service, wire the whole stack

Adding `services.yaml` alone is not enough. You also need to:

- create `challenges/<service-name>/`
- add its `Dockerfile`, app code, requirements, and `k8s/` manifests
- update `scripts/build-images.sh`
- update `scripts/load-images.sh`
- update `scripts/deploy.sh`
- optionally add a local `make run-...` target in `Makefile`

If the new problem depends on a new Python library, add that dependency to:

- `runner-python/requirements.txt`

That is enough for both execution and API-side Python IntelliSense, because the API image installs the runner requirements too.

### 7. Validate the new problem

For local development:

- restart the local API server or run `make seed-local`

For the Kind deployment:

- use `make setup` for the complete setup path
- use `make build load deploy seed port-forward` only when you intentionally want a shorter refresh loop on an existing cluster

For quick sanity checks:

- `make verify`
- open `http://localhost:3000`
- open `http://localhost:8000/docs`

### 8. Keep problem assets inside the problem directory

The file explorer in the UI exposes files directly from the problem bundle, so place user-visible resources under the same problem directory:

- `fixtures/` for sample JSON/input payloads
- `assets/` for images or reference files
- markdown notes when they help the exercise

## Common Pitfalls

- Forgetting `test_cases_file` or `description_file` in `problem.yaml`.
- Adding a new problem on disk but not rebuilding/redeploying the API server for Kind.
- Adding a new challenge service without updating `build-images.sh`, `load-images.sh`, and `deploy.sh`.
- Adding a new runtime package but not updating `runner-python/requirements.txt`.
- Creating a non-Python starter when the platform currently only runs Python solutions.

## Safe Defaults For Agents

- Prefer changing the smallest number of files that solves the task.
- Run targeted verification after edits, not just broad guesses.
- Preserve existing problem IDs, slugs, and service URLs unless the task explicitly requires changing them.
- When touching problem bundles, check both the bundle files and the deployment wiring if services are involved.

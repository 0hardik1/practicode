# PractiCode

PractiCode is a local-first coding assessment platform for practical engineering exercises. This repository currently contains the first backend implementation slice:

- `api-server/`: problem catalog, submission tracking, and executor callbacks
- `code-executor/`: local execution orchestration with a spec-aligned execution payload
- `runner-python/`: execution harness and validators
- `challenges/`: mock services used by the starter problems
- `problems/`: seeded problem definitions

## Current State

The implementation is intentionally local-first for the first pass:

- the API server defaults to SQLite so it can run without PostgreSQL
- the code executor defaults to a local subprocess runner instead of Kubernetes Jobs
- service configuration keeps the structure needed for the later Kind/Kubernetes rollout

The next major slice is the browser UI and cluster manifests that wire these pieces together inside Kind.

## Setup

The repository now has a single bootstrap command for the current stack:

```bash
make setup
```

That command will:

- verify local prerequisites (`docker`, `kind`, `kubectl`, `python3`, `make`)
- create `.venv` and install all Python requirements
- create the `practicode` Kind cluster if needed
- build and load all backend images
- apply Kubernetes manifests
- seed all problems
- start background port-forwards for:
  - the UI at `http://localhost:3000`
  - the API docs at `http://localhost:8000/docs`

Run `make help` to see the full list of supported commands.

## Local Development

If you want to run the services directly outside Kind, use separate shells:

```bash
make run-oauth
make run-data-api
make run-image-service
make run-executor
make run-api
```

The API server seeds problems from `problems/` on startup.

## Current Kind Scope

`make setup` provisions the current implementation on Kind:

- frontend
- API server
- code executor
- oauth mock
- data API
- image service

The browser frontend and Postgres-backed cluster deployment from the full spec are not implemented yet.

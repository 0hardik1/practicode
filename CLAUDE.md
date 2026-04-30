# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PractiCode is a local-first coding assessment platform. It runs as a small Kind cluster: a React/Monaco frontend talks to a FastAPI API server, which orchestrates a code-executor service that shells out to a Python runner harness, against problem-specific mock challenge services.

`AGENTS.md` is the canonical agent guide for this repo (problem bundle authoring, validation types, common pitfalls). Read it before authoring or editing problems.

## Common Commands

The local loop is `make`-driven. Run `make help` for the full list.

- `make setup` — full bootstrap (clean → install → Kind cluster → build → load → deploy → seed → port-forward). UI on `:3000`, API docs on `:8000/docs`.
- `make setup-from-scratch` — same as `setup` but skips the initial `clean`/teardown.
- `make verify` — syntax-only `compileall` over `api-server/app`, `code-executor/app`, `runner-python/app`, `challenges`. Fastest gate after Python edits.
- `make seed-local` — reseeds problems into the local SQLite DB (`practicode.db`) without touching Kind.
- `make stop-port-forward` / `make teardown` — stop forwards / delete the cluster.

Local service runners (each uses `.venv` and `uvicorn --reload`):

- `make run-api` (`:8000`), `make run-executor` (`:8080`)
- `make run-oauth` (`:9001`), `make run-data-api` (`:9002`), `make run-image-service` (`:9003`)

Frontend (under `frontend/`): `npm run dev` (Vite on `:5173`), `npm run build` (runs `tsc -b` then `vite build`). There is no test runner wired up; verification for frontend changes is `docker build -f frontend/Dockerfile -t practicode-frontend:latest ./frontend`.

There is no Python test suite in this repo; `make verify` is the only Python check, and there is no linter configured.

## Architecture

Request path for a submission: **frontend → api-server → code-executor → runner-python → (optional) challenge services**, with results posted back to the API server via callback.

### api-server (`api-server/app`)

FastAPI app, async SQLAlchemy over SQLite. Entry: `main.py` registers `routers/problems.py` and `routers/submissions.py`. On startup it calls `services.problem_loader.seed_problems` against `settings.problems_dir`. Key services: `executor_client.py` (dispatches jobs to code-executor), `problem_loader.py` (parses `problem.yaml` + `tests.json` into DB rows — this is the source of truth for the bundle schema), `python_intellisense.py` (powers Monaco completion/hover via Jedi). Settings come from `config.py` with `PRACTICODE_` env prefix.

### code-executor (`code-executor/app`)

Thin FastAPI wrapper. `LocalJobManager` (`job_manager.py`) materializes a workspace under `tempfile.mkdtemp(...)`, copies starter/solution files plus problem assets, injects challenge service URLs as env vars, and `asyncio.create_subprocess_exec`s the Python runner. Status is held in an in-process `ExecutionStore` (not durable; results go back to the API via `CALLBACK_URL`).

### runner-python (`runner-python/app`)

`harness.py` is the entry point inside the executor's subprocess. For each test case it `subprocess.run`s the user solution with `WORKSPACE_DIR`/`TEST_INPUT` env, then dispatches to one of four validators (`validators/`):

- `exact_match` — stdout vs `expected` (with debug-line fallback)
- `program_output` — always passes; for ad-hoc Run
- `http_validation` — POSTs `test_id` to `validation_endpoint` on a challenge service
- `custom_script` — runs `validator_script` from the workspace

User-installable Python deps live in `runner-python/requirements.txt`. The api-server image installs the same file so editor IntelliSense matches the runner environment — keep them in lockstep.

### challenges/ (mock external services)

`oauth-mock`, `data-api`, `image-service` are independent FastAPI apps with their own `Dockerfile` + k8s manifests. They are **not** auto-discovered. Adding a new one requires editing `scripts/build-images.sh`, `scripts/load-images.sh`, and `scripts/deploy.sh` plus k8s manifests under `k8s/` (and optionally a `make run-...` target).

### problems/ (problem bundles)

Each directory is a self-contained bundle: `problem.yaml`, `description.md`, `starter.py`, `solution.py`, `tests.json`, optional `services.yaml`/`api-docs.md`/`fixtures/`/`assets/`. Schema is enforced by `api-server/app/services/problem_loader.py` — see AGENTS.md for the exact YAML/JSON shapes. `services.yaml` carries dual `local_url`/`service_url` so the same bundle works under `make run-*` and inside Kind.

### frontend (`frontend/src`)

Vite + React 18 + TypeScript. Single-page workspace UI: `App.tsx` composes `Sidebar`, `ProblemPanel`, `ProblemFilesPanel`, `EditorPane`, `ResultsPanel`. All API calls go through `api/client.ts`. Monaco IntelliSense is wired through `pythonIntellisense.ts`, which calls the api-server's Python completion/hover endpoints.

## Critical Coupling To Remember

- **Bundle changes don't reach Kind on disk edit alone.** The api-server image bakes `problems/` in, so editing a problem requires `make build load deploy seed` (or `make setup`) before it shows up in the cluster. Local `make run-api` reseeds on startup, and `make seed-local` reseeds the local DB.
- **New runtime Python deps go in `runner-python/requirements.txt`** — that single file feeds both the runner and api-server IntelliSense.
- **Adding a challenge service is a multi-file change**: `challenges/<name>/`, k8s manifests, `build-images.sh`, `load-images.sh`, `deploy.sh`. `services.yaml` alone is not enough.
- **Python is the only supported user-runtime today.** `starter_code.python` in `problem.yaml` is what the editor and runner consume.

## Settings & Conventions

- All service settings use the `PRACTICODE_` env prefix (e.g. `PRACTICODE_DATABASE_URL`, `PRACTICODE_EXECUTOR_BASE_URL`).
- SQLite DB file `practicode.db` and `.venv/` are gitignored; don't commit them.
- The Kind cluster name is `practicode` (override via `CLUSTER_NAME`).

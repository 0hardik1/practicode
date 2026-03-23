SHELL := /bin/bash
.DEFAULT_GOAL := help

CLUSTER_NAME ?= practicode
VENV_DIR ?= .venv
VENV_BIN := $(CURDIR)/$(VENV_DIR)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
UVICORN := $(VENV_BIN)/uvicorn
PYTHONPYCACHEPREFIX ?= /tmp/practicode-pycache

.PHONY: help setup setup-from-scratch check-prereqs venv install cluster build load deploy seed \
	port-forward stop-port-forward status teardown clean verify seed-local \
	run-api run-executor run-oauth run-data-api run-image-service

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Run clean first, then install dependencies, rebuild the cluster, deploy services, seed problems, and expose the UI and API
	@$(MAKE) clean
	@$(MAKE) setup-from-scratch

setup-from-scratch: check-prereqs install cluster build load deploy seed port-forward ## Internal target used by setup after clean
	@printf 'PractiCode UI is available at http://localhost:3000\n'
	@printf 'PractiCode API docs are available at http://localhost:8000/docs\n'

check-prereqs: ## Verify required local tooling is installed and Docker is running
	./scripts/check-prerequisites.sh

venv: ## Create the local Python virtual environment
	test -d "$(VENV_DIR)" || python3 -m venv "$(VENV_DIR)"

install: venv ## Install all local Python dependencies into .venv
	"$(PIP)" install --upgrade pip setuptools wheel
	"$(PIP)" install -r requirements-dev.txt

cluster: ## Create the Kind cluster if it does not already exist
	./scripts/setup-kind.sh "$(CLUSTER_NAME)"

build: ## Build all Docker images needed by the current stack
	./scripts/build-images.sh

load: ## Load built Docker images into the Kind cluster
	./scripts/load-images.sh "$(CLUSTER_NAME)"

deploy: ## Apply Kubernetes manifests and wait for rollouts
	./scripts/deploy.sh

seed: ## Seed all problems into the deployed API server
	./scripts/seed-problems.sh

port-forward: ## Start background port-forwards for the frontend and API services
	./scripts/port-forward.sh

stop-port-forward: ## Stop the background frontend and API port-forwards
	./scripts/stop-port-forward.sh

status: ## Show pods and services across all namespaces
	kubectl get pods -A
	kubectl get svc -A

teardown: stop-port-forward ## Delete the Kind cluster
	kind delete cluster --name "$(CLUSTER_NAME)"

clean: teardown ## Alias for teardown

verify: ## Run a syntax-only verification pass over the Python services
	env PYTHONPYCACHEPREFIX="$(PYTHONPYCACHEPREFIX)" python3 -m compileall -q api-server/app
	env PYTHONPYCACHEPREFIX="$(PYTHONPYCACHEPREFIX)" python3 -m compileall -q code-executor/app
	env PYTHONPYCACHEPREFIX="$(PYTHONPYCACHEPREFIX)" python3 -m compileall -q runner-python/app
	env PYTHONPYCACHEPREFIX="$(PYTHONPYCACHEPREFIX)" python3 -m compileall -q challenges

seed-local: install ## Seed problems into the local SQLite database
	cd api-server && "$(PYTHON)" -m app.seed

run-api: install ## Run the API server locally on port 8000
	cd api-server && "$(UVICORN)" app.main:app --reload --port 8000

run-executor: install ## Run the code executor locally on port 8080
	cd code-executor && "$(UVICORN)" app.main:app --reload --port 8080

run-oauth: install ## Run the OAuth mock locally on port 9001
	cd challenges/oauth-mock && "$(UVICORN)" main:app --reload --port 9001

run-data-api: install ## Run the data API locally on port 9002
	cd challenges/data-api && "$(UVICORN)" main:app --reload --port 9002

run-image-service: install ## Run the image service locally on port 9003
	cd challenges/image-service && "$(UVICORN)" main:app --reload --port 9003

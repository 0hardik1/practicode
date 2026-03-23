#!/usr/bin/env bash
set -euo pipefail

docker build -f api-server/Dockerfile -t practicode-api-server:latest .
docker build -f code-executor/Dockerfile -t practicode-code-executor:latest .
docker build -f frontend/Dockerfile -t practicode-frontend:latest ./frontend
docker build -f runner-python/Dockerfile -t practicode-runner-python:latest ./runner-python
docker build -f challenges/oauth-mock/Dockerfile -t practicode-oauth-mock:latest ./challenges/oauth-mock
docker build -f challenges/data-api/Dockerfile -t practicode-data-api:latest ./challenges/data-api
docker build -f challenges/image-service/Dockerfile -t practicode-image-service:latest ./challenges/image-service

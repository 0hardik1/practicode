#!/usr/bin/env bash
set -euo pipefail

cluster_name="${1:-practicode}"
images=(
  practicode-api-server:latest
  practicode-code-executor:latest
  practicode-frontend:latest
  practicode-runner-python:latest
  practicode-oauth-mock:latest
  practicode-data-api:latest
  practicode-image-service:latest
)

for image in "${images[@]}"; do
  kind load docker-image --name "${cluster_name}" "${image}"
done

#!/usr/bin/env bash
set -euo pipefail

kubectl rollout status deployment/api-server -n practicode --timeout=180s >/dev/null
kubectl exec -n practicode deployment/api-server -- python -m app.seed


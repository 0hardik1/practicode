#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/resource-quotas.yaml
kubectl apply -f k8s/api-server
kubectl apply -f k8s/code-executor
kubectl apply -f k8s/frontend
kubectl apply -f challenges/oauth-mock/k8s
kubectl apply -f challenges/data-api/k8s
kubectl apply -f challenges/image-service/k8s

kubectl rollout restart deployment/oauth-mock -n challenges
kubectl rollout restart deployment/data-api -n challenges
kubectl rollout restart deployment/image-service -n challenges
kubectl rollout restart deployment/code-executor -n practicode
kubectl rollout restart deployment/api-server -n practicode
kubectl rollout restart deployment/frontend -n practicode

kubectl rollout status deployment/oauth-mock -n challenges --timeout=180s
kubectl rollout status deployment/data-api -n challenges --timeout=180s
kubectl rollout status deployment/image-service -n challenges --timeout=180s
kubectl rollout status deployment/code-executor -n practicode --timeout=180s
kubectl rollout status deployment/api-server -n practicode --timeout=180s
kubectl rollout status deployment/frontend -n practicode --timeout=180s

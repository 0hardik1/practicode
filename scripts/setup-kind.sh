#!/usr/bin/env bash
set -euo pipefail

cluster_name="${1:-practicode}"

if kind get clusters | grep -qx "${cluster_name}"; then
  printf 'Kind cluster "%s" already exists.\n' "${cluster_name}"
  exit 0
fi

kind create cluster --name "${cluster_name}" --config kind-config.yaml


#!/usr/bin/env bash
set -euo pipefail

start_forward() {
  local name="$1"
  local service="$2"
  local ports="$3"
  local pid_file="/tmp/practicode-${name}-port-forward.pid"
  local log_file="/tmp/practicode-${name}-port-forward.log"

  if [[ -f "${pid_file}" ]]; then
    local existing_pid
    existing_pid="$(cat "${pid_file}")"
    if kill -0 "${existing_pid}" >/dev/null 2>&1; then
      return 0
    fi
    rm -f "${pid_file}"
  fi

  nohup kubectl port-forward -n practicode "svc/${service}" "${ports}" >"${log_file}" 2>&1 &
  echo "$!" >"${pid_file}"
  sleep 2

  if ! kill -0 "$(cat "${pid_file}")" >/dev/null 2>&1; then
    printf 'Failed to start %s port-forward. See %s\n' "${name}" "${log_file}" >&2
    exit 1
  fi
}

start_forward "api" "api-server-svc" "8000:8000"
start_forward "frontend" "frontend-svc" "3000:80"

printf 'Frontend available at http://localhost:3000\n'
printf 'API docs available at http://localhost:8000/docs\n'

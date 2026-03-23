#!/usr/bin/env bash
set -euo pipefail

stop_forward() {
  local name="$1"
  local pid_file="/tmp/practicode-${name}-port-forward.pid"

  if [[ ! -f "${pid_file}" ]]; then
    return 0
  fi

  local pid
  pid="$(cat "${pid_file}")"
  if kill -0 "${pid}" >/dev/null 2>&1; then
    kill "${pid}"
  fi
  rm -f "${pid_file}"
}

stop_forward "frontend"
stop_forward "api"
printf 'Stopped PractiCode port-forwards.\n'

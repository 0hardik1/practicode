#!/usr/bin/env bash
set -euo pipefail

required_commands=(docker kind kubectl python3 make)
missing=()

for command_name in "${required_commands[@]}"; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    missing+=("${command_name}")
  fi
done

if ((${#missing[@]} > 0)); then
  printf 'Missing required tools: %s\n' "${missing[*]}" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  printf 'Docker is installed but the daemon is not reachable.\n' >&2
  exit 1
fi

printf 'Prerequisite check passed.\n'


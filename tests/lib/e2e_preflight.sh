#!/usr/bin/env bash

# Shared preflight helpers for e2e shell suites.
# Exit code 2 means "blocked / prerequisites missing".

_e2e_blocked() {
  echo "⛔ BLOCKED: $1"
  exit 2
}

e2e_require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    _e2e_blocked "Required command '$cmd' is not available"
  fi
}

e2e_require_http() {
  local name="$1"
  local url="$2"
  if ! curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
    _e2e_blocked "$name is not reachable at $url"
  fi
}

e2e_detect_container() {
  local name
  for name in "$@"; do
    if docker ps --format '{{.Names}}' | grep -x "$name" >/dev/null 2>&1; then
      echo "$name"
      return 0
    fi
  done
  return 1
}

e2e_require_container() {
  local label="$1"
  shift
  local found
  found="$(e2e_detect_container "$@" || true)"
  if [ -z "$found" ]; then
    _e2e_blocked "$label container not running (checked: $*)"
  fi
  echo "$found"
}

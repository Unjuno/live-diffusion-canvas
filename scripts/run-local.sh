#!/usr/bin/env bash
set -euo pipefail

backend_pid=""
cleanup() {
  if [[ -n "$backend_pid" ]]; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

runtime_url="${VITE_RUNTIME_URL:-http://127.0.0.1:8000}"
if curl --silent --fail --max-time 2 "$runtime_url/runtime/health" >/dev/null 2>&1; then
  echo "Using existing runtime at $runtime_url" >&2
else
  echo "Starting local runtime" >&2
  ./scripts/run-backend.sh &
  backend_pid=$!
  for _ in {1..60}; do
    if curl --silent --fail --max-time 2 "$runtime_url/runtime/health" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if ! curl --silent --fail --max-time 2 "$runtime_url/runtime/health" >/dev/null 2>&1; then
    echo "Runtime did not become ready at $runtime_url" >&2
    exit 1
  fi
fi

exec npm run dev -- --host 127.0.0.1

#!/usr/bin/env bash
set -euo pipefail

runtime_url="${RUNTIME_URL:-http://127.0.0.1:8000}"
health="$(curl --silent --show-error --fail --max-time 5 "$runtime_url/runtime/health?model=segmind%2Ftiny-sd")" || {
  echo "Runtime is not reachable at $runtime_url" >&2
  exit 1
}
echo "$health"
if [[ "$health" != *'"status":"ok"'* ]]; then
  echo "Runtime health status is not ok" >&2
  exit 1
fi
if [[ "${REQUIRE_REAL:-0}" == "1" && "$health" != *'"runtime":"diffusers"'* ]]; then
  echo "A real Diffusers runtime is required but the health response is not real" >&2
  exit 1
fi
if [[ "${REQUIRE_REAL:-0}" == "1" && "$health" != *'"modelReady":true'* ]]; then
  echo "The requested real model is not ready" >&2
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail
if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Create the environment first: python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000

#!/usr/bin/env bash
set -euo pipefail
if [[ -x .venv-real/bin/uvicorn ]]; then
  echo "Starting real TinySD/Diffusers runtime (.venv-real)" >&2
  DIFFUSION_REAL="${DIFFUSION_REAL:-1}" PYTHONPATH=. \
    .venv-real/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
  exit 0
fi

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Create the real environment first: .venv-real/bin/pip install -r backend/requirements-real.txt" >&2
  echo "Or create the mock environment: python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

echo "Starting mock runtime (.venv). Use .venv-real for TinySD/Diffusers." >&2
DIFFUSION_REAL="${DIFFUSION_REAL:-0}" .venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000

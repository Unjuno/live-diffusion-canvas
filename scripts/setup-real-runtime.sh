#!/usr/bin/env bash
set -euo pipefail

python_command="${PYTHON_COMMAND:-python3.12}"
environment="${REAL_RUNTIME_ENV:-.venv-real}"

if ! command -v "$python_command" >/dev/null 2>&1; then
  echo "Python executable not found: $python_command" >&2
  echo "Install Python 3.12 or set PYTHON_COMMAND=/path/to/python3.12" >&2
  exit 1
fi

if [[ ! -x "$environment/bin/python" ]]; then
  "$python_command" -m venv "$environment"
fi

"$environment/bin/python" -m pip install --upgrade pip
"$environment/bin/python" -m pip install -r backend/requirements-real.txt

"$environment/bin/python" - <<'PY'
from importlib.util import find_spec
required = ("torch", "diffusers", "transformers", "fastapi", "PIL")
missing = [name for name in required if find_spec(name) is None]
if missing:
    raise SystemExit(f"Runtime setup incomplete; missing: {', '.join(missing)}")
print("Real runtime dependencies are installed.")
PY

echo "Runtime environment ready: $environment" >&2
echo "The model is downloaded on the first real generation request." >&2
echo "Start it with: DIFFUSION_REAL=1 ./scripts/run-backend.sh" >&2

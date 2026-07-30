# Live Diffusion Canvas

Local application for exploring and steering intermediate diffusion states with
Guide Canvas, generated-state intervention, Noise Brush, and snapshots.

## Run locally

```bash
npm install
npm run dev -- --host 127.0.0.1
```

Open the printed Vite URL. Without a runtime server, the UI uses its local
preview path. For the supported stateful API, start the backend in a second
terminal.

For local use with one command, use:

```bash
./scripts/run-local.sh
```

It starts the runtime when needed and cleans it up when the web process exits.

## Verification

```bash
npm test
npm run build
```

The browser-first app is structured so the same React UI can be packaged with Tauri and connected to a local FastAPI/Diffusers runtime. `segmind/tiny-sd` is the configured real local model on Apple MPS; the lightweight mock remains available for fast tests. The Tauri bundle includes the FastAPI source and attempts to start it automatically when a compatible Python environment is available.

## Optional FastAPI runtime

Mock runtime:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
DIFFUSION_REAL=0 PYTHONPATH=. uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Real TinySD/Diffusers runtime (Apple MPS or CPU):

```bash
./scripts/setup-real-runtime.sh
DIFFUSION_REAL=1 PYTHONPATH=. uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Before opening the UI, verify the selected real runtime and model readiness:

```bash
REQUIRE_REAL=1 ./scripts/check-runtime.sh
```

The first real generation may download `segmind/tiny-sd` from Hugging Face and
requires network access and local disk space.

The repository also provides `scripts/run-backend.sh`, which selects the real
environment when `.venv-real` exists and otherwise starts the mock runtime.

When using the packaged macOS app, install the real environment once from the
repository before building or on the target machine:

```bash
./scripts/setup-real-runtime.sh
```

The app searches `DIFFUSION_PYTHON`, the packaged `.venv-real`, and `python3`.
If no usable Diffusers environment is available, the app still opens and the
Mock Runtime remains usable; select TinySD only after the real runtime health
badge reports readiness.

To produce a self-contained macOS app with the current Python environment and
the cached TinySD snapshot embedded, use:

```bash
./scripts/build-macos-full.sh
```

This produces an approximately 1.2 GB app on the current environment. The
runtime and model are stored as archives in the app and unpacked into the
user's application-data directory on first launch.

The runtime exposes `/runtime/health`, `/runtime/session`,
`/runtime/intervention`, `/runtime/finish`, and snapshot endpoints. The health
endpoint is the authoritative check that the selected model is available.

## Regression checks

```bash
npm test -- --run
npm run build
.venv/bin/python -m pytest -q

# while the real backend is running
RUNTIME_URL=http://127.0.0.1:8000 \
  .venv-real/bin/python scripts/regression-real-runtime.py
RUNTIME_URL=http://127.0.0.1:8000 RUNTIME_KIND=tinysd \
  .venv-real/bin/python scripts/regression-midstream-intervention.py
```

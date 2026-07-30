# Local operation

## Mock-only browser mode

```bash
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/` and leave Backend as `Mock Runtime`.

## FastAPI-connected mode

The recommended local entrypoint is:

```bash
./scripts/run-local.sh
```

This starts the runtime and web app together, reuses a healthy runtime already
running on port 8000, and stops a runtime it started when the web process exits.

Terminal 1:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
./scripts/run-backend.sh
```

If `.venv-real` exists, `run-backend.sh` automatically starts the real
TinySD/Diffusers runtime. Set `DIFFUSION_REAL=0` explicitly when the mock
runtime is needed.

Terminal 2:

```bash
./scripts/run-web.sh
```

Select `TinySD · local Diffusers` to use the real local model. The default route uses the stateful mock adapter; the real route is enabled with `DIFFUSION_REAL=1`.

## Real local image generation

On Apple Silicon, bootstrap the Python 3.12 environment for the actual Diffusers model:

```bash
./scripts/setup-real-runtime.sh
REQUIRE_REAL=1 ./scripts/check-runtime.sh
DIFFUSION_REAL=1 PYTHONPATH=. .venv-real/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

The first request downloads and loads `segmind/tiny-sd` (about 1 GB) and can take around two minutes on this M1 Max. Subsequent requests reuse the loaded pipeline. The generated preview is a real PNG returned by FastAPI.

## Verification

```bash
python3 -m compileall -q backend
.venv/bin/pytest backend/test_app.py
npm test
npm run build
```

## Real-runtime regression images

With the real FastAPI runtime running, generate the fixed interaction scenario
and inspect `artifacts/regression/00-contact-sheet.png`:

```bash
.venv-real/bin/python scripts/regression-real-runtime.py
```

The script compares Prompt, Guide, Noise Brush, and continued exploration
against the same-seed baseline. It fails on near-identical interaction output,
dark previews, or a stalled diffusion step.

## Desktop packaging decision

Tauri is the selected desktop shell because the UI is Vite-based and the runtime is local. Run `npm run tauri dev` for desktop development; it uses `scripts/run-local.sh` so the web UI and local FastAPI runtime share the development lifecycle. Run `npm run tauri build` to create a bundle. A production bundle still requires a separately installed Python/Diffusers runtime and model files; the bundle does not claim those assets are included.

For CI/headless macOS packaging, use `npm run tauri build -- --bundles app`. The resulting Apple Silicon app is under `src-tauri/target/release/bundle/macos/`. A full DMG build may require an interactive macOS session because its packaging script invokes AppleScript.

The desktop bundle contains the backend source and attempts to launch it on
startup. It is not a self-contained Python/model installer: set up the target
machine with `setup-real-runtime.sh` (or set `DIFFUSION_PYTHON`) and use
`check-runtime.sh` as the readiness probe before selecting TinySD. If the real
runtime is unavailable, the desktop UI still opens with Mock Runtime.

For a self-contained macOS build from an already prepared machine, use
`scripts/build-macos-full.sh`. It embeds the Python environment and the cached
TinySD snapshot as archives and verifies the packaged runtime on first launch.
The resulting app is about 1.2 GB and the first launch expands the archives
under the app's application-data directory.

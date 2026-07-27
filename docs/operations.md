# Local operation

## Mock-only browser mode

```bash
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/` and leave Backend as `Mock Runtime`.

## FastAPI-connected mode

Terminal 1:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
./scripts/run-backend.sh
```

Terminal 2:

```bash
./scripts/run-web.sh
```

Select `TinySD · local Diffusers` to use the real local model. The default route uses the stateful mock adapter; the real route is enabled with `DIFFUSION_REAL=1`.

## Real local image generation

On Apple Silicon, use the Python 3.12 environment created for the actual Diffusers model:

```bash
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

Tauri is the selected desktop shell because the UI is Vite-based and the runtime is local. Run `npm run tauri dev` for desktop development or `npm run tauri build` to create a bundle. FastAPI remains a separately launched local runtime in this first shell.

For CI/headless macOS packaging, use `npm run tauri build -- --bundles app`. The resulting Apple Silicon app is under `src-tauri/target/release/bundle/macos/`. A full DMG build may require an interactive macOS session because its packaging script invokes AppleScript.

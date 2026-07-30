# Live Diffusion Canvas

Live Diffusion Canvas is a local application for exploring and steering
intermediate diffusion states. It is designed around a rolling diffusion
session, not one-shot prompt-to-final-image generation.

```text
Prompt → Guide Canvas → Generated State → Noise Brush → Snapshot
                                      ↘ Restore / Finish
```

The application keeps the Guide Canvas separate from the Generated Image. A
guide can be drawn or imported, while Noise Brush temporarily rejects a local
solution in the generated state during a press/drag gesture.

## Features

- Stateful Mock Runtime for fast development and demos
- Real local Diffusers/TinySD runtime (`segmind/tiny-sd`)
- Rolling Run / Pause / Resume loop
- Guide Canvas with imported image, drawing layer, and non-destructive erase
- Momentary Noise Brush with adjustable size and rejection strength
- Exploration noise, temperature, CFG, guide influence, seed, and step settings
- IndexedDB-backed Snapshot Timeline
- Snapshot Restore and Finish-from-Snapshot
- Tauri macOS desktop bundle
- Long-horizon and midstream intervention regression experiments

## Requirements

For Mock Runtime development:

- Node.js 22 or newer
- npm

For running the Python test suite locally, install the development requirements:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
```

For the real local model:

- Python 3.12 recommended
- Apple Silicon macOS with MPS, or a compatible CPU environment
- Approximately 1 GB for TinySD model files
- Network access for the first dependency/model download

## Quick start: Mock Runtime

The Mock Runtime requires no Python environment and is the quickest way to
inspect the UI and interaction model.

```bash
npm install
npm run dev -- --host 127.0.0.1
```

Open the printed Vite URL and leave `Backend` set to `Mock Runtime`.

For a single command that starts the web app and a local FastAPI runtime when
needed:

```bash
./scripts/run-local.sh
```

The script reuses a healthy runtime on port 8000. If it starts one itself, it
stops that process when the web process exits.

## Real TinySD runtime

Create the real environment and install the backend dependencies:

```bash
./scripts/setup-real-runtime.sh
```

Start the runtime:

```bash
DIFFUSION_REAL=1 PYTHONPATH=. \
  .venv-real/bin/uvicorn backend.app:app \
  --host 127.0.0.1 --port 8000
```

Check that the real runtime and model are ready before opening the UI:

```bash
REQUIRE_REAL=1 ./scripts/check-runtime.sh
```

The first generation can download and load `segmind/tiny-sd`; subsequent
requests reuse the loaded pipeline. The UI's real-model badge reports the
runtime type, model, device, and readiness state.

The model selector also includes Stable Diffusion 1.5, SD-Turbo, and SDXL
base. Stable Diffusion 1.5 is verified on the 64 GB Apple Silicon machine.
SD-Turbo and SDXL are experimental catalog entries: download their weights
and run the regression suite before treating them as supported.

The catalog and local readiness can be inspected without loading weights:

```bash
curl http://127.0.0.1:8000/runtime/models
```

To test a downloaded model with the same midstream intervention sequence:

```bash
MODEL_ID=stable-diffusion-v1-5/stable-diffusion-v1-5 \
RUNTIME_URL=http://127.0.0.1:8000 RUNTIME_KIND=tinysd \
EXPERIMENT_OUT=artifacts/midstream/sd15 \
.venv-real/bin/python scripts/regression-midstream-intervention.py
```

### Environment overrides

| Variable | Purpose | Default |
| --- | --- | --- |
| `PYTHON_COMMAND` | Python executable used by setup | `python3.12` |
| `REAL_RUNTIME_ENV` | Real virtualenv directory | `.venv-real` |
| `DIFFUSION_REAL` | Enable Diffusers runtime | `0` |
| `DIFFUSION_MODEL` | Local model path or Hub id | `segmind/tiny-sd` |
| `VITE_RUNTIME_URL` | Runtime URL used by the web app | `http://127.0.0.1:8000` |
| `RUNTIME_URL` | Runtime URL used by diagnostics | `http://127.0.0.1:8000` |

## How to use the application

1. Enter or revise the prompt.
2. Draw a positive guide, or import an image into Guide Canvas.
3. Press `Run` to start the rolling exploration loop.
4. Use `Pause` when you want to inspect the current state.
5. Hold and drag on Generated State to reject a local solution. The brush is
   momentary and clears on release.
6. Adjust temperature, global exploration, guide influence, CFG, and brush
   size while exploring.
7. Press `Save` in Snapshot Timeline to keep a state.
8. Use the snapshot's `Restore` to return to it, or `Finish` to denoise it to
   the final diffusion step.
9. Use `Reset session` only when you intentionally want a new runtime state.

Imported images are guide-only. They do not automatically reset the runtime or
replace the Generated Image.

## Verification

Run the lightweight checks from the repository root:

```bash
npm test -- --run
npm run build
.venv/bin/python -m pytest -q
.venv-real/bin/python -m compileall -q backend scripts
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo check --manifest-path src-tauri/Cargo.toml
```

Verify a live runtime and one real image response:

```bash
RUNTIME_URL=http://127.0.0.1:8000 \
  MODEL_ID=segmind/tiny-sd RUNTIME_KIND=real \
  ./scripts/verify-runtime.sh
```

The diagnostic writes no repository files. Experiment scripts write generated
frames and metrics below the ignored `artifacts/` directory.

## Regression experiments

With a real runtime running, collect a long-horizon image series:

```bash
RUNTIME_URL=http://127.0.0.1:8000 \
RUNTIME_KIND=tinysd EXPERIMENT_HORIZON=24 \
EXPERIMENT_OUT=artifacts/long-horizon \
.venv-real/bin/python scripts/long-horizon-intervention.py
```

Test intervention while the same Explore session is still advancing:

```bash
RUNTIME_URL=http://127.0.0.1:8000 \
RUNTIME_KIND=tinysd EXPERIMENT_OUT=artifacts/midstream \
.venv-real/bin/python scripts/regression-midstream-intervention.py
```

These checks measure unique frames, frame differences, luma, clipping,
diffusion-step progression, Guide effect, Brush effect, and session continuity.
Inspect the generated `contact-sheet.png` and `metrics.json` together.

## Desktop packaging

### Lightweight shell

Build the normal Tauri app shell:

```bash
npm run tauri build -- --bundles app
```

The resulting Apple Silicon app is placed under:

```text
src-tauri/target/release/bundle/macos/Live Diffusion Canvas.app
```

The shell includes the backend source and tries to start a compatible local
runtime. If no real environment is available, the UI can still use Mock
Runtime.

### Self-contained macOS app

After `setup-real-runtime.sh` has installed the dependencies and TinySD has
been downloaded once, build the full app:

```bash
./scripts/build-macos-full.sh
```

This embeds the Python environment and TinySD weights as compressed resources.
The current build is approximately 1.2 GB and expands them into the app's
application-data directory on first launch. The script is intended for a
prepared Apple Silicon macOS build machine; it does not cross-compile the
Python environment for another operating system or CPU architecture.

## Architecture

```text
React + Vite + TypeScript
  ├─ Zustand              UI and runtime state
  ├─ Konva/react-konva    canvas interaction layer
  └─ Dexie/IndexedDB      semantic snapshot persistence

FastAPI local runtime
  ├─ Mock Stateful Runtime
  └─ TinySD / Diffusers stateful denoising runtime

Tauri 2 desktop shell
  └─ optional packaged runtime and model archives
```

The HTTP runtime exposes:

- `GET /runtime/health`
- `POST /runtime/session`
- `POST /runtime/intervention`
- `POST /runtime/finish`
- `POST /runtime/snapshot`
- `POST /runtime/snapshot/restore`

The source of truth for v0.1 product semantics is under [`docs/sdd/`](docs/sdd/).
Start with [`AGENTS.md`](AGENTS.md) and [`docs/sdd/README.md`](docs/sdd/README.md).

## Repository layout

```text
backend/       FastAPI runtime and runtime tests
docs/          SDD, ADRs, and operations documentation
scripts/       setup, diagnostics, regression, and packaging commands
src/           React UI, state, canvas, and persistence
src-tauri/     Tauri desktop shell and packaging configuration
public/        static web assets
```

Generated files such as `artifacts/`, `dist/`, virtual environments, Tauri
targets, and browser logs are intentionally ignored by Git.

## Known limitations

- The full self-contained packaging path currently targets Apple Silicon macOS.
- TinySD is the real-runtime integration target; it is not a production-scale
  image-quality model.
- WebSocket transport, cloud deployment, authentication, collaboration, and
  ControlNet are outside the v0.1 scope.
- Model quality depends on local hardware, Diffusers versions, prompt, seed,
  and the selected exploration settings.

## License

Apache License 2.0. See [LICENSE](LICENSE).

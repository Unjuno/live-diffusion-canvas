# Live Diffusion Canvas

SDD-first prototype for exploring and steering intermediate diffusion states.

## Run locally

```bash
npm install
npm run dev
```

Open the printed Vite URL. The current runtime is intentionally a Mock Stateful Runtime: it demonstrates session continuity, rolling updates, Guide Canvas input, momentary Noise Brush rejection, and Snapshot restore without requiring a GPU.

## Verification

```bash
npm test
npm run build
```

The browser-first app is structured so the same React UI can be packaged with Tauri and connected to a local FastAPI/Diffusers runtime. `segmind/tiny-sd` is the configured real local model on Apple MPS; the lightweight mock remains available for fast tests.

## Optional FastAPI runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload --port 8000
```

The runtime exposes `/runtime/health`, `/runtime/session`, `/runtime/intervention`, and `/runtime/finish`. Set `DIFFUSION_REAL=1` to use the local TinySD Diffusers runtime; otherwise the browser uses the lightweight mock path.

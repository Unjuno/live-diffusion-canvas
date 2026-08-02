# Contributing

Thanks for contributing to Live Diffusion Canvas. The project is experimental
and follows the SDD documents under [`docs/sdd/`](docs/sdd/).

## Before changing code

1. Read [`AGENTS.md`](AGENTS.md) and the relevant SDD documents.
2. Keep Guide Canvas separate from Generated Image.
3. Keep Noise Brush momentary and limited to Generated Image.
4. Preserve the stateful Run / Pause / Resume model; do not turn the app into
   one-shot image generation or ordinary inpainting.
5. Update the relevant SDD/ADR when behavior or scope changes.

## Local checks

```bash
npm install
npm test -- --run
npm run build
./scripts/test-backend.sh
python3 -m compileall -q backend scripts
```

For real-runtime changes, also run the appropriate regression script against a
prepared local Diffusers environment and include its metrics in the pull
request.

## Pull requests

Describe the user-visible behavior, runtime/state impact, tests run, and any
model or hardware assumptions. Keep generated artifacts, virtualenvs, model
weights, and local logs out of commits.

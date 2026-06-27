# Architecture Decision Records

This directory contains Architecture Decision Records for Live Diffusion Canvas.

The SDD files in `docs/sdd/` remain the implementation source of truth. ADRs explain why key architectural decisions were made and what tradeoffs they imply.

## Index

| ADR | Decision |
|---|---|
| [ADR-0001](0001-stateful-diffusion-runtime.md) | Use a Stateful Diffusion Runtime abstraction |
| [ADR-0002](0002-guide-canvas-replaces-human-layer.md) | Use Guide Canvas instead of standalone Human Layer |
| [ADR-0003](0003-run-loop-no-user-facing-step-mode.md) | Use Run / Pause / Resume instead of user-facing Step Mode |
| [ADR-0004](0004-momentary-noise-brush.md) | Treat Noise Brush as momentary local rejection input |
| [ADR-0005](0005-custom-first-fork-adapter-allowed.md) | Prefer custom minimal app first while allowing fork/adapter routes |
| [ADR-0006](0006-frontend-canvas-stack.md) | Select React/Vite/TypeScript and Konva for frontend canvas stack |
| [ADR-0007](0007-state-and-snapshot-persistence.md) | Select Zustand and Dexie/IndexedDB for state and Snapshot persistence |
| [ADR-0008](0008-backend-transport-stack.md) | Select FastAPI and HTTP-first transport for backend runtime service |
| [ADR-0009](0009-mock-runtime-before-real-diffusion.md) | Implement Mock Stateful Runtime before real diffusion backend |
| [ADR-0010](0010-real-backend-integration-strategy.md) | Use Diffusers/TinySD as first real backend spike and ComfyUI adapter later |

## ADR format

Each ADR uses:

```text
Status
Context
Decision
Consequences
Rejected alternatives
References
```

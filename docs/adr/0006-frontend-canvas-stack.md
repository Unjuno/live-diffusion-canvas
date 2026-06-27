# ADR-0006: Select React/Vite/TypeScript and Konva for frontend canvas stack

## Status

Accepted.

## Context

Live Diffusion Canvas v0.1 is a canvas-heavy interaction prototype. The critical UI requirements are:

- Guide Canvas with imported image, drawing layer, erase mask, and composite export
- Generated Image Canvas with momentary Noise Brush input
- Run / Pause / Resume interaction
- Snapshot thumbnails and restore behavior
- fast local iteration before real diffusion backend quality work

The app does not need SSR, complex routing, auth, or production deployment in v0.1.

## Decision

Use this frontend and canvas stack:

```text
React + Vite + TypeScript
Konva + react-konva
```

React + Vite is the default app shell.

Konva / react-konva is the default visible canvas layer system.

## Consequences

Positive:

- Fast SPA development path.
- TypeScript makes AppState, runtime contracts, and Snapshot shape explicit.
- Konva maps well to Stage / Layer / Shape / Image interactions.
- Image import, opacity, pointer input, and export can be implemented without building everything on raw Canvas.

Negative:

- Konva adds an abstraction layer that may need custom export helpers for masks and composites.
- Very high-performance rendering work may later require direct Canvas or WebGL paths.

## Rejected alternatives

### Next.js

Rejected as the default v0.1 shell because SSR/routing/deployment are not the current hard problems.

### SvelteKit

Rejected because React ecosystem compatibility and react-konva availability are more relevant for this prototype.

### PixiJS

Rejected as the default v0.1 canvas because it is more rendering-engine oriented than needed.

### Raw HTML Canvas only

Rejected as the default because it increases implementation work for layer management and pointer interactions.

## References

- `docs/sdd/tech_stack.md`
- `docs/sdd/architecture.md`
- `docs/sdd/tasks.md`

# ADR-0005: Prefer custom minimal app first while allowing fork/adapter routes

## Status

Accepted.

## Context

The project can potentially reuse existing diffusion tools, canvases, or backends. Candidate routes include direct Diffusers/TinySD runtime, ComfyUI backend adapter, InvokeAI fork/adapter, or other compatible tools.

However, the product semantics are specific:

```text
Guide Canvas
Run loop
global exploration noise
momentary Noise Brush local rejection
Snapshot / Restore / Finish
stateful or simulated-state runtime semantics
```

Many existing tools are optimized for prompt-to-final-image, img2img, inpainting, or node workflows. Reusing them can accelerate backend or canvas work, but can also pull the product away from its intended interaction model.

## Decision

Use custom minimal UI + Mock Stateful Runtime as the default v0.1 route.

Forks and adapters are allowed after the UI semantics are correct, if they accelerate real backend integration or canvas functionality without changing the product concept.

Allowed routes include:

```text
Direct Diffusers / TinySD runtime
ComfyUI backend adapter
InvokeAI fork or adapter
other compatible backend adapter
```

## Consequences

Positive:

- Keeps the prototype focused and conceptually clean.
- Avoids inheriting a large UI model that may not match the product.
- Allows fast exploration through Mock Stateful Runtime.
- Still permits practical reuse when it helps.

Negative:

- Building custom canvas pieces requires work.
- Real backend integration may come later than if an existing tool were forked immediately.
- Adapter evaluation must be done explicitly.

## Rejected alternatives

### Fork-first approach

Rejected as the default because existing tools may impose ordinary inpainting or workflow-editor semantics.

### Custom-only approach

Rejected because existing tools may provide useful model execution, canvas infrastructure, or workflow capabilities.

### Backend-first approach

Rejected because the UI interaction concept should be validated before optimizing model quality.

## References

- `docs/sdd/implementation_strategy.md`
- `docs/sdd/spec.md`
- `docs/sdd/architecture.md`
- `docs/sdd/tasks.md`

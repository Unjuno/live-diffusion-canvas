# ADR-0010: Use Diffusers/TinySD as first real backend spike and ComfyUI adapter later

## Status

Accepted.

## Context

After Mock Stateful Runtime validates the UX, the project needs a real diffusion backend path.

Candidate routes include:

- direct Diffusers runtime
- TinySD or other small SD-compatible model
- ComfyUI adapter
- InvokeAI adapter/fork
- AUTOMATIC1111 / Forge extension

The backend route must not collapse the product into ordinary prompt-to-final-image generation or one-shot inpainting.

## Decision

Use this order:

```text
1. Diffusers + TinySD or small SD-compatible model as first real backend spike
2. ComfyUI adapter later if workflow/model reuse is useful
3. InvokeAI as reference first, adapter/fork only if clearly beneficial
4. AUTOMATIC1111 / Forge is not a first candidate
```

TinySD is a runtime integration spike target, not the product-quality image target.

ComfyUI should be used as backend adapter, not as the primary Live Diffusion Canvas UI.

## Consequences

Positive:

- Diffusers gives the most direct control for runtime experiments.
- TinySD/small models reduce iteration cost for backend integration.
- ComfyUI remains available for model/workflow breadth later.
- The custom UI remains the product UX source of truth.

Negative:

- TinySD may not demonstrate final product quality.
- Diffusers runtime work may require custom pipeline/scheduler handling.
- ComfyUI adapter may only approximate stateful live intervention without custom nodes.

## Rejected alternatives

### ComfyUI-first UI

Rejected because the product is not a node workflow editor.

### InvokeAI fork-first

Rejected as default because inheriting a large canvas product may slow or distort the custom interaction model.

### AUTOMATIC1111 / Forge first backend

Rejected because it is less aligned with live stateful canvas semantics and may push the product toward repeated img2img/inpainting.

## References

- `docs/sdd/tech_stack.md`
- `docs/sdd/implementation_strategy.md`
- `docs/sdd/runtime.md`

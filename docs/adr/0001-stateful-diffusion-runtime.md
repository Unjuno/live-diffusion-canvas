# ADR-0001: Use a Stateful Diffusion Runtime abstraction

## Status

Accepted.

## Context

Live Diffusion Canvas is not intended to be a one-shot prompt-to-final-image application.

The product value comes from letting the user steer an intermediate generation process:

```text
Run loop
→ low global exploration movement
→ Guide Canvas as positive guide
→ momentary Noise Brush local rejection
→ Snapshot / Restore / Finish
```

A pure image API that accepts a prompt and returns a final image cannot represent this interaction cleanly. A normal img2img or inpainting loop may approximate the behavior, but it tends to push the product back toward stateless editing.

## Decision

Use a Stateful Diffusion Runtime abstraction.

The runtime should:

- create or simulate a session
- keep runtime state across normal Explore updates
- accept Prompt, Guide Composite, global exploration noise, and optional activeNoiseMask
- advance a small number of updates
- return preview image output
- protect against stale responses with requestId or single-flight control

Stateless backends may be wrapped by adapters for v0.1 only if the adapter preserves the product semantics and simulates session continuity.

## Consequences

Positive:

- Keeps the product centered on generation-process steering.
- Allows Mock Stateful Runtime to validate the core interaction before real model integration.
- Allows direct runtime, ComfyUI adapter, InvokeAI adapter, or other backends behind the same contract.

Negative:

- More architectural discipline is required than a simple prompt/image API.
- True latent/timestep continuity may not be available in all backends.
- Some adapter routes will only approximate the stateful behavior.

## Rejected alternatives

### Pure prompt-to-final-image backend

Rejected because it cannot represent live intermediate-state steering.

### Plain img2img/inpainting loop as the product model

Rejected as the primary abstraction because it risks reducing the product to ordinary one-shot image editing.

## References

- `docs/sdd/spec.md`
- `docs/sdd/runtime.md`
- `docs/sdd/implementation_strategy.md`

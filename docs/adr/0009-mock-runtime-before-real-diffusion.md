# ADR-0009: Implement Mock Stateful Runtime before real diffusion backend

## Status

Accepted.

## Context

The product's main risk is interaction semantics, not final image quality.

The key behavior to validate is:

```text
Run loop
→ low global exploration movement
→ Guide Canvas separation
→ momentary Noise Brush local rejection
→ Snapshot / Restore / Finish
```

Real diffusion backends introduce GPU setup, model performance, scheduling, and image quality variables before the UI concept is proven.

## Decision

Build Mock Stateful Runtime first.

The mock must simulate or expose:

- sessionId
- requestId
- runtime state continuity
- guideComposite presence/influence
- global exploration movement
- activeNoiseMask presence only while Noise Brush is active
- local rejection effect only while active
- Snapshot / Restore / Finish flow
- stale response handling

Real backend integration comes after this behavior is demonstrable.

## Consequences

Positive:

- UI and state semantics can be validated without GPU/model setup.
- Prevents the product from being shaped by backend limitations too early.
- Provides a stable fallback when real backend is unavailable.

Negative:

- Mock output will not prove real model quality.
- Some runtime assumptions may need adjustment once Diffusers/TinySD is connected.

## Rejected alternatives

### Real backend first

Rejected because it risks spending time on model setup before proving the interaction loop.

### Static UI mock only

Rejected because Run loop, activeNoiseMask lifetime, requestId, and Snapshot restore require executable state transitions.

## References

- `docs/sdd/tech_stack.md`
- `docs/sdd/runtime.md`
- `docs/sdd/tasks.md`

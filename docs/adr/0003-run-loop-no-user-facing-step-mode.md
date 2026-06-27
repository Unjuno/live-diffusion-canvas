# ADR-0003: Use Run / Pause / Resume instead of user-facing Step Mode

## Status

Accepted.

## Context

The product is meant to feel like a live generation-intervention loop. The user should start the loop, guide it, reject local regions while it is running, save promising intermediate states, and finish from a selected Snapshot.

A user-facing Step Mode would shift the interaction toward discrete manual generation steps. That is not the intended primary experience.

An internal one-tick function is still useful for implementation, testing, and the Run loop scheduler.

## Decision

v0.1 has no user-facing Step Mode and no Step button.

The product controls are:

```text
Run
Pause
Resume
Snapshot
Finish
```

The implementation may still have an internal function such as `runOneTick()` or `applyRuntimeUpdateOnce()`, but it must not be exposed as a product mode.

## Consequences

Positive:

- Keeps the UX focused on live generation-process steering.
- Reduces UI complexity.
- Aligns Noise Brush with active hold/drag behavior.

Negative:

- Manual debugging may need developer-only tools or internal functions.
- Some users may expect a single-step control if they are familiar with generation pipelines.

## Rejected alternatives

### Keep Step Mode as a visible control

Rejected because it conflicts with the intended live loop interaction.

### Make Step the primary mode and Auto optional

Rejected because it reverses the core product concept.

## References

- `docs/sdd/spec.md`
- `docs/sdd/architecture.md`
- `docs/sdd/tasks.md`
- `docs/sdd/acceptance.md`

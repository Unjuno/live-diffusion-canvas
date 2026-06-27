# ADR-0004: Treat Noise Brush as momentary local rejection input

## Status

Accepted.

## Context

Noise Brush is not intended to be an eraser, a persistent inpainting mask, or a tool for applying Guide Canvas to a region.

The intended user action is closer to:

```text
This local result is unwanted right now.
While I brush here, make this area uncertain again and search for something else.
When I release the brush, stop forcing that local rejection.
```

Because the Run loop is already live, the brush does not need to persist after release.

## Decision

Noise Brush is momentary in v0.1.

```text
pointerdown / drag:
  noiseBrushActive = true
  activeNoiseMask is updated

pointerup / touchend / cancel:
  noiseBrushActive = false
  activeNoiseMask = null
```

`lastNoiseMask` may be retained only as debug/history/Snapshot metadata. It must not be restored as active intervention.

Noise Brush applies only to Generated Image, not Guide Canvas.

## Consequences

Positive:

- Matches real-time brushing behavior.
- Prevents accidental persistent corruption of a region.
- Keeps the semantic clear: Noise Brush means "not this," not "erase" or "apply guide here."

Negative:

- Users cannot pin a rejection region in v0.1.
- If persistent masks become useful later, they must be introduced explicitly as a separate feature.

## Rejected alternatives

### Persistent active mask by default

Rejected because it can keep disrupting a region after the user's active gesture ends.

### One-shot mask on next update only

Rejected as too weak for a live brush interaction; if the brush is held, it should continue applying while held.

### Eraser or inpainting mask

Rejected because it changes the concept from generation-process steering to ordinary image editing.

## References

- `docs/sdd/spec.md`
- `docs/sdd/runtime.md`
- `docs/sdd/acceptance.md`

# Agent Handoff v0.3

You are implementing Live Diffusion Canvas v0.1.

The core runtime is stateful. Do not implement the product as a pure prompt-to-final-image or blank-state image-to-image generator.

## Read first

1. `AGENTS.md`
2. `docs/sdd/README.md`
3. `docs/sdd/spec.md`
4. `docs/sdd/runtime.md`
5. `docs/sdd/architecture.md`
6. `docs/sdd/tasks.md`
7. `docs/sdd/acceptance.md`
8. `docs/sdd/glossary.md`
9. `docs/sdd/decisions.md`
10. `docs/sdd/grill.md`
11. `docs/sdd/research/extensions.md`

## Build target

Implement this interaction:

```text
Prompt input
→ runtime session creation
→ Human Layer drawing
→ Auto rolling intervention loop
→ low global exploration noise keeps state moving
→ Noise Brush held over bad region
→ local rejection boost applies only while held/dragged
→ release Noise Brush
→ local rejection boost stops
→ Snapshot save
→ Snapshot restore
→ Finish from Snapshot
```

## Work order

Follow `docs/sdd/tasks.md`.

Start with Static UI, AppState, Human Layer, runtime types, and Mock Stateful Runtime.

TinySD integration comes after Mock Stateful Runtime works.

## Most important constraints

- Human Layer and Generated Image are separate.
- Generated Image updates do not change Human Layer.
- Auto Mode is a rolling intervention loop, not only a forward-to-final generation run.
- Explore updates include low `globalExplorationNoiseStrength`.
- Noise Brush applies to Generated Image only.
- Noise Brush is a "not this local solution" intervention.
- Noise Brush is momentary: it applies only while the user is pressing or dragging.
- On release/cancel, `noiseBrushActive = false` and `activeNoiseMask = null`.
- Do not implement Noise Brush as normal erase.
- Do not implement Noise Brush as local Human Layer application.
- Do not restore `lastNoiseMask` as active intervention.
- Prompt, Human Layer, and surrounding state guide the alternative solution after local rejection input.
- Auto Mode can be paused.
- Runtime state is kept across normal Explore updates.
- Snapshot is the base for Restore and Finish.
- Finish from Snapshot stops Auto Mode while Finish runs.
- Mock Stateful Runtime must support UI validation.
- TinySD is the first real stateful latent runtime candidate, not merely a distant extension.

## Completion

Use `docs/sdd/acceptance.md`.

If the spec is unclear, use `docs/sdd/grill.md` before changing implementation scope.

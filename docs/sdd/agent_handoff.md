# Agent Handoff v0.4

You are implementing Live Diffusion Canvas v0.1.

The core runtime is stateful. Do not implement the product as a pure prompt-to-final-image, blank-state image-to-image generator, or ordinary one-shot inpainting UI.

## Read first

1. `AGENTS.md`
2. `docs/sdd/README.md`
3. `docs/sdd/spec.md`
4. `docs/sdd/runtime.md`
5. `docs/sdd/implementation_strategy.md`
6. `docs/sdd/architecture.md`
7. `docs/sdd/tasks.md`
8. `docs/sdd/acceptance.md`
9. `docs/sdd/glossary.md`
10. `docs/sdd/decisions.md`
11. `docs/sdd/grill.md`
12. `docs/sdd/research/extensions.md`

## Build target

Implement this interaction:

```text
Prompt input
→ Import Image into Guide Canvas or draw directly
→ edit Guide Canvas with Human Draw Layer and Guide Erase Mask
→ create Guide Composite
→ Run rolling intervention loop
→ low global exploration noise keeps state moving
→ Noise Brush held over bad Generated Image region
→ local rejection boost applies only while held/dragged
→ release Noise Brush
→ local rejection boost stops
→ Snapshot save
→ Snapshot restore
→ Finish from Snapshot
```

## Implementation route

Default route:

```text
custom minimal web UI
→ Mock Stateful Runtime
→ adapter/fork spike only after UI semantics are correct
```

Fork/adapter routes are allowed if they preserve the SDD semantics:

```text
Direct Diffusers / TinySD runtime
ComfyUI backend adapter
InvokeAI fork or adapter
other compatible tool adapter
```

Do not use a fork if it forces the product back into Step Mode, ordinary inpainting, or prompt-to-final-image semantics.

## Work order

Follow `docs/sdd/tasks.md`.

Start with Static UI, AppState, Guide Canvas, runtime types, and Mock Stateful Runtime.

Real backend or adapter integration comes after Mock Stateful Runtime works.

## Most important constraints

- No user-facing Step Mode or Step button.
- Guide Canvas and Generated Image are separate.
- Guide Canvas replaces old standalone Human Layer.
- Imported Image is guide-only in v0.1; do not auto-start Base Image Init Mode.
- Generated Image updates do not change Guide Canvas.
- Run loop is a rolling intervention loop, not only a forward-to-final generation run.
- Explore updates include low `globalExplorationNoiseStrength`.
- Noise Brush applies to Generated Image only.
- Noise Brush is a "not this local solution" intervention.
- Noise Brush is momentary: it applies only while the user is pressing or dragging.
- On release/cancel, `noiseBrushActive = false` and `activeNoiseMask = null`.
- Do not implement Noise Brush as normal erase.
- Do not implement Noise Brush as local Guide Canvas application.
- Do not restore `lastNoiseMask` as active intervention.
- Prompt, Guide Composite, and surrounding state guide the alternative solution after local rejection input.
- Run loop can be paused and resumed.
- Runtime state is kept across normal Explore updates.
- Snapshot is the base for Restore and Finish.
- Finish from Snapshot stops Run loop while Finish runs.
- Mock Stateful Runtime must support UI validation.

## Completion

Use `docs/sdd/acceptance.md`.

If the spec is unclear, use `docs/sdd/grill.md` before changing implementation scope.

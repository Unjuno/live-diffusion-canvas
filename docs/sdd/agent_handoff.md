# Agent Handoff v0.2

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
→ Generated Image preview update
→ Noise Brush mask
→ stateful runtime intervention
→ Auto loop
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
- Noise Brush applies to Generated Image only.
- Noise Brush creates an intervention mask, not an erase operation.
- Auto Mode can be paused.
- Runtime state is kept across normal Explore updates.
- Snapshot is the base for Restore and Finish.
- Mock Stateful Runtime must support UI validation.
- TinySD is the first real stateful latent runtime candidate, not merely a distant extension.

## Completion

Use `docs/sdd/acceptance.md`.

If the spec is unclear, use `docs/sdd/grill.md` before changing implementation scope.

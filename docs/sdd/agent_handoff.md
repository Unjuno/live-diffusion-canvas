# Agent Handoff v0.1

You are implementing Live Diffusion Canvas v0.1.

## Read first

1. `AGENTS.md`
2. `docs/sdd/README.md`
3. `docs/sdd/spec.md`
4. `docs/sdd/architecture.md`
5. `docs/sdd/tasks.md`
6. `docs/sdd/acceptance.md`
7. `docs/sdd/glossary.md`
8. `docs/sdd/decisions.md`
9. `docs/sdd/grill.md`

## Build target

Implement this interaction:

```text
Prompt input
→ Human Layer drawing
→ Generated Image update
→ Noise Brush mask
→ Auto loop
→ Snapshot save
→ Snapshot restore
→ Finish from Snapshot
```

## Work order

Follow `docs/sdd/tasks.md`.

Start with Static UI, AppState, Human Layer, and Mock backend.

Real model integration comes after Mock backend works.

## Most important constraints

- Human Layer and Generated Image are separate.
- Generated Image updates do not change Human Layer.
- Noise Brush applies to Generated Image only.
- Auto Mode can be paused.
- Snapshot is the base for Restore and Finish.
- Mock backend must support UI validation.

## Completion

Use `docs/sdd/acceptance.md`.

If the spec is unclear, use `docs/sdd/grill.md` before changing implementation scope.

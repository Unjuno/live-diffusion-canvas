# Live Diffusion Canvas

Live Diffusion Canvas is an SDD-first prototype for interacting with intermediate diffusion generation states.

## Core workflow

```text
Prompt
→ Human Layer
→ Generated Image
→ Noise Brush
→ Snapshot
→ Restore / Finish from Snapshot
```

The application is not centered on one-shot final-image generation. It is centered on exploring and steering intermediate states.

## SDD source of truth

Read the SDD documents under:

```text
docs/sdd/
```

Start with:

1. `AGENTS.md`
2. `docs/sdd/README.md`
3. `docs/sdd/spec.md`
4. `docs/sdd/architecture.md`
5. `docs/sdd/tasks.md`
6. `docs/sdd/acceptance.md`

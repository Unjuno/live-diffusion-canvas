# AGENTS.md

This repository is an SDD-first implementation project.

## Source of truth

Use `docs/sdd/` as the source of truth for v0.1.

Read in this order:

1. `docs/sdd/README.md`
2. `docs/sdd/spec.md`
3. `docs/sdd/runtime.md`
4. `docs/sdd/architecture.md`
5. `docs/sdd/tasks.md`
6. `docs/sdd/acceptance.md`
7. `docs/sdd/glossary.md`
8. `docs/sdd/decisions.md`
9. `docs/sdd/grill.md`
10. `docs/sdd/agent_handoff.md`
11. `docs/sdd/research/extensions.md`

## Core implementation rules

- Follow `docs/sdd/spec.md`.
- Treat backend semantics as Stateful Diffusion Runtime per `docs/sdd/runtime.md`.
- Work through `docs/sdd/tasks.md` in order.
- Use `docs/sdd/acceptance.md` for completion checks.
- Start with Mock Stateful Runtime before a real model runtime.
- Keep Human Layer separate from Generated Image.
- Apply Noise Brush to Generated Image only.
- Treat Noise Brush as state intervention, not erase.
- Keep Auto Mode stoppable.
- Keep Snapshot restore and Finish from Snapshot working.
- Do not make normal Explore updates always restart from blank state.

## v0.1 exclusions

The v0.1 scope does not include ControlNet, diagram recognition, Mermaid conversion, authentication, collaboration, cloud deployment, required full latent-state snapshot restart, StreamDiffusion, or SDXL Finish backend.

TinySD Stateful Latent Runtime is allowed as the first real backend candidate if the environment permits it.

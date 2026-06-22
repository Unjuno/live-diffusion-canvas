# AGENTS.md

This repository is an SDD-first implementation project.

## Source of truth

Use `docs/sdd/` as the source of truth for v0.1.

Read in this order:

1. `docs/sdd/README.md`
2. `docs/sdd/spec.md`
3. `docs/sdd/architecture.md`
4. `docs/sdd/tasks.md`
5. `docs/sdd/acceptance.md`
6. `docs/sdd/glossary.md`
7. `docs/sdd/decisions.md`
8. `docs/sdd/grill.md`
9. `docs/sdd/agent_handoff.md`

## Core implementation rules

- Follow `docs/sdd/spec.md`.
- Work through `docs/sdd/tasks.md` in order.
- Use `docs/sdd/acceptance.md` for completion checks.
- Start with a mock generation backend before a real model backend.
- Keep Human Layer separate from Generated Image.
- Apply Noise Brush to Generated Image only.
- Keep Auto Mode stoppable.
- Keep Snapshot restore and Finish from Snapshot working.

## v0.1 exclusions

The v0.1 scope does not include ControlNet, diagram recognition, Mermaid conversion, authentication, collaboration, cloud deployment, or full latent-state snapshot restart.

# AGENTS.md

This repository is an SDD-first implementation project.

## Source of truth

Use `docs/sdd/` as the source of truth for v0.1.

Read in this order:

1. `docs/sdd/README.md`
2. `docs/sdd/spec.md`
3. `docs/sdd/runtime.md`
4. `docs/sdd/implementation_strategy.md`
5. `docs/sdd/architecture.md`
6. `docs/sdd/tasks.md`
7. `docs/sdd/acceptance.md`
8. `docs/sdd/glossary.md`
9. `docs/sdd/decisions.md`
10. `docs/sdd/grill.md`
11. `docs/sdd/agent_handoff.md`
12. `docs/sdd/research/extensions.md`

## Core implementation rules

- Follow `docs/sdd/spec.md`.
- Treat backend semantics as Stateful Diffusion Runtime per `docs/sdd/runtime.md`.
- Use `docs/sdd/implementation_strategy.md` before choosing custom build, fork, or adapter route.
- Work through `docs/sdd/tasks.md` in order.
- Use `docs/sdd/acceptance.md` for completion checks.
- Prefer custom minimal UI + Mock Stateful Runtime first unless a fork/adapter clearly preserves the product semantics faster.
- Do not expose a user-facing Step Mode or Step button.
- Guide Canvas replaces the old standalone Human Layer concept.
- Keep Guide Canvas separate from Generated Image.
- Imported Image is guide-only in v0.1. Do not automatically start Base Image Init Mode.
- Apply Noise Brush to Generated Image only.
- Noise Brush marks the current local output as unwanted.
- Noise Brush is momentary: use it only while the user is pressing or dragging.
- On release or cancel, clear activeNoiseMask and stop local brush influence.
- Do not interpret Noise Brush as applying Guide Canvas to the masked region.
- Explore must include low global exploration noise or a mock equivalent.
- Keep Run loop stoppable and resumable.
- Keep Snapshot restore and Finish from Snapshot working.
- Do not restore lastNoiseMask as active brush input.
- Do not make normal Explore updates always restart from blank state.
- If using an existing tool fork or adapter, do not let it collapse the product into ordinary one-shot inpainting or prompt-to-final-image generation.

## v0.1 exclusions

The v0.1 scope does not include user-facing Step Mode, Base Image Init Mode, ControlNet as required runtime, diagram recognition, Mermaid conversion, authentication, collaboration, cloud deployment, required full latent-state snapshot restart, persistent/pinned rejection masks, StreamDiffusion, or SDXL Finish backend.

Existing tool fork/adapter use is allowed but not required.

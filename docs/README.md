# Documentation map

Live Diffusion Canvas keeps product semantics and implementation notes in
separate layers.

## Start here

- [Repository README](../README.md): setup, usage, runtime choices, and checks.
- [Operations guide](operations.md): local web, FastAPI, real-model, and Tauri
  commands.
- [AGENTS.md](../AGENTS.md): implementation rules for contributors and agents.

## Product and architecture source of truth

- [SDD package](sdd/README.md): v0.1 scope and reading order.
- [Acceptance criteria](sdd/acceptance.md): observable completion checks.
- [Runtime contract](sdd/runtime.md): stateful runtime and intervention
  semantics.
- [Architecture](sdd/architecture.md): frontend, backend, and persistence
  structure.
- [ADRs](adr/README.md): rationale for major decisions.

## Research and diagnostics

- [Model compatibility](sdd/research/model-compatibility.md): model support
  and caveats.
- [Extension research](sdd/research/extensions.md): future ideas, not v0.1
  commitments.

Generated frames, metrics, model caches, and virtual environments are local
diagnostic artifacts and should not be committed.

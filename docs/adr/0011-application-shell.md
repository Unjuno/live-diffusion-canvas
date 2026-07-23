# ADR 0011: Application shell and undefined behavior decisions

## Decision

Implement v0.1 as a React + Vite + TypeScript browser application first. Keep modules compatible with a later Tauri shell; do not make Tauri or a native build prerequisite for validating the core interaction.

## Undefined behavior resolved

- Run before a preview: create the mock session implicitly and show the first state on the next update.
- Pause: stop scheduling new updates; an already running update may finish.
- Resume: continue from the current tick/state.
- Restore: replace the preview and prompt with the selected Snapshot and pause the loop; active Noise Brush state is always cleared.
- Finish: reserved for the next runtime milestone; the v0.1 UI will expose it only after a runtime implementation exists.
- Import: guide-only; it never resets a runtime session.
- Pointer release/cancel: clear active mask and stop local rejection; history may remain as metadata.

## Rationale

The browser-first shell gives fast, verifiable feedback and matches the selected stack. Tauri can later package the same UI and launch a local FastAPI process without changing product semantics.

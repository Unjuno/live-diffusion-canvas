# ADR 0013: Tauri packaging readiness

## Decision

Keep the application browser-first while providing a verified Tauri 2 desktop shell. The shell packages the same Vite frontend; FastAPI remains a separately launched local runtime in v0.1.

## Rationale

React + Vite provides the desktop shell frontend. The current product semantics do not depend on native APIs, so Tauri is packaging rather than a second UI implementation. The Apple Silicon `.app` bundle has been built successfully; DMG creation is a separate packaging step that requires a GUI-capable macOS session.

# ADR 0012: FastAPI runtime connection

## Decision

Keep the browser Mock Runtime as the default. When the backend selector is `tinysd`, the UI uses the HTTP-first FastAPI runtime contract at `127.0.0.1:8000`.

## Undefined behavior resolved

- Runtime session is created lazily on the first non-mock update.
- A failed runtime request pauses the loop and displays `errorMessage`.
- CORS is restricted to local Vite development origins.
- The current FastAPI implementation is a stateful mock adapter; the selector name is a future backend route, not a claim of model-quality generation.
- `DIFFUSION_REAL=1` switches the same endpoint to the real `segmind/tiny-sd` Diffusers pipeline; without it, the lightweight mock remains the default for tests.

## Rationale

This preserves the SDD's stateful intervention semantics and allows the UI, API contract, and real model implementation to be tested independently.

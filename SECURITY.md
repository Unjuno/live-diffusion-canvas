# Security Policy

## Scope

This is a local-first experimental application. The FastAPI runtime is intended
to bind to localhost and is not hardened for public exposure.

## Reporting a vulnerability

Do not post credentials, tokens, model access keys, or exploitable payloads in a
public issue. Use GitHub's private vulnerability reporting for this repository
when available. If it is unavailable, open a minimal issue asking for a
private contact channel and omit sensitive details.

Please include the affected commit, reproduction steps, impact, and a proposed
mitigation if known.

## User data

Snapshots are stored locally in IndexedDB. Do not include personal images,
tokens, model caches, or generated artifacts in bug reports or pull requests.

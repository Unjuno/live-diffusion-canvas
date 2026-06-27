# ADR-0008: Select FastAPI and HTTP-first transport for backend runtime service

## Status

Accepted.

## Context

The first real backend path needs to connect the custom frontend to Python diffusion tooling while keeping v0.1 simple.

The required runtime contract is:

```text
createSession
applyIntervention
finishFromSnapshot
health check
```

The initial product loop is client-driven. It does not require server-pushed frame streaming in v0.1.

## Decision

Use:

```text
Python FastAPI
HTTP-first transport
WebSocket optional later
```

Initial endpoints should be shaped around:

```text
POST /runtime/session
POST /runtime/intervention
POST /runtime/finish
GET  /runtime/health
```

WebSocket is deferred until progress streaming, cancellation, runtime telemetry, or preview streaming requires it.

## Consequences

Positive:

- Natural fit for Diffusers and Python image/mask processing.
- Simple client implementation with HTTP request/response.
- Keeps v0.1 backend testable without streaming infrastructure.
- Allows WebSocket later without changing product semantics.

Negative:

- HTTP polling/request loop may not be the lowest-latency option.
- Large image/mask payloads need careful encoding and upload handling.
- Cancellation/progress may require a later protocol extension.

## Rejected alternatives

### Node.js backend as default

Rejected because the real diffusion runtime path is Python-centric.

### Next.js API routes

Rejected because frontend app shell is React/Vite and the runtime should remain a separate service.

### WebSocket-first transport

Rejected for v0.1 because it adds complexity before streaming is required.

## References

- `docs/sdd/tech_stack.md`
- `docs/sdd/runtime.md`
- `docs/sdd/implementation_strategy.md`

# ADR-0007: Select Zustand and Dexie/IndexedDB for state and Snapshot persistence

## Status

Accepted.

## Context

Live Diffusion Canvas v0.1 has state-heavy interactions:

- prompt and backend/model selection
- Guide Canvas layers
- Generated Image preview
- Run loop status
- runtime session and requestId
- momentary activeNoiseMask
- Snapshot / Restore / Finish
- image, mask, and guide composite persistence

Snapshots must preserve semantic data, not just the visual state of a canvas implementation.

## Decision

Use:

```text
Zustand for AppState
Dexie + IndexedDB for Snapshot persistence
```

Zustand is the default frontend state store.

Dexie wraps IndexedDB for local persistence of larger structured data and image/mask blobs.

Snapshot persistence should store semantic blobs and settings:

```text
prompt
settings
generatedImageBlob
importedImageBlob?
humanDrawLayerBlob?
guideEraseMaskBlob?
guideCompositeBlob?
lastNoiseMaskBlob? as metadata only
runtimeStateMeta?
```

Konva JSON may be stored as auxiliary metadata only. It is not the canonical Snapshot format.

## Consequences

Positive:

- Keeps state management lightweight and inspectable.
- Avoids Redux boilerplate for v0.1.
- Supports local image/blob Snapshot persistence without a backend database.
- Preserves Snapshot semantics independently of the canvas library.

Negative:

- IndexedDB schema migration must be handled once Snapshot shape changes.
- Large blobs can increase local storage usage.
- Cross-device persistence is not included in v0.1.

## Rejected alternatives

### Redux Toolkit

Rejected as the default because v0.1 does not need its boilerplate or ecosystem weight.

### React local state only

Rejected because Run loop, Snapshot, canvas layers, and runtime state need shared app-level coordination.

### localStorage

Rejected because Snapshot data includes image and mask blobs.

### Konva JSON as primary Snapshot format

Rejected because it couples persistence to canvas implementation details and is insufficient as the product source of truth.

## References

- `docs/sdd/tech_stack.md`
- `docs/sdd/architecture.md`
- `docs/sdd/tasks.md`

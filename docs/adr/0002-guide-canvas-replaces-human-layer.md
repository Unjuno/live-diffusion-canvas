# ADR-0002: Use Guide Canvas instead of standalone Human Layer

## Status

Accepted.

## Context

The original concept used Human Layer as a separate positive intervention layer. The product now also needs image import: users should be able to load an image, edit or erase parts of it, draw on top of it, and use the result as a generation guide.

Putting imported images directly into a standalone Human Layer would make the concept ambiguous:

```text
Is the layer hand-drawn guidance?
Is it an imported reference image?
Is it a composited guide?
Is it an initial image?
```

## Decision

Replace standalone Human Layer with Guide Canvas.

Guide Canvas contains:

```text
Imported Image Layer
Human Draw Layer
Guide Erase Mask
Guide Composite
```

In v0.1, imported images are guide-only. Importing an image does not automatically reset or initialize the runtime session.

Guide Composite is the runtime-facing positive guide input. It may be used directly, or the runtime may receive individual sublayers if a backend benefits from that.

## Consequences

Positive:

- Separates positive guidance from Generated Image output.
- Supports both image import and user drawing without conflating concepts.
- Makes Snapshot restore cleaner because guide data can be saved separately.
- Keeps a future path open for ControlNet, T2I-Adapter, or image-conditioning backends.

Negative:

- More state must be stored than a single Human Layer.
- The UI must support image import, drawing, erase mask, opacity, and composite export.
- Runtime behavior may initially be only debug-visible in Mock runtime or weakly used by real backends.

## Rejected alternatives

### Put imported image directly into Human Layer

Rejected because it blurs hand-drawn guide, imported reference, and composite guide semantics.

### Treat imported image as initial image by default

Rejected for v0.1 because Base Image Init Mode is a different behavior from guide-only import and would complicate runtime semantics.

## References

- `docs/sdd/spec.md`
- `docs/sdd/architecture.md`
- `docs/sdd/glossary.md`

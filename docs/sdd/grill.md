# Spec Review Protocol v0.1

Use this file before changing v0.1 scope.

## Core question

Does the change help this v0.1 goal?

```text
Prompt + Human Layer + Noise Brush + Snapshot-based exploration of intermediate generation states.
```

If not, defer it.

## Review checklist

Before adding a feature, answer:

1. Does it support the v0.1 demo path?
2. Can it be tested with Mock backend?
3. Does it keep Human Layer separate from Generated Image?
4. Does it keep Noise Brush limited to Generated Image?
5. Does it preserve Snapshot restore and Finish?
6. Does it have observable acceptance criteria?
7. Does it avoid increasing model-quality work before UI flow works?
8. Does it avoid v0.1 excluded areas?

## v0.1 excluded areas

- Diagram structure recognition
- Mermaid / UML / SVG conversion
- ControlNet
- Complex semantic layers
- Authentication
- Collaboration
- Cloud deployment
- Full latent-state snapshot restart
- Production-quality model tuning

## Change procedure

If the change is accepted, update all relevant files:

- `docs/sdd/spec.md`
- `docs/sdd/architecture.md`
- `docs/sdd/tasks.md`
- `docs/sdd/acceptance.md`
- `docs/sdd/glossary.md`
- `docs/sdd/decisions.md`

## Proposal template

```md
## Proposal: <name>

### Purpose

### v0.1 relevance

### Inputs

### Outputs

### State changes

### UI changes

### Error behavior

### Acceptance criteria

### Decision

Adopt / Defer / Reject
```

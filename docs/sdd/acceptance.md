# Acceptance Criteria v0.1

v0.1 is complete when the following are true.

## Core

1. User can enter a prompt.
2. User can select a model.
3. User can run one Step update.
4. User can draw on Human Layer.
5. Human Layer is stored separately from Generated Image.
6. User can paint a Noise Brush area on Generated Image.
7. The next generation request includes the noiseMask.
8. User can start Auto mode.
9. User can Pause Auto mode.
10. User can save a Snapshot.
11. User can restore a Snapshot.
12. User can run Finish from a selected Snapshot.
13. Generation errors are visible in the UI.
14. The UI remains usable after a generation error.
15. Generated Image updates do not change Human Layer.

## Minimal demo

```text
Open app
→ enter Prompt
→ Step
→ draw on Human Layer
→ Auto
→ paint Noise Brush
→ Save Snapshot
→ continue generation
→ Restore Snapshot
→ Finish from Snapshot
```

## Failure conditions

v0.1 is not complete if:

- Human Layer disappears after Generated Image update.
- Auto cannot be paused.
- Snapshot cannot be restored.
- Noise Brush changes Human Layer.
- UI becomes unusable after backend error.
- Generated Image is always recreated from scratch without current-image continuity.

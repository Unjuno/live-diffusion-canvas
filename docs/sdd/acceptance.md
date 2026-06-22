# Acceptance Criteria v0.3

v0.1 is complete only when the following observable criteria pass.

## 1. Core completion

1. User can enter a Prompt.
2. User can select `selectedBackend` and `selectedModel`.
3. User can run one Step runtime update.
4. User can draw on Human Layer.
5. Human Layer is stored separately from Generated Image.
6. User can hold/drag Noise Brush on Generated Image.
7. While Noise Brush is active, the next DiffusionIntervention includes activeNoiseMask.
8. After Noise Brush release, active local rejection stops.
9. User can start Auto Mode.
10. User can Pause Auto Mode.
11. User can save a Snapshot.
12. User can restore a Snapshot.
13. User can run Finish from a selected Snapshot.
14. Generation errors are visible in the UI through `errorMessage` or equivalent.
15. The UI remains usable after a generation error.
16. Generated Image updates do not change Human Layer.
17. Old responses cannot overwrite newer Generated Image state.
18. Normal Explore updates do not always restart from blank state.
19. Explore Auto updates include low global exploration noise or an inspectable mock equivalent.
20. Noise Brush is implemented as momentary local rejection / uncertainty boost, not as erase, persistent mask, or local Human Layer application.

## 2. UI criteria

### AC-UI-001: Layout

The app shows:

- Prompt input
- Backend / Model selector
- Step / Auto / Pause controls
- Human Layer canvas
- Generated Image canvas
- Snapshot Timeline
- Generation settings
- Noise Brush settings

### AC-UI-002: Settings

The user can change:

- Steps
- CFG
- Global Exploration Noise Strength
- Local Rejection Strength
- Seed
- Update Interval
- Brush Size

## 3. Runtime criteria

### AC-RUNTIME-001: Session

The runtime creates or simulates a session identified by sessionId.

### AC-RUNTIME-002: Stateful update

Step and Auto call a runtime update against existing session state when session state exists.

### AC-RUNTIME-003: Mock stateful behavior

Mock runtime visibly or inspectably changes state across updates. It must not behave as a pure stateless final-image generator.

### AC-RUNTIME-004: TinySD positioning

TinySD is treated as the first real stateful latent runtime candidate. It is not treated only as a distant future extension.

### AC-RUNTIME-005: Global exploration noise

Explore updates apply low global exploration noise or a visible/inspectable mock equivalent.

## 4. Human Layer criteria

### AC-HL-001: Drawing

Drawing on Human Layer appears immediately.

### AC-HL-002: Separation

Generated Image updates do not clear or change Human Layer.

### AC-HL-003: Clear

Clear Human Layer clears only Human Layer. Generated Image remains.

## 5. Generation criteria

### AC-GEN-001: Step

When Prompt exists and Step is pressed, exactly one runtime update is attempted and Generated Image preview updates on success.

### AC-GEN-002: Status

While a request is running, generationStatus is `generating` or equivalent.

### AC-GEN-003: Error

When runtime fails, generationStatus becomes `error`, errorMessage is visible, and the app remains usable.

### AC-GEN-004: Current state continuity

When runtime state exists, Step and Auto use it as the base. The app must not always recreate from blank state.

### AC-GEN-005: requestId

Every request has a requestId, and every response includes the same requestId.

### AC-GEN-006: Prompt update policy

Prompt changes during Auto Mode do not destroy the runtime session. They are applied from a later runtime update.

## 6. Noise Brush criteria

### AC-NB-001: Active mask drawing

Pressing and dragging Noise Brush on Generated Image creates or updates activeNoiseMask.

### AC-NB-002: Brush size

Brush Size changes the painted mask size.

### AC-NB-003: Active intervention inclusion

When noiseBrushActive is true and activeNoiseMask exists, Step and Auto include it in DiffusionIntervention or the compatibility GenerationRequest.

### AC-NB-004: Human Layer unchanged

Noise Brush does not modify Human Layer.

### AC-NB-005: Local Rejection Strength meaning

Local Rejection Strength is interpreted as the strength of reintroducing uncertainty in the activeNoiseMask region.

### AC-NB-006: Semantic meaning

Noise Brush means that the current local solution in the masked region is rejected by the user.

It must not be implemented as:

- a normal erase operation
- a direct Human Layer apply operation

### AC-NB-007: Alternative search behavior

While Noise Brush is active, future updates should attempt to move the masked region away from the previous local interpretation while remaining conditioned by Prompt, Human Layer, and surrounding runtime state.

### AC-NB-008: Momentary lifetime

When the user releases/cancels the brush interaction, noiseBrushActive becomes false and activeNoiseMask is cleared.

### AC-NB-009: No persistent mask by default

After release, local rejection boost must stop. lastNoiseMask may remain only as debug/history/Snapshot metadata and must not be used as active intervention.

## 7. Auto Loop criteria

### AC-LOOP-001: Auto start

Auto Mode attempts runtime updates every updateIntervalMs.

### AC-LOOP-002: Pause

Pause stops new runtime requests.

### AC-LOOP-003: UI remains usable

During Auto Mode, the user can still draw Human Layer, hold/drag Noise Brush, save Snapshot, and press Pause.

### AC-LOOP-004: stale response protection

If an old response returns late, it must not overwrite newer Generated Image state or runtime state.

This can be implemented with requestId checking or single-flight request control.

### AC-LOOP-005: Rolling intervention loop

Auto Mode is a rolling intervention loop. It must not be implemented only as a forward-to-final-image process that stops the interaction after convergence.

## 8. Snapshot criteria

### AC-SNAP-001: Save

Save Snapshot adds a Snapshot to Snapshot Timeline.

Snapshot stores at least:

- id
- parentId
- createdAt
- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- generatedImageDataUrl

### AC-SNAP-002: Layer and metadata

If Human Layer exists, Snapshot stores humanLayerDataUrl.

If lastNoiseMask exists, Snapshot may store lastNoiseMaskDataUrl as metadata.

### AC-SNAP-003: Restore

Restore Snapshot restores Generated Image and main generation settings.

If runtime state is available, Restore may restore runtime state.

If runtime state is not available, Restore may use image Snapshot pseudo resume.

### AC-SNAP-004: Original retained

Restore and Finish do not delete the original Snapshot.

### AC-SNAP-005: Branch UI excluded

v0.1 does not require Branch Tree UI. parentId may be stored for future use only.

### AC-SNAP-006: No active mask restore

Restore must not reactivate lastNoiseMaskDataUrl as activeNoiseMask.

## 9. Finish criteria

### AC-FIN-001: Select

Clicking a Snapshot sets selectedSnapshotId.

### AC-FIN-002: Finish request

Finish from Snapshot uses selected Snapshot generatedImageDataUrl or saved runtime state as base.

### AC-FIN-003: Finish settings

Finish uses finish-oriented settings:

```text
steps: 12-30
globalExplorationNoiseStrength: 0.00
localRejectionStrength: 0.05-0.20
cfg: 3.0-6.0
```

### AC-FIN-004: Finish result

Finish success updates Generated Image and can be saved as a new Snapshot.

### AC-FIN-005: Finish stops Auto

Starting Finish from Snapshot stops Auto Mode and prevents concurrent Auto requests while Finish is running.

## 10. Mock runtime criteria

### AC-MOCK-001: Works without real model

The app supports Step, Auto, Snapshot, Restore, and Finish with Mock Stateful Runtime only.

### AC-MOCK-002: Inspectable request

Mock runtime exposes or logs:

- requestId
- sessionId
- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- noiseBrushActive
- activeNoiseMask presence
- humanLayer presence

## 11. Minimal demo

```text
Open app
→ enter Prompt
→ Step
→ draw on Human Layer
→ Auto
→ hold/drag Noise Brush over bad region
→ region changes while brush is active
→ release Noise Brush
→ local rejection stops
→ Save Snapshot
→ Restore Snapshot
→ Finish from Snapshot
```

## 12. Failure conditions

v0.1 is not complete if:

- Human Layer disappears after Generated Image update.
- Auto cannot be paused.
- Snapshot cannot be restored.
- Noise Brush changes Human Layer.
- Noise Brush is implemented as a normal eraser.
- Noise Brush is implemented as direct local Human Layer application.
- Noise Brush remains active after pointerup / touchend / cancel.
- lastNoiseMask is restored as active rejection input.
- UI becomes unusable after runtime error.
- Generated Image is always recreated from blank state without current-state continuity.
- Auto has no global exploration noise or mock equivalent.
- old responses can overwrite newer state.
- Model and Backend selection are ambiguous in state.
- globalExplorationNoiseStrength and localRejectionStrength are conflated.
- the runtime is specified only as a final-image generator.

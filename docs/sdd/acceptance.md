# Acceptance Criteria v0.1

v0.1 is complete only when the following observable criteria pass.

## 1. Core completion

1. User can enter a Prompt.
2. User can select `selectedBackend` and `selectedModel`.
3. User can run one Step update.
4. User can draw on Human Layer.
5. Human Layer is stored separately from Generated Image.
6. User can paint a Noise Brush area on Generated Image.
7. The next GenerationRequest includes `noiseMask` when a mask exists.
8. User can start Auto Mode.
9. User can Pause Auto Mode.
10. User can save a Snapshot.
11. User can restore a Snapshot.
12. User can run Finish from a selected Snapshot.
13. Generation errors are visible in the UI through `errorMessage` or equivalent.
14. The UI remains usable after a generation error.
15. Generated Image updates do not change Human Layer.
16. Old responses cannot overwrite newer Generated Image state.

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
- Noise Strength
- Seed
- Update Interval
- Brush Size

## 3. Human Layer criteria

### AC-HL-001: Drawing

Drawing on Human Layer appears immediately.

### AC-HL-002: Separation

Generated Image updates do not clear or change Human Layer.

### AC-HL-003: Clear

Clear Human Layer clears only Human Layer. Generated Image remains.

## 4. Generation criteria

### AC-GEN-001: Step

When Prompt exists and Step is pressed, exactly one GenerationRequest is sent and Generated Image updates.

### AC-GEN-002: Status

While a request is running, generationStatus is `generating` or equivalent.

### AC-GEN-003: Error

When backend fails, generationStatus becomes `error`, errorMessage is visible, and the app remains usable.

### AC-GEN-004: Current image continuity

When Generated Image exists, Step and Auto use it as base image. The app must not always recreate from blank state.

### AC-GEN-005: requestId

Every request has a requestId, and every response includes the same requestId.

## 5. Noise Brush criteria

### AC-NB-001: Mask drawing

Painting on Generated Image creates or updates noiseMask.

### AC-NB-002: Brush size

Brush Size changes the painted mask size.

### AC-NB-003: Request inclusion

When noiseMask exists, Step and Auto include it in GenerationRequest.

### AC-NB-004: Human Layer unchanged

Noise Brush does not modify Human Layer.

### AC-NB-005: Noise Strength meaning

Noise Strength is interpreted as the strength of reinterpreting the noiseMask region. v0.1 does not define a second global noise strength.

## 6. Auto Loop criteria

### AC-LOOP-001: Auto start

Auto Mode attempts generation updates every updateIntervalMs.

### AC-LOOP-002: Pause

Pause stops new generation requests.

### AC-LOOP-003: UI remains usable

During Auto Mode, the user can still draw Human Layer, paint Noise Brush, save Snapshot, and press Pause.

### AC-LOOP-004: stale response protection

If an old response returns late, it must not overwrite newer Generated Image state.

This can be implemented with requestId checking or single-flight request control.

## 7. Snapshot criteria

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
- noiseStrength
- generatedImageDataUrl

### AC-SNAP-002: Layer data

If Human Layer exists, Snapshot stores humanLayerDataUrl.

If noiseMask exists, Snapshot stores noiseMaskDataUrl.

### AC-SNAP-003: Restore

Restore Snapshot restores Generated Image and main generation settings.

### AC-SNAP-004: Original retained

Restore and Finish do not delete the original Snapshot.

### AC-SNAP-005: Branch UI excluded

v0.1 does not require Branch Tree UI. parentId may be stored for future use only.

## 8. Finish criteria

### AC-FIN-001: Select

Clicking a Snapshot sets selectedSnapshotId.

### AC-FIN-002: Finish request

Finish from Snapshot uses selected Snapshot generatedImageDataUrl as base image.

### AC-FIN-003: Finish settings

Finish uses finish-oriented settings:

```text
steps: 12-30
noiseStrength: 0.05-0.20
cfg: 3.0-6.0
```

### AC-FIN-004: Finish result

Finish success updates Generated Image and can be saved as a new Snapshot.

## 9. Mock backend criteria

### AC-MOCK-001: Works without real model

The app supports Step, Auto, Snapshot, Restore, and Finish with Mock backend only.

### AC-MOCK-002: Inspectable request

Mock backend exposes or logs:

- requestId
- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- noiseStrength
- image presence
- noiseMask presence
- humanLayer presence

## 10. Minimal demo

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

## 11. Failure conditions

v0.1 is not complete if:

- Human Layer disappears after Generated Image update.
- Auto cannot be paused.
- Snapshot cannot be restored.
- Noise Brush changes Human Layer.
- UI becomes unusable after backend error.
- Generated Image is always recreated from scratch without current-image continuity.
- old responses can overwrite newer state.
- Model and Backend selection are ambiguous in state.
- Noise Strength has two conflicting meanings.

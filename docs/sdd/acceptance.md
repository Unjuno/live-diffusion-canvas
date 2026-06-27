# Acceptance Criteria v0.4

v0.1 is complete only when the following observable criteria pass.

## 1. Core completion

1. User can enter a Prompt.
2. User can select `selectedBackend` and `selectedModel`.
3. User can import an image into Guide Canvas.
4. User can draw on Human Draw Layer.
5. User can erase/hide parts of Imported Image non-destructively through Guide Erase Mask.
6. Guide Canvas is stored separately from Generated Image.
7. User can start Run loop.
8. User can Pause and Resume Run loop.
9. User can hold/drag Noise Brush on Generated Image.
10. While Noise Brush is active, the next DiffusionIntervention includes activeNoiseMask.
11. After Noise Brush release, active local rejection stops.
12. User can save a Snapshot.
13. User can restore a Snapshot.
14. User can run Finish from a selected Snapshot.
15. Generation errors are visible in the UI through `errorMessage` or equivalent.
16. The UI remains usable after a generation error.
17. Generated Image updates do not change Guide Canvas.
18. Old responses cannot overwrite newer Generated Image state.
19. Normal Explore updates do not always restart from blank state.
20. Explore Run updates include low global exploration noise or an inspectable mock equivalent.
21. Noise Brush is implemented as momentary local rejection / uncertainty boost, not as erase, persistent mask, or local Guide Canvas application.
22. The UI has no user-facing Step Mode or Step button.

## 2. UI criteria

### AC-UI-001: Layout

The app shows:

- Prompt input
- Backend / Model selector
- Run / Pause / Resume controls
- Guide Canvas
- Generated Image canvas
- Snapshot Timeline
- Generation settings
- Guide settings
- Noise Brush settings

### AC-UI-002: Settings

The user can change:

- CFG
- Global Exploration Noise Strength
- Local Rejection Strength
- Guide Influence
- Seed
- Update Interval
- Brush Size

### AC-UI-003: No Step Mode

The UI must not expose a Step button or user-facing Step Mode.

A private internal runtime tick function is allowed.

## 3. Guide Canvas criteria

### AC-GUIDE-001: Import Image

User can import an image into Imported Image Layer.

### AC-GUIDE-002: Draw

Drawing on Human Draw Layer appears immediately.

### AC-GUIDE-003: Separation

Generated Image updates do not clear or change Guide Canvas.

### AC-GUIDE-004: Clear Draw

Clear Draw clears only Human Draw Layer. Imported Image remains.

### AC-GUIDE-005: Guide Erase

Guide Erase Mask hides parts of Imported Image non-destructively.

### AC-GUIDE-006: Guide Composite

The app can export or inspect Guide Composite.

### AC-GUIDE-007: Guide-only import

Import Image does not automatically reset runtime session or start Base Image Init Mode.

### AC-GUIDE-008: Generated Image separation

Guide Canvas operations do not directly modify Generated Image pixels.

## 4. Runtime criteria

### AC-RUNTIME-001: Session

The runtime creates or simulates a session identified by sessionId.

### AC-RUNTIME-002: Stateful update

Run loop calls runtime update against existing session state when session state exists.

### AC-RUNTIME-003: Mock stateful behavior

Mock runtime visibly or inspectably changes state across updates. It must not behave as a pure stateless final-image generator.

### AC-RUNTIME-004: Backend positioning

The first working runtime must be Mock Stateful Runtime. Real runtime may be direct Diffusers/TinySD, ComfyUI adapter, InvokeAI fork/adapter, or another compatible adapter.

### AC-RUNTIME-005: Global exploration noise

Explore updates apply low global exploration noise or a visible/inspectable mock equivalent.

### AC-RUNTIME-006: Adapter semantics

Any fork or adapter must preserve Run loop, Guide Canvas, momentary Noise Brush, Snapshot, and stateful/simulated-state semantics.

## 5. Generation criteria

### AC-GEN-001: Run

When Prompt exists and Run is pressed, repeated runtime updates are attempted and Generated Image preview updates on success.

### AC-GEN-002: Status

While a request is running, generationStatus is `generating` or equivalent.

### AC-GEN-003: Error

When runtime fails, generationStatus becomes `error`, errorMessage is visible, and the app remains usable.

### AC-GEN-004: Current state continuity

When runtime state exists, Run loop uses it as the base. The app must not always recreate from blank state.

### AC-GEN-005: requestId

Every request has a requestId, and every response includes the same requestId.

### AC-GEN-006: Prompt update policy

Prompt changes during Run loop do not destroy the runtime session. They are applied from a later runtime update.

## 6. Noise Brush criteria

### AC-NB-001: Active mask drawing

Pressing and dragging Noise Brush on Generated Image creates or updates activeNoiseMask.

### AC-NB-002: Brush size

Brush Size changes the painted mask size.

### AC-NB-003: Active intervention inclusion

When noiseBrushActive is true and activeNoiseMask exists, Run loop includes it in DiffusionIntervention or the compatibility GenerationRequest.

### AC-NB-004: Guide Canvas unchanged

Noise Brush does not modify Guide Canvas.

### AC-NB-005: Local Rejection Strength meaning

Local Rejection Strength is interpreted as the strength of reintroducing uncertainty in the activeNoiseMask region.

### AC-NB-006: Semantic meaning

Noise Brush means that the current local solution in the masked region is rejected by the user.

It must not be implemented as:

- a normal erase operation
- a direct Guide Canvas apply operation

### AC-NB-007: Alternative search behavior

While Noise Brush is active, future updates should attempt to move the masked region away from the previous local interpretation while remaining conditioned by Prompt, Guide Composite, and surrounding runtime state.

### AC-NB-008: Momentary lifetime

When the user releases/cancels the brush interaction, noiseBrushActive becomes false and activeNoiseMask is cleared.

### AC-NB-009: No persistent mask by default

After release, local rejection boost must stop. lastNoiseMask may remain only as debug/history/Snapshot metadata and must not be used as active intervention.

## 7. Run Loop criteria

### AC-LOOP-001: Run start

Run starts repeated runtime updates every updateIntervalMs.

### AC-LOOP-002: Pause

Pause stops new runtime requests.

### AC-LOOP-003: Resume

Resume restarts repeated updates from the current runtime state.

### AC-LOOP-004: UI remains usable

During Run loop, the user can still edit Guide Canvas, hold/drag Noise Brush, save Snapshot, and press Pause.

### AC-LOOP-005: stale response protection

If an old response returns late, it must not overwrite newer Generated Image state or runtime state.

This can be implemented with requestId checking or single-flight request control.

### AC-LOOP-006: Rolling intervention loop

Run loop is a rolling intervention loop. It must not be implemented only as a forward-to-final-image process that stops the interaction after convergence.

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
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- guideInfluence
- generatedImageDataUrl

### AC-SNAP-002: Guide data and metadata

If present, Snapshot stores:

- importedImageDataUrl
- humanDrawLayerDataUrl
- guideEraseMaskDataUrl
- guideCompositeDataUrl

If lastNoiseMask exists, Snapshot may store lastNoiseMaskDataUrl as metadata.

### AC-SNAP-003: Restore

Restore Snapshot restores Generated Image, Guide Canvas data, and main generation settings.

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
updates: 12-30
globalExplorationNoiseStrength: 0.00
localRejectionStrength: 0.05-0.20
guideInfluence: 0.3-0.7
cfg: 3.0-6.0
```

### AC-FIN-004: Finish result

Finish success updates Generated Image and can be saved as a new Snapshot.

### AC-FIN-005: Finish stops Run

Starting Finish from Snapshot stops Run loop and prevents concurrent Run loop requests while Finish is running.

## 10. Mock runtime criteria

### AC-MOCK-001: Works without real model

The app supports Run, Pause, Resume, Snapshot, Restore, and Finish with Mock Stateful Runtime only.

### AC-MOCK-002: Inspectable request

Mock runtime exposes or logs:

- requestId
- sessionId
- prompt
- selectedBackend
- selectedModel
- seed
- cfg
- guideInfluence
- guideComposite presence
- globalExplorationNoiseStrength
- localRejectionStrength
- noiseBrushActive
- activeNoiseMask presence

## 11. Minimal demo

```text
Open app
→ enter Prompt
→ import image into Guide Canvas
→ draw/edit Guide Canvas
→ Run
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

- User-facing Step Mode or Step button exists.
- Guide Canvas disappears after Generated Image update.
- Run cannot be paused.
- Resume does not continue from current state.
- Snapshot cannot be restored.
- Noise Brush changes Guide Canvas.
- Noise Brush is implemented as a normal eraser.
- Noise Brush is implemented as direct local Guide Canvas application.
- Noise Brush remains active after pointerup / touchend / cancel.
- lastNoiseMask is restored as active rejection input.
- Imported Image import automatically triggers Base Image Init Mode.
- UI becomes unusable after runtime error.
- Generated Image is always recreated from blank state without current-state continuity.
- Run loop has no global exploration noise or mock equivalent.
- old responses can overwrite newer state.
- globalExplorationNoiseStrength and localRejectionStrength are conflated.
- fork/adapter route turns the product into ordinary one-shot inpainting UI.
- the runtime is specified only as a final-image generator.

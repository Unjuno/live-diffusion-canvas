# Tasks v0.3

Implement in this order. Do not skip ahead to model-quality work before the UI, state, and Mock Stateful Runtime work.

## Common rules

- Follow `docs/sdd/spec.md`.
- Use `docs/sdd/runtime.md` for runtime semantics.
- Use `docs/sdd/architecture.md` for types and module boundaries.
- Use `docs/sdd/acceptance.md` for completion checks.
- Start with `MockStatefulRuntime` before any real model backend.
- Keep Human Layer separate from Generated Image.
- Keep Noise Brush limited to Generated Image.
- Noise Brush is momentary: it applies only while the user is pressing or dragging.
- Normal Explore updates must not always regenerate from blank state.
- Explore Auto loop should include low global exploration noise.

## Task 0: Project scaffold

Purpose: create the minimal web app foundation.

Implement:

- Web app directory.
- Dependency management.
- Local dev command.
- Minimal lint, format, or type-check path.

Done when:

- The app starts locally.
- A placeholder page renders.
- Startup instructions exist.

Acceptance: AC-UI-001 partial.

## Task 1: Static UI

Purpose: make the product skeleton visible without AI.

Implement:

- App name.
- Backend / Model selector.
- Prompt input.
- Step / Auto / Pause controls.
- Human Layer canvas placeholder.
- Generated Image canvas placeholder.
- Settings panel.
- Snapshot Timeline placeholder.

Done when:

- All major UI regions exist.
- Controls are clickable or editable.
- No runtime is required.

Acceptance: AC-UI-001, AC-UI-002.

## Task 2: App state model

Purpose: centralize UI, runtime, canvas, and snapshot state.

Implement `AppState` from `docs/sdd/spec.md`, including:

- prompt
- selectedBackend
- selectedModel
- controlMode
- generationPhase
- generationStatus
- errorMessage
- steps
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- brushSize
- updateIntervalMs
- seed
- seedLocked
- humanLayer
- generatedImage
- noiseBrushActive
- activeNoiseMask
- lastNoiseMask
- runtimeSessionId
- latestRequestId
- snapshots
- selectedSnapshotId

Done when:

- UI updates write to state.
- State defaults match the spec.
- State can be inspected during development.

## Task 3: Human Layer canvas

Purpose: implement the user-controlled positive intervention layer.

Implement:

- Drawing on the left canvas.
- Clear Human Layer.
- Export to data URL or equivalent.
- Separate storage from Generated Image.

Done when:

- Drawing appears immediately.
- Clear only clears Human Layer.
- Generated Image updates do not change Human Layer.

Acceptance: AC-HL-001, AC-HL-002, AC-HL-003.

## Task 4: Runtime types and interface

Purpose: establish stateful runtime semantics before backend implementation.

Implement types from `docs/sdd/runtime.md` and `docs/sdd/architecture.md`:

- DiffusionRuntimeState
- DiffusionIntervention
- DiffusionRuntimeResponse
- DiffusionRuntime interface
- compatibility aliases for GenerationRequest / GenerationResponse if useful

Done when:

- A runtime can create a session.
- A runtime can apply an intervention.
- requestId and sessionId are part of the flow.
- The naming does not imply blank-state regeneration.
- `phase` and `controlMode` are not conflated.

Acceptance: AC-RUNTIME-001, AC-RUNTIME-002.

## Task 5: Mock Stateful Runtime

Purpose: validate UI and state flow before real model work.

Implement:

- `MockStatefulRuntime`.
- sessionId creation.
- pseudo runtime state update.
- preview image output.
- low global exploration noise simulation.
- momentary local rejection boost simulation.
- latencyMs output.
- visible or logged intervention metadata.
- error simulation path.

Done when:

- Step can produce a generated placeholder preview.
- requestId, sessionId, prompt, selectedBackend, selectedModel, seed, steps, cfg, globalExplorationNoiseStrength, localRejectionStrength, noiseBrushActive, activeNoiseMask presence, and humanLayer presence are inspectable.
- Runtime state visibly changes across updates.
- Global exploration noise is visible or inspectable across repeated Auto updates.
- Local rejection boost is visible or inspectable only while Noise Brush is active.
- Error handling can be tested.

Acceptance: AC-MOCK-001, AC-MOCK-002, AC-RUNTIME-003.

## Task 6: Basic runtime update flow

Purpose: connect state, controls, and runtime response.

Implement:

- Create runtime session when none exists.
- Build `DiffusionIntervention` from AppState.
- Increment latestRequestId for each request.
- Set generationStatus to generating.
- Call runtime.applyIntervention.
- Apply response only when requestId is current.
- Update generatedImage with response.previewImage.
- Keep updated runtime state for the next intervention.
- Set generationStatus to idle or error.
- Set errorMessage on failure.

Done when:

- Step performs exactly one runtime update.
- Generated Image preview is displayed.
- Runtime state persists across Step calls.
- Errors are visible and non-blocking.

Acceptance: AC-GEN-001, AC-GEN-002, AC-GEN-003, AC-GEN-004, AC-GEN-005.

## Task 7: Momentary Noise Brush input

Purpose: allow the user to reject a local solution only while actively brushing.

Implement:

- Brush interaction on Generated Image canvas.
- Brush Size setting.
- `noiseBrushActive` state.
- `activeNoiseMask` state.
- `lastNoiseMask` metadata.
- Include `activeNoiseMask` in DiffusionIntervention only when `noiseBrushActive` is true.
- Clear `activeNoiseMask` on pointerup / touchend / cancel.

Done when:

- User can paint a rejection mask on Generated Image.
- Brush Size changes the painted area size.
- Step and Auto interventions include activeNoiseMask only while the brush is active.
- On release, active local rejection stops.
- lastNoiseMask may remain only as metadata.
- Human Layer is not changed.

Acceptance: AC-NB-001 through AC-NB-009.

## Task 8: Step / Auto / Pause loop

Purpose: create the continuous intermediate-state interaction loop.

Implement:

- Step mode: one runtime update per click.
- Auto mode: try runtime updates every updateIntervalMs.
- Auto mode: include globalExplorationNoiseStrength in every Explore update.
- Auto mode: include localRejectionStrength only while noiseBrushActive is true.
- Pause mode: stop new requests.
- In-flight request handling by skip, wait, or single-flight.
- stale response protection with requestId or equivalent.

Done when:

- Step updates once.
- Auto updates repeatedly.
- Auto updates show or simulate low global exploration movement.
- Noise Brush affects local region only while active.
- Pause stops Auto.
- UI remains usable in Auto.
- Older responses cannot overwrite newer state.

Acceptance: AC-LOOP-001, AC-LOOP-002, AC-LOOP-003, AC-LOOP-004, AC-LOOP-005.

## Task 9: Snapshot save / restore

Purpose: preserve and recover promising intermediate states.

Implement:

- Save Snapshot.
- Snapshot type.
- Snapshot Timeline thumbnail list.
- Snapshot selection.
- Restore Snapshot.
- Optional runtimeStateRef if the runtime supports it.

Snapshot must store:

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
- humanLayerDataUrl when present
- lastNoiseMaskDataUrl when present as metadata
- runtimeStateRef when available

Done when:

- Snapshot save works.
- Restore reloads image and main settings.
- Restore uses runtime state when available.
- Restore can fall back to pseudo resume when runtime state is unavailable.
- Restore does not reactivate lastNoiseMask as active rejection input.
- Original Snapshot remains.

Acceptance: AC-SNAP-001, AC-SNAP-002, AC-SNAP-003, AC-SNAP-004, AC-SNAP-005, AC-SNAP-006.

## Task 10: Finish from Snapshot

Purpose: turn a selected intermediate state into a finishing base.

Implement:

- Select Snapshot.
- Finish from Snapshot button.
- Stop Auto when Finish starts.
- Build intervention using selected Snapshot generatedImage or runtime state as base.
- Apply finish-oriented settings.
- Display Finish result.

Done when:

- Finish requires selectedSnapshotId.
- Finish uses selected Snapshot as base.
- Runtime state is used if available.
- Auto is stopped while Finish runs.
- Original Snapshot remains.
- Finish result can be saved as a new Snapshot.

Acceptance: AC-FIN-001, AC-FIN-002, AC-FIN-003, AC-FIN-004, AC-FIN-005.

## Task 11: TinySD Stateful Latent Runtime hook

Purpose: add the first real stateful diffusion runtime after the mock flow works.

Implement:

- TinySD runtime behind DiffusionRuntime interface.
- Runtime session with latent/timestep where feasible.
- Prompt embedding cache where feasible.
- globalExplorationNoiseStrength as low ambient state noise where feasible.
- activeNoiseMask to latent-mask conversion only while noiseBrushActive is true.
- Local rejection noise injection where feasible.
- 1 to 3 denoise steps per Explore update.
- Preview decode.
- Fallback to mock when TinySD is unavailable.
- UI-visible error handling for backend failure.

Done when:

- selectedBackend can choose mock or tinysd.
- App still starts when TinySD is unavailable.
- TinySD path follows stateful runtime semantics where environment permits.
- Failures show errorMessage without breaking the UI.

## Task 12: Documentation and demo path

Purpose: make the project handoff-ready.

Implement:

- Local startup instructions.
- v0.1 demo steps.
- Known limitations.
- Explanation that runtime is stateful and not ordinary blank-state regeneration.
- Explanation that Noise Brush is momentary and only active while pressed/dragged.

Minimum demo:

```text
Prompt → Step → Human Layer → Auto → hold Noise Brush → release Noise Brush → Snapshot → Restore → Finish
```

Done when:

- A new agent can run the project.
- The demo path can be followed from documentation.

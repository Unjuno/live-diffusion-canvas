# Tasks v0.2

Implement in this order. Do not skip ahead to model-quality work before the UI, state, and Mock Stateful Runtime work.

## Common rules

- Follow `docs/sdd/spec.md`.
- Use `docs/sdd/runtime.md` for runtime semantics.
- Use `docs/sdd/architecture.md` for types and module boundaries.
- Use `docs/sdd/acceptance.md` for completion checks.
- Start with `MockStatefulRuntime` before any real model backend.
- Keep Human Layer separate from Generated Image.
- Keep Noise Brush limited to Generated Image.
- Normal Explore updates must not always regenerate from blank state.

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
- mode
- generationStatus
- errorMessage
- steps
- cfg
- noiseStrength
- brushSize
- updateIntervalMs
- seed
- seedLocked
- humanLayer
- generatedImage
- noiseMask
- runtimeSessionId
- latestRequestId
- snapshots
- selectedSnapshotId

Done when:

- UI updates write to state.
- State defaults match the spec.
- State can be inspected during development.

## Task 3: Human Layer canvas

Purpose: implement the user-controlled intervention layer.

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

Acceptance: AC-RUNTIME-001, AC-RUNTIME-002.

## Task 5: Mock Stateful Runtime

Purpose: validate UI and state flow before real model work.

Implement:

- `MockStatefulRuntime`.
- sessionId creation.
- pseudo runtime state update.
- preview image output.
- latencyMs output.
- visible or logged intervention metadata.
- error simulation path.

Done when:

- Step can produce a generated placeholder preview.
- requestId, sessionId, prompt, selectedBackend, selectedModel, seed, steps, cfg, noiseStrength, image presence, noiseMask presence, and humanLayer presence are inspectable.
- Runtime state visibly changes across updates.
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

## Task 7: Noise Brush mask

Purpose: allow the user to mark regions of Generated Image for runtime intervention.

Implement:

- Brush interaction on Generated Image canvas.
- Brush Size setting.
- noiseMask state.
- noiseMask export.
- Include noiseMask in the next DiffusionIntervention.

Done when:

- User can paint a mask on Generated Image.
- Brush Size changes the painted area size.
- Step and Auto interventions include noiseMask when present.
- Human Layer is not changed.

Acceptance: AC-NB-001, AC-NB-002, AC-NB-003, AC-NB-004, AC-NB-005.

## Task 8: Step / Auto / Pause loop

Purpose: create the continuous intermediate-state interaction loop.

Implement:

- Step mode: one runtime update per click.
- Auto mode: try runtime updates every updateIntervalMs.
- Pause mode: stop new requests.
- In-flight request handling by skip, wait, or single-flight.
- stale response protection with requestId or equivalent.

Done when:

- Step updates once.
- Auto updates repeatedly.
- Pause stops Auto.
- UI remains usable in Auto.
- Older responses cannot overwrite newer state.

Acceptance: AC-LOOP-001, AC-LOOP-002, AC-LOOP-003, AC-LOOP-004.

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
- noiseStrength
- generatedImageDataUrl
- humanLayerDataUrl when present
- noiseMaskDataUrl when present
- runtimeStateRef when available

Done when:

- Snapshot save works.
- Restore reloads image and main settings.
- Restore uses runtime state when available.
- Restore can fall back to pseudo resume when runtime state is unavailable.
- Original Snapshot remains.

Acceptance: AC-SNAP-001, AC-SNAP-002, AC-SNAP-003, AC-SNAP-004, AC-SNAP-005.

## Task 10: Finish from Snapshot

Purpose: turn a selected intermediate state into a finishing base.

Implement:

- Select Snapshot.
- Finish from Snapshot button.
- Build intervention using selected Snapshot generatedImage or runtime state as base.
- Apply finish-oriented settings.
- Display Finish result.

Done when:

- Finish requires selectedSnapshotId.
- Finish uses selected Snapshot as base.
- Runtime state is used if available.
- Original Snapshot remains.
- Finish result can be saved as a new Snapshot.

Acceptance: AC-FIN-001, AC-FIN-002, AC-FIN-003, AC-FIN-004.

## Task 11: TinySD Stateful Latent Runtime hook

Purpose: add the first real stateful diffusion runtime after the mock flow works.

Implement:

- TinySD runtime behind DiffusionRuntime interface.
- Runtime session with latent/timestep where feasible.
- Prompt embedding cache where feasible.
- noiseMask to latent-mask conversion where feasible.
- Local latent noise injection where feasible.
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

Minimum demo:

```text
Prompt → Step → Human Layer → Auto → Noise Brush → Snapshot → Restore → Finish
```

Done when:

- A new agent can run the project.
- The demo path can be followed from documentation.

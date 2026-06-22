# Tasks v0.1

Implement in this order. Do not skip ahead to model-quality work before the UI and mock flow work.

## Common rules

- Follow `docs/sdd/spec.md`.
- Use `docs/sdd/architecture.md` for types and module boundaries.
- Use `docs/sdd/acceptance.md` for completion checks.
- Start with `MockGenerationBackend` before any real model backend.
- Keep Human Layer separate from Generated Image.
- Keep Noise Brush limited to Generated Image.

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
- No backend is required.

Acceptance: AC-UI-001, AC-UI-002.

## Task 2: App state model

Purpose: centralize UI, generation, canvas, and snapshot state.

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
- snapshots
- selectedSnapshotId
- latestRequestId

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

## Task 4: Mock generation backend

Purpose: validate UI and state flow before real model work.

Implement:

- `GenerationRequest` and `GenerationResponse` types.
- `GenerationBackend` interface.
- `MockGenerationBackend`.
- Data URL image output.
- latencyMs output.
- Visible or logged request metadata.
- Error simulation path.

Done when:

- Step can produce a generated placeholder image.
- requestId, prompt, selectedBackend, selectedModel, seed, steps, cfg, noiseStrength, image presence, noiseMask presence, and humanLayer presence are inspectable.
- Error handling can be tested.

Acceptance: AC-MOCK-001, AC-MOCK-002.

## Task 5: Basic generation flow

Purpose: connect state, controls, and backend response.

Implement:

- Build `GenerationRequest` from AppState.
- Increment latestRequestId for each request.
- Set generationStatus to generating.
- Call backend.generate.
- Apply response only when requestId is current.
- Update generatedImage.
- Set generationStatus to idle or error.
- Set errorMessage on failure.

Done when:

- Step performs exactly one update.
- Generated Image is displayed.
- Errors are visible and non-blocking.

Acceptance: AC-GEN-001, AC-GEN-002, AC-GEN-003, AC-GEN-004.

## Task 6: Noise Brush mask

Purpose: allow the user to mark regions of Generated Image for re-generation.

Implement:

- Brush interaction on Generated Image canvas.
- Brush Size setting.
- noiseMask state.
- noiseMask export.
- Include noiseMask in the next GenerationRequest.

Done when:

- User can paint a mask on Generated Image.
- Brush Size changes the painted area size.
- Step and Auto requests include noiseMask when present.
- Human Layer is not changed.

Acceptance: AC-NB-001, AC-NB-002, AC-NB-003, AC-NB-004.

## Task 7: Step / Auto / Pause loop

Purpose: create the continuous intermediate-state interaction loop.

Implement:

- Step mode: one update per click.
- Auto mode: try updates every updateIntervalMs.
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

## Task 8: Snapshot save / restore

Purpose: preserve and recover promising intermediate states.

Implement:

- Save Snapshot.
- Snapshot type.
- Snapshot Timeline thumbnail list.
- Snapshot selection.
- Restore Snapshot.

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

Done when:

- Snapshot save works.
- Restore reloads image and main settings.
- Original Snapshot remains.

Acceptance: AC-SNAP-001, AC-SNAP-002, AC-SNAP-003, AC-SNAP-004.

## Task 9: Finish from Snapshot

Purpose: turn a selected intermediate state into a finishing base.

Implement:

- Select Snapshot.
- Finish from Snapshot button.
- Build request using selected Snapshot generatedImage as base image.
- Apply finish-oriented settings.
- Display Finish result.

Done when:

- Finish requires selectedSnapshotId.
- Finish uses selected Snapshot as base.
- Original Snapshot remains.
- Finish result can be saved as a new Snapshot.

Acceptance: AC-FIN-001, AC-FIN-002, AC-FIN-003, AC-FIN-004.

## Task 10: TinySD backend hook

Purpose: add a real lightweight backend after the mock flow works.

Implement:

- TinySD backend behind GenerationBackend interface.
- Fallback to mock when TinySD is unavailable.
- UI-visible error handling for backend failure.

Done when:

- selectedBackend can choose mock or tinysd.
- App still starts when TinySD is unavailable.
- Failures show errorMessage without breaking the UI.

## Task 11: Documentation and demo path

Purpose: make the project handoff-ready.

Implement:

- Local startup instructions.
- v0.1 demo steps.
- Known limitations.

Minimum demo:

```text
Prompt → Step → Human Layer → Auto → Noise Brush → Snapshot → Restore → Finish
```

Done when:

- A new agent can run the project.
- The demo path can be followed from documentation.

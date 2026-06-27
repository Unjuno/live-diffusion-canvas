# Tasks v0.4

Implement in this order. Do not skip ahead to model-quality work before the UI, Guide Canvas, state, and Mock Stateful Runtime work.

## Common rules

- Follow `docs/sdd/spec.md`.
- Use `docs/sdd/runtime.md` for runtime semantics.
- Use `docs/sdd/implementation_strategy.md` when choosing custom build, fork, or adapter route.
- Use `docs/sdd/architecture.md` for types and module boundaries.
- Use `docs/sdd/acceptance.md` for completion checks.
- Start with custom minimal UI and `MockStatefulRuntime` unless a fork/adapter demonstrably accelerates the same semantics.
- Do not implement user-facing Step Mode or Step button.
- Keep Guide Canvas separate from Generated Image.
- Keep Noise Brush limited to Generated Image.
- Noise Brush is momentary: it applies only while the user is pressing or dragging.
- Normal Explore updates must not always regenerate from blank state.
- Run loop should include low global exploration noise.

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

## Task 1: Static UI

Purpose: make the product skeleton visible without AI.

Implement:

- App name.
- Backend / Model selector.
- Prompt input.
- Run / Pause / Resume controls.
- Guide Canvas placeholder.
- Generated Image canvas placeholder.
- Settings panel.
- Snapshot Timeline placeholder.

Done when:

- All major UI regions exist.
- Controls are clickable or editable.
- No runtime is required.
- No user-facing Step button exists.

Acceptance: AC-UI-001, AC-UI-002.

## Task 2: App state model

Purpose: centralize UI, guide, runtime, canvas, and snapshot state.

Implement `AppState` from `docs/sdd/spec.md`, including:

- prompt
- selectedBackend
- selectedModel
- loopStatus
- generationPhase
- generationStatus
- errorMessage
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- guideInfluence
- brushSize
- updateIntervalMs
- seed
- seedLocked
- importedImage
- importedImageOpacity
- humanDrawLayer
- guideEraseMask
- guideComposite
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
- There is no `controlMode: "step"` or equivalent user-facing Step Mode state.

## Task 3: Guide Canvas

Purpose: implement the editable positive guide surface.

Implement:

- Import Image into Imported Image Layer.
- Imported Image opacity.
- Human Draw Layer drawing.
- Clear Draw affecting Human Draw Layer only.
- Guide Erase Mask for non-destructive hiding of Imported Image.
- Guide Composite export.
- Separate storage from Generated Image.

Done when:

- Imported image appears in Guide Canvas.
- User can draw on Human Draw Layer.
- Clear Draw does not remove Imported Image.
- Guide Erase hides imported image non-destructively.
- Guide Composite can be exported.
- Generated Image updates do not change Guide Canvas.

Acceptance: AC-GUIDE-001 through AC-GUIDE-008.

## Task 4: Runtime types and interface

Purpose: establish stateful runtime semantics before backend implementation.

Implement types from `docs/sdd/runtime.md` and `docs/sdd/architecture.md`:

- DiffusionRuntimeState
- DiffusionIntervention
- DiffusionRuntimeResponse
- DiffusionRuntime interface
- BackendAdapter compatibility aliases if useful

Done when:

- A runtime can create a session.
- A runtime can apply an intervention.
- requestId and sessionId are part of the flow.
- guideComposite and guideInfluence are part of the intervention.
- The naming does not imply blank-state regeneration.
- `phase` and `loopStatus` are not conflated.

Acceptance: AC-RUNTIME-001, AC-RUNTIME-002.

## Task 5: Mock Stateful Runtime

Purpose: validate UI and state flow before real model work.

Implement:

- `MockStatefulRuntime`.
- sessionId creation.
- pseudo runtime state update.
- preview image output.
- guideComposite influence simulation or debug visualization.
- low global exploration noise simulation.
- momentary local rejection boost simulation.
- latencyMs output.
- visible or logged intervention metadata.
- error simulation path.

Done when:

- Run can produce a generated placeholder preview.
- requestId, sessionId, prompt, selectedBackend, selectedModel, seed, cfg, guideInfluence, globalExplorationNoiseStrength, localRejectionStrength, noiseBrushActive, activeNoiseMask presence, and guideComposite presence are inspectable.
- Runtime state visibly changes across updates.
- Global exploration noise is visible or inspectable across repeated Run updates.
- Local rejection boost is visible or inspectable only while Noise Brush is active.
- Error handling can be tested.

Acceptance: AC-MOCK-001, AC-MOCK-002, AC-RUNTIME-003.

## Task 6: Basic Run loop

Purpose: connect state, controls, and runtime response.

Implement:

- Run starts loopStatus running.
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
- Pause stops new requests.
- Resume continues from current runtime state.

Done when:

- Run starts repeated runtime updates.
- Pause stops new runtime requests.
- Resume restarts loop from current state.
- Generated Image preview is displayed.
- Runtime state persists across Run updates.
- Errors are visible and non-blocking.

Acceptance: AC-GEN-001 through AC-GEN-006, AC-LOOP-001 through AC-LOOP-005.

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
- Run interventions include activeNoiseMask only while the brush is active.
- On release, active local rejection stops.
- lastNoiseMask may remain only as metadata.
- Guide Canvas is not changed.

Acceptance: AC-NB-001 through AC-NB-009.

## Task 8: Snapshot save / restore

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
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- guideInfluence
- generatedImageDataUrl
- importedImageDataUrl when present
- humanDrawLayerDataUrl when present
- guideEraseMaskDataUrl when present
- guideCompositeDataUrl when present
- lastNoiseMaskDataUrl when present as metadata
- runtimeStateRef when available

Done when:

- Snapshot save works.
- Restore reloads image, guide data, and main settings.
- Restore uses runtime state when available.
- Restore can fall back to pseudo resume when runtime state is unavailable.
- Restore does not reactivate lastNoiseMask as active rejection input.
- Original Snapshot remains.

Acceptance: AC-SNAP-001 through AC-SNAP-006.

## Task 9: Finish from Snapshot

Purpose: turn a selected intermediate state into a finishing base.

Implement:

- Select Snapshot.
- Finish from Snapshot button.
- Stop Run loop when Finish starts.
- Build intervention using selected Snapshot generatedImage or runtime state as base.
- Apply finish-oriented settings.
- Display Finish result.

Done when:

- Finish requires selectedSnapshotId.
- Finish uses selected Snapshot as base.
- Runtime state is used if available.
- Run loop is stopped while Finish runs.
- Original Snapshot remains.
- Finish result can be saved as a new Snapshot.

Acceptance: AC-FIN-001 through AC-FIN-005.

## Task 10: Backend adapter spike

Purpose: decide whether to build direct runtime or reuse an existing tool.

Investigate one or more:

- Direct Diffusers / TinySD runtime.
- ComfyUI backend adapter.
- InvokeAI fork or adapter.
- Other compatible tool adapter.

Done when:

- A short note records which route is chosen and why.
- The route preserves Guide Canvas, Run loop, momentary Noise Brush, and Snapshot semantics.
- If no real backend is feasible, Mock runtime remains the working v0.1 demo path.

## Task 11: Real backend hook

Purpose: add first real runtime path after the mock flow works.

Implement according to the chosen route:

- Runtime behind DiffusionRuntime interface.
- Runtime session or simulated session continuity.
- Prompt conditioning where feasible.
- guideComposite handling where feasible.
- globalExplorationNoiseStrength as low ambient state noise where feasible.
- activeNoiseMask to runtime mask only while noiseBrushActive is true.
- Local rejection noise injection where feasible.
- 1 to 3 updates per Explore tick.
- Preview decode or output fetch.
- Fallback to mock when backend unavailable.
- UI-visible error handling for backend failure.

Done when:

- selectedBackend can choose mock or the real/adapter backend.
- App still starts when real backend is unavailable.
- Real path follows stateful runtime semantics where environment permits.
- Failures show errorMessage without breaking the UI.

## Task 12: Documentation and demo path

Purpose: make the project handoff-ready.

Implement:

- Local startup instructions.
- v0.1 demo steps.
- Known limitations.
- Explanation that runtime is stateful and not ordinary blank-state regeneration.
- Explanation that Guide Canvas replaces old Human Layer.
- Explanation that Noise Brush is momentary and only active while pressed/dragged.
- Explanation that existing-tool fork/adapter is allowed but not required.

Minimum demo:

```text
Prompt → Import Image → Draw/Edit Guide Canvas → Run → hold Noise Brush → release Noise Brush → Snapshot → Restore → Finish
```

Done when:

- A new agent can run the project.
- The demo path can be followed from documentation.

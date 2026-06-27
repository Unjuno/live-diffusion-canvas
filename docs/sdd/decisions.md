# Decisions v0.4

## D-001: This is not a final-image app

Live Diffusion Canvas is not designed as a one-shot prompt-to-final-image tool.

The central workflow is:

```text
Explore intermediate state → Snapshot → Restore or Finish
```

## D-002: Guide Canvas replaces standalone Human Layer

The old Human Layer concept is promoted into Guide Canvas.

Guide Canvas contains:

```text
Imported Image Layer
Human Draw Layer
Guide Erase Mask
Guide Composite
```

Guide Canvas is the positive guide surface. Generated Image updates and Noise Brush must not modify it.

## D-003: Imported image is guide-only in v0.1

Imported Image Layer is used as an editable guide base.

Importing an image does not automatically initialize or reset the runtime session.

Base Image Init Mode may be added later, but is out of scope for v0.1.

## D-004: Noise Brush is not an eraser

Noise Brush marks a Generated Image region for runtime intervention. It does not mean ordinary deletion.

## D-005: v0.1 requires image Snapshot and permits runtime-state Snapshot

v0.1 must store image snapshots and main parameters.

Guide Canvas data should be stored when present.

Runtime-state Snapshot is optional.

If runtime state is unavailable, Restore may use image Snapshot pseudo resume.

## D-006: Mock Stateful Runtime comes first

The first implementation target is UI and state flow.

Mock Stateful Runtime must work before direct real model runtime or fork/adapter backend.

## D-007: Existing tool fork / adapter is allowed but not required

The project may use an existing tool through fork or adapter if that accelerates delivery.

Allowed route examples:

```text
custom minimal app + Mock runtime
direct Diffusers / TinySD runtime
ComfyUI backend adapter
InvokeAI fork or adapter
other compatible tool adapter
```

Forking is not a shortcut to changing the product concept.

Any fork or adapter must preserve:

```text
Guide Canvas
Run loop
global exploration noise
momentary Noise Brush
Snapshot / Restore / Finish
stateful or simulated-state runtime semantics
```

## D-008: Tree UI is out of scope

Snapshots may keep `parentId`, but v0.1 only requires a simple timeline UI.

Branch Tree UI is explicitly out of scope.

## D-009: Scheduler is fixed in v0.1

Scheduler / sampler settings are not shown in v0.1 UI.

The runtime may keep scheduler state internally.

## D-010: Run loop must be pausable

Continuous generation must remain controllable by the user.

## D-011: stale responses must not overwrite newer state

Run loop generation is asynchronous. The implementation must protect the current state from older responses.

Use requestId checking or single-flight control.

## D-012: selectedBackend and selectedModel are separate

`selectedBackend` chooses the runtime/backend implementation.

`selectedModel` is the model identifier passed to that runtime/backend.

This avoids ambiguity between the UI model selector and the actual execution backend.

## D-013: Exploration noise and local rejection strength are separate

v0.1 separates two strengths:

```text
globalExplorationNoiseStrength
localRejectionStrength
```

`globalExplorationNoiseStrength` is low ambient uncertainty that keeps Explore moving.

`localRejectionStrength` applies only while Noise Brush is active and controls uncertainty boost in the activeNoiseMask region.

These must not be collapsed into a single ambiguous `noiseStrength` value.

## D-014: Runtime abstraction is stateful

The backend abstraction is corrected from simple image-to-image generation to Stateful Diffusion Runtime.

The runtime should hold or simulate diffusion process state, accept interventions, advance a small number of updates, return a preview, and keep state for the next intervention.

## D-015: Extensions are intervention axes, not just model upgrades

Future extensions should be organized by what they intervene in:

```text
latent intervention
mask intervention
conditioning intervention
reference intervention
scheduler/runtime intervention
streaming intervention
```

This keeps ControlNet, IP-Adapter, LCM, StreamDiffusion, and SDXL-class backends aligned with the same product concept instead of treating them as unrelated model swaps.

## D-016: Noise Brush expresses local rejection, not local Guide Canvas application

Noise Brush does not mean "apply Guide Canvas here".

Noise Brush means that the current local solution is rejected by the user.

The runtime should increase uncertainty in that region so future updates move away from the current local interpretation and search for an alternative local solution.

Prompt, Guide Composite, and surrounding runtime state then act as conditions for that alternative search.

## D-017: Noise Brush is momentary in v0.1

Noise Brush applies only while the user is actively pressing or dragging.

On pointerup, touchend, or cancel:

```text
noiseBrushActive = false
activeNoiseMask = null
```

The local rejection boost must stop after release.

`lastNoiseMask` may remain as debug/history/Snapshot metadata only. It must not be restored as active rejection input.

Persistent / pinned rejection masks are out of scope for v0.1.

## D-018: Explore is a rolling intervention loop

Explore is not merely a forward-to-final-image process.

Each Run update should apply Guide Composite, low global exploration noise, then optional momentary local rejection boost if Noise Brush is active, then advance a few updates and keep runtime state.

## D-019: Prompt changes preserve session by default

Prompt changes during Run loop do not destroy the current runtime session.

The next runtime update should use the updated Prompt as a condition.

Only an explicit Reset Session action should create a new runtime session from scratch.

## D-020: Finish stops Run loop

Starting Finish from Snapshot should stop Run loop and prevent concurrent Run loop requests until Finish completes.

## D-021: No user-facing Step Mode in v0.1

v0.1 does not include a user-facing Step Mode or Step button.

An internal one-tick runtime update function is allowed as implementation detail only.

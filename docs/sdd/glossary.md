# Glossary v0.3

## Live Diffusion Canvas

A prototype for steering intermediate diffusion generation states with Prompt, Human Layer, Noise Brush, and Snapshot.

## Stateful Diffusion Runtime

A backend/runtime that holds diffusion process state, accepts human interventions, advances a small number of steps, returns a preview, and keeps updated state for the next intervention.

It is not a pure prompt-to-final-image API.

## DiffusionRuntimeState

The runtime state for an active session.

May include sessionId, prompt, prompt embedding, latent, timestep, scheduler state, seed, image size, and latest preview image.

## DiffusionIntervention

Human or UI input applied to a runtime state.

May include prompt changes, Human Layer, global exploration noise, momentary Noise Brush state, activeNoiseMask, localRejectionStrength, stepsToAdvance, and phase.

## DiffusionRuntimeResponse

Response from a runtime update.

Contains requestId, sessionId, previewImage, seed, optional timestep, and latencyMs.

## Prompt

Text condition that defines the generation direction.

Prompt changes do not automatically destroy the current runtime session.

## Human Layer

Independent drawing layer controlled by the user. It is not the final image. It is a positive intervention signal or guiding condition.

Generated Image updates, Noise Brush, and Auto Mode must not modify Human Layer.

Noise Brush does not mean that Human Layer is applied to the masked region.

## Generated Image

Preview image decoded or simulated from the current runtime state.

Step, Auto, and Finish update Generated Image.

## Global Exploration Noise

Low-strength uncertainty injected into the runtime state during Explore Mode to keep the generation process moving.

It is controlled by `globalExplorationNoiseStrength`.

## Noise Brush

Momentary brush used on Generated Image to mark a region whose **current local solution is rejected**.

It applies only while the user is actively pressing or dragging.

It is not:

- a normal eraser
- a direct Human Layer apply tool
- a persistent mask by default

Its role is to increase uncertainty in that region during active brushing so future runtime updates move away from the current local interpretation.

## noiseBrushActive

Boolean state indicating whether the user is currently pressing or dragging the Noise Brush.

When false, local rejection boost must not be applied.

## activeNoiseMask

Current mask produced while Noise Brush is active.

Semantic meaning:

```text
the current output in this active brushed region is not acceptable
```

The runtime uses this mask to increase local uncertainty and search for an alternative local solution.

In a real latent runtime, the mask may be resized to latent resolution and used for local uncertainty or noise injection.

`activeNoiseMask` must be cleared on pointerup, touchend, or cancel.

## lastNoiseMask

Optional metadata representing the most recent Noise Brush stroke.

It may be stored for debug, history, or Snapshot metadata.

It is not active intervention state and must not be restored as active rejection input.

## Local Rejection Strength

Single v0.1 value that controls the strength of reintroducing uncertainty in the activeNoiseMask region while Noise Brush is active.

It is controlled by `localRejectionStrength`.

## Snapshot

Saved intermediate state. It is used for restore and finish base.

Snapshot must store image and settings. It may also reference runtime state when available.

Snapshot may include `parentId`, but v0.1 does not require Branch Tree UI.

Snapshot may include `lastNoiseMaskDataUrl` as metadata, but Restore must not reactivate it.

## Restore

Operation that loads a saved Snapshot back into current state.

If runtime state is available, Restore may recover it. Otherwise it may use image Snapshot pseudo resume.

Restore must not reactivate lastNoiseMask as active rejection input.

## Finish

Operation that starts from a selected Snapshot and runs a stronger finishing update.

Starting Finish should stop Auto Mode.

## Explore Mode

Mode for finding promising intermediate structure.

Explore Mode uses a rolling intervention loop and low global exploration noise.

## Finish Mode

Mode for refining a selected Snapshot.

## Step Mode

One user action triggers one runtime update.

## Auto Mode

Runtime updates are attempted repeatedly at a configured interval.

If the previous request is still running, the implementation may skip or wait.

Auto Mode should behave as a rolling intervention loop, not only a forward-to-final-image process.

## Pause Mode

Stops Auto Mode while keeping UI interaction available.

## controlMode

UI control mode.

Allowed values:

```text
step
auto
pause
```

## generationPhase

Runtime phase.

Allowed values:

```text
explore
finish
```

## selectedBackend

The runtime/backend implementation selected for generation.

Allowed v0.1 values:

```text
mock
tinysd
```

## selectedModel

The model identifier passed to the selected backend.

For mock backend, `mock` is acceptable.

## Seed

Randomness control value.

## CFG / Guidance Scale

Controls how strongly Prompt is followed.

## Steps

Number of denoising or runtime-update steps.

## Update Interval

Auto Mode interval in milliseconds.

## Mock Stateful Runtime

Non-model runtime used to validate UI and state flow before real model integration.

It should simulate session state rather than behave like a purely stateless final-image generator.

## TinySD Stateful Latent Runtime

Preferred first real backend candidate for v0.1 if environment permits.

It should maintain latent state and timestep where feasible, apply global exploration noise, apply activeNoiseMask only while Noise Brush is active, advance a few steps, and decode preview.

## requestId

Monotonic request identifier used to prevent stale responses from overwriting newer state.

## sessionId

Identifier for an active runtime session.

## stale response

A response from an older request that returns after a newer request has already been issued.

It must not overwrite newer Generated Image state or runtime state.

## Pseudo resume

Using saved image Snapshot as a base image when runtime state is unavailable.

This is allowed in v0.1.

## True latent resume

Resume from latent state and timestep.

It is optional in v0.1 and may become stronger in later versions.

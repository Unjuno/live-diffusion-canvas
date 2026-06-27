# Glossary v0.4

## Live Diffusion Canvas

A prototype for steering intermediate diffusion generation states with Prompt, Guide Canvas, Noise Brush, and Snapshot.

## Stateful Diffusion Runtime

A backend/runtime that holds diffusion process state, accepts interventions, advances a small number of update steps, returns a preview, and keeps updated state for the next intervention.

It is not a pure prompt-to-final-image API.

## Guide Canvas

Editable positive guide surface used to direct generation.

It replaces the older standalone Human Layer concept.

Guide Canvas is separate from Generated Image and must not be modified by generation updates or Noise Brush.

## Imported Image Layer

Image imported into Guide Canvas as a guide base.

In v0.1, import is guide-only and does not automatically initialize runtime state from the image.

## Human Draw Layer

User-drawn sublayer inside Guide Canvas.

Clear Draw affects this sublayer only and must not delete Imported Image Layer.

## Guide Erase Mask

Non-destructive mask that hides parts of Imported Image Layer.

It is not Noise Brush and does not reject Generated Image content.

## Guide Composite

Composite guide image produced from Imported Image Layer, Guide Erase Mask, and Human Draw Layer.

It may be passed to the runtime as `guideComposite`.

## Guide Influence

Strength of Guide Composite influence on runtime updates.

Represented as `guideInfluence`.

## DiffusionRuntimeState

The runtime state for an active session.

May include sessionId, prompt, prompt embedding, latent, timestep, scheduler state, seed, image size, and latest preview image.

## DiffusionIntervention

Human or UI input applied to a runtime state.

May include prompt changes, guideComposite, guideInfluence, global exploration noise, momentary Noise Brush state, activeNoiseMask, localRejectionStrength, updatesToAdvance, and phase.

## DiffusionRuntimeResponse

Response from a runtime update.

Contains requestId, sessionId, previewImage, seed, optional timestep, and latencyMs.

## Prompt

Text condition that defines the generation direction.

Prompt changes do not automatically destroy the current runtime session.

## Generated Image

Preview image decoded or simulated from the current runtime state.

Run loop and Finish update Generated Image.

## Global Exploration Noise

Low-strength uncertainty injected into the runtime state during Explore to keep the generation process moving.

It is controlled by `globalExplorationNoiseStrength`.

## Noise Brush

Momentary brush used on Generated Image to mark a region whose current local solution is rejected.

It applies only while the user is actively pressing or dragging.

It is not:

- a normal eraser
- a direct Guide Canvas apply tool
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

Snapshot must store image and settings. It should store Guide Canvas data when present. It may also reference runtime state when available.

Snapshot may include `parentId`, but v0.1 does not require Branch Tree UI.

Snapshot may include `lastNoiseMaskDataUrl` as metadata, but Restore must not reactivate it.

## Restore

Operation that loads a saved Snapshot back into current state.

If runtime state is available, Restore may recover it. Otherwise it may use image Snapshot pseudo resume.

Restore must not reactivate lastNoiseMask as active rejection input.

## Finish

Operation that starts from a selected Snapshot and runs a stronger finishing update.

Starting Finish should stop Run loop.

## Explore

Phase for finding promising intermediate structure.

Explore uses a rolling intervention loop and low global exploration noise.

## Finish Phase

Phase for refining a selected Snapshot.

## Run loop

Repeated runtime updates at a configured interval.

Run loop is the primary interaction mode in v0.1.

## Pause

Stops new Run loop requests while keeping UI interaction available.

## Resume

Restarts Run loop from the current runtime state.

## Step Mode

User-facing Step Mode is out of scope for v0.1.

An internal one-tick runtime function is allowed, but it must not appear as a product mode.

## loopStatus

UI loop state.

Allowed values:

```text
idle
running
paused
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

May be `mock`, a direct runtime, or a fork/adapter backend.

## selectedModel

The model identifier passed to the selected backend.

For mock backend, `mock` is acceptable.

## Backend Adapter

A wrapper around an existing tool or backend that exposes Live Diffusion Canvas runtime semantics.

An adapter may simulate state for v0.1 but must not turn the product into ordinary one-shot generation.

## Fork Strategy

Using an existing project as a starting point is allowed if it preserves the SDD semantics.

Forking is optional, not required.

## Seed

Randomness control value.

## CFG / Guidance Scale

Controls how strongly Prompt is followed.

## Update Interval

Run loop interval in milliseconds.

## Mock Stateful Runtime

Non-model runtime used to validate UI and state flow before real model integration.

It should simulate session state rather than behave like a purely stateless final-image generator.

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

# Glossary v0.1

## Live Diffusion Canvas

A prototype for steering intermediate diffusion generation states with Prompt, Human Layer, Noise Brush, and Snapshot.

## Prompt

Text condition that defines the generation direction.

## Human Layer

Independent drawing layer controlled by the user. It is not the final image. It is an intervention signal.

Generated Image updates, Noise Brush, and Auto Mode must not modify Human Layer.

## Generated Image

Current image state shown on the generated-image canvas.

Step, Auto, and Finish update Generated Image.

## Noise Brush

Brush used on Generated Image to mark a region for re-generation. It is not a normal eraser.

## noiseMask

Mask created by Noise Brush. It tells the next GenerationRequest which region should be reconsidered.

## Noise Strength

Single v0.1 value that controls the strength of reinterpreting the noiseMask region.

v0.1 does not define a separate global denoise strength.

## Snapshot

Saved intermediate state. It is used for restore and finish base.

Snapshot may include `parentId`, but v0.1 does not require Branch Tree UI.

## Restore

Operation that loads a saved Snapshot back into current state.

## Finish

Operation that starts from a selected Snapshot and runs a stronger finishing generation.

## Explore Mode

Mode for finding promising intermediate structure.

## Finish Mode

Mode for refining a selected Snapshot.

## Step Mode

One user action triggers one generation update.

## Auto Mode

Generation updates are attempted repeatedly at a configured interval.

If the previous request is still running, the implementation may skip or wait.

## Pause Mode

Stops Auto Mode while keeping UI interaction available.

## selectedBackend

The backend implementation selected for generation.

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

Number of denoising or generation-update steps.

## Update Interval

Auto Mode interval in milliseconds.

## Mock backend

Non-model backend used to validate UI and state flow before real model integration.

## TinySD backend

Lightweight diffusion backend target after the mock implementation works.

## requestId

Monotonic request identifier used to prevent stale responses from overwriting newer state.

## stale response

A response from an older request that returns after a newer request has already been issued.

It must not overwrite newer Generated Image state.

## Pseudo resume

Using saved image Snapshot as a base image. This is allowed in v0.1.

## True latent resume

Resume from latent state and timestep. This is out of scope for v0.1.

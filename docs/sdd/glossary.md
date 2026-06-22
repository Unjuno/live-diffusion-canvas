# Glossary v0.1

## Live Diffusion Canvas

A prototype for steering intermediate diffusion generation states with Prompt, Human Layer, Noise Brush, and Snapshot.

## Prompt

Text condition that defines the generation direction.

## Human Layer

Independent drawing layer controlled by the user. It is not the final image. It is an intervention signal.

## Generated Image

Current image state shown on the right-side canvas.

## Noise Brush

Brush used on Generated Image to mark a region for re-generation. It is not a normal eraser.

## noiseMask

Mask created by Noise Brush. It tells the next generation request which region should be reconsidered.

## Snapshot

Saved intermediate state. It is used for restore, branch base, and finish base.

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

Generation updates repeatedly at a configured interval.

## Pause Mode

Stops Auto Mode while keeping UI interaction available.

## Seed

Randomness control value.

## CFG / Guidance Scale

Controls how strongly Prompt is followed.

## Steps

Number of denoising or generation-update steps.

## Noise Strength

Controls how much a region is returned to uncertainty.

## Update Interval

Auto Mode interval in milliseconds.

## Mock backend

Non-model backend used to validate UI and state flow before real model integration.

## TinySD backend

Lightweight diffusion backend target after the mock implementation works.

## Pseudo resume

Using saved image Snapshot as a base image. This is allowed in v0.1.

## True latent resume

Resume from latent state and timestep. This is out of scope for v0.1.

# Decisions v0.1

## D-001: This is not a final-image app

Live Diffusion Canvas is not designed as a one-shot prompt-to-final-image tool.

The central workflow is:

```text
Explore intermediate state → Snapshot → Restore or Finish
```

## D-002: Human Layer stays independent

Human Layer is a user-controlled intervention layer.

Generated Image updates, Noise Brush, and Auto Mode must not modify it.

## D-003: Noise Brush is not an eraser

Noise Brush marks a region for re-generation. It does not mean ordinary deletion.

## D-004: v0.1 uses pseudo resume

v0.1 stores image snapshots and main parameters.

True latent-state resume is valuable but out of scope for v0.1.

## D-005: Mock backend comes first

The first implementation target is UI and state flow.

Mock backend must work before TinySD or any other real model backend.

## D-006: TinySD is for interaction testing

TinySD or an equivalent lightweight model is treated as a real-time interaction testbed, not as a final image quality target.

## D-007: Tree UI is out of scope

Snapshots may keep `parentId`, but v0.1 only requires a simple timeline UI.

Branch Tree UI is explicitly out of scope.

## D-008: Scheduler is fixed in v0.1

Scheduler / sampler settings are not shown in v0.1 UI.

## D-009: Auto Mode must be pausable

Continuous generation must remain controllable by the user.

## D-010: stale responses must not overwrite newer state

Auto generation is asynchronous. The implementation must protect the current state from older responses.

Use requestId checking or single-flight control.

## D-011: selectedBackend and selectedModel are separate

`selectedBackend` chooses the generation backend implementation.

`selectedModel` is the model identifier passed to that backend.

This avoids ambiguity between the UI model selector and the actual execution backend.

## D-012: Noise Strength has one meaning in v0.1

v0.1 uses one `noiseStrength` value.

It controls the strength of reinterpreting the `noiseMask` region.

A separate global denoise strength may be added in a later version only after a spec update.

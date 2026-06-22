# Decisions v0.2

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

Noise Brush marks a region for runtime intervention. It does not mean ordinary deletion.

## D-004: v0.1 requires image Snapshot and permits runtime-state Snapshot

v0.1 must store image snapshots and main parameters.

Runtime-state Snapshot is optional.

If runtime state is unavailable, Restore may use image Snapshot pseudo resume.

## D-005: Mock Stateful Runtime comes first

The first implementation target is UI and state flow.

Mock Stateful Runtime must work before TinySD or any other real model runtime.

## D-006: TinySD is the first real stateful runtime candidate

TinySD or an equivalent lightweight diffusion model is not merely a distant extension.

If environment permits, TinySD should be treated as the first real Stateful Latent Runtime candidate for v0.1.

## D-007: Tree UI is out of scope

Snapshots may keep `parentId`, but v0.1 only requires a simple timeline UI.

Branch Tree UI is explicitly out of scope.

## D-008: Scheduler is fixed in v0.1

Scheduler / sampler settings are not shown in v0.1 UI.

The runtime may keep scheduler state internally.

## D-009: Auto Mode must be pausable

Continuous generation must remain controllable by the user.

## D-010: stale responses must not overwrite newer state

Auto generation is asynchronous. The implementation must protect the current state from older responses.

Use requestId checking or single-flight control.

## D-011: selectedBackend and selectedModel are separate

`selectedBackend` chooses the runtime/backend implementation.

`selectedModel` is the model identifier passed to that runtime/backend.

This avoids ambiguity between the UI model selector and the actual execution backend.

## D-012: Noise Strength has one meaning in v0.1

v0.1 uses one `noiseStrength` value.

It controls the strength of reintroducing uncertainty into the `noiseMask` region.

A separate global denoise strength may be added in a later version only after a spec update.

## D-013: Runtime abstraction is stateful

The backend abstraction is corrected from simple image-to-image generation to Stateful Diffusion Runtime.

The runtime should hold or simulate diffusion process state, accept interventions, advance a small number of steps, return a preview, and keep state for the next intervention.

## D-014: Extensions are intervention axes, not just model upgrades

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

## D-015: Noise Brush expresses local rejection, not local Human Layer application

Noise Brush does not mean "apply Human Layer here".

Noise Brush means that the current local solution is rejected by the user.

The runtime should increase uncertainty in that region so future updates move away from the current local interpretation and search for an alternative local solution.

Prompt, Human Layer, and surrounding runtime state then act as conditions for that alternative search.

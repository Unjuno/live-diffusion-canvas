# Stateful Diffusion Runtime v0.1

This document corrects the backend abstraction for Live Diffusion Canvas.

The core backend is not merely an image-in / image-out generator. The intended abstraction is a runtime that can hold diffusion process state, accept human interventions, advance a small number of diffusion steps, and return a preview.

## 1. Core principle

Live Diffusion Canvas should be designed around this loop:

```text
hold diffusion state
→ receive Human Layer / Noise Brush / Snapshot intervention
→ modify diffusion state or conditioning
→ advance a few steps
→ decode preview
→ keep updated state for the next intervention
```

This applies to TinySD, Stable Diffusion, SDXL, LCM-style runtimes, ControlNet-conditioned runtimes, IP-Adapter reference runtimes, and streaming diffusion runtimes when their internal state can be accessed or represented.

A fully black-box image API that only accepts a prompt and returns a final image is not the target backend model.

## 2. Runtime classes

### Runtime A: Mock Stateful Runtime

Purpose:

- validate UI and state transitions
- simulate requestId and session state
- support Snapshot, Restore, Finish, and error handling without a real model

This runtime is required for v0.1.

### Runtime B: TinySD Stateful Latent Runtime

Purpose:

- preferred first real backend candidate
- maintain latent state and timestep
- apply noiseMask to latent regions
- advance 1 to 3 denoise steps per update
- decode preview image when needed

This is not a distant real-time extension. It is the main v0.1 real-backend target if environment permits.

### Runtime C: SD / SDXL Stateful Latent Runtime

Purpose:

- same runtime concept with larger models
- potentially slower Explore loop
- more useful for Finish or higher-quality previews

### Runtime D: Masked Intervention Runtime

Purpose:

- strengthen Noise Brush using mask-aware denoising or inpainting
- SDEdit-style local re-noising
- RePaint-style masked denoising

### Runtime E: Conditioning Runtime

Purpose:

- turn Human Layer into an active conditioning signal
- ControlNet Scribble / Lineart
- T2I-Adapter structure control

### Runtime F: Reference Runtime

Purpose:

- use Snapshot as an image reference or anchor
- IP-Adapter-style snapshot reference

### Runtime G: Streaming Runtime

Purpose:

- keep an interactive generation stream alive
- optimize throughput and latency
- StreamDiffusion-style pipeline

## 3. Runtime state

A real stateful backend should expose or internally preserve a state equivalent to:

```ts
type DiffusionRuntimeState = {
  sessionId: string;

  prompt: string;
  promptEmbedding?: unknown;

  latent?: unknown;
  timestep?: number;
  schedulerState?: unknown;

  width: number;
  height: number;
  seed: number;

  latestPreviewImage?: string;
};
```

The exact type of `latent`, `promptEmbedding`, and `schedulerState` is backend-specific.

For Mock backend, these can be simulated.

## 4. Intervention payload

Human input should be represented as an intervention, not as a full regenerate command.

```ts
type DiffusionIntervention = {
  requestId: number;
  sessionId: string;

  prompt?: string;
  humanLayer?: string;
  noiseMask?: string;

  brushNoiseStrength: number;
  stepsToAdvance: number;

  mode: "explore" | "finish";
};
```

Interpretation notes:

- `humanLayer` is a positive intervention signal or guiding condition.
- `noiseMask` is a negative intervention signal meaning: "not this current local solution".
- The runtime must not interpret `noiseMask` as "apply Human Layer only in this region".
- Prompt, Human Layer, and surrounding runtime state guide the alternative search after noise intervention.

## 5. Runtime response

```ts
type DiffusionRuntimeResponse = {
  requestId: number;
  sessionId: string;

  previewImage: string;
  seed: number;
  timestep?: number;
  latencyMs: number;
};
```

## 6. Noise Brush as state intervention

Noise Brush should be interpreted as a **rejected local solution marker**.

It is not:

- a normal eraser
- a direct Human Layer apply brush

Its meaning is:

```text
the current local solution in this region is rejected by the user
→ increase uncertainty in that region
→ move future updates away from the current local interpretation
```

Preferred real-backend behavior:

```text
noiseMask
→ resize to latent resolution
→ inject additional uncertainty/noise into the masked latent region
→ denoise 1 to 3 steps
→ decode preview
→ keep updated latent/runtime state
```

Prompt, Human Layer, and surrounding runtime state then act as conditions for selecting a new local interpretation.

This differs from image-to-image regeneration. The runtime should avoid restarting from blank state during normal Explore updates.

## 7. Human Layer as intervention

v0.1 keeps Human Layer as an independent layer and passes it to the backend.

Possible backend interpretations:

```text
mock: render/debug overlay only
TinySD stateful: optional weak conditioning or ignored initially
Control runtime: Scribble / Lineart / adapter condition
```

v0.1 does not require Human Layer to become ControlNet conditioning, but the runtime abstraction must not block that future path.

Noise Brush does not mean "apply Human Layer here". Noise Brush only means that the current local solution is rejected and should be made uncertain again.

## 8. Snapshot and runtime state

v0.1 Snapshot still stores image and settings for portability.

A richer runtime may also store:

```text
sessionId
latent
timestep
schedulerState
promptEmbedding
```

For v0.1:

- image Snapshot is required
- runtime-state Snapshot is optional
- if runtime-state Snapshot is unavailable, Restore may use pseudo resume

## 9. GenerationBackend compatibility

`GenerationBackend` remains acceptable as a thin API name, but its intended semantics are stateful.

The implementation may keep these compatibility types:

```ts
type GenerationRequest = DiffusionIntervention & {
  selectedBackend: "mock" | "tinysd";
  selectedModel: string;
  image?: string;
};

type GenerationResponse = DiffusionRuntimeResponse;
```

The important constraint is behavioral:

```text
normal Explore updates should advance existing diffusion/session state, not always regenerate from blank state.
```

## 10. v0.1 implementation rule

v0.1 implementation order remains:

```text
Mock Stateful Runtime
→ UI/state/canvas/Snapshot correctness
→ TinySD Stateful Latent Runtime if feasible
```

LCM, StreamDiffusion, ControlNet, T2I-Adapter, IP-Adapter, and SDXL are not v0.1 implementation scope, but they are compatible with the stateful runtime abstraction.

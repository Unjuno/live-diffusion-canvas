# Stateful Diffusion Runtime v0.3

This document defines the backend abstraction for Live Diffusion Canvas.

The core backend is not merely an image-in / image-out generator. The intended abstraction is a runtime that can hold diffusion process state, accept human interventions, advance a small number of update steps, and return a preview.

Existing tools or forks may be used through adapters, but they must preserve the semantics in this document.

## 1. Core principle

Live Diffusion Canvas should be designed around this loop:

```text
hold diffusion state
→ inject low global exploration noise during Explore
→ receive Prompt / Guide Composite conditions
→ optionally receive momentary Noise Brush rejection input while the brush is active
→ modify diffusion state or conditioning
→ advance a few update steps
→ decode preview
→ keep updated state for the next intervention
```

A fully black-box image API that only accepts a prompt and returns a final image is not the target backend model.

A stateless backend may be wrapped by an adapter for v0.1 only if the adapter simulates session continuity and does not expose ordinary one-shot generation as the product behavior.

## 2. Runtime classes

### Runtime A: Mock Stateful Runtime

Required for v0.1.

Purpose:

- validate UI and state transitions
- simulate requestId and session state
- simulate global exploration noise
- simulate Guide Composite influence
- simulate momentary local rejection input
- support Snapshot, Restore, Finish, and error handling without a real model

### Runtime B: Direct Diffusers / TinySD Stateful Runtime

Preferred when precise runtime control matters.

Purpose:

- maintain latent state and timestep where feasible
- apply low global exploration noise in Explore
- apply guideComposite as weak conditioning or explicit debug-visible input
- apply activeNoiseMask to latent regions only while Noise Brush is active
- advance 1 to 3 update steps per loop tick
- decode preview image when needed

### Runtime C: ComfyUI Adapter

Allowed when workflow/model reuse matters.

Purpose:

- reuse ComfyUI workflows, nodes, model support, and API/custom node capabilities
- approximate or implement stateful runtime behavior through an adapter
- keep Live Diffusion Canvas UI separate from ComfyUI node editing unless explicitly chosen

### Runtime D: InvokeAI Fork / Adapter

Allowed when canvas reuse matters.

Purpose:

- reuse canvas/image management and image editing infrastructure
- adapt it to Guide Canvas, Run loop, momentary Noise Brush, and Snapshot semantics

### Runtime E: Other Existing Tool Adapter

Allowed if it satisfies the adapter contract and does not contradict the product semantics.

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

  guideComposite?: string;
  guideInfluence: number;

  globalExplorationNoiseStrength: number;

  noiseBrushActive: boolean;
  activeNoiseMask?: string;
  localRejectionStrength: number;

  updatesToAdvance: number;
  phase: "explore" | "finish";
};
```

Interpretation notes:

- `guideComposite` is a positive guide condition produced by Guide Canvas.
- `guideInfluence` controls how strongly the guide should pull the runtime.
- `globalExplorationNoiseStrength` is low ambient uncertainty used to keep Explore moving.
- `activeNoiseMask` is a negative intervention signal meaning: "not this current local solution".
- `activeNoiseMask` is only valid while `noiseBrushActive` is true.
- The runtime must not interpret `activeNoiseMask` as "apply Guide Canvas only in this region".
- Prompt, Guide Composite, and surrounding runtime state guide the alternative search after local rejection input.

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

## 6. Explore loop behavior

Explore is a rolling intervention loop.

It is not a forward-only process whose only goal is final timestep completion.

Each Explore update should conceptually do this:

```text
current runtime state
→ apply low global exploration noise
→ apply Prompt and Guide Composite conditions
→ if noiseBrushActive, apply local rejection boost in activeNoiseMask region
→ denoise / update 1 to 3 steps
→ decode preview
→ keep updated runtime state
```

`globalExplorationNoiseStrength` should be low by default.

`localRejectionStrength` should be stronger than the global value, but only applied while the user is actively pressing or dragging the Noise Brush.

## 7. Noise Brush as momentary local rejection input

Noise Brush should be interpreted as a **momentary rejected local solution marker**.

It is not:

- a normal eraser
- a direct Guide Canvas apply brush
- a persistent mask by default

Its meaning is:

```text
the current local solution in this region is rejected by the user
→ while the brush is active, increase uncertainty in that region
→ move future updates away from the current local interpretation
→ when the user releases the brush, stop local rejection boost
```

Preferred real-backend behavior:

```text
if noiseBrushActive and activeNoiseMask exists:
  activeNoiseMask
  → resize to latent resolution
  → inject additional uncertainty/noise into the masked latent region
else:
  do not apply local rejection boost

always in Explore:
  apply low global exploration noise
  apply guideComposite if present
  denoise/update 1 to 3 steps
  decode preview
  keep updated latent/runtime state
```

This differs from image-to-image regeneration. The runtime should avoid restarting from blank state during normal Explore updates.

## 8. Guide Canvas as intervention

v0.1 keeps Guide Canvas as an independent editable guide surface and passes `guideComposite` to the backend.

Possible backend interpretations:

```text
mock: render/debug overlay or visible influence only
direct Diffusers/TinySD: optional weak conditioning or explicit no-op with UI/debug disclosure
ComfyUI adapter: pass guideComposite into a workflow as image/conditioning input
InvokeAI adapter: reuse canvas image as guide input where feasible
future Control runtime: Scribble / Lineart / adapter condition
```

v0.1 does not require Guide Composite to become ControlNet conditioning, but the runtime abstraction must not block that future path.

Noise Brush does not mean "apply Guide Canvas here". Noise Brush only means that the current local solution is rejected and should be made uncertain again while the brush is active.

## 9. Snapshot and runtime state

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
- Guide Canvas data is required when present
- runtime-state Snapshot is optional
- lastNoiseMask metadata is optional
- activeNoiseMask must not be restored as active rejection input by default
- if runtime-state Snapshot is unavailable, Restore may use pseudo resume

## 10. Backend adapter compatibility

`GenerationBackend` remains acceptable as a thin API name, but its intended semantics are stateful.

The implementation may keep compatibility aliases:

```ts
type GenerationRequest = DiffusionIntervention & {
  selectedBackend: string;
  selectedModel: string;
  image?: string;
};

type GenerationResponse = DiffusionRuntimeResponse;
```

The important constraint is behavioral:

```text
normal Explore updates should advance existing diffusion/session state, not always regenerate from blank state.
```

## 11. v0.1 implementation rule

v0.1 implementation order:

```text
Mock Stateful Runtime
→ UI/state/canvas/Snapshot correctness
→ fork/adapter spike if useful
→ direct Diffusers/TinySD or adapter backend if feasible
```

ControlNet, T2I-Adapter, IP-Adapter, LCM, StreamDiffusion, and SDXL are not required v0.1 implementation scope, but they are compatible with the stateful runtime abstraction.

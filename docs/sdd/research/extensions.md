# Extension Research v0.4

This document records future extension candidates for Live Diffusion Canvas.

Extensions are not primarily model-name upgrades. They are different ways to intervene in diffusion runtime state or reuse existing tooling while preserving the product semantics.

These items are research notes unless explicitly promoted into `spec.md`, `runtime.md`, `implementation_strategy.md`, `architecture.md`, `tasks.md`, `acceptance.md`, and `decisions.md`.

## 1. Correct abstraction

The project should not be framed as:

```text
prompt or image input
→ regenerate image
→ return final image
```

The intended abstraction is:

```text
hold diffusion runtime state
→ apply low global exploration noise
→ apply Prompt and Guide Composite
→ optionally apply momentary local rejection while Noise Brush is active
→ advance a few updates
→ return preview
→ keep state alive
```

## 2. v0.1 tool reuse note

Using an existing tool is allowed if it accelerates delivery.

Potential routes:

```text
custom minimal app + Mock Stateful Runtime
direct Diffusers / TinySD runtime
ComfyUI backend adapter
InvokeAI fork or adapter
other compatible tool adapter
```

Tool reuse must not change the product into ordinary one-shot inpainting or prompt-to-final-image generation.

## 3. Intervention axes

Future extensions should be classified by the kind of state they intervene in.

| Axis | Intervention target | Example technologies |
|---|---|---|
| Latent intervention | latent state, timestep, scheduler | TinySD, SD1.5, SDXL |
| Mask intervention | active rejected masked latent/image region | SDEdit, RePaint, inpainting |
| Conditioning intervention | Guide Composite as external spatial condition | ControlNet, T2I-Adapter |
| Reference intervention | image/reference embedding | IP-Adapter, snapshot reference |
| Scheduler/runtime intervention | step schedule, consistency path | LCM, SDXL Turbo |
| Streaming intervention | persistent interactive pipeline | StreamDiffusion |
| Tool adapter | existing UI/backend reuse | ComfyUI, InvokeAI, Diffusers app |

## 4. Latent intervention

### 4.1 Direct Diffusers / TinySD Stateful Runtime

Preferred if precise runtime control matters.

Potential mapping:

```text
DiffusionRuntimeState.latent
+ DiffusionRuntimeState.timestep
+ Guide Composite
+ globalExplorationNoiseStrength
+ activeNoiseMask only while Noise Brush is active
→ low ambient latent noise
→ guide-aware update
→ optional local rejection noise injection
→ 1 to 3 updates
→ preview decode
```

Scope:

```text
v0.1 preferred real backend if feasible
```

### 4.2 SD / SDXL Stateful Latent Runtime

The same concept can apply to larger Stable Diffusion variants if the runtime can hold latent state and timestep.

Scope:

```text
future backend plugin
```

## 5. Mask intervention

Mask intervention in this project should be understood as:

- rejection of the current local solution
- temporary increase of local uncertainty while Noise Brush is active
- search for an alternative local interpretation

It should not be framed as "apply Guide Canvas inside the mask".

In v0.1, Noise Brush is momentary. Persistent / pinned masks are out of scope.

### 5.1 SDEdit-style local re-diffusion

Use the current state, inject noise, then denoise back toward the prompt and guide.

Potential mapping:

```text
activeNoiseMask = active rejected local solution region
localRejectionStrength = amount of local uncertainty injection
globalExplorationNoiseStrength = low ambient exploration noise
Prompt / Guide Composite / surrounding state = conditions for alternative search
```

Scope:

```text
v0.2 candidate
```

### 5.2 RePaint-style masked denoising

Use a mask to preserve known regions and regenerate unknown regions.

In this project, the masked region means "the current local solution is rejected," not "put Guide Canvas here."

Scope:

```text
v0.2 or v0.3 candidate
```

### 5.3 DiffEdit-style smart mask

Suggest the mask from semantic or prompt difference.

This extends manual Noise Brush into assisted rejection-mask proposal.

Scope:

```text
later than v0.2
```

## 6. Conditioning intervention

### 6.1 ControlNet Scribble / Lineart

Use Guide Composite as spatial conditioning.

Potential mapping:

```text
Guide Composite
→ scribble / lineart / image condition
→ conditioned diffusion state update
```

Scope:

```text
v0.3 candidate
```

### 6.2 T2I-Adapter

Use a lightweight adapter to condition generation with external structure.

Potential mapping:

```text
Guide Composite
→ structure adapter
→ generation control
```

Scope:

```text
v0.3 or later
```

## 7. Reference intervention

### 7.1 IP-Adapter snapshot reference

Use a selected Snapshot as an image prompt or reference.

Potential mapping:

```text
selected Snapshot
→ image reference embedding
→ preserve style, structure, or layout
```

Scope:

```text
v0.4 candidate
```

## 8. Tool adapter routes

### 8.1 ComfyUI backend adapter

Use ComfyUI for model/workflow execution while keeping Live Diffusion Canvas as the UX.

Scope:

```text
v0.1 spike or v0.2 backend route
```

### 8.2 InvokeAI fork or adapter

Use InvokeAI-like canvas infrastructure if canvas reuse is faster.

Scope:

```text
v0.1 spike or v0.2 backend route
```

## 9. Scheduler and runtime intervention

### 9.1 LCM / LCM-LoRA

Use low-step latent consistency behavior to make state updates faster.

This should be viewed as a runtime optimization for the same intervention loop, not as a separate product concept.

Scope:

```text
v0.3 or later
```

### 9.2 SDXL Turbo / ADD-style backend

Use few-step distilled generation for rapid previews.

Scope:

```text
v0.4 candidate
```

## 10. Streaming intervention

### 10.1 StreamDiffusion-style runtime

Use a pipeline designed for interactive image generation.

Scope:

```text
v0.5 or later
```

## 11. Revised roadmap

### v0.1

```text
Guide Canvas
Mock Stateful Runtime
Run loop
Global Exploration Noise
Momentary Noise Brush local rejection
Snapshot
Finish from Snapshot
Backend adapter spike if useful
```

### v0.2

```text
SDEdit-style local re-diffusion
RePaint-style mask handling
stronger adapter backend
```

### v0.3

```text
ControlNet Scribble / Lineart
T2I-Adapter structure control
LCM-style speedup if needed
```

### v0.4+

```text
IP-Adapter snapshot reference
SDXL Finish backend
StreamDiffusion-style runtime
```

## 12. Explicit non-scope for v0.1

The following must not be implemented in v0.1 unless the SDD is updated:

- user-facing Step Mode
- Base Image Init Mode
- SDEdit local re-diffusion as a required feature
- RePaint mask inpainting as a required feature
- DiffEdit smart mask
- ControlNet as required runtime
- T2I-Adapter as required runtime
- IP-Adapter as required runtime
- LCM / LCM-LoRA as required runtime
- SDXL Turbo
- StreamDiffusion
- persistent / pinned rejection masks
- SDXL Finish backend
- SD3 / SD3.5 / Flux-class backend

Important nuance:

```text
Existing tool fork/adapter use is allowed.
Custom minimal build remains the default if it is clearer and faster.
Noise Brush is a momentary rejection brush, not a persistent mask and not a Guide Canvas apply mask.
```

# Extension Research v0.2

This document records future extension candidates for Live Diffusion Canvas.

The correction in this version is important: extensions are not primarily model-name upgrades. They are different ways to intervene in diffusion runtime state.

These items are research notes unless explicitly promoted into `spec.md`, `architecture.md`, `tasks.md`, `acceptance.md`, and `decisions.md`.

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
→ apply human intervention
→ advance a few steps
→ return preview
→ keep state alive
```

This means TinySD is not merely a placeholder model. TinySD can be the first real stateful diffusion runtime if it exposes enough internal state for latent and timestep intervention.

## 2. Intervention axes

Future extensions should be classified by the kind of state they intervene in.

| Axis | Intervention target | Example technologies |
|---|---|---|
| Latent intervention | latent state, timestep, scheduler | TinySD, SD1.5, SDXL |
| Mask intervention | masked latent/image region | SDEdit, RePaint, inpainting |
| Conditioning intervention | external spatial condition | ControlNet, T2I-Adapter |
| Reference intervention | image/reference embedding | IP-Adapter, snapshot reference |
| Scheduler/runtime intervention | step schedule, consistency path | LCM, SDXL Turbo |
| Streaming intervention | persistent interactive pipeline | StreamDiffusion |

## 3. Latent intervention

### 3.1 TinySD Stateful Latent Runtime

TinySD should be treated as the preferred first real backend candidate, not as a distant extension.

Potential mapping:

```text
DiffusionRuntimeState.latent
+ DiffusionRuntimeState.timestep
+ noiseMask
→ local latent noise injection
→ 1 to 3 denoise steps
→ preview decode
```

Scope:

```text
v0.1 preferred real backend if feasible
```

### 3.2 SD / SDXL Stateful Latent Runtime

The same concept can apply to larger Stable Diffusion variants if the runtime can hold latent state and timestep.

Potential mapping:

```text
same intervention model
larger model
slower Explore loop
better Finish quality
```

Scope:

```text
future backend plugin
```

## 4. Mask intervention

### 4.1 SDEdit-style local re-diffusion

Use the current state, inject noise, then denoise back toward the prompt.

This is a direct formalization of Noise Brush.

Potential mapping:

```text
noiseMask = local intervention region
noiseStrength = amount of uncertainty injection
Prompt = denoise direction
```

Scope:

```text
v0.2 candidate
```

Reference:

- SDEdit: Guided Image Synthesis and Editing with Stochastic Differential Equations
- https://arxiv.org/abs/2108.01073

### 4.2 RePaint-style masked denoising

Use a mask to preserve known regions and regenerate unknown regions.

Potential mapping:

```text
unmasked region = preserved state
masked region = active uncertainty region
```

Scope:

```text
v0.2 or v0.3 candidate
```

Reference:

- RePaint: Inpainting using Denoising Diffusion Probabilistic Models
- https://arxiv.org/abs/2201.09865

### 4.3 DiffEdit-style smart mask

Suggest the mask from semantic or prompt difference.

This extends manual Noise Brush into assisted Noise Brush.

Scope:

```text
later than v0.2
```

Reference:

- DiffEdit: Diffusion-based semantic image editing with mask guidance
- https://arxiv.org/abs/2210.11427

## 5. Conditioning intervention

### 5.1 ControlNet Scribble / Lineart

Use Human Layer as spatial conditioning.

Potential mapping:

```text
Human Layer
→ scribble / lineart condition
→ conditioned diffusion state update
```

This changes Human Layer from independent stored layer into active conditioning input.

Scope:

```text
v0.3 candidate
```

Reference:

- Adding Conditional Control to Text-to-Image Diffusion Models
- https://arxiv.org/abs/2302.05543

### 5.2 T2I-Adapter

Use a lightweight adapter to condition generation with external structure.

Potential mapping:

```text
Human Layer
→ structure adapter
→ generation control
```

Scope:

```text
v0.3 or later
```

Reference:

- T2I-Adapter: Learning Adapters to Dig out More Controllable Ability for Text-to-Image Diffusion Models
- https://arxiv.org/abs/2302.08453

## 6. Reference intervention

### 6.1 IP-Adapter snapshot reference

Use a selected Snapshot as an image prompt or reference.

Potential mapping:

```text
selected Snapshot
→ image reference embedding
→ preserve style, structure, or layout
```

This matches the idea that a good intermediate state can become an anchor.

Scope:

```text
v0.4 candidate
```

Reference:

- IP-Adapter: Text Compatible Image Prompt Adapter for Text-to-Image Diffusion Models
- https://arxiv.org/abs/2308.06721

## 7. Scheduler and runtime intervention

### 7.1 LCM / LCM-LoRA

Use low-step latent consistency behavior to make state updates faster.

This should be viewed as a runtime optimization for the same intervention loop, not as a separate product concept.

Scope:

```text
v0.3 or later
```

Reference:

- Latent Consistency Models / LCM-LoRA
- https://arxiv.org/abs/2311.05556

### 7.2 SDXL Turbo / ADD-style backend

Use few-step distilled generation for rapid previews.

Potential mapping:

```text
Explore Mode = fast few-step runtime
Finish Mode = slower high-quality runtime
```

Scope:

```text
v0.4 candidate
```

Reference:

- Adversarial Diffusion Distillation
- https://arxiv.org/abs/2311.17042

## 8. Streaming intervention

### 8.1 StreamDiffusion-style runtime

Use a pipeline designed for interactive image generation.

Potential mapping:

```text
continuous human input
→ persistent generation stream
→ low-latency preview updates
```

Scope:

```text
v0.5 or later
```

Reference:

- StreamDiffusion: A Pipeline-level Solution for Real-time Interactive Generation
- https://arxiv.org/abs/2312.12491

## 9. Quality and model upgrades

### 9.1 SDXL Finish backend

Use SDXL or another high-quality model only for Finish Mode.

Potential mapping:

```text
Explore Mode = TinySD / fast runtime
Finish Mode = SDXL / higher-quality runtime
```

Scope:

```text
v0.4 candidate
```

Reference:

- SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis
- https://arxiv.org/abs/2307.01952

### 9.2 SD3 / SD3.5 / Flux-class backends

Treat future model families as runtime plugins.

Scope:

```text
future backend plugin only
```

## 10. Revised roadmap

### v0.1

Keep current SDD scope, but use stateful runtime terminology.

```text
Mock Stateful Runtime
TinySD Stateful Latent Runtime if feasible
Human Layer
Noise Brush
Snapshot
Finish from Snapshot
```

### v0.2

Strengthen Noise Brush as state intervention.

```text
SDEdit-style local re-diffusion
RePaint-style mask handling
```

### v0.3

Make Human Layer an active conditioning signal.

```text
ControlNet Scribble / Lineart
T2I-Adapter structure control
LCM-style speedup if needed
```

### v0.4

Use Snapshot as a stronger anchor and improve Finish.

```text
IP-Adapter snapshot reference
SDXL Finish backend
SDXL Turbo / ADD-style preview
```

### v0.5

Move toward persistent streaming generation.

```text
StreamDiffusion-style runtime
more aggressive runtime scheduling
```

## 11. Explicit non-scope for v0.1

The following must not be implemented in v0.1 unless the SDD is updated:

- SDEdit local re-diffusion as a required feature
- RePaint mask inpainting
- DiffEdit smart mask
- ControlNet
- T2I-Adapter
- IP-Adapter
- LCM / LCM-LoRA as required runtime
- SDXL Turbo
- StreamDiffusion
- SDXL Finish backend
- SD3 / SD3.5 / Flux-class backend

Important nuance:

```text
TinySD Stateful Latent Runtime is allowed as the first real v0.1 backend.
LCM / StreamDiffusion are future optimizations, not prerequisites for real-time-ish interaction.
```

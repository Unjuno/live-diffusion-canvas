# Extension Research v0.1

This document records future extension candidates for Live Diffusion Canvas.

These items are research notes only. They are not v0.1 implementation scope.

## 1. Current v0.1 assumption

v0.1 assumes a simple generation backend:

```text
mock first
→ TinySD or simple Stable Diffusion backend later
```

The current v0.1 scope remains:

```text
Prompt
+ Human Layer
+ Generated Image
+ Noise Brush
+ Snapshot
+ Restore / Finish from Snapshot
```

Do not add the extensions below to implementation tasks unless the SDD files are updated first.

## 2. Extension taxonomy

Future extensions are grouped into four tracks.

| Track | Purpose | Priority |
|---|---|---|
| Editing / re-diffusion | Make Noise Brush technically stronger | High |
| Control / conditioning | Make Human Layer influence generation more directly | Medium |
| Real-time acceleration | Make the loop feel live | High |
| Quality / model upgrade | Improve final output quality | Medium |

## 3. Editing / re-diffusion extensions

### 3.1 SDEdit-style local re-diffusion

Use the current image as input, add noise, then denoise back toward the prompt.

This is the closest conceptual match for Noise Brush.

Potential mapping:

```text
Generated Image = input image
noiseMask = local region to disturb
noiseStrength = how strongly to disturb it
Prompt = direction for denoising
```

Recommended scope:

```text
v0.2 candidate
```

Reference:

- SDEdit: Guided Image Synthesis and Editing with Stochastic Differential Equations
- https://arxiv.org/abs/2108.01073

### 3.2 RePaint-style mask inpainting

Treat Noise Brush as an inpainting mask.

Potential mapping:

```text
unmasked region = preserved Generated Image
masked region = re-generated target
```

Recommended scope:

```text
v0.2 or v0.3 candidate
```

Reference:

- RePaint: Inpainting using Denoising Diffusion Probabilistic Models
- https://arxiv.org/abs/2201.09865

### 3.3 DiffEdit-style smart mask

Use prompt difference or semantic difference to suggest the region that should change.

This would turn manual Noise Brush into assisted Noise Brush.

Recommended scope:

```text
later than v0.2
```

Reference:

- DiffEdit: Diffusion-based semantic image editing with mask guidance
- https://arxiv.org/abs/2210.11427

## 4. Control / conditioning extensions

### 4.1 ControlNet Scribble / Lineart

Use Human Layer as a spatial conditioning input.

Potential mapping:

```text
Human Layer
→ scribble / lineart condition
→ ControlNet-conditioned generation
```

This is a major scope increase because Human Layer changes from stored intervention layer to active conditioning signal.

Recommended scope:

```text
v0.3 candidate
```

Reference:

- Adding Conditional Control to Text-to-Image Diffusion Models
- https://arxiv.org/abs/2302.05543

### 4.2 T2I-Adapter

Use lightweight adapters to condition generation with structure, color, or other external signals while keeping the base model mostly fixed.

Potential mapping:

```text
Human Layer
→ structure adapter
→ generation control
```

Recommended scope:

```text
v0.3 or later
```

Reference:

- T2I-Adapter: Learning Adapters to Dig out More Controllable Ability for Text-to-Image Diffusion Models
- https://arxiv.org/abs/2302.08453

### 4.3 IP-Adapter snapshot reference

Use a selected Snapshot as an image prompt or reference.

Potential mapping:

```text
selected Snapshot
→ image prompt / reference
→ preserve style, structure, or layout during new generation
```

This is highly aligned with the idea that a good intermediate state can become an anchor.

Recommended scope:

```text
v0.4 candidate
```

Reference:

- IP-Adapter: Text Compatible Image Prompt Adapter for Text-to-Image Diffusion Models
- https://arxiv.org/abs/2308.06721

## 5. Real-time acceleration extensions

### 5.1 LCM / LCM-LoRA backend

Use a low-step latent consistency backend for faster updates.

Potential mapping:

```text
Explore Mode
→ low step generation
→ faster feedback loop
```

Recommended scope:

```text
v0.3 candidate
```

Reference:

- Latent Consistency Models / LCM-LoRA
- https://arxiv.org/abs/2311.05556

### 5.2 SDXL Turbo / ADD-style backend

Use distilled few-step generation for fast exploration or finish preview.

Potential mapping:

```text
Explore Mode = fast few-step model
Finish Mode = slower higher-quality model
```

Recommended scope:

```text
v0.4 candidate
```

Reference:

- Adversarial Diffusion Distillation
- https://arxiv.org/abs/2311.17042

### 5.3 StreamDiffusion-style runtime

Use a streaming pipeline designed for interactive image generation.

Potential mapping:

```text
continuous input updates
→ streaming generation backend
→ near-real-time preview
```

Recommended scope:

```text
v0.5 or later
```

Reference:

- StreamDiffusion: A Pipeline-level Solution for Real-time Interactive Generation
- https://arxiv.org/abs/2312.12491

## 6. Quality / model upgrade extensions

### 6.1 SDXL Finish backend

Use SDXL or another higher-quality model only for Finish Mode.

Potential mapping:

```text
Explore Mode = TinySD / mock / fast backend
Finish Mode = SDXL or higher-quality backend
```

Recommended scope:

```text
v0.4 candidate
```

Reference:

- SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis
- https://arxiv.org/abs/2307.01952

### 6.2 SD3 / SD3.5 / Flux-class backends

Treat future model families as backend plugins, not as v0.1 assumptions.

Recommended scope:

```text
future backend plugin only
```

## 7. Recommended roadmap

### v0.1

Keep the current SDD scope.

```text
Mock backend
TinySD backend hook
Human Layer
Noise Brush
Snapshot
Finish from Snapshot
```

### v0.2

Strengthen Noise Brush.

```text
SDEdit-style local re-diffusion
RePaint-style mask handling
```

### v0.3

Make Human Layer an active conditioning signal.

```text
ControlNet Scribble / Lineart
T2I-Adapter structure control
```

### v0.4

Use Snapshot as a stronger anchor.

```text
IP-Adapter snapshot reference
SDXL Finish backend
```

### v0.5

Move toward real-time generation.

```text
LCM / LCM-LoRA
SDXL Turbo / ADD-style backend
StreamDiffusion-style runtime
```

## 8. Explicit non-scope for v0.1

The following must not be implemented in v0.1:

- SDEdit local re-diffusion
- RePaint mask inpainting
- DiffEdit smart mask
- ControlNet
- T2I-Adapter
- IP-Adapter
- LCM / LCM-LoRA
- SDXL Turbo
- StreamDiffusion
- SDXL Finish backend
- SD3 / SD3.5 / Flux-class backend

They may be used only as design references unless the SDD is updated.

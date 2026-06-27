# Implementation Strategy v0.1

This document defines how to build Live Diffusion Canvas quickly without overbuilding from scratch.

## 1. Principle

The project may be implemented by:

```text
forking an existing image generation UI
using an existing diffusion backend as an adapter
building a thin custom frontend on top of an existing backend
or implementing a minimal runtime directly
```

The implementation choice must preserve the product semantics from `spec.md` and `runtime.md`:

```text
Run loop
→ stateful or simulated-state runtime update
→ low global exploration noise
→ Guide Canvas as positive guide
→ momentary Noise Brush as local rejection input
→ Snapshot / Restore / Finish
```

Do not choose a base project if it forces the product back into ordinary prompt-to-final-image or one-shot inpainting semantics.

## 2. Preferred implementation routes

### Route A: Minimal custom app + Diffusers/TinySD runtime

Use this when the goal is conceptual clarity and direct control.

Shape:

```text
custom web UI
→ local Python runtime server
→ Diffusers or TinySD-style backend
→ custom stateful runtime abstraction
```

Pros:

- cleanest match to the SDD
- easiest to implement momentary Noise Brush semantics precisely
- easiest to keep Guide Canvas and Generated Image separate
- easiest to avoid inherited UI complexity

Cons:

- more backend work
- real-time performance is uncertain
- canvas tooling must be built

Use this as the default route if the team wants a focused prototype.

### Route B: InvokeAI fork or adapter

Use this when the fastest path is a canvas-first workflow.

InvokeAI already has a web UI, Unified Canvas, brush-style image editing, gallery/boards, and workflow concepts.

Shape:

```text
InvokeAI fork or local adapter
→ reuse canvas/image management where possible
→ add Guide Canvas semantics
→ add Run loop / momentary Noise Brush semantics
```

Pros:

- strong existing canvas foundation
- closer to image editing UX
- useful if importing/editing guide images is important

Cons:

- existing semantics may be closer to inpainting than stateful live intervention
- larger codebase
- may require deeper UI surgery

Use this route if canvas UX speed matters more than runtime purity.

### Route C: ComfyUI backend / custom node / API adapter

Use this when the goal is to reuse powerful diffusion workflows and model support.

ComfyUI has a node/graph workflow system, broad model support, API usage, inpainting, ControlNet/T2I-Adapter support, and workflow save/load.

Shape:

```text
custom Live Diffusion Canvas frontend
→ ComfyUI API or custom node backend
→ workflow executes guide + noise intervention approximations
```

Pros:

- strong model and workflow ecosystem
- extensible through nodes
- easier to experiment with ControlNet, inpainting, LCM, etc.

Cons:

- ComfyUI UI itself is not the intended UX
- true stateful runtime behavior may require custom nodes or approximation
- risk of becoming workflow-editing instead of live canvas interaction

Use this route if backend capability matters more than frontend speed.

### Route D: AUTOMATIC1111 / Forge style extension

Use this only if the goal is compatibility with existing SD WebUI users.

Shape:

```text
extension or fork
→ reuse img2img/inpaint/script infrastructure
→ approximate Run loop and momentary rejection brush
```

Pros:

- broad community familiarity
- existing img2img/inpainting features
- extension ecosystem

Cons:

- UI model is less aligned with live stateful canvas
- harder to keep product concept clean
- likely becomes repeated img2img rather than true stateful runtime

Use this route only as a fallback.

## 3. Recommended v0.1 route

For v0.1, prefer this order:

```text
1. Custom minimal web UI with Mock Stateful Runtime
2. Guide Canvas implementation
3. Momentary Noise Brush implementation
4. Snapshot / Restore / Finish
5. Backend adapter spike:
   a. Diffusers/TinySD direct runtime, or
   b. InvokeAI adapter if canvas reuse is faster, or
   c. ComfyUI adapter if workflow/model reuse is faster
```

Do not block the UI prototype on a real diffusion backend.

Mock Stateful Runtime must be sufficient to demonstrate:

```text
Run loop
low global exploration movement
Guide Canvas separation
momentary Noise Brush local rejection
Snapshot / Restore / Finish
```

## 4. Fork usage policy

Forking is allowed if:

- license is compatible with the intended use
- the fork does not force Step Mode back into the product
- Guide Canvas remains separate from Generated Image
- Noise Brush remains momentary
- local rejection is not implemented as normal erase
- lastNoiseMask is not restored as active intervention
- Snapshot semantics remain intact

Forking is not a shortcut to changing the product concept.

## 5. Backend adapter contract

Any fork or existing backend must satisfy this adapter shape:

```ts
type BackendAdapter = {
  name: string;

  createSession(input: {
    prompt: string;
    seed: number;
    width: number;
    height: number;
    guideComposite?: string;
  }): Promise<DiffusionRuntimeState>;

  applyIntervention(
    state: DiffusionRuntimeState,
    intervention: DiffusionIntervention
  ): Promise<{
    state: DiffusionRuntimeState;
    response: DiffusionRuntimeResponse;
  }>;
};
```

If the backend is stateless, the adapter may simulate state for v0.1, but it must not expose that behavior to the product UI as ordinary one-shot generation.

## 6. Decision rule

Choose implementation route by this rule:

```text
If speed of UX prototype matters most:
  custom UI + mock runtime first.

If canvas editing reuse matters most:
  investigate InvokeAI fork/adapter.

If model/workflow reuse matters most:
  investigate ComfyUI backend adapter.

If precise runtime control matters most:
  use Diffusers/TinySD direct runtime.
```

## 7. Non-goals

The fork strategy does not add these to v0.1 scope:

- user-facing Step Mode
- persistent / pinned rejection mask
- full ControlNet integration
- full Base Image Init Mode
- full latent snapshot persistence
- production deployment
- multi-user collaboration

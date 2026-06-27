# Implementation Strategy v0.2

This document defines how to build Live Diffusion Canvas quickly without overbuilding from scratch.

The selected v0.1 stack is fixed in `docs/sdd/tech_stack.md`.

## 1. Principle

The project may be implemented by:

```text
building a custom minimal web UI
using an existing diffusion backend as an adapter
forking an existing image generation UI only if it preserves product semantics
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

## 2. Selected v0.1 stack

```text
Frontend:
  React + Vite + TypeScript

Canvas:
  Konva + react-konva

State:
  Zustand

Snapshot persistence:
  Dexie + IndexedDB

Backend API:
  Python FastAPI

Transport:
  HTTP-first
  WebSocket optional later

Runtime:
  Mock Stateful Runtime first
  Diffusers + TinySD spike second
  ComfyUI adapter later if useful
```

This stack is selected because v0.1 needs a clean canvas-heavy SPA, predictable state, local image/blob persistence, and a Python path to diffusion runtime experiments.

## 3. Preferred implementation routes

### Route A: Custom minimal app + Mock Stateful Runtime

Default v0.1 route.

Shape:

```text
React + Vite + TypeScript frontend
→ Konva / react-konva canvas UI
→ Zustand state
→ Dexie / IndexedDB Snapshot persistence
→ Mock Stateful Runtime in frontend or local runtime layer
```

Pros:

- cleanest match to the SDD
- fastest way to validate Guide Canvas, Run loop, Noise Brush, and Snapshot semantics
- easiest to avoid inherited UI complexity
- not blocked by GPU/model setup

Cons:

- real image quality is not validated
- canvas tooling must be implemented

Use this route first.

### Route B: Custom frontend + FastAPI + Diffusers/TinySD

First real backend spike route.

Shape:

```text
React/Vite frontend
→ HTTP-first FastAPI runtime service
→ Diffusers + TinySD or other small SD-compatible model
→ custom stateful or pseudo-stateful runtime abstraction
```

Pros:

- best path for precise runtime control
- natural Python/Diffusers integration
- easy to test guideComposite and activeNoiseMask transport
- can evolve toward true latent/timestep experimentation

Cons:

- real-time performance is uncertain
- true latent resume may be backend-specific
- TinySD is a runtime spike target, not product-quality output

Use this after Mock runtime validates the UX.

### Route C: Custom frontend + ComfyUI adapter

Use this when model/workflow reuse matters.

Shape:

```text
custom Live Diffusion Canvas frontend
→ ComfyUI API or custom node backend
→ workflow executes guide + mask intervention approximations
```

Pros:

- strong model and workflow ecosystem
- extensible through nodes
- easier to experiment with ControlNet, inpainting, LCM, etc.

Cons:

- ComfyUI UI itself is not the intended UX
- true stateful runtime behavior may require custom nodes or approximation
- risk of becoming workflow-editing instead of live canvas interaction

Use this after the custom UI semantics are stable.

### Route D: InvokeAI reference or adapter

Use as a reference for canvas/product patterns, not as the default route.

Pros:

- mature canvas-oriented image generation product
- useful reference for image management and editing UX

Cons:

- large inherited codebase
- existing semantics may be closer to image editing/inpainting than live stateful intervention
- fork-first route risks slowing the custom product concept

Use as reference first. Consider adapter/fork only if it clearly accelerates without changing the concept.

### Route E: AUTOMATIC1111 / Forge

Not a first candidate.

Reasons:

- less aligned with live stateful canvas semantics
- likely to collapse into repeated img2img/inpainting
- license and extension constraints add decision cost

Use only as a fallback compatibility route.

## 4. Recommended v0.1 route

For v0.1, implement in this order:

```text
1. React + Vite + TypeScript scaffold
2. Zustand AppState
3. Konva Guide Canvas
4. Konva Generated Image Canvas
5. Mock Stateful Runtime
6. Run / Pause / Resume loop
7. Momentary Noise Brush
8. Dexie + IndexedDB Snapshot persistence
9. Snapshot / Restore / Finish
10. FastAPI runtime service scaffold
11. Diffusers + TinySD spike
12. ComfyUI adapter spike if needed
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

## 5. Fork / adapter usage policy

Forking or adapting is allowed if:

- license is compatible with the intended use
- the route does not force Step Mode back into the product
- Guide Canvas remains separate from Generated Image
- Noise Brush remains momentary
- local rejection is not implemented as normal erase
- Guide Canvas is not locally applied by Noise Brush
- lastNoiseMask is not restored as active intervention
- Snapshot semantics remain intact
- the product remains a live intervention canvas, not ordinary inpainting UI

Forking is not a shortcut to changing the product concept.

## 6. Backend adapter contract

Any real backend must satisfy this adapter shape:

```ts
type BackendAdapter = {
  name: string;

  createSession(input: {
    prompt: string;
    seed: number;
    width: number;
    height: number;
    guideComposite?: Blob | string;
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

## 7. Decision rule

Choose implementation route by this rule:

```text
If building v0.1 UX:
  React/Vite + Konva + Zustand + Dexie + Mock Runtime.

If testing precise real runtime control:
  FastAPI + Diffusers/TinySD.

If reusing powerful model workflows:
  ComfyUI backend adapter.

If studying mature canvas UX:
  inspect InvokeAI as reference.

If seeking SD WebUI compatibility:
  A1111/Forge only as fallback.
```

## 8. Non-goals

The stack decision does not add these to v0.1 scope:

- user-facing Step Mode
- persistent / pinned rejection mask
- full ControlNet integration
- full Base Image Init Mode
- full latent snapshot persistence
- production deployment
- multi-user collaboration
- auth/account system
- cloud object storage
- WebSocket as required transport
- ComfyUI as primary UI
- InvokeAI fork-first implementation
- AUTOMATIC1111 / Forge first backend

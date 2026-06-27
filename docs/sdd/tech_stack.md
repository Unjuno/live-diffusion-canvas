# Technology Stack v0.1

This document fixes the initial technology stack for Live Diffusion Canvas v0.1.

The stack is selected for fast interaction prototyping, canvas-heavy UI work, state clarity, local persistence, and a clean path from Mock Stateful Runtime to a real diffusion backend.

## 1. Selected stack

```text
Frontend:
  React + Vite + TypeScript

Canvas:
  Konva + react-konva

App state:
  Zustand

Snapshot persistence:
  Dexie + IndexedDB

Backend API:
  Python FastAPI

Transport:
  HTTP-first
  WebSocket optional later

Runtime v0.1:
  Mock Stateful Runtime first

Real backend spike:
  Diffusers + TinySD or small Stable Diffusion model

Existing tool route:
  ComfyUI adapter later
  InvokeAI reference only
  AUTOMATIC1111 / Forge not first candidate
```

## 2. Rationale

The hardest part of v0.1 is not final image quality.

The hardest part is preserving this interaction:

```text
Guide Canvas
→ Run loop
→ low global exploration movement
→ momentary Noise Brush local rejection
→ Snapshot / Restore / Finish
```

Therefore the first stack must make UI, canvas state, masks, export, async runtime requests, and persistence simple.

## 3. Frontend selection

Use:

```text
React + Vite + TypeScript
```

Reasons:

- fast local development
- minimal routing / SSR complexity
- strong canvas and state-management ecosystem
- easy integration with a local Python runtime server
- good fit for an interaction-heavy SPA

Do not use Next.js as the default v0.1 app shell unless routing, SSR, auth, or deployment needs become primary.

## 4. Canvas selection

Use:

```text
Konva + react-konva
```

Reasons:

- natural React integration
- Stage / Layer / Shape model fits Guide Canvas and Generated Image Canvas
- image import, opacity, pointer interactions, and export are straightforward
- easier than raw Canvas for v0.1 layer composition
- less rendering-engine overhead than PixiJS for this product stage

Use Konva for visible interactive canvas layers.

Use helper functions where needed to export masks/composites to Blob or Data URL.

Do not make Konva JSON the only Snapshot source of truth.

## 5. State selection

Use:

```text
Zustand
```

Reasons:

- low boilerplate
- clear global AppState
- simple async action handling
- good fit for Run loop state, requestId, selectedSnapshotId, activeNoiseMask, and runtimeSessionId

Redux Toolkit is not needed for v0.1 unless state transitions become much more complex.

## 6. Persistence selection

Use:

```text
Dexie + IndexedDB
```

Reasons:

- IndexedDB is suitable for larger local structured data and blobs
- Snapshot data includes image blobs, guide composites, masks, and preview images
- Dexie makes IndexedDB usage simpler and more maintainable

Snapshot persistence should store semantic data, not just canvas implementation data.

Preferred Snapshot storage:

```ts
type PersistedSnapshot = {
  id: string;
  parentId: string | null;
  createdAt: number;

  prompt: string;
  selectedBackend: string;
  selectedModel: string;

  seed: number;
  cfg: number;
  guideInfluence: number;
  globalExplorationNoiseStrength: number;
  localRejectionStrength: number;

  generatedImageBlob: Blob;
  importedImageBlob?: Blob;
  humanDrawLayerBlob?: Blob;
  guideEraseMaskBlob?: Blob;
  guideCompositeBlob?: Blob;
  lastNoiseMaskBlob?: Blob;

  runtimeStateMeta?: unknown;
  note?: string;
};
```

Konva stage JSON may be stored as auxiliary metadata, but it is not the canonical Snapshot format.

## 7. Backend selection

Use:

```text
Python FastAPI
```

Reasons:

- natural fit with Diffusers and Python image tooling
- straightforward HTTP API for createSession / applyIntervention
- supports file upload and WebSocket later if needed
- keeps frontend and runtime concerns separated

## 8. Transport selection

Use HTTP-first.

Initial endpoints:

```text
POST /runtime/session
POST /runtime/intervention
POST /runtime/finish
GET  /runtime/health
```

WebSocket is optional later for:

- progress streaming
- continuous preview streaming
- cancellation control
- lower-latency runtime telemetry

Do not block v0.1 on WebSocket.

## 9. Runtime selection

### Required first runtime

```text
Mock Stateful Runtime
```

Required because it validates:

- Run loop
- Guide Canvas separation
- activeNoiseMask lifecycle
- global exploration movement
- Snapshot / Restore / Finish
- stale response handling

### First real backend spike

```text
Diffusers + TinySD or other small SD-compatible model
```

Purpose:

- validate backend API shape
- test guideComposite transport
- test mask transport
- test pseudo-stateful or stateful update path

TinySD is not the product quality target. It is a runtime integration spike target.

### Later adapter route

```text
ComfyUI adapter
```

Use ComfyUI later if workflow/model reuse matters.

Do not make ComfyUI the v0.1 UI.

### Not first candidate

```text
AUTOMATIC1111 / Forge
```

Reason:

- less aligned with live stateful canvas semantics
- likely to collapse into repeated img2img/inpainting
- license and extension constraints add decision cost

## 10. Repository shape

Recommended initial shape:

```text
apps/
  web/
    package.json
    index.html
    src/
      app/
      components/
      canvas/
      guide/
      runtime/
      snapshots/
      state/
      storage/
      types/

services/
  runtime/
    pyproject.toml
    app/
      main.py
      api/
      runtime/
      adapters/
      models/
```

## 11. Implementation order

```text
1. React + Vite + TypeScript app scaffold
2. Zustand AppState
3. Konva Guide Canvas
4. Konva Generated Image Canvas
5. Mock Stateful Runtime in frontend
6. Run / Pause / Resume loop
7. Dexie Snapshot persistence
8. FastAPI runtime service scaffold
9. HTTP adapter from web app to runtime service
10. Diffusers + TinySD spike
11. ComfyUI adapter spike if needed
```

## 12. Stack non-goals

Do not introduce these in v0.1 unless the SDD is updated:

- Next.js as default shell
- Redux Toolkit as default state store
- PixiJS as default canvas engine
- WebSocket as required transport
- ComfyUI as the primary UI
- InvokeAI fork as the default route
- AUTOMATIC1111 / Forge as first backend
- production deployment stack
- auth / accounts
- cloud object storage

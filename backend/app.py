from __future__ import annotations

import os
import json
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Live Diffusion Canvas Runtime", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://tauri.localhost"],
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost):(3000|4173|517[0-9])$",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class SessionRequest(BaseModel):
    seed: int = 42
    model: str | None = None


class Intervention(BaseModel):
    requestId: int
    sessionId: str
    prompt: str = ""
    guideComposite: str | None = None
    importedImage: str | None = None
    guideEraseMask: str | None = None
    guideInfluence: float = Field(0.5, ge=0, le=1)
    cfg: float = Field(7.5, ge=1, le=20)
    globalExplorationNoiseStrength: float = Field(0.04, ge=0, le=1)
    temperature: float = Field(0.7, ge=0, le=2)
    noiseBrushActive: bool = False
    activeNoiseMask: str | None = None
    localRejectionStrength: float = Field(0.7, ge=0, le=1)
    brushSize: int = Field(34, ge=10, le=80)
    updatesToAdvance: int = Field(1, ge=1, le=3)
    phase: str = "explore"
    diffusionSteps: int = Field(8, ge=4, le=20)


class RuntimeResponse(BaseModel):
    requestId: int
    sessionId: str
    previewImage: str
    seed: int
    latencyMs: int
    diffusionStep: int = 0
    diffusionSteps: int = 0


class SnapshotRequest(BaseModel):
    sessionId: str
    snapshotId: str | None = None


class SnapshotResponse(BaseModel):
    snapshotId: str
    sessionId: str
    diffusionStep: int
    diffusionSteps: int
    previewImage: str


@dataclass
class Session:
    seed: int
    model: str = "segmind/tiny-sd"
    tick: int = 0
    real_state: object | None = None


sessions: dict[str, Session] = {}
real_runtimes: dict[str, object] = {}
real_runtime_lock = threading.Lock()
runtime_snapshots: dict[str, object] = {}

MODEL_CATALOG = (
    {"id": "segmind/tiny-sd", "label": "TinySD", "profile": "sd15-compatible"},
    {"id": "stable-diffusion-v1-5/stable-diffusion-v1-5", "label": "Stable Diffusion 1.5", "profile": "sd15-compatible"},
    {"id": "stabilityai/sd-turbo", "label": "SD-Turbo", "profile": "sd15-compatible"},
    {"id": "stabilityai/stable-diffusion-xl-base-1.0", "label": "SDXL base (experimental)", "profile": "sdxl-experimental"},
)


def _model_ready(model_id: str) -> bool:
    """Return whether the complete local model snapshot is available."""
    model_path = Path(model_id)
    if model_path.exists():
        root = model_path
        has = lambda *parts: any((root / part).exists() for part in parts)
        return all((root / part).exists() for part in ("model_index.json", "scheduler/scheduler_config.json", "unet/config.json", "vae/config.json")) and all((
            has("unet/diffusion_pytorch_model.safetensors", "unet/diffusion_pytorch_model.bin"),
            has("vae/diffusion_pytorch_model.safetensors", "vae/diffusion_pytorch_model.bin"),
            has("text_encoder/model.safetensors", "text_encoder/pytorch_model.bin"),
        ))
    try:
        from huggingface_hub import try_to_load_from_cache
        required = (
            ("model_index.json",),
            ("scheduler/scheduler_config.json",),
            ("unet/config.json",),
            ("unet/diffusion_pytorch_model.safetensors", "unet/diffusion_pytorch_model.bin"),
            ("vae/config.json",),
            ("vae/diffusion_pytorch_model.safetensors", "vae/diffusion_pytorch_model.bin"),
            ("text_encoder/config.json",),
            ("text_encoder/model.safetensors", "text_encoder/pytorch_model.bin"),
            ("tokenizer/vocab.json",),
            ("tokenizer/merges.txt",),
            ("tokenizer/tokenizer_config.json",),
        )
        return all(any(try_to_load_from_cache(model_id, filename=name, revision="main") is not None for name in alternatives) for alternatives in required)
    except Exception:
        return False


@app.get("/runtime/health")
def health(model: str | None = Query(default=None)) -> dict[str, str | bool]:
    real = os.getenv("DIFFUSION_REAL", "0") == "1"
    active_model = (model or os.getenv("DIFFUSION_MODEL", "segmind/tiny-sd")) if real else "mock-stateful-v0.1"
    device = "mock" if not real else ("mps" if __import__("torch").backends.mps.is_available() else "cpu")
    return {
        "status": "ok",
        "runtime": "diffusers" if real else "mock-stateful",
        "model": active_model,
        "modelReady": _model_ready(active_model) if real else True,
        "device": device,
    }


@app.get("/runtime/models")
def models() -> list[dict[str, str | bool]]:
    """Report selectable models and local readiness without loading weights."""
    real = os.getenv("DIFFUSION_REAL", "0") == "1"
    return [{**entry, "modelReady": _model_ready(entry["id"]) if real else True} for entry in MODEL_CATALOG]


@app.post("/runtime/session")
def create_session(request: SessionRequest) -> dict[str, str | int]:
    runtime_name = "real" if os.getenv("DIFFUSION_REAL", "0") == "1" else "mock"
    session_id = f"{runtime_name}-{uuid.uuid4()}"
    configured_model = os.getenv("DIFFUSION_MODEL", "segmind/tiny-sd")
    requested_model = request.model or configured_model
    # A packaged app exposes the friendly Hub id in the UI but can point the
    # runtime at a bundled local snapshot through DIFFUSION_MODEL.
    if requested_model == "segmind/tiny-sd" and configured_model != "segmind/tiny-sd":
        requested_model = configured_model
    sessions[session_id] = Session(seed=request.seed, model=requested_model)
    return {"sessionId": session_id, "seed": request.seed}


@app.post("/runtime/intervention", response_model=RuntimeResponse)
def intervention(request: Intervention) -> RuntimeResponse:
    session = sessions.get(request.sessionId)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Runtime session not found: {request.sessionId}")
    if os.getenv("DIFFUSION_REAL", "0") == "1" and not _model_ready(session.model):
        raise HTTPException(status_code=409, detail=f"Model is not ready: {session.model}")
    session.tick += request.updatesToAdvance
    if os.getenv("DIFFUSION_REAL", "0") == "1":
        with real_runtime_lock:
            runtime = real_runtimes.get(session.model)
            if runtime is None:
                from backend.diffusion_runtime import TinySDRuntime
                runtime = TinySDRuntime(session.model)
                real_runtimes[session.model] = runtime
            rejection_mask = None
            if request.noiseBrushActive and request.activeNoiseMask:
                try:
                    rejection_mask = json.loads(request.activeNoiseMask)
                except json.JSONDecodeError:
                    rejection_mask = None
            if session.real_state is None or session.real_state.requested_steps != request.diffusionSteps:
                session.real_state = runtime.start(request.prompt, session.seed + session.tick, steps=request.diffusionSteps, guidance_scale=request.cfg, guide_composite=request.guideComposite, imported_image=request.importedImage, guide_erase_mask=request.guideEraseMask, guide_influence=request.guideInfluence)
            elif (session.real_state.prompt != request.prompt or
                  session.real_state.guide_composite != request.guideComposite or
                  session.real_state.imported_image != request.importedImage or
                  session.real_state.guide_erase_mask != request.guideEraseMask or
                  session.real_state.guide_influence != request.guideInfluence or
                  session.real_state.guidance_scale != request.cfg):
                runtime.update_conditions(session.real_state, request.prompt, request.guideComposite, request.importedImage, request.guideEraseMask, request.guideInfluence, request.cfg)
            image = ""
            latency_ms = 0
            step = session.real_state.step_index
            for _ in range(request.updatesToAdvance):
                image, extra_latency, step = runtime.advance(
                    session.real_state,
                    rejection_mask=rejection_mask,
                    rejection_strength=request.localRejectionStrength if request.noiseBrushActive else 0.0,
                    exploration_strength=request.globalExplorationNoiseStrength,
                    temperature=request.temperature,
                    brush_size=request.brushSize,
                )
                latency_ms += extra_latency
            if request.phase == "finish":
                while step < len(session.real_state.timesteps):
                    image, extra_latency, step = runtime.advance(session.real_state, exploration_strength=0.0)
                    latency_ms += extra_latency
        return RuntimeResponse(requestId=request.requestId, sessionId=request.sessionId, previewImage=image, seed=session.seed, latencyMs=latency_ms, diffusionStep=step, diffusionSteps=len(session.real_state.timesteps))
    accent = "f06b5d" if request.noiseBrushActive and request.activeNoiseMask else ("20c997" if request.guideComposite or request.importedImage else "7c5cff")
    guide_marker = "GUIDE ACTIVE" if request.guideComposite or request.importedImage else "GUIDE OFF"
    cx = 120 + ((session.tick * 47) % 660)
    radius = 54 + int(max(0, min(request.temperature, 2)) * 18)
    image = "data:image/svg+xml," + f"<svg xmlns='http://www.w3.org/2000/svg' width='900' height='600'><rect width='900' height='600' fill='%23{accent}'/><circle cx='{cx}' cy='330' r='{radius}' fill='%23f7d774' opacity='.8'/><path d='M70 490 Q300 {360 - (session.tick % 5) * 18} 480 470 T840 420' fill='none' stroke='white' stroke-width='12' opacity='.7'/><text x='40' y='80' fill='white' font-size='28'>FASTAPI STATE {session.tick}</text><text x='40' y='125' fill='white' font-size='18'>{request.prompt[:55]}</text><text x='40' y='170' fill='white' font-size='16'>{guide_marker} · TEMP {request.temperature:.1f}</text></svg>"
    mock_step = ((session.tick - 1) % request.diffusionSteps) + 1
    return RuntimeResponse(requestId=request.requestId, sessionId=request.sessionId, previewImage=image, seed=session.seed, latencyMs=1, diffusionStep=mock_step, diffusionSteps=request.diffusionSteps)


@app.post("/runtime/finish", response_model=RuntimeResponse)
def finish(request: Intervention) -> RuntimeResponse:
    request.phase = "finish"
    return intervention(request)


@app.post("/runtime/snapshot", response_model=SnapshotResponse)
def save_runtime_snapshot(request: SnapshotRequest) -> SnapshotResponse:
    session = sessions.get(request.sessionId)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Runtime session not found: {request.sessionId}")
    if session.real_state is None:
        raise HTTPException(status_code=409, detail="Runtime session has no real diffusion state")
    snapshot_id = str(uuid.uuid4())
    runtime_snapshots[snapshot_id] = session.real_state.clone()
    state = runtime_snapshots[snapshot_id]
    runtime = real_runtimes[session.model]
    with real_runtime_lock:
        image = runtime._preview(runtime._pipeline(), state.latents)
    return SnapshotResponse(snapshotId=snapshot_id, sessionId=request.sessionId, diffusionStep=state.step_index, diffusionSteps=len(state.timesteps), previewImage=image)


@app.post("/runtime/snapshot/restore", response_model=SnapshotResponse)
def restore_runtime_snapshot(request: SnapshotRequest) -> SnapshotResponse:
    if request.sessionId not in sessions or not request.snapshotId or request.snapshotId not in runtime_snapshots:
        raise HTTPException(status_code=404, detail="Runtime snapshot not found")
    state = runtime_snapshots[request.snapshotId].clone()
    sessions[request.sessionId].real_state = state
    runtime = real_runtimes[sessions[request.sessionId].model]
    with real_runtime_lock:
        pipe = runtime._pipeline()
        # The scheduler is mutable and may still point at the state that was
        # active immediately before Restore. Reopen its history so the next
        # Finish/Explore step follows the restored diffusion index.
        runtime._reset_scheduler(pipe, state.requested_steps)
        image = runtime._preview(pipe, state.latents)
    return SnapshotResponse(snapshotId=request.snapshotId, sessionId=request.sessionId, diffusionStep=state.step_index, diffusionSteps=len(state.timesteps), previewImage=image)

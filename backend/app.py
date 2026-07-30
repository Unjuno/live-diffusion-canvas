from __future__ import annotations

import os
import json
import threading
import uuid
from dataclasses import dataclass

from fastapi import FastAPI
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


class Intervention(BaseModel):
    requestId: int
    sessionId: str
    prompt: str = ""
    guideComposite: str | None = None
    guideInfluence: float = Field(0.5, ge=0, le=1)
    globalExplorationNoiseStrength: float = Field(0.04, ge=0, le=1)
    noiseBrushActive: bool = False
    activeNoiseMask: str | None = None
    localRejectionStrength: float = Field(0.7, ge=0, le=1)
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
    tick: int = 0
    real_state: object | None = None


sessions: dict[str, Session] = {}
real_runtime = None
real_runtime_lock = threading.Lock()
runtime_snapshots: dict[str, object] = {}


@app.get("/runtime/health")
def health() -> dict[str, str]:
    real = os.getenv("DIFFUSION_REAL", "0") == "1"
    return {
        "status": "ok",
        "runtime": "diffusers" if real else "mock-stateful",
        "model": os.getenv("DIFFUSION_MODEL", "segmind/tiny-sd") if real else "mock-stateful-v0.1",
    }


@app.post("/runtime/session")
def create_session(request: SessionRequest) -> dict[str, str | int]:
    runtime_name = "real" if os.getenv("DIFFUSION_REAL", "0") == "1" else "mock"
    session_id = f"{runtime_name}-{uuid.uuid4()}"
    sessions[session_id] = Session(seed=request.seed)
    return {"sessionId": session_id, "seed": request.seed}


@app.post("/runtime/intervention", response_model=RuntimeResponse)
def intervention(request: Intervention) -> RuntimeResponse:
    session = sessions.setdefault(request.sessionId, Session(seed=42))
    session.tick += request.updatesToAdvance
    if os.getenv("DIFFUSION_REAL", "0") == "1":
        global real_runtime
        with real_runtime_lock:
            if real_runtime is None:
                from backend.diffusion_runtime import TinySDRuntime
                real_runtime = TinySDRuntime()
            rejection_mask = None
            if request.noiseBrushActive and request.activeNoiseMask:
                try:
                    rejection_mask = json.loads(request.activeNoiseMask)
                except json.JSONDecodeError:
                    rejection_mask = None
            if session.real_state is None or len(session.real_state.timesteps) != request.diffusionSteps:
                session.real_state = real_runtime.start(request.prompt, session.seed + session.tick, steps=request.diffusionSteps, guide_composite=request.guideComposite, guide_influence=request.guideInfluence)
            elif (session.real_state.prompt != request.prompt or
                  session.real_state.guide_composite != request.guideComposite or
                  session.real_state.guide_influence != request.guideInfluence):
                real_runtime.update_conditions(session.real_state, request.prompt, request.guideComposite, request.guideInfluence)
            image, latency_ms, step = real_runtime.advance(session.real_state, rejection_mask=rejection_mask, rejection_strength=request.localRejectionStrength if request.noiseBrushActive else 0.0, exploration_strength=request.globalExplorationNoiseStrength)
            if request.phase == "finish":
                while step < len(session.real_state.timesteps):
                    image, extra_latency, step = real_runtime.advance(session.real_state, exploration_strength=0.0)
                    latency_ms += extra_latency
        return RuntimeResponse(requestId=request.requestId, sessionId=request.sessionId, previewImage=image, seed=session.seed, latencyMs=latency_ms, diffusionStep=step, diffusionSteps=len(session.real_state.timesteps))
    accent = "f06b5d" if request.noiseBrushActive and request.activeNoiseMask else "7c5cff"
    image = "data:image/svg+xml," + f"<svg xmlns='http://www.w3.org/2000/svg' width='900' height='600'><rect width='900' height='600' fill='%23{accent}'/><text x='40' y='80' fill='white' font-size='28'>FASTAPI STATE {session.tick}</text><text x='40' y='125' fill='white' font-size='18'>{request.prompt[:55]}</text></svg>"
    return RuntimeResponse(requestId=request.requestId, sessionId=request.sessionId, previewImage=image, seed=session.seed, latencyMs=1)


@app.post("/runtime/finish", response_model=RuntimeResponse)
def finish(request: Intervention) -> RuntimeResponse:
    request.phase = "finish"
    return intervention(request)


@app.post("/runtime/snapshot", response_model=SnapshotResponse)
def save_runtime_snapshot(request: SnapshotRequest) -> SnapshotResponse:
    session = sessions[request.sessionId]
    if session.real_state is None:
        raise ValueError("Runtime session has no real state")
    snapshot_id = str(uuid.uuid4())
    runtime_snapshots[snapshot_id] = session.real_state.clone()
    state = runtime_snapshots[snapshot_id]
    with real_runtime_lock:
        image = real_runtime._preview(real_runtime._pipeline(), state.latents)
    return SnapshotResponse(snapshotId=snapshot_id, sessionId=request.sessionId, diffusionStep=state.step_index, diffusionSteps=len(state.timesteps), previewImage=image)


@app.post("/runtime/snapshot/restore", response_model=SnapshotResponse)
def restore_runtime_snapshot(request: SnapshotRequest) -> SnapshotResponse:
    if request.sessionId not in sessions or not request.snapshotId or request.snapshotId not in runtime_snapshots:
        raise ValueError("Runtime snapshot not found")
    state = runtime_snapshots[request.snapshotId].clone()
    sessions[request.sessionId].real_state = state
    with real_runtime_lock:
        image = real_runtime._preview(real_runtime._pipeline(), state.latents)
    return SnapshotResponse(snapshotId=request.snapshotId, sessionId=request.sessionId, diffusionStep=state.step_index, diffusionSteps=len(state.timesteps), previewImage=image)

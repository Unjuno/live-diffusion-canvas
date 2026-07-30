import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { create } from "zustand";
import "./styles.css";
import "./real-model.css";
import { makePreview } from "./runtime";
import { clearSnapshots, loadSnapshots, persistSnapshot, type StoredSnapshot } from "./db";

type LoopStatus = "idle" | "running" | "paused";
type Snapshot = StoredSnapshot;
type State = {
  prompt: string;
  backend: string;
  model: string;
  loopStatus: LoopStatus;
  generationStatus: "idle" | "generating" | "error";
  generationPhase: "explore" | "finish";
  errorMessage: string | null;
  guideInfluence: number;
  globalNoise: number;
  temperature: number;
  localRejection: number;
  cfg: number;
  brushSize: number;
  updateInterval: number;
  seed: number;
  generatedImage: string | null;
  guideImage: string | null;
  drawPoints: [number, number][];
  guideErasePoints: [number, number][];
  guideMode: "draw" | "erase";
  guideEraseMask: string | null;
  guideComposite: string | null;
  noiseBrushActive: boolean;
  activeNoiseMask: [number, number][];
  lastNoiseMask: [number, number][];
  runtimeSessionId: string | null;
  runtimeModel: string | null;
  runtimeModelReady: boolean | null;
  runtimeDevice: string | null;
  snapshots: Snapshot[];
  tick: number;
  diffusionStep: number;
  diffusionSteps: number;
  diffusionStepCount: number;
  run(): void;
  pause(): void;
  resume(): void;
  tickOnce(): Promise<void>;
  saveSnapshot(): Promise<void>;
  restoreSnapshot(snapshot: Snapshot): Promise<void>;
  finish(snapshot: Snapshot): Promise<void>;
  resetSession(): void;
};

let runtimeRequestInFlight = false;
const RUNTIME_URL = import.meta.env.VITE_RUNTIME_URL ?? "http://127.0.0.1:8000";

async function runtimeJson<T>(url: string, init: RequestInit, timeoutMs = 120_000): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = body && typeof body === "object" && "detail" in body ? String(body.detail) : `HTTP ${response.status}`;
      throw new Error(`Runtime request failed: ${detail}`);
    }
    return body as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Runtime request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

const useApp = create<State>((set, get) => ({
  prompt: "a quiet architectural landscape at blue hour",
  backend: "mock",
  model: "mock-stateful-v0.1",
  loopStatus: "idle",
  generationStatus: "idle",
  generationPhase: "explore",
  errorMessage: null,
  guideInfluence: 0.5,
  globalNoise: 0.04,
  temperature: 0.7,
  localRejection: 0.7,
  cfg: 7.5,
  brushSize: 34,
  updateInterval: 1200,
  seed: 42,
  generatedImage: null,
  guideImage: null,
  drawPoints: [],
  guideErasePoints: [],
  guideMode: "draw",
  guideEraseMask: null,
  guideComposite: null,
  noiseBrushActive: false,
  activeNoiseMask: [],
  lastNoiseMask: [],
  runtimeSessionId: null,
  runtimeModel: null,
  runtimeModelReady: null,
  runtimeDevice: null,
  snapshots: [],
  tick: 0,
  diffusionStep: 0,
  diffusionSteps: 0,
  diffusionStepCount: 8,
  run: () => {
    const current = get();
    if (current.backend === "tinysd" && current.runtimeModelReady !== true) {
      set({
        loopStatus: "paused",
        generationStatus: "error",
        errorMessage: `${current.model} is not ready. Download the model files before running.`,
      });
      return;
    }
    set({
      loopStatus: "running",
      generationPhase: "explore",
      errorMessage: null,
    });
  },
  pause: () => set({ loopStatus: "paused" }),
  resume: () => set({ loopStatus: "running" }),
  tickOnce: async () => {
    if (runtimeRequestInFlight) return;
    runtimeRequestInFlight = true;
    const s = get();
    if (s.backend === "tinysd" && s.runtimeModelReady !== true) {
      runtimeRequestInFlight = false;
      set({
        generationStatus: "error",
        loopStatus: "paused",
        errorMessage: `${s.model} is not ready. Download the model files before running.`,
      });
      return;
    }
    const tick = s.tick + 1;
    set({ generationStatus: "generating" });
    try {
      if (s.backend === "mock") {
        set({
          tick,
          generatedImage: makePreview(tick, s.seed, s.noiseBrushActive),
          generationStatus: "idle",
          errorMessage: null,
        });
        return;
      }
      let sessionId = s.runtimeSessionId;
      if (!sessionId) {
        const session = await runtimeJson<{sessionId:string}>(`${RUNTIME_URL}/runtime/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seed: s.seed, model: s.model }),
        });
        sessionId = session.sessionId;
        set({ runtimeSessionId: sessionId });
      }
      const response = await runtimeJson<{
        previewImage:string; diffusionStep?:number; diffusionSteps?:number;
      }>(
        `${RUNTIME_URL}/runtime/intervention`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            requestId: tick,
            sessionId,
            prompt: s.prompt,
            guideComposite: s.guideComposite,
            importedImage: s.guideImage,
            guideEraseMask: s.guideEraseMask,
            guideInfluence: s.guideInfluence,
            cfg: s.cfg,
            globalExplorationNoiseStrength: s.globalNoise,
            temperature: s.temperature,
            noiseBrushActive: s.noiseBrushActive,
            activeNoiseMask: s.activeNoiseMask.length
              ? JSON.stringify(s.activeNoiseMask)
              : null,
            localRejectionStrength: s.localRejection,
            brushSize: s.brushSize,
            updatesToAdvance: 1,
            phase: "explore",
            diffusionSteps: s.diffusionStepCount,
          }),
        },
      );
      const latest = useApp.getState();
      if (latest.backend !== s.backend || latest.runtimeSessionId !== sessionId) return;
      set({
        tick,
        generatedImage: response.previewImage,
        diffusionStep: response.diffusionStep ?? 0,
        diffusionSteps: response.diffusionSteps ?? 0,
        generationStatus: "idle",
        errorMessage: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Runtime unavailable";
      const sessionExpired = message.includes("Runtime session not found");
      set({
        generationStatus: "error",
        runtimeSessionId: sessionExpired ? null : get().runtimeSessionId,
        errorMessage: sessionExpired
          ? "Runtime session expired. Resume to start a new stateful session."
          : error instanceof TypeError && error.message === "Failed to fetch"
          ? `Runtime unavailable at ${RUNTIME_URL}. Start the FastAPI runtime.`
          : message,
        loopStatus: "paused",
      });
    } finally {
      runtimeRequestInFlight = false;
    }
  },
  saveSnapshot: async () => {
    const s = get();
    if (!s.generatedImage) return;
    let runtimeSnapshotId: string | undefined;
    if (s.backend === "tinysd" && s.runtimeSessionId) {
      const response = await runtimeJson<{snapshotId:string}>(`${RUNTIME_URL}/runtime/snapshot`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId: s.runtimeSessionId }) });
      runtimeSnapshotId = response.snapshotId;
    }
    const snapshot = {
      id: crypto.randomUUID(),
      createdAt: Date.now(),
      generatedImage: s.generatedImage,
      prompt: s.prompt,
      note: `Explore update ${s.tick}`,
      importedImage: s.guideImage ?? undefined,
      humanDrawLayer: s.drawPoints,
      guideEraseMask: s.guideEraseMask ?? undefined,
      guideComposite: s.guideComposite ?? undefined,
      lastNoiseMask: s.lastNoiseMask,
      diffusionStepCount: s.diffusionStepCount,
      seed: s.seed,
      cfg: s.cfg,
      temperature: s.temperature,
      runtimeSnapshotId,
      runtimeSessionId: s.backend === "tinysd" ? s.runtimeSessionId ?? undefined : undefined,
    };
    await persistSnapshot(snapshot);
    set({ snapshots: [...s.snapshots, snapshot] });
  },
  restoreSnapshot: async (snapshot) => {
    const s = get();
    let generatedImage = snapshot.generatedImage;
    let diffusionStep = s.diffusionStep;
    let diffusionSteps = s.diffusionSteps;
    if (s.backend === "tinysd" && snapshot.runtimeSnapshotId && s.runtimeSessionId === snapshot.runtimeSessionId) {
      const response = await runtimeJson<{previewImage:string; diffusionStep:number; diffusionSteps:number}>(`${RUNTIME_URL}/runtime/snapshot/restore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: s.runtimeSessionId, snapshotId: snapshot.runtimeSnapshotId }),
      });
      generatedImage = response.previewImage;
      diffusionStep = response.diffusionStep;
      diffusionSteps = response.diffusionSteps;
    }
    set({
      generatedImage,
      prompt: snapshot.prompt,
      guideImage: snapshot.importedImage ?? null,
      drawPoints: snapshot.humanDrawLayer ?? [],
      guideEraseMask: snapshot.guideEraseMask ?? null,
      guideErasePoints: snapshot.guideEraseMask ? JSON.parse(snapshot.guideEraseMask) : [],
      guideComposite: snapshot.guideComposite ?? null,
      diffusionStepCount: snapshot.diffusionStepCount ?? s.diffusionStepCount,
      seed: snapshot.seed ?? s.seed,
      cfg: snapshot.cfg ?? s.cfg,
      temperature: snapshot.temperature ?? s.temperature,
      diffusionStep,
      diffusionSteps,
      noiseBrushActive: false,
      activeNoiseMask: [],
      loopStatus: "paused",
      errorMessage: null,
    });
  },
  finish: async (snapshot) => {
    set({
      loopStatus: "paused",
      generationStatus: "generating",
      generationPhase: "finish",
    });
    const s = get();
    if (s.backend === "mock") {
      set({ generatedImage: makePreview(s.tick + 1, s.seed, false), generationStatus: "idle", prompt: snapshot.prompt, tick: s.tick + 1 });
      return;
    }
    try {
      const response = await runtimeJson<{previewImage:string; diffusionStep:number; diffusionSteps:number}>(`${RUNTIME_URL}/runtime/finish`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ requestId: s.tick + 1, sessionId: s.runtimeSessionId, prompt: snapshot.prompt, guideComposite: snapshot.guideComposite, importedImage: snapshot.importedImage, guideEraseMask: snapshot.guideEraseMask, guideInfluence: s.guideInfluence, cfg: 5, globalExplorationNoiseStrength: 0, temperature: 0, noiseBrushActive: false, activeNoiseMask: null, localRejectionStrength: s.localRejection, updatesToAdvance: 1, phase: "finish", diffusionSteps: s.diffusionStepCount }) });
      set({ generatedImage: response.previewImage, diffusionStep: response.diffusionStep, diffusionSteps: response.diffusionSteps, generationStatus: "idle", prompt: snapshot.prompt, tick: s.tick + 1, errorMessage: null });
    } catch (error) {
      set({ generationStatus: "error", errorMessage: error instanceof Error ? error.message : "Finish failed" });
    }
  },
  resetSession: () => set({
    runtimeSessionId: null,
    runtimeModel: null,
    runtimeModelReady: null,
    runtimeDevice: null,
    generatedImage: null,
    generationStatus: "idle",
    generationPhase: "explore",
    loopStatus: "idle",
    errorMessage: null,
    tick: 0,
    diffusionStep: 0,
    diffusionSteps: 0,
    noiseBrushActive: false,
    activeNoiseMask: [],
    lastNoiseMask: [],
  }),
}));

function Slider({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="slider">
      <span>
        {label}
        <b>{value}</b>
      </span>
      <input
        name={label.toLowerCase().replace(/\s+/g, "-")}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
function guideCompositeFor(points: [number, number][]) {
  const polyline = points.map((point) => point.join(",")).join(" ");
  return `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><rect width="512" height="512" fill="#0b1525"/><polyline points="${polyline}" fill="none" stroke="#ffc857" stroke-width="8" stroke-linecap="round"/></svg>`)}`;
}

function downloadGuideComposite(composite: string | null) {
  if (!composite) return;
  const link = document.createElement("a");
  link.href = composite;
  link.download = "live-diffusion-guide.svg";
  link.click();
}

async function copyRuntimeSetupCommand() {
  await navigator.clipboard?.writeText("./scripts/setup-real-runtime.sh");
}

function Canvas({ guide = false }: { guide?: boolean }) {
  const s = useApp();
  const ref = useRef<HTMLDivElement>(null);
  const [drawing, setDrawing] = useState(false);
  const points = guide ? s.drawPoints.filter(([x, y]) => s.guideErasePoints.every(([ex, ey]) => Math.hypot(x - ex, y - ey) > 8)) : s.activeNoiseMask;
  const add = (e: React.PointerEvent) => {
    if (!drawing) return;
    const r = ref.current!.getBoundingClientRect();
    const p: [number, number] = [
      ((e.clientX - r.left) / r.width) * 100,
      ((e.clientY - r.top) / r.height) * 100,
    ];
    if (guide) {
      const current = useApp.getState();
      if (current.guideMode === "erase") {
        const erased = [...current.guideErasePoints, p];
        const visible = current.drawPoints.filter(([x, y]) => erased.every(([ex, ey]) => Math.hypot(x - ex, y - ey) > 8));
        useApp.setState({ guideErasePoints: erased, guideEraseMask: JSON.stringify(erased), guideComposite: guideCompositeFor(visible) });
        return;
      }
      const points = [...current.drawPoints, p];
      useApp.setState({ drawPoints: points, guideComposite: guideCompositeFor(points) });
    } else
      useApp.setState({
        activeNoiseMask: [...useApp.getState().activeNoiseMask, p],
        noiseBrushActive: true,
      });
  };
  const release = () => {
    setDrawing(false);
    if (!guide) {
      const mask = useApp.getState().activeNoiseMask;
      if (mask.length) {
        // Submit the completed stroke while its mask is still active. Clearing
        // it before tickOnce() made the real backend receive no brush input.
        useApp.setState({ noiseBrushActive: true });
        const submit = () => {
          if (runtimeRequestInFlight) {
            window.setTimeout(submit, 100);
            return;
          }
          void useApp.getState().tickOnce().finally(() => {
          useApp.setState({
            noiseBrushActive: false,
            activeNoiseMask: [],
            lastNoiseMask: mask,
          });
          });
        };
        submit();
      } else {
        useApp.setState({ noiseBrushActive: false, activeNoiseMask: [] });
      }
    }
  };
  return (
    <div
      ref={ref}
      className={`canvas ${guide ? "guide-canvas" : "generated-canvas"}`}
      onPointerDown={(e) => {
        setDrawing(true);
        try {
          ref.current?.setPointerCapture(e.pointerId);
        } catch {
          // Synthetic pointer events and some touch implementations do not
          // expose an active pointer to capture. Drawing still works without
          // capture; the real pointer path keeps capture for drag continuity.
        }
        add(e);
      }}
      onPointerMove={add}
      onPointerUp={release}
      onPointerCancel={release}
    >
      {!guide && s.generatedImage && (
        <img src={s.generatedImage} alt="Generated state preview" />
      )}
      {guide && s.guideImage && (
        <svg className="guide-image-layer" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Imported guide image">
          <defs>
            <mask id="guide-import-mask">
              <rect width="100" height="100" fill="white" />
              {s.guideErasePoints.map(([x, y], index) => <circle key={index} cx={x} cy={y} r="4" fill="black" />)}
            </mask>
          </defs>
          <image href={s.guideImage} x="0" y="0" width="100" height="100" preserveAspectRatio="none" mask="url(#guide-import-mask)" />
        </svg>
      )}
      <div className="grid" />
      <svg viewBox="0 0 100 100" preserveAspectRatio="none">
        {points.length > 1 && (
          <polyline
            points={points.map((p) => p.join(",")).join(" ")}
            fill="none"
            stroke={guide ? "#ffc857" : "#ff6b6b"}
            strokeWidth={guide ? "1.2" : String(Math.max(1.5, s.brushSize / 18))}
            strokeLinecap="round"
          />
        )}
      </svg>
      <div className="canvas-label">
        {guide ? "DRAW GUIDE" : "HOLD TO REJECT"}
      </div>
    </div>
  );
}

function App() {
  const s = useApp();
  useEffect(() => {
    if (s.loopStatus !== "running") return;
    const id = window.setInterval(
      () => void useApp.getState().tickOnce(),
      s.updateInterval,
    );
    return () => clearInterval(id);
  }, [s.loopStatus, s.updateInterval]);
  return (
    <main>
      <header>
        <div>
          <div className="eyebrow">STATEFUL DIFFUSION RUNTIME · v0.1</div>
          <h1>
            Live Diffusion <em>Canvas</em>
          </h1>
        </div>
        <div className="runtime">
          <span className="dot" /> {s.loopStatus.toUpperCase()}{" "}
          <small>SESSION {s.runtimeSessionId ?? "—"}</small>
        </div>
      </header>
      <section className="toolbar">
        <input
          name="prompt"
          aria-label="Prompt"
          value={s.prompt}
          onChange={(e) => useApp.setState({ prompt: e.target.value })}
        />
        <select
          name="backend"
          aria-label="Backend"
          value={s.backend}
          onChange={(e) => useApp.setState({
            backend: e.target.value,
            model: e.target.value === "mock" ? "mock-stateful-v0.1" : "segmind/tiny-sd",
            runtimeSessionId: null,
            runtimeModel: null,
            runtimeModelReady: null,
            runtimeDevice: null,
            generatedImage: null,
            diffusionStep: 0,
            diffusionSteps: 0,
            generationStatus: "idle",
            loopStatus: "paused",
            errorMessage: null,
          })}
        >
          <option value="mock">Mock Runtime</option>
          <option value="tinysd">TinySD · local Diffusers</option>
        </select>
        <span className="toolbar-status" aria-live="polite">
          {s.loopStatus === "running" ? "● Exploring" : s.loopStatus === "paused" ? "Ⅱ Paused" : "Ready"}
        </span>
        <select
          name="model"
          aria-label="Model"
          value={s.model}
          onChange={(e) => useApp.setState({ model: e.target.value, runtimeSessionId: null, generatedImage: null, diffusionStep: 0, diffusionSteps: 0, generationStatus: "idle", loopStatus: "paused" })}
        >
          <option value="mock-stateful-v0.1">Mock Stateful v0.1</option>
          <option value="segmind/tiny-sd">segmind/tiny-sd</option>
          <option value="stable-diffusion-v1-5/stable-diffusion-v1-5">Stable Diffusion 1.5</option>
        </select>
        <button className="primary" onClick={s.run} disabled={s.loopStatus === "running" || (s.backend === "tinysd" && s.runtimeModelReady !== true)}>
          {s.loopStatus === "running" ? "Running…" : "Run"}
        </button>
        <button onClick={s.pause} disabled={s.loopStatus !== "running"}>Pause</button>
        <button onClick={s.resume} disabled={s.loopStatus !== "paused"}>Resume</button>
        <button onClick={s.resetSession} disabled={s.generationStatus === "generating"}>Reset session</button>
      </section>
      <div className="workspace">
        <section className="panel">
            <div className="panel-head">
              <span>01 / GUIDE CANVAS</span>
              <div>
                <button onClick={() => useApp.setState({ guideMode: "draw" })}>Draw</button>
                <button onClick={() => useApp.setState({ guideMode: "erase" })}>Erase</button>
                <button onClick={() => useApp.setState({ drawPoints: [], guideComposite: null })}>Clear draw</button>
                <button onClick={() => { const current = useApp.getState(); useApp.setState({ guideErasePoints: [], guideEraseMask: null, guideComposite: guideCompositeFor(current.drawPoints) }); }}>Reset erase</button>
                <button onClick={() => downloadGuideComposite(s.guideComposite)} disabled={!s.guideComposite}>Export guide</button>
              </div>
            </div>
          <Canvas guide />
          <p className="hint">
            Draw a positive guide or import a photo. The guide influences the
            next denoise updates; it does not replace the generated state.
          </p>
          <label className="upload">
            ＋ Import guide image
            <input
              name="guide-image"
              type="file"
              accept="image/*"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  if (!f.type.startsWith("image/") || f.size > 10 * 1024 * 1024) {
                    useApp.setState({ generationStatus: "error", errorMessage: "Guide image must be an image file smaller than 10 MB." });
                    return;
                  }
                  const r = new FileReader();
                  r.onerror = () => useApp.setState({ generationStatus: "error", errorMessage: "Guide image could not be read." });
                  r.onload = () => useApp.setState({ guideImage: String(r.result), guideComposite: s.drawPoints.length ? s.guideComposite : String(r.result), errorMessage: null, generationStatus: "idle" });
                  r.readAsDataURL(f);
                }
              }}
            />
          </label>
        </section>
        <section className="panel">
          <div className="panel-head">
            <span>02 / GENERATED STATE</span>
            <span className="live">● LIVE PREVIEW</span>
          </div>
          <Canvas />
          <p className="hint">
            Hold and drag to reject a local solution. It only applies while
            pressed.
          </p>
        </section>
        <aside className="side">
          <section className="panel">
            <div className="panel-head">
              <span>RUNTIME SETTINGS</span>
            </div>
            <Slider
              label="Guide influence"
              value={s.guideInfluence}
              min={0}
              max={1}
              step={0.05}
              onChange={(v) => useApp.setState({ guideInfluence: v })}
            />
            <Slider
              label="CFG / guidance"
              value={s.cfg}
              min={1}
              max={20}
              step={0.5}
              onChange={(v) => useApp.setState({ cfg: v })}
            />
            <Slider
              label="Global exploration"
              value={s.globalNoise}
              min={0}
              max={0.1}
              step={0.01}
              onChange={(v) => useApp.setState({ globalNoise: v })}
            />
            <Slider
              label="Temperature / variation"
              value={s.temperature}
              min={0}
              max={2}
              step={0.1}
              onChange={(v) => useApp.setState({ temperature: v })}
            />
            <Slider
              label="Local rejection"
              value={s.localRejection}
              min={0}
              max={1}
              step={0.05}
              onChange={(v) => useApp.setState({ localRejection: v })}
            />
            <Slider
              label="Brush size"
              value={s.brushSize}
              min={10}
              max={80}
              step={2}
              onChange={(v) => useApp.setState({ brushSize: v })}
            />
            <Slider
              label="Diffusion steps"
              value={s.diffusionStepCount}
              min={4}
              max={20}
              step={1}
              onChange={(v) => useApp.setState({ diffusionStepCount: v })}
            />
            <div className="mini-fields">
              <label>
                Seed
                <input
                  name="seed"
                  type="number"
                  value={s.seed}
                  onChange={(e) =>
                    useApp.setState({ seed: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Interval
                <input
                  name="update-interval"
                  type="number"
                  value={s.updateInterval}
                  onChange={(e) =>
                    useApp.setState({ updateInterval: Number(e.target.value) })
                  }
                />
              </label>
            </div>
          </section>
          <section className="panel snapshots">
            <div className="panel-head">
              <span>SNAPSHOT TIMELINE</span>
              <div>
                <button onClick={() => void s.saveSnapshot().catch((error) => useApp.setState({
                  generationStatus: "error",
                  errorMessage: error instanceof Error ? error.message : "Snapshot save failed",
                }))} disabled={!s.generatedImage || s.generationStatus === "generating"} title={!s.generatedImage ? "Generate an image before saving a snapshot" : "Save the current generated state"}>Save</button>
                <button className="panel-action" onClick={() => void clearSnapshots().then(() => useApp.setState({ snapshots: [] }))} disabled={s.snapshots.length === 0}>Clear</button>
              </div>
            </div>
          {(s.backend === "tinysd"
            ? s.snapshots.filter((x) => x.runtimeSessionId === s.runtimeSessionId)
            : s.snapshots
          ).length === 0 ? (
              <div className="empty">
                Run the canvas, then save a state to branch from it.
              </div>
            ) : (
              (s.backend === "tinysd"
                ? s.snapshots.filter((x) => x.runtimeSessionId === s.runtimeSessionId)
                : s.snapshots
              ).map((x, i) => (
                <div className="snapshot" key={x.id}>
                  <img src={x.generatedImage} alt={`Snapshot ${String(i + 1).padStart(2, "0")}`} />
                  <div>
                    <b>Snapshot {String(i + 1).padStart(2, "0")}</b>
                    <small>{x.note}</small>
                  </div>
                  <button
                    onClick={() => void useApp.getState().restoreSnapshot(x).catch((error) => useApp.setState({
                      generationStatus: "error",
                      errorMessage: error instanceof Error ? error.message : "Restore failed",
                    }))}
                  >
                    Restore
                  </button>
                  <button
                    onClick={() => void useApp.getState().finish(x).catch((error) => useApp.setState({
                      generationStatus: "error",
                      errorMessage: error instanceof Error ? error.message : "Finish failed",
                    }))}
                    disabled={s.generationStatus === "generating"}
                  >
                    Finish
                  </button>
                </div>
              ))
            )}
          </section>
        </aside>
      </div>
      <footer>
        <span>
          {s.generationStatus === "generating"
            ? "Loading model / generating"
            : s.generationPhase === "finish" && s.generationStatus === "idle"
              ? "Finished from snapshot"
              : s.loopStatus === "running"
                ? "Explore is rolling from the current state"
                : s.loopStatus === "paused"
                  ? "Exploration paused"
                  : "Ready to explore"}
          {` · global noise ${s.globalNoise.toFixed(2)} · guide ${Math.round(s.guideInfluence * 100)}%`}
        </span>
          <span>
            Updates: {s.tick}
            {s.backend === "tinysd" && s.diffusionSteps > 0
              ? ` · Diffusion step ${s.diffusionStep}/${s.diffusionSteps}`
              : ""}
          </span>
      </footer>
    </main>
  );
}
function PersistenceBootstrap() {
  const s = useApp();
  useEffect(() => {
    void loadSnapshots().then((snapshots) => useApp.setState({ snapshots }));
  }, []);
  useEffect(() => {
    if (s.backend !== "tinysd") return;
    void fetch(`${RUNTIME_URL}/runtime/health?model=${encodeURIComponent(s.model)}`)
      .then((response) => response.ok ? response.json() : null)
      .then((health) => {
        if (health?.model) useApp.setState({
          runtimeModel: health.model,
          runtimeModelReady: health.runtime === "diffusers" && health.modelReady !== false,
          runtimeDevice: health.device ?? null,
          errorMessage: null,
        });
      })
      .catch(() => useApp.setState({ runtimeModel: null, runtimeModelReady: null, runtimeDevice: null }));
  }, [s.backend, s.model]);
  const visibleSnapshots = s.backend === "tinysd"
    ? s.snapshots.filter((x) => x.runtimeSessionId === s.runtimeSessionId)
    : s.snapshots;
  const latest = visibleSnapshots[visibleSnapshots.length - 1];
  const finish = () => {
    if (latest) useApp.getState().finish(latest);
  };
  const restore = async () => {
    if (latest) {
      try {
        await useApp.getState().restoreSnapshot(latest);
      } catch (error) {
        useApp.setState({
          generationStatus: "error",
          errorMessage: error instanceof Error ? error.message : "Restore failed",
        });
      }
    }
  };
  return (
    <>
      {s.errorMessage && (
        <div className="runtime-error">Runtime error: {s.errorMessage}</div>
      )}
      {s.backend === "tinysd" && (
        <div className={`real-model-badge ${s.runtimeModelReady === true ? "ready" : "needs-setup"}`}>
          <span>
            {s.runtimeModelReady === true
              ? `Real model route: ${s.runtimeModel ?? "TinySD"} · ${s.runtimeDevice ?? "ready"}`
              : "TinySD runtime is not ready. Mock Runtime is available."}
          </span>
          {s.runtimeModelReady !== true && (
            <button onClick={() => void copyRuntimeSetupCommand()}>Copy setup command</button>
          )}
        </div>
      )}
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <PersistenceBootstrap />
    <App />
  </React.StrictMode>,
);

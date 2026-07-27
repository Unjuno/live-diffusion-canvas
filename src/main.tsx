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
  localRejection: number;
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
  finish(snapshot: Snapshot): Promise<void>;
};

let runtimeRequestInFlight = false;
const RUNTIME_URL = import.meta.env.VITE_RUNTIME_URL ?? "http://127.0.0.1:8000";

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
  localRejection: 0.7,
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
  snapshots: [],
  tick: 0,
  diffusionStep: 0,
  diffusionSteps: 0,
  diffusionStepCount: 8,
  run: () =>
    set({
      loopStatus: "running",
      generationPhase: "explore",
      errorMessage: null,
    }),
  pause: () => set({ loopStatus: "paused" }),
  resume: () => set({ loopStatus: "running" }),
  tickOnce: async () => {
    if (runtimeRequestInFlight) return;
    runtimeRequestInFlight = true;
    const s = get();
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
        const session = await fetch(`${RUNTIME_URL}/runtime/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seed: s.seed }),
        }).then((r) => r.json());
        sessionId = session.sessionId;
        set({ runtimeSessionId: sessionId });
      }
      const response = await fetch(
        `${RUNTIME_URL}/runtime/intervention`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            requestId: tick,
            sessionId,
            prompt: s.prompt,
            guideComposite: s.guideComposite,
            guideInfluence: s.guideInfluence,
            globalExplorationNoiseStrength: s.globalNoise,
            noiseBrushActive: s.noiseBrushActive,
            activeNoiseMask: s.activeNoiseMask.length
              ? JSON.stringify(s.activeNoiseMask)
              : null,
            localRejectionStrength: s.localRejection,
            updatesToAdvance: 1,
            phase: "explore",
            diffusionSteps: s.diffusionStepCount,
          }),
        },
      ).then(async (r) => {
        if (!r.ok) throw new Error(`Runtime HTTP ${r.status}`);
        return r.json();
      });
      set({
        tick,
        generatedImage: response.previewImage,
        diffusionStep: response.diffusionStep ?? 0,
        diffusionSteps: response.diffusionSteps ?? 0,
        generationStatus: "idle",
        errorMessage: null,
      });
    } catch (error) {
      set({
        generationStatus: "error",
      errorMessage: error instanceof TypeError && error.message === "Failed to fetch"
          ? `Runtime unavailable at ${RUNTIME_URL}. Start the FastAPI runtime.`
          : error instanceof Error ? error.message : "Runtime unavailable",
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
      const response = await fetch(`${RUNTIME_URL}/runtime/snapshot`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId: s.runtimeSessionId }) });
      if (!response.ok) throw new Error(`Snapshot HTTP ${response.status}`);
      runtimeSnapshotId = (await response.json()).snapshotId;
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
      runtimeSnapshotId,
      runtimeSessionId: s.backend === "tinysd" ? s.runtimeSessionId ?? undefined : undefined,
    };
    void persistSnapshot(snapshot);
    set({ snapshots: [...s.snapshots, snapshot] });
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
      const response = await fetch(`${RUNTIME_URL}/runtime/finish`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ requestId: s.tick + 1, sessionId: s.runtimeSessionId, prompt: snapshot.prompt, guideComposite: snapshot.guideComposite, guideInfluence: s.guideInfluence, globalExplorationNoiseStrength: 0, noiseBrushActive: false, activeNoiseMask: null, localRejectionStrength: s.localRejection, updatesToAdvance: 1, phase: "finish", diffusionSteps: s.diffusionStepCount }) }).then(async (r) => { if (!r.ok) throw new Error(`Finish HTTP ${r.status}`); return r.json(); });
      set({ generatedImage: response.previewImage, diffusionStep: response.diffusionStep, diffusionSteps: response.diffusionSteps, generationStatus: "idle", prompt: snapshot.prompt, tick: s.tick + 1, errorMessage: null });
    } catch (error) {
      set({ generationStatus: "error", errorMessage: error instanceof Error ? error.message : "Finish failed" });
    }
  },
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
        const polyline = visible.map((point) => point.join(",")).join(" ");
        const guideComposite = `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><rect width="512" height="512" fill="#0b1525"/><polyline points="${polyline}" fill="none" stroke="#ffc857" stroke-width="8" stroke-linecap="round"/></svg>`)}`;
        useApp.setState({ guideErasePoints: erased, guideEraseMask: JSON.stringify(erased), guideComposite });
        return;
      }
      const points = [...current.drawPoints, p];
      const polyline = points.map((point) => point.join(",")).join(" ");
      const guideComposite = `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><rect width="512" height="512" fill="#0b1525"/><polyline points="${polyline}" fill="none" stroke="#ffc857" stroke-width="8" stroke-linecap="round"/></svg>`)}`;
      useApp.setState({ drawPoints: points, guideComposite });
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
        ref.current?.setPointerCapture(e.pointerId);
        add(e);
      }}
      onPointerMove={add}
      onPointerUp={release}
      onPointerCancel={release}
    >
      {!guide && s.generatedImage && (
        <img src={s.generatedImage} alt="Generated state preview" />
      )}
      {guide && s.guideImage && <img src={s.guideImage} alt="Imported guide" />}
      <div className="grid" />
      <svg viewBox="0 0 100 100" preserveAspectRatio="none">
        {points.length > 1 && (
          <polyline
            points={points.map((p) => p.join(",")).join(" ")}
            fill="none"
            stroke={guide ? "#ffc857" : "#ff6b6b"}
            strokeWidth={guide ? "1.2" : "2"}
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
          aria-label="Prompt"
          value={s.prompt}
          onChange={(e) => useApp.setState({ prompt: e.target.value })}
        />
        <select
          aria-label="Backend"
          value={s.backend}
          onChange={(e) => useApp.setState({
            backend: e.target.value,
            runtimeSessionId: null,
            generatedImage: null,
            diffusionStep: 0,
            diffusionSteps: 0,
            loopStatus: "paused",
          })}
        >
          <option value="mock">Mock Runtime</option>
          <option value="tinysd">TinySD · local Diffusers</option>
        </select>
        <button className="primary" onClick={s.run}>
          Run
        </button>
        <button onClick={s.pause} disabled={s.loopStatus !== "running"}>Pause</button>
        <button onClick={s.resume} disabled={s.loopStatus !== "paused"}>Resume</button>
      </section>
      <div className="workspace">
        <section className="panel">
          <div className="panel-head">
            <span>01 / GUIDE CANVAS</span>
            <div>
              <button onClick={() => useApp.setState({ guideMode: "draw" })}>Draw</button>
              <button onClick={() => useApp.setState({ guideMode: "erase" })}>Erase</button>
              <button onClick={() => useApp.setState({ drawPoints: [], guideErasePoints: [], guideEraseMask: null, guideComposite: null })}>Clear</button>
            </div>
          </div>
          <Canvas guide />
          <p className="hint">
            Draw a positive guide. Imported images remain separate from the
            generated state.
          </p>
          <label className="upload">
            ＋ Import guide image
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  const r = new FileReader();
                  r.onload = () =>
                    useApp.setState({ guideImage: String(r.result) });
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
              label="Global exploration"
              value={s.globalNoise}
              min={0}
              max={0.1}
              step={0.01}
              onChange={(v) => useApp.setState({ globalNoise: v })}
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
                <button onClick={s.saveSnapshot}>Save</button>
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
                  <img src={x.generatedImage} />
                  <div>
                    <b>Snapshot {String(i + 1).padStart(2, "0")}</b>
                    <small>{x.note}</small>
                  </div>
                  <button
                    onClick={() =>
                      useApp.setState({
                        generatedImage: x.generatedImage,
                        prompt: x.prompt,
                        loopStatus: "paused",
                      })
                    }
                  >
                    Restore
                  </button>
                </div>
              ))
            )}
          </section>
        </aside>
      </div>
      <footer>
        <span>
          {s.generationStatus === "generating" ? "Loading model / generating" : s.loopStatus === "running" ? "Explore is rolling from the current state" : s.loopStatus === "paused" ? "Exploration paused" : "Ready to explore"}
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
  const visibleSnapshots = s.backend === "tinysd"
    ? s.snapshots.filter((x) => x.runtimeSessionId === s.runtimeSessionId)
    : s.snapshots;
  const latest = visibleSnapshots[visibleSnapshots.length - 1];
  const finish = () => {
    if (latest) useApp.getState().finish(latest);
  };
  const restore = async () => {
    if (latest) {
      let generatedImage = latest.generatedImage;
      let diffusionStep = useApp.getState().diffusionStep;
      let diffusionSteps = useApp.getState().diffusionSteps;
      const sessionId = useApp.getState().runtimeSessionId;
      if (latest.runtimeSnapshotId && sessionId) {
        const response = await fetch(`${RUNTIME_URL}/runtime/snapshot/restore`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sessionId, snapshotId: latest.runtimeSnapshotId }) });
        if (!response.ok) throw new Error(`Restore HTTP ${response.status}`);
        const runtimeSnapshot = await response.json();
        generatedImage = runtimeSnapshot.previewImage;
        diffusionStep = runtimeSnapshot.diffusionStep;
        diffusionSteps = runtimeSnapshot.diffusionSteps;
      }
      useApp.setState({
        generatedImage,
        prompt: latest.prompt,
        guideImage: latest.importedImage ?? null,
        drawPoints: latest.humanDrawLayer ?? [],
        guideEraseMask: latest.guideEraseMask ?? null,
        guideErasePoints: latest.guideEraseMask ? JSON.parse(latest.guideEraseMask) : [],
        guideComposite: latest.guideComposite ?? null,
        diffusionStepCount: latest.diffusionStepCount ?? s.diffusionStepCount,
        seed: latest.seed ?? s.seed,
        diffusionStep,
        diffusionSteps,
        noiseBrushActive: false,
        activeNoiseMask: [],
        loopStatus: "paused",
      });
    }
  };
  return (
    <>
      {s.errorMessage && (
        <div className="runtime-error">Runtime error: {s.errorMessage}</div>
      )}
      {s.backend === "tinysd" && (
        <span className="real-model-badge">
          Real model route: segmind/tiny-sd · MPS
        </span>
      )}
      <div className="snapshot-actions">
        <button onClick={restore} disabled={!latest}>
          Restore latest
        </button>
        <button onClick={finish} disabled={!latest}>
          Finish latest
        </button>
      </div>
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <PersistenceBootstrap />
    <App />
  </React.StrictMode>,
);

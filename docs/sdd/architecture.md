# Live Diffusion Canvas 実装アーキテクチャ v0.4

この文書は、Live Diffusion Canvas v0.1 の実装構造を定義する。

重要な前提：backend は単なる image-to-image 再生成器ではなく、`docs/sdd/runtime.md` で定義する Stateful Diffusion Runtime として扱う。

実装は custom minimal app を第一候補とする。ただし、速度や reuse のために既存ツール fork / adapter を使ってよい。詳細は `docs/sdd/implementation_strategy.md` を参照する。

## 1. 推奨構成

v0.1 は Web アプリとして実装する。

```text
apps/
  web/
    src/
      app/
      components/
      state/
      runtime/
      generation/
      canvas/
      guide/
      snapshots/
      types/
```

`generation/` は互換名として残してよいが、中心概念は `runtime/` である。

## 2. レイヤー構成

```text
UI Layer
  PromptInput
  BackendModelSelector
  ControlBar
  GuideCanvas
  GeneratedImageCanvas
  SettingsPanel
  SnapshotTimeline

State Layer
  AppState
  actions
  selectors

Guide Layer
  ImportedImageLayer
  HumanDrawLayer
  GuideEraseMask
  GuideComposite export

Runtime Layer
  DiffusionRuntime interface
  MockStatefulRuntime
  BackendAdapter
  DirectDiffusersTinySDRuntime placeholder
  ComfyUIAdapter placeholder
  InvokeAIAdapter placeholder

Canvas Layer
  guide drawing capture
  guide erase capture
  momentary Noise Brush input
  activeNoiseMask capture
  lastNoiseMask metadata
  image export

Snapshot Layer
  save
  restore
  finish base selection
  optional runtime state reference
```

## 3. コンポーネント責務

### AppShell

全体レイアウトを管理する。

含むもの：

- TopBar
- MainWorkspace
- SettingsPanel
- SnapshotTimeline

### TopBar

含むもの：

- app name
- backend / model selector
- prompt input
- Run button
- Pause button
- Resume button

ユーザー向け Step button は実装しない。

### GuideCanvas

責務：

- Import Image
- Imported Image Layer 表示
- Imported Image opacity 調整
- Human Draw Layer 描画
- Clear Draw
- Guide Erase Mask 編集
- Guide Composite preview / export

Guide Canvas は Generated Image と別 state として保持する。

Guide Canvas は「こうしたい」という正の guide であり、Generated Image 側の Noise Brush とは役割が違う。

### GeneratedImageCanvas

責務：

- Generated Image preview 表示
- Noise Brush pointer input
- `noiseBrushActive` の更新
- `activeNoiseMask` の作成
- pointerup / touchend / cancel 時の `activeNoiseMask` clear
- `lastNoiseMask` metadata 更新

Noise Brush は Generated Image 上だけで動作する。

Noise Brush は persistent mask ではない。ユーザーが押下・ドラッグしている間だけ local rejection boost として runtime に渡す。

### SettingsPanel

責務：

- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- guideInfluence
- seed
- seedLocked
- updateIntervalMs
- brushSize

### SnapshotTimeline

責務：

- Snapshot サムネイル表示
- Snapshot 選択
- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

## 4. 型定義

### AppState

```ts
type AppState = {
  prompt: string;
  selectedBackend: string;
  selectedModel: string;

  loopStatus: "idle" | "running" | "paused";
  generationPhase: "explore" | "finish";
  generationStatus: "idle" | "generating" | "error";
  errorMessage: string | null;

  cfg: number;
  globalExplorationNoiseStrength: number;
  localRejectionStrength: number;
  guideInfluence: number;
  brushSize: number;
  updateIntervalMs: number;
  seed: number;
  seedLocked: boolean;

  importedImage: string | null;
  importedImageOpacity: number;
  humanDrawLayer: string | null;
  guideEraseMask: string | null;
  guideComposite: string | null;

  generatedImage: string | null;

  noiseBrushActive: boolean;
  activeNoiseMask: string | null;
  lastNoiseMask: string | null;

  runtimeSessionId: string | null;
  latestRequestId: number;

  snapshots: Snapshot[];
  selectedSnapshotId: string | null;
};
```

### Snapshot

```ts
type Snapshot = {
  id: string;
  parentId: string | null;
  createdAt: number;

  prompt: string;
  selectedBackend: string;
  selectedModel: string;

  seed: number;
  cfg: number;
  globalExplorationNoiseStrength: number;
  localRejectionStrength: number;
  guideInfluence: number;

  generatedImageDataUrl: string;
  importedImageDataUrl?: string;
  humanDrawLayerDataUrl?: string;
  guideEraseMaskDataUrl?: string;
  guideCompositeDataUrl?: string;
  lastNoiseMaskDataUrl?: string;

  runtimeStateRef?: string;
  note?: string;
};
```

`lastNoiseMaskDataUrl` は metadata である。Restore 時に active rejection input として再開してはならない。

### DiffusionRuntimeState

```ts
type DiffusionRuntimeState = {
  sessionId: string;
  prompt: string;
  promptEmbedding?: unknown;
  latent?: unknown;
  timestep?: number;
  schedulerState?: unknown;
  width: number;
  height: number;
  seed: number;
  latestPreviewImage?: string;
};
```

### DiffusionIntervention

```ts
type DiffusionIntervention = {
  requestId: number;
  sessionId: string;
  prompt?: string;

  guideComposite?: string;
  guideInfluence: number;

  globalExplorationNoiseStrength: number;

  noiseBrushActive: boolean;
  activeNoiseMask?: string;
  localRejectionStrength: number;

  updatesToAdvance: number;
  phase: "explore" | "finish";
};
```

### DiffusionRuntimeResponse

```ts
type DiffusionRuntimeResponse = {
  requestId: number;
  sessionId: string;
  previewImage: string;
  seed: number;
  timestep?: number;
  latencyMs: number;
};
```

## 5. Runtime interface

```ts
interface DiffusionRuntime {
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
}
```

`GenerationBackend` / `GenerationRequest` / `GenerationResponse` という名前を内部互換として残してもよい。ただし意味は stateful runtime update であり、通常の Explore update で毎回 blank state から再生成してはならない。

## 6. Run flow

```text
1. loopStatus を running にする。
2. runtimeSessionId がなければ createSession する。
3. updateIntervalMs ごとに runtime tick を試みる。
4. 各 tick で latestRequestId を increment する。
5. AppState から DiffusionIntervention を作る。
6. guideComposite、guideInfluence、globalExplorationNoiseStrength を含める。
7. noiseBrushActive が true の場合だけ activeNoiseMask と localRejectionStrength を含める。
8. generationStatus を generating にする。
9. runtime.applyIntervention(state, intervention) を呼ぶ。
10. response.requestId が latestRequestId と一致する場合のみ反映する。
11. generatedImage を response.previewImage に更新する。
12. runtime state を保持する。
13. generationStatus を idle に戻す。
14. loopStatus が running なら繰り返す。
```

エラー時は `generationStatus = error` とし、`errorMessage` を設定する。ただし UI は継続操作可能であること。

## 7. Pause / Resume flow

```text
Pause:
  loopStatus = paused
  new runtime request を出さない

Resume:
  loopStatus = running
  現在の runtime state から Run flow を再開する
```

ユーザー向け Step Mode は存在しない。内部関数として `runOneTick()` または同等の 1 tick 更新関数を持つのは許可する。

## 8. Guide Canvas flow

```text
Import Image:
  importedImage を設定する
  importedImageOpacity を初期値にする
  runtime session は自動リセットしない

Draw:
  humanDrawLayer を更新する

Guide Erase:
  guideEraseMask を更新する

Compose:
  importedImage + guideEraseMask + humanDrawLayer から guideComposite を作る
```

Import Image は v0.1 では guide-only である。Base Image Init Mode は実装しない。

## 9. Noise Brush pointer flow

```text
pointerdown / touchstart:
  noiseBrushActive = true
  activeNoiseMask を作成または初期化

pointermove / touchmove:
  activeNoiseMask を更新
  lastNoiseMask を更新してよい

pointerup / touchend / pointercancel:
  noiseBrushActive = false
  lastNoiseMask = activeNoiseMask
  activeNoiseMask = null
```

`lastNoiseMask` は履歴・debug・Snapshot metadata 用であり、runtime intervention には使わない。

Persistent / pinned rejection mask は v0.1 では実装しない。

## 10. stale response 対策

各 request に `requestId` を付与する。

response 反映時に以下を確認する。

```ts
if (response.requestId !== state.latestRequestId) {
  return;
}
```

または、single-flight 方式で同時に 1 request だけ実行してもよい。

どちらを採用しても、古い response が新しい state を上書きしてはならない。

## 11. Runtime behavior

Preferred real-runtime behavior:

```text
always in Explore:
  guideComposite + guideInfluence
  globalExplorationNoiseStrength
  → low-strength guide-aware runtime update

only while Noise Brush is active:
  activeNoiseMask
  → latent resolution に変換
  → mask 領域だけ latent に local rejection noise を混ぜる

then:
  → 1〜3 update
  → preview decode
  → updated runtime state を保持
```

Mock runtime では、この処理を視覚的・ログ的に模倣してよい。

## 12. Snapshot flow

### Save Snapshot

保存対象：

- prompt
- selectedBackend
- selectedModel
- seed
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- guideInfluence
- generatedImage
- importedImage
- humanDrawLayer
- guideEraseMask
- guideComposite
- lastNoiseMask metadata if present
- parentId
- runtimeStateRef if available

### Restore Snapshot

復元対象：

- prompt
- selectedBackend
- selectedModel
- seed
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- guideInfluence
- generatedImage
- importedImage
- humanDrawLayer
- guideEraseMask
- guideComposite
- selectedSnapshotId
- runtimeSessionId if recoverable

Do not restore `lastNoiseMaskDataUrl` as active rejection input.

If runtime state cannot be restored, use image Snapshot pseudo resume.

### Finish from Snapshot

選択 Snapshot の generatedImage を base preview として Finish を開始する。

Runtime state が保存されている場合は、それを優先して使う。

Finish 用の設定を使う。

```text
updates: 12-30
globalExplorationNoiseStrength: 0.00
localRejectionStrength: 0.05-0.20
guideInfluence: 0.3-0.7
cfg: 3.0-6.0
```

Finish 開始時は Run loop を停止する。

元 Snapshot は削除しない。

## 13. Backend strategy

Default route:

```text
custom minimal web UI
→ Mock Stateful Runtime
→ adapter spike only after UI semantics are correct
```

Allowed adapter routes:

```text
Direct Diffusers / TinySD runtime
ComfyUI backend adapter
InvokeAI fork or adapter
other compatible tool adapter
```

Fork / adapter use must not reintroduce:

- user-facing Step Mode
- ordinary one-shot inpainting semantics
- persistent Noise Brush mask
- local Guide Canvas apply brush

## 14. 実装しないもの

- user-facing Step Mode
- Base Image Init Mode
- persistent database
- user authentication
- multi-user session
- required ControlNet pipeline
- required latent state persistence
- persistent / pinned rejection mask
- production deployment
- StreamDiffusion runtime

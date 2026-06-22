# Live Diffusion Canvas 実装アーキテクチャ v0.3

この文書は、Live Diffusion Canvas v0.1 の実装構造を定義する。

重要な前提：backend は単なる image-to-image 再生成器ではなく、`docs/sdd/runtime.md` で定義する Stateful Diffusion Runtime として扱う。

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
  HumanLayerCanvas
  GeneratedImageCanvas
  SettingsPanel
  SnapshotTimeline

State Layer
  AppState
  actions
  selectors

Runtime Layer
  DiffusionRuntime interface
  MockStatefulRuntime
  TinySDStatefulLatentRuntime placeholder

Canvas Layer
  human drawing capture
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
- Step button
- Auto button
- Pause button

### HumanLayerCanvas

責務：

- Human Layer 描画
- clear
- data URL export

Human Layer は Generated Image と別 state として保持する。

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

- steps
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
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
  selectedBackend: "mock" | "tinysd";
  selectedModel: string;

  controlMode: "step" | "auto" | "pause";
  generationPhase: "explore" | "finish";
  generationStatus: "idle" | "generating" | "error";
  errorMessage: string | null;

  steps: number;
  cfg: number;
  globalExplorationNoiseStrength: number;
  localRejectionStrength: number;
  brushSize: number;
  updateIntervalMs: number;
  seed: number;
  seedLocked: boolean;

  humanLayer: string | null;
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
  selectedBackend: "mock" | "tinysd";
  selectedModel: string;

  seed: number;
  steps: number;
  cfg: number;
  globalExplorationNoiseStrength: number;
  localRejectionStrength: number;

  generatedImageDataUrl: string;
  humanLayerDataUrl?: string;
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
  humanLayer?: string;

  globalExplorationNoiseStrength: number;

  noiseBrushActive: boolean;
  activeNoiseMask?: string;
  localRejectionStrength: number;

  stepsToAdvance: number;
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
  name: "mock" | "tinysd";
  createSession(input: {
    prompt: string;
    seed: number;
    width: number;
    height: number;
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

## 6. Step flow

```text
1. runtimeSessionId がなければ createSession する。
2. latestRequestId を increment する。
3. AppState から DiffusionIntervention を作る。
4. controlMode が step の場合も、generationPhase は通常 explore とする。
5. generationStatus を generating にする。
6. runtime.applyIntervention(state, intervention) を呼ぶ。
7. response.requestId が latestRequestId と一致する場合のみ反映する。
8. generatedImage を response.previewImage に更新する。
9. runtime state を保持する。
10. generationStatus を idle に戻す。
```

エラー時は `generationStatus = error` とし、`errorMessage` を設定する。

## 7. Auto flow

```text
1. controlMode を auto にする。
2. updateIntervalMs ごとに Step 相当の runtime update を試みる。
3. 各 update には globalExplorationNoiseStrength を含める。
4. noiseBrushActive が true の場合だけ activeNoiseMask と localRejectionStrength を含める。
5. 生成中に次の tick が来た場合は skip または待機する。
6. Pause が押されたら新しい request を出さない。
```

## 8. Noise Brush pointer flow

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

## 9. stale response 対策

各 request に `requestId` を付与する。

response 反映時に以下を確認する。

```ts
if (response.requestId !== state.latestRequestId) {
  return;
}
```

または、single-flight 方式で同時に 1 request だけ実行してもよい。

どちらを採用しても、古い response が新しい state を上書きしてはならない。

## 10. Runtime behavior

Preferred real-runtime behavior:

```text
always in Explore:
  globalExplorationNoiseStrength
  → low-strength uncertainty injection across state

only while Noise Brush is active:
  activeNoiseMask
  → latent resolution に変換
  → mask 領域だけ latent に local rejection noise を混ぜる

then:
  → 1〜3 step denoise
  → preview decode
  → updated runtime state を保持
```

Mock runtime では、この処理を視覚的・ログ的に模倣してよい。

## 11. Snapshot flow

### Save Snapshot

保存対象：

- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- generatedImage
- humanLayer
- lastNoiseMask metadata if present
- parentId
- runtimeStateRef if available

### Restore Snapshot

復元対象：

- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- globalExplorationNoiseStrength
- localRejectionStrength
- generatedImage
- humanLayer
- selectedSnapshotId
- runtimeSessionId if recoverable

Do not restore `lastNoiseMaskDataUrl` as active rejection input.

If runtime state cannot be restored, use image Snapshot pseudo resume.

### Finish from Snapshot

選択 Snapshot の generatedImage を base preview として Finish を開始する。

Runtime state が保存されている場合は、それを優先して使う。

Finish 用の設定を使う。

```text
steps: 12-30
globalExplorationNoiseStrength: 0.00
localRejectionStrength: 0.05-0.20
cfg: 3.0-6.0
```

Finish 開始時は Auto を停止する。

元 Snapshot は削除しない。

## 12. Mock Stateful Runtime

Mock runtime は実際の拡散品質を目指さない。

最低限、以下を満たす。

- sessionId を作る。
- request を受け取る。
- preview image を返す。
- prompt、requestId、seed、globalExplorationNoiseStrength、noiseBrushActive、activeNoiseMask 有無などを画像またはログで確認できる。
- latencyMs を返す。
- runtime state 更新を擬似的に示す。
- global exploration noise の常時揺らぎを擬似的に示す。
- local rejection boost が Noise Brush 操作中だけ効くことを擬似的に示す。
- エラー状態のテストができる。

## 13. TinySD Stateful Latent Runtime

TinySD runtime は v0.1 の first real backend candidate である。

要求される方向性：

- latent state を保持する。
- timestep を保持する。
- scheduler state を保持できるなら保持する。
- Prompt embedding を cache できるなら cache する。
- globalExplorationNoiseStrength を低強度の常時揺らぎとして扱う。
- noiseBrushActive 中だけ activeNoiseMask を latent 解像度に変換する。
- mask 領域に local rejection noise を注入する。
- 1〜3 step 進める。
- preview を decode する。

TinySD が利用不可でもアプリは Mock runtime で起動しなければならない。

## 14. 実装しないもの

- persistent database
- user authentication
- multi-user session
- ControlNet pipeline
- required latent state persistence
- persistent / pinned rejection mask
- production deployment
- StreamDiffusion runtime

# Live Diffusion Canvas 実装アーキテクチャ v0.1

この文書は、Live Diffusion Canvas v0.1 の実装構造を定義する。

## 1. 推奨構成

v0.1 は Web アプリとして実装する。

```text
apps/
  web/
    src/
      app/
      components/
      state/
      generation/
      canvas/
      snapshots/
      types/
```

実装フレームワークは固定しない。エージェントが判断する場合は React / Next.js 相当を優先する。

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

Generation Layer
  GenerationBackend interface
  MockGenerationBackend
  TinySDGenerationBackend placeholder

Canvas Layer
  human drawing capture
  noise mask capture
  image export

Snapshot Layer
  save
  restore
  finish base selection
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

- Generated Image 表示
- Noise Brush 入力
- noiseMask export

Noise Brush は Generated Image 上だけで動作する。

### SettingsPanel

責務：

- steps
- cfg
- noiseStrength
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

  mode: "step" | "auto" | "pause";
  generationStatus: "idle" | "generating" | "error";
  errorMessage: string | null;

  steps: number;
  cfg: number;
  noiseStrength: number;
  brushSize: number;
  updateIntervalMs: number;
  seed: number;
  seedLocked: boolean;

  humanLayer: string | null;
  generatedImage: string | null;
  noiseMask: string | null;

  snapshots: Snapshot[];
  selectedSnapshotId: string | null;

  latestRequestId: number;
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
  noiseStrength: number;

  generatedImageDataUrl: string;
  humanLayerDataUrl?: string;
  noiseMaskDataUrl?: string;

  note?: string;
};
```

### GenerationRequest

```ts
type GenerationRequest = {
  requestId: number;
  prompt: string;
  selectedBackend: "mock" | "tinysd";
  selectedModel: string;
  image?: string;
  noiseMask?: string;
  humanLayer?: string;
  seed: number;
  steps: number;
  cfg: number;
  noiseStrength: number;
};
```

### GenerationResponse

```ts
type GenerationResponse = {
  requestId: number;
  image: string;
  seed: number;
  latencyMs: number;
};
```

## 5. GenerationBackend interface

```ts
interface GenerationBackend {
  name: "mock" | "tinysd";
  generate(request: GenerationRequest): Promise<GenerationResponse>;
}
```

v0.1 では、まず `MockGenerationBackend` を実装する。

TinySD backend は、同じ interface を満たす別実装として追加する。

## 6. 生成フロー

### Step

```text
1. latestRequestId を increment する。
2. AppState から GenerationRequest を作る。
3. generationStatus を generating にする。
4. backend.generate(request) を呼ぶ。
5. response.requestId が latestRequestId と一致する場合のみ反映する。
6. generatedImage を response.image に更新する。
7. generationStatus を idle に戻す。
```

エラー時は `generationStatus = error` とし、`errorMessage` を設定する。

### Auto

```text
1. mode を auto にする。
2. updateIntervalMs ごとに Step 相当の処理を試みる。
3. 生成中に次の tick が来た場合は skip または待機する。
4. Pause が押されたら新しい request を出さない。
```

## 7. stale response 対策

各 request に `requestId` を付与する。

response 反映時に以下を確認する。

```ts
if (response.requestId !== state.latestRequestId) {
  return;
}
```

または、single-flight 方式で同時に 1 request だけ実行してもよい。

どちらを採用しても、古い response が新しい状態を上書きしてはならない。

## 8. Snapshot フロー

### Save Snapshot

保存対象：

- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- noiseStrength
- generatedImage
- humanLayer
- noiseMask
- parentId

### Restore Snapshot

復元対象：

- prompt
- selectedBackend
- selectedModel
- seed
- steps
- cfg
- noiseStrength
- generatedImage
- humanLayer
- noiseMask
- selectedSnapshotId

### Finish from Snapshot

選択 Snapshot の generatedImage を base image として generation request を作る。

Finish 用の設定を使う。

```text
steps: 12-30
noiseStrength: 0.05-0.20
cfg: 3.0-6.0
```

元 Snapshot は削除しない。

## 9. Mock backend の仕様

Mock backend は実際の拡散品質を目指さない。

最低限、以下を満たす。

- request を受け取る。
- data URL 画像を返す。
- prompt、requestId、seed、noiseMask 有無などを画像またはログで確認できる。
- latencyMs を返す。
- エラー状態のテストができる。

Mock 画像は canvas で生成してよい。

## 10. 実モデル接続の境界

TinySD などの実モデル接続は、UI と state から分離する。

UI は backend 実装の詳細を直接知らない。

Backend / Model selector は `selectedBackend` と `selectedModel` を更新するだけにする。

## 11. エラー処理

生成エラー時：

- generationStatus を error にする。
- errorMessage を表示する。
- Human Layer、Generated Image、Snapshot は保持する。
- Step / Auto / Pause の操作は継続可能にする。

## 12. 実装しないもの

- persistent database
- user authentication
- multi-user session
- ControlNet pipeline
- latent state persistence
- production deployment

# Live Diffusion Canvas 仕様書 v0.3

## 0. 位置づけ

本仕様書は、Live Diffusion Canvas v0.1 実装の source of truth である。

Live Diffusion Canvas は、Prompt、Human Layer、Generated Image、Noise Brush、Snapshot を使って、拡散モデルの生成途中状態を人間が探索・介入・仕上げできることを示すプロトタイプである。

重要な修正点：本プロトタイプの backend は、単なる image-to-image 再生成器ではない。意図する抽象は、拡散過程の state を保持し、人間の入力でその state に介入し、少数 step だけ進めて preview を返す **Stateful Diffusion Runtime** である。

さらに v0.1 の Explore Mode は、停止した画像に対して単発編集するものではない。Auto loop は、低強度の global exploration noise により state を少し揺らし続ける。Noise Brush は、その常時 loop に対して、ユーザーが押下・ドラッグしている間だけ局所的な rejection boost を加える momentary input である。

詳細は `docs/sdd/runtime.md` を参照する。

## 1. プロダクト定義

Live Diffusion Canvas は、一発で完成画像を生成するツールではない。

目的は、生成途中の状態を探索し、良い中間状態を Snapshot として保存し、そこから復元・分岐・仕上げを行うことである。

基本体験は以下である。

```text
Prompt を設定する
→ 生成ループを開始する
→ runtime が低強度の global exploration noise で少しずつ揺らぎ続ける
→ Human Layer で人間が正の介入信号を与える
→ 気に入らない局所解を Noise Brush でこする
→ ブラシ操作中だけ、その領域の不確定性が強く上がる
→ ブラシを離すと局所 rejection boost は止まる
→ runtime が Prompt / Human Layer / 周辺 state を条件に別の局所解を探索する
→ 良い骨格を Snapshot として保存する
→ Snapshot を選び、そこから Restore または Finish する
```

本プロトタイプの価値は、画像生成を「Prompt → 完成画像」ではなく、「生成途中 state を人間が操作できる過程」として提示する点にある。

## 2. コアコンセプト

### 2.1 Prompt

Prompt は生成の方向性を定義するテキスト条件である。

Prompt は「何を作るか」「どの特徴に注意を向けるか」を決める。

Prompt 変更は runtime session を破棄しない。次回以降の runtime update から新しい Prompt を条件として使う。Reset Session が明示された場合のみ runtime state を初期化する。

### 2.2 Human Layer

Human Layer は、人間が描く独立レイヤーである。

Human Layer は完成画像そのものではなく、生成過程に対する正の介入信号または guide として扱う。

Human Layer は Generated Image と分離して保持する。

生成処理、Noise Brush、Auto Mode は Human Layer を変更してはならない。

重要：Noise Brush は Human Layer を局所適用するための仕組みではない。Human Layer は全体または runtime session に対する継続的な guide であり、Noise Brush は現在の局所解を reject して別解探索を促す負の momentary 介入である。

v0.1 では Human Layer を active ControlNet 条件にする必要はない。ただし runtime abstraction は、将来 Human Layer を conditioning input として使う拡張を妨げてはならない。

### 2.3 Generated Image

Generated Image は、現在の runtime state から得られた preview image である。

Auto Mode では、Generated Image を毎回ゼロから再生成するのではなく、保持されている runtime state を少しずつ進めた preview として更新する。

Mock backend では、この stateful behavior を擬似的に再現してよい。

### 2.4 Global Exploration Noise

Global Exploration Noise は、Explore Mode の各 Auto update で全体に低強度で入る揺らぎである。

目的は、生成状態を完全に固定せず、生成途中の形が少しずつ変化し続ける状態を保つことである。

この強度は `globalExplorationNoiseStrength` で表す。

v0.1 では UI に出す場合も、初期値は低くする。

```text
globalExplorationNoiseStrength: 0.02-0.10
```

### 2.5 Noise Brush

Noise Brush は、Generated Image 上で指定した領域の **現在の局所解を reject する** ための momentary brush である。

これは通常の消しゴムではない。また、Human Layer をその領域へ直接適用するブラシでもない。

Noise Brush は、ユーザーが押下・ドラッグしている間だけ active になる。ブラシを離した後、局所 rejection boost は停止し、active mask は clear される。

Noise Brush 操作中は `noiseBrushActive = true` になり、現在の stroke は `activeNoiseMask` として `DiffusionIntervention` に含まれる。

`activeNoiseMask` の意味は以下である。

```text
この領域に現在出ている解は不採用である。
したがって、ブラシ操作中だけこの領域の不確定性を強く上げ、
現在の局所解から離れた別解を探索させる。
```

実 backend では、`activeNoiseMask` を latent 解像度へ変換し、該当領域に局所的な uncertainty injection を行い、1〜3 step だけ denoise を進める実装を優先する。

再探索時には Prompt、Human Layer、周辺 runtime state が条件として作用する。

v0.1 では、Noise Brush は Generated Image にのみ適用する。Human Layer には適用しない。

`lastNoiseMask` は debug/history metadata として保持してよいが、active intervention ではない。Snapshot へ保存してもよいが、Restore 時に自動で再適用してはならない。

Persistent / pinned rejection mask は v0.1 の範囲外である。

### 2.6 Snapshot

Snapshot は、生成途中の状態を保存する単位である。

Snapshot は単なる履歴ではなく、復元と Finish の起点である。

v0.1 では image Snapshot は必須である。

runtime が対応する場合、Snapshot は runtime state も保存してよい。

```text
image Snapshot = required
runtime-state Snapshot = optional
lastNoiseMask metadata = optional, not active on restore
```

runtime-state Snapshot がない場合、Restore は image Snapshot による擬似再開でよい。

### 2.7 Backend、Model、Runtime

v0.1 では `selectedBackend` と `selectedModel` を分ける。

- `selectedBackend`: 実行 runtime/backend を表す。値は `mock` または `tinysd`。
- `selectedModel`: runtime/backend に渡すモデル名。v0.1 では `mock` または TinySD 相当のモデル名でよい。

最初に実装する backend は `mock` である。

次の real backend 候補は `tinysd` である。TinySD は単なる遠い拡張ではなく、v0.1 の first real stateful latent runtime 候補である。

## 3. MVP の範囲

### 3.1 含める機能

v0.1 では以下を実装対象とする。

- Prompt 入力
- Backend / Model 選択
- Human Layer キャンバス
- Generated Image キャンバス
- Noise Brush
- Step 実行
- Auto 実行
- Pause
- Snapshot 保存
- Snapshot 復元
- Snapshot から Finish
- 基本生成設定
  - Steps
  - CFG / Guidance Scale
  - Global Exploration Noise Strength
  - Local Rejection Strength
  - Seed
  - Update Interval
  - Brush Size
- Mock Stateful Runtime
- Stateful Diffusion Runtime 抽象
- TinySD Stateful Latent Runtime hook

### 3.2 含めない機能

v0.1 では以下を実装しない。

- 図構造認識
- Mermaid / UML / SVG 変換
- ControlNet
- T2I-Adapter
- IP-Adapter
- LCM / LCM-LoRA を必須 runtime とすること
- StreamDiffusion
- SDXL Finish backend
- 複雑なレイヤー管理
- Semantic editing
- latent snapshot の完全保存を必須にすること
- persistent / pinned rejection mask
- 認証
- クラウドデプロイ
- 共同編集
- 本番品質の最適化
- 複数ユーザー同期
- 永続サーバーストレージ
- Branch Tree UI

## 4. 画面構成

```text
上部:
  - アプリ名
  - Backend / Model 選択
  - Prompt 入力
  - Step / Auto / Pause

中央左:
  - Human Layer キャンバス

中央右:
  - Generated Image キャンバス
  - Noise Brush 操作対象

下部:
  - Snapshot Timeline

右側または下部:
  - Generation Settings
  - Noise Brush Settings
```

## 5. UI 要素

### 5.1 Prompt 入力

ユーザーは Prompt を入力できる。

Prompt は現在の runtime session に適用される。

Auto Mode 中に Prompt が変更された場合、session を破棄せず、次回以降の runtime update に反映される。

### 5.2 Backend / Model 選択

v0.1 の backend は `mock` と `tinysd` を想定する。

初期値は `mock` とする。

TinySD が利用できない環境でも、Mock Stateful Runtime により UI と状態遷移を確認できなければならない。

### 5.3 Human Layer キャンバス

要件：

- 描画は体感即時で反映されること
- Human Layer は Generated Image と分離されること
- 生成処理によって Human Layer が変更されないこと
- Clear 操作で Human Layer のみ消去できること
- export 可能な形式で保持できること

### 5.4 Generated Image キャンバス

Generated Image は現在の runtime state から得られた preview を表示する。

Noise Brush は Generated Image に対して、押下・ドラッグ中だけ momentary に適用される。

### 5.5 Noise Brush

Noise Brush の設定項目：

- Brush Size
- Local Rejection Strength

`Local Rejection Strength` は、Noise Brush で指定された active rejected region にどれだけ強く不確定性を再注入するかを表す。

Noise Brush は押下・ドラッグ中だけ効く。pointerup / touchend / cancel 後は `noiseBrushActive = false` になり、`activeNoiseMask` は clear される。

### 5.6 Snapshot Timeline

Snapshot Timeline は、保存済み中間状態を横並びで表示する。

最低限必要な操作：

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

`parentId` は将来の分岐管理のために保存するが、v0.1 では Branch Tree UI を実装しない。

## 6. 生成モード

### 6.1 Step Mode

ボタンを押すたびに 1 回だけ runtime update を行う。

### 6.2 Auto Mode

一定間隔で runtime update を試みる。

Auto Mode は rolling intervention loop である。final timestep 到達だけを目的にせず、global exploration noise により state を低強度で揺らし続ける。

初期値：

```text
update_interval_ms: 300
steps_per_loop: 1-3
global_exploration_noise_strength: 0.04
local_rejection_strength: 0.25
cfg: 3.0
```

Auto Mode は停止できなければならない。

前回 request が未完了の状態で次の tick が来た場合、実装は skip または待機を選んでよい。ただし古い response が新しい state を上書きしてはならない。

### 6.3 Pause Mode

生成ループを停止する。

Pause 中も Human Layer の描画、Noise Brush の指定、Snapshot 操作は可能とする。

## 7. Explore Mode

Explore Mode は、良い中間状態・良い骨格を探すためのモードである。

推奨初期値：

```text
steps_per_loop: 1-3
update_interval_ms: 300
global_exploration_noise_strength: 0.02-0.10
local_rejection_strength: 0.20-0.35
cfg: 2.0-4.0
seed_locked: true
```

Explore Mode では、完成品質よりも生成過程の操作性を優先する。

## 8. Finish Mode

Finish Mode は、選択した Snapshot から仕上げ生成を行うための明示操作である。

推奨初期値：

```text
finish_steps: 12-30
global_exploration_noise_strength: 0.00
local_rejection_strength: 0.05-0.20
cfg: 3.0-6.0
seed_locked: true
```

Finish Mode では、選択した中間状態の骨格を大きく崩さず、細部を整えることを目的とする。

Finish from Snapshot を開始したら Auto Mode は停止する。Finish request 中は新しい Auto request を出さない。Finish 完了後の mode は pause または step に戻す。

## 9. Runtime update loop

基本処理：

```text
DiffusionRuntimeState を取得
→ Prompt / Human Layer / globalExplorationNoiseStrength を DiffusionIntervention にする
→ noiseBrushActive が true の場合だけ activeNoiseMask と localRejectionStrength を含める
→ runtime.applyIntervention または互換 backend.generate を呼ぶ
→ runtime が global exploration noise と optional local rejection boost を state に適用する
→ runtime が少数 step 進める
→ requestId が最新なら preview を Generated Image に反映する
→ state を保持する
→ Auto Mode なら繰り返す
```

`activeNoiseMask` は「ここに Human Layer を適用する」という意味ではない。

`activeNoiseMask` は「この領域の現在の局所解は reject された」という意味を持つ。runtime はブラシ操作中だけこの情報を使って局所不確定性を上げ、現在の局所解から離れた別解を探索する。その探索に対して Prompt、Human Layer、周辺 runtime state が条件として作用する。

初期状態で runtime state が存在しない場合は、Prompt から初期 state を作るか、Mock Stateful Runtime のプレースホルダー state を作る。

## 10. Snapshot 仕様

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

v0.1 では以下を実装する。

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

`runtimeStateRef` は任意である。runtime が state snapshot に対応しない場合は保存しなくてよい。

`lastNoiseMaskDataUrl` は metadata である。Restore 時に active rejection mask として再開してはならない。

## 11. 生成設定

| 設定 | 意味 | 初期値 |
|---|---|---|
| selectedBackend | 実行 runtime/backend | mock |
| selectedModel | backend に渡すモデル名 | mock |
| Prompt | 生成方向 | ユーザー入力 |
| Steps | 1 update あたり進める step 数 | Explore: 1-3 / Finish: 12-30 |
| CFG | Prompt の強さ | 3.0 |
| Global Exploration Noise Strength | Explore loop 全体を低強度で揺らす強さ | 0.04 |
| Local Rejection Strength | Noise Brush 操作中の rejected region への不確定性注入の強さ | 0.25 |
| Seed | 乱数固定 | ON |
| Update Interval | Auto 更新間隔 | 300ms |
| Brush Size | Noise Brush の大きさ | 32px |

Scheduler は v0.1 では UI に出さず固定でよい。

## 12. Runtime / Backend 抽象化

詳細は `docs/sdd/runtime.md` を参照する。

互換 API として以下を使ってよい。

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

type DiffusionRuntimeResponse = {
  requestId: number;
  sessionId: string;
  previewImage: string;
  seed: number;
  timestep?: number;
  latencyMs: number;
};
```

Existing `GenerationRequest` / `GenerationResponse` names may remain as thin compatibility aliases, but the semantics are stateful.

## 13. アプリ状態

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

## 14. 受け入れ条件

v0.1 の受け入れ条件は `docs/sdd/acceptance.md` を参照する。

## 15. 非機能要件

- Human Layer 描画は体感即時であること。
- 生成更新は best effort でよい。
- Auto 更新間隔は設定可能であること。
- 通常操作で Prompt、Generated Image、Human Layer、Snapshot を失わないこと。
- 通常の Explore update は毎回 blank state から再生成しないこと。
- Noise Brush の local rejection boost は押下・ドラッグ中だけ active であること。

## 16. 開発ルール

v0.1 では、本仕様書に書かれていない機能を実装しない。

新しい機能が必要になった場合、先に `docs/sdd/grill.md` の確認手順を通し、仕様書を更新する。

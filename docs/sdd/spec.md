# Live Diffusion Canvas 仕様書 v0.4

## 0. 位置づけ

本仕様書は、Live Diffusion Canvas v0.1 実装の source of truth である。

Live Diffusion Canvas は、Prompt、Guide Canvas、Generated Image、Noise Brush、Snapshot を使って、拡散モデルの生成途中状態を人間が探索・介入・仕上げできることを示すプロトタイプである。

重要な前提：本プロトタイプの backend は、単なる image-to-image 再生成器ではない。意図する抽象は、拡散過程の state を保持し、人間の入力でその state に介入し、少数 update だけ進めて preview を返す **Stateful Diffusion Runtime** である。

v0.1 の Explore は、停止した画像に対する単発編集ではない。Run loop は、低強度の `globalExplorationNoiseStrength` により state を少し揺らし続ける。Noise Brush は、その常時 loop に対して、ユーザーが押下・ドラッグしている間だけ局所的な rejection boost を加える momentary input である。

v0.1 にはユーザー向け Step Mode / Step button は存在しない。内部実装として 1 tick の runtime update 関数を持ってよいが、UI と product flow は Run / Pause / Resume を中心にする。

実装はゼロから作ってもよいが、既存ツールを fork / extension / backend として利用してよい。詳細は `docs/sdd/implementation_strategy.md` を参照する。

## 1. プロダクト定義

Live Diffusion Canvas は、一発で完成画像を生成するツールではない。

目的は、生成途中の状態を探索し、良い中間状態を Snapshot として保存し、そこから復元・分岐・仕上げを行うことである。

基本体験は以下である。

```text
Prompt を設定する
→ Guide Canvas に画像を import する、または直接描く
→ Run で生成介入ループを開始する
→ runtime が低強度の global exploration noise で少しずつ揺らぎ続ける
→ Guide Canvas が正の guide として働く
→ 気に入らない局所解を Noise Brush でこする
→ ブラシ操作中だけ、その領域の不確定性が強く上がる
→ ブラシを離すと局所 rejection boost は止まる
→ runtime が Prompt / Guide Composite / 周辺 state を条件に別の局所解を探索する
→ 良い骨格を Snapshot として保存する
→ Snapshot を選び、そこから Restore または Finish する
```

本プロトタイプの価値は、画像生成を「Prompt → 完成画像」ではなく、「生成途中 state を人間が操作できる過程」として提示する点にある。

## 2. コアコンセプト

### 2.1 Prompt

Prompt は生成の方向性を定義するテキスト条件である。

Prompt 変更は runtime session を破棄しない。次回以降の runtime update から新しい Prompt を条件として使う。Reset Session が明示された場合のみ runtime state を初期化する。

### 2.2 Guide Canvas

Guide Canvas は、生成を誘導する編集可能なガイド面である。

旧 Human Layer の上位概念として扱う。v0.1 では Human Layer という単独概念ではなく、Guide Canvas の中に Human Draw Layer を含める。

Guide Canvas は Generated Image と分離して保持する。

生成処理、Noise Brush、Run loop は Guide Canvas を破壊的に変更してはならない。

Guide Canvas は以下の sublayer を持つ。

```text
Imported Image Layer: 取り込み画像。guide の基盤。
Human Draw Layer: ユーザーが描き足す線・形・指示。
Guide Erase Mask: Imported Image Layer の不要部分を非破壊に隠す mask。
Guide Composite: runtime に渡す合成 guide image。
```

Guide Canvas は「こうしたい」という正の guide である。Noise Brush は Generated Image 側の「これは嫌だ」という負の momentary input である。この2つを混同してはならない。

v0.1 では Guide Composite を active ControlNet 条件にする必要はない。ただし runtime abstraction は、将来 Guide Composite を conditioning input として使う拡張を妨げてはならない。

### 2.3 Imported Image Layer

Imported Image Layer は、Guide Canvas に読み込まれた基底画像である。

目的は、既存画像を編集可能な guide として使うことである。

v0.1 では Import Image は **guide-only** とする。つまり、画像 import は runtime session を自動初期化しない。

将来、画像を initial image / initial latent として使う Base Image Init Mode を追加してよい。ただし v0.1 では範囲外である。

Imported Image Layer は opacity を持ってよい。

### 2.4 Human Draw Layer

Human Draw Layer は、Guide Canvas 上でユーザーが描き足す手描き sublayer である。

Clear Draw は Human Draw Layer のみを消す。Imported Image Layer は消さない。

### 2.5 Guide Erase Mask

Guide Erase Mask は、Imported Image Layer の不要部分を隠すための非破壊 mask である。

これは Generated Image 側の Noise Brush とは別物である。

Guide Erase は「guide の見え方を編集する」ための操作であり、Generated Image の局所解を reject する操作ではない。

### 2.6 Guide Composite

Guide Composite は、Imported Image Layer、Guide Erase Mask、Human Draw Layer を合成した runtime 入力である。

```text
Guide Composite = Compose(Imported Image Layer, Guide Erase Mask, Human Draw Layer)
```

Runtime には、個別 sublayer を渡してもよいが、v0.1 の最小実装では `guideComposite` を渡せればよい。

Guide Composite の効き具合は `guideInfluence` で表す。

```text
guideInfluence: 0.0-1.0
initial: 0.5
```

### 2.7 Generated Image

Generated Image は、現在の runtime state から得られた preview image である。

Run loop では、Generated Image を毎回ゼロから再生成するのではなく、保持されている runtime state を少しずつ進めた preview として更新する。

Mock backend では、この stateful behavior を擬似的に再現してよい。

### 2.8 Global Exploration Noise

Global Exploration Noise は、Explore の各 Run loop update で全体に低強度で入る揺らぎである。

目的は、生成状態を完全に固定せず、生成途中の形が少しずつ変化し続ける状態を保つことである。

この強度は `globalExplorationNoiseStrength` で表す。

```text
globalExplorationNoiseStrength: 0.02-0.10
```

### 2.9 Noise Brush

Noise Brush は、Generated Image 上で指定した領域の **現在の局所解を reject する** ための momentary brush である。

これは通常の消しゴムではない。また、Guide Canvas / Human Draw Layer をその領域へ直接適用するブラシでもない。

Noise Brush は、ユーザーが押下・ドラッグしている間だけ active になる。ブラシを離した後、局所 rejection boost は停止し、active mask は clear される。

Noise Brush 操作中は `noiseBrushActive = true` になり、現在の stroke は `activeNoiseMask` として `DiffusionIntervention` に含まれる。

`activeNoiseMask` の意味は以下である。

```text
この領域に現在出ている解は不採用である。
したがって、ブラシ操作中だけこの領域の不確定性を強く上げ、
現在の局所解から離れた別解を探索させる。
```

実 backend では、`activeNoiseMask` を latent 解像度へ変換し、該当領域に局所的な uncertainty injection を行い、1〜3 update だけ進める実装を優先する。

再探索時には Prompt、Guide Composite、周辺 runtime state が条件として作用する。

v0.1 では、Noise Brush は Generated Image にのみ適用する。Guide Canvas には適用しない。

`lastNoiseMask` は debug/history metadata として保持してよいが、active intervention ではない。Snapshot へ保存してもよいが、Restore 時に自動で再適用してはならない。

Persistent / pinned rejection mask は v0.1 の範囲外である。

### 2.10 Snapshot

Snapshot は、生成途中の状態を保存する単位である。

Snapshot は単なる履歴ではなく、復元と Finish の起点である。

v0.1 では image Snapshot は必須である。

runtime が対応する場合、Snapshot は runtime state も保存してよい。

```text
image Snapshot = required
runtime-state Snapshot = optional
guide data = required when present
lastNoiseMask metadata = optional, not active on restore
```

runtime-state Snapshot がない場合、Restore は image Snapshot による擬似再開でよい。

### 2.11 Backend、Model、Runtime

v0.1 では `selectedBackend` と `selectedModel` を分ける。

- `selectedBackend`: 実行 runtime/backend を表す。値は `mock`、`tinysd`、または fork / adapter backend。
- `selectedModel`: runtime/backend に渡すモデル名。v0.1 では `mock` または TinySD 相当のモデル名でよい。

最初に実装する backend は `mock` である。

次の real backend 候補は `tinysd`、Diffusers backend、ComfyUI adapter、InvokeAI fork/adapter のいずれかでよい。優先順位は `implementation_strategy.md` に従う。

## 3. MVP の範囲

### 3.1 含める機能

v0.1 では以下を実装対象とする。

- Prompt 入力
- Backend / Model 選択
- Guide Canvas
- Imported Image Layer
- Human Draw Layer
- Guide Erase Mask
- Guide Composite export
- Generated Image キャンバス
- Momentary Noise Brush
- Run
- Pause / Resume
- Snapshot 保存
- Snapshot 復元
- Snapshot から Finish
- 基本生成設定
  - CFG / Guidance Scale
  - Global Exploration Noise Strength
  - Local Rejection Strength
  - Guide Influence
  - Seed
  - Update Interval
  - Brush Size
- Mock Stateful Runtime
- Stateful Diffusion Runtime 抽象
- fork / adapter based backend path

### 3.2 含めない機能

v0.1 では以下を実装しない。

- ユーザー向け Step Mode / Step button
- Base Image Init Mode
- 図構造認識
- Mermaid / UML / SVG 変換
- ControlNet を必須 runtime とすること
- T2I-Adapter を必須 runtime とすること
- IP-Adapter を必須 runtime とすること
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
  - Run / Pause / Resume

中央左:
  - Guide Canvas
    - Import Image
    - Imported Image Layer
    - Human Draw Layer
    - Guide Erase
    - Guide Composite preview/export

中央右:
  - Generated Image キャンバス
  - Noise Brush 操作対象

下部:
  - Snapshot Timeline

右側または下部:
  - Generation Settings
  - Guide Settings
  - Noise Brush Settings
```

## 5. UI 要素

### 5.1 Prompt 入力

ユーザーは Prompt を入力できる。

Prompt は現在の runtime session に適用される。

Run loop 中に Prompt が変更された場合、session を破棄せず、次回以降の runtime update に反映される。

### 5.2 Backend / Model 選択

初期 backend は `mock` とする。

実 backend は、TinySD / Diffusers / ComfyUI adapter / InvokeAI fork or adapter のいずれかでよい。

実 backend が利用できない環境でも、Mock Stateful Runtime により UI と状態遷移を確認できなければならない。

### 5.3 Guide Canvas

要件：

- 画像を import できること
- Imported Image Layer を保持できること
- Imported Image Layer の opacity を調整できること
- Human Draw Layer に描けること
- Clear Draw は Human Draw Layer のみ消すこと
- Guide Erase は Imported Image Layer を非破壊に隠すこと
- Guide Composite を export できること
- 生成処理によって Guide Canvas が破壊的に変更されないこと

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

## 6. 生成操作

### 6.1 Run

Run は生成介入ループを開始する。

Run loop は一定間隔で runtime update を試みる。

Run loop は rolling intervention loop である。final timestep 到達だけを目的にせず、global exploration noise により state を低強度で揺らし続ける。

初期値：

```text
update_interval_ms: 300
updates_per_loop: 1-3
global_exploration_noise_strength: 0.04
local_rejection_strength: 0.25
guide_influence: 0.5
cfg: 3.0
```

前回 request が未完了の状態で次の tick が来た場合、実装は skip または待機を選んでよい。ただし古い response が新しい state を上書きしてはならない。

### 6.2 Pause / Resume

Pause は新しい runtime request を止める。

Resume は現在の runtime state から Run loop を再開する。

Pause 中も Guide Canvas の編集、Noise Brush の指定、Snapshot 操作は可能とする。ただし Noise Brush の効果は Run loop 中にのみ runtime update として現れる。

### 6.3 Finish Mode

Finish Mode は、選択した Snapshot から仕上げ生成を行うための明示操作である。

推奨初期値：

```text
finish_updates: 12-30
global_exploration_noise_strength: 0.00
local_rejection_strength: 0.05-0.20
guide_influence: 0.3-0.7
cfg: 3.0-6.0
seed_locked: true
```

Finish from Snapshot を開始したら Run loop は停止する。Finish request 中は新しい Run loop request を出さない。Finish 完了後の loopStatus は paused または idle に戻す。

## 7. Runtime update loop

基本処理：

```text
DiffusionRuntimeState を取得
→ Prompt / Guide Composite / guideInfluence / globalExplorationNoiseStrength を DiffusionIntervention にする
→ noiseBrushActive が true の場合だけ activeNoiseMask と localRejectionStrength を含める
→ runtime.applyIntervention または互換 backend.generate を呼ぶ
→ runtime が guide / global exploration noise / optional local rejection boost を state に適用する
→ runtime が少数 update 進める
→ requestId が最新なら preview を Generated Image に反映する
→ state を保持する
→ loopStatus が running なら繰り返す
```

`activeNoiseMask` は「ここに Guide Canvas を適用する」という意味ではない。

`activeNoiseMask` は「この領域の現在の局所解は reject された」という意味を持つ。runtime はブラシ操作中だけこの情報を使って局所不確定性を上げ、現在の局所解から離れた別解を探索する。その探索に対して Prompt、Guide Composite、周辺 runtime state が条件として作用する。

初期状態で runtime state が存在しない場合は、Prompt と Guide Composite から初期 state を作るか、Mock Stateful Runtime のプレースホルダー state を作る。

## 8. Snapshot 仕様

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

v0.1 では以下を実装する。

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

`runtimeStateRef` は任意である。runtime が state snapshot に対応しない場合は保存しなくてよい。

`lastNoiseMaskDataUrl` は metadata である。Restore 時に active rejection mask として再開してはならない。

## 9. Runtime / Backend 抽象化

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

  guideComposite?: string;
  guideInfluence: number;

  globalExplorationNoiseStrength: number;

  noiseBrushActive: boolean;
  activeNoiseMask?: string;
  localRejectionStrength: number;

  updatesToAdvance: number;
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

## 10. アプリ状態

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

## 11. 非機能要件

- Guide Canvas の描画は体感即時であること。
- 生成更新は best effort でよい。
- Run loop 更新間隔は設定可能であること。
- 通常操作で Prompt、Guide Canvas、Generated Image、Snapshot を失わないこと。
- 通常の Explore update は毎回 blank state から再生成しないこと。
- Noise Brush の local rejection boost は押下・ドラッグ中だけ active であること。

## 12. 開発ルール

v0.1 では、本仕様書に書かれていない機能を実装しない。

新しい機能が必要になった場合、先に `docs/sdd/grill.md` の確認手順を通し、仕様書を更新する。

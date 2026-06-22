# Live Diffusion Canvas 仕様書 v0.1

## 0. 位置づけ

本仕様書は、Live Diffusion Canvas v0.1 の source of truth である。

Live Diffusion Canvas は、Prompt、Human Layer、Generated Image、Noise Brush、Snapshot を使って、拡散モデルの生成途中状態を人間が探索・介入・仕上げできることを示すプロトタイプである。

## 1. プロダクト定義

Live Diffusion Canvas は、一発で完成画像を生成するツールではない。

目的は、生成途中の状態を探索し、良い中間状態を Snapshot として保存し、そこから復元・分岐・仕上げを行うことである。

基本体験は以下である。

```text
Prompt を設定する
→ 生成ループを開始する
→ Human Layer で人間が方向を与える
→ Noise Brush で Generated Image の一部を不確定状態に戻す
→ Generated Image が少しずつ変化する
→ 良い骨格を Snapshot として保存する
→ Snapshot を選び、そこから Finish する
```

本プロトタイプの価値は、画像生成を「Prompt → 完成画像」ではなく、「生成途中状態を人間が操作できる過程」として提示する点にある。

## 2. コアコンセプト

### 2.1 Prompt

Prompt は生成の方向性を定義するテキスト条件である。

Prompt は「何を作るか」「どの特徴に注意を向けるか」を決める。

例：

```text
simple technical diagram, clean black lines, white background
```

### 2.2 Human Layer

Human Layer は、人間が描く独立レイヤーである。

Human Layer は完成画像そのものではなく、生成過程に対する介入信号として扱う。

Human Layer は Generated Image と分離して保持する。

生成処理、Noise Brush、Auto Mode は Human Layer を変更してはならない。

### 2.3 Generated Image

Generated Image は、現在の生成状態を表示する画像である。

Auto Mode では、Generated Image を現在状態として保持し、少しずつ更新する。

毎回ゼロから生成するのではなく、現在の Generated Image を base image として更新する。

### 2.4 Noise Brush

Noise Brush は、Generated Image の一部を次回生成で再解釈させるためのブラシである。

これは通常の消しゴムではない。

Noise Brush は `noiseMask` を作る。`noiseMask` は次回の `GenerationRequest` に含まれる。

v0.1 では、Noise Brush は Generated Image にのみ適用する。Human Layer には適用しない。

### 2.5 Snapshot

Snapshot は、生成途中の状態を保存する単位である。

Snapshot は単なる履歴ではなく、復元と Finish の起点である。

v0.1 では画像 Snapshot による擬似再開でよい。latent state、timestep、scheduler state を保存する真の途中再開は v0.1 の範囲外である。

### 2.6 Backend と Model

v0.1 では `selectedBackend` と `selectedModel` を分ける。

- `selectedBackend`: 実行 backend を表す。値は `mock` または `tinysd`。
- `selectedModel`: backend に渡すモデル名。v0.1 では `mock` または TinySD 相当のモデル名でよい。

最初に実装する backend は `mock` である。TinySD backend は Mock backend が動いた後に接続する。

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
  - Noise Strength
  - Seed
  - Update Interval
  - Brush Size
- Mock backend
- GenerationBackend 抽象

### 3.2 含めない機能

v0.1 では以下を実装しない。

- 図構造認識
- Mermaid / UML / SVG 変換
- ControlNet
- 複雑なレイヤー管理
- Semantic editing
- Latent snapshot の完全保存
- 認証
- クラウドデプロイ
- 共同編集
- 本番品質の最適化
- 高品質モデルへの最適化
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

Prompt は現在の生成ループに適用される。

Auto Mode 中に Prompt が変更された場合、次回以降の生成更新に反映される。

### 5.2 Backend / Model 選択

v0.1 の backend は `mock` と `tinysd` を想定する。

初期値は `mock` とする。

TinySD が利用できない環境でも、Mock backend により UI と状態遷移を確認できなければならない。

### 5.3 Human Layer キャンバス

要件：

- 描画は体感即時で反映されること
- Human Layer は Generated Image と分離されること
- 生成処理によって Human Layer が変更されないこと
- Clear 操作で Human Layer のみ消去できること
- export 可能な形式で保持できること

### 5.4 Generated Image キャンバス

Generated Image は現在の生成画像を表示する。

Noise Brush は Generated Image に対して適用される。

Generated Image は Auto Mode の現在状態として保持される。

### 5.5 Noise Brush

Noise Brush の設定項目：

- Brush Size
- Noise Strength

`Noise Strength` は v0.1 では 1 つの値として扱う。

この値は、Noise Brush で指定された `noiseMask` 領域をどれだけ再解釈させるかを表す。全体画像用の別 noise strength は v0.1 では定義しない。

### 5.6 Snapshot Timeline

Snapshot Timeline は、保存済み中間状態を横並びで表示する。

最低限必要な操作：

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

`parentId` は将来の分岐管理のために保存するが、v0.1 では Branch Tree UI を実装しない。

## 6. 生成モード

### 6.1 Step Mode

ボタンを押すたびに 1 回だけ生成更新を行う。

### 6.2 Auto Mode

一定間隔で生成更新を試みる。

初期値：

```text
update_interval_ms: 300
steps_per_loop: 1-3
noise_strength: 0.25
cfg: 3.0
```

Auto Mode は停止できなければならない。

前回 request が未完了の状態で次の tick が来た場合、実装は skip または待機を選んでよい。ただし古い response が新しい状態を上書きしてはならない。

### 6.3 Pause Mode

生成ループを停止する。

Pause 中も Human Layer の描画、Noise Brush の指定、Snapshot 操作は可能とする。

## 7. Explore Mode

Explore Mode は、良い中間状態・良い骨格を探すためのモードである。

推奨初期値：

```text
steps_per_loop: 1-3
update_interval_ms: 300
noise_strength: 0.20-0.35
cfg: 2.0-4.0
seed_locked: true
```

Explore Mode では、完成品質よりも生成過程の操作性を優先する。

## 8. Finish Mode

Finish Mode は、選択した Snapshot から仕上げ生成を行うための明示操作である。

推奨初期値：

```text
finish_steps: 12-30
noise_strength: 0.05-0.20
cfg: 3.0-6.0
seed_locked: true
```

Finish Mode では、選択した中間状態の骨格を大きく崩さず、細部を整えることを目的とする。

## 9. 生成ループ

基本処理：

```text
現在の Generated Image を取得
→ noiseMask を取得
→ GenerationRequest を作る
→ backend.generate(request) を呼ぶ
→ requestId が最新なら Generated Image を更新する
→ 表示
→ Auto Mode なら繰り返す
```

初期状態で Generated Image が存在しない場合は、Prompt から初期画像を生成するか、Mock backend のプレースホルダー画像を生成する。

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
  noiseStrength: number;

  generatedImageDataUrl: string;
  humanLayerDataUrl?: string;
  noiseMaskDataUrl?: string;

  note?: string;
};
```

v0.1 では以下を実装する。

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

## 11. 生成設定

| 設定 | 意味 | 初期値 |
|---|---|---|
| selectedBackend | 実行 backend | mock |
| selectedModel | backend に渡すモデル名 | mock |
| Prompt | 生成方向 | ユーザー入力 |
| Steps | denoise または生成更新回数 | Explore: 1-3 / Finish: 12-30 |
| CFG | Prompt の強さ | 3.0 |
| Noise Strength | noiseMask 領域の再解釈の強さ | 0.25 |
| Seed | 乱数固定 | ON |
| Update Interval | Auto 更新間隔 | 300ms |
| Brush Size | Noise Brush の大きさ | 32px |

Scheduler は v0.1 では UI に出さず固定でよい。

## 12. Backend 抽象化

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

type GenerationResponse = {
  requestId: number;
  image: string;
  seed: number;
  latencyMs: number;
};

interface GenerationBackend {
  name: "mock" | "tinysd";
  generate(request: GenerationRequest): Promise<GenerationResponse>;
}
```

## 13. アプリ状態

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

## 14. 受け入れ条件

v0.1 の受け入れ条件は `docs/sdd/acceptance.md` を参照する。

## 15. 非機能要件

- Human Layer 描画は体感即時であること。
- 生成更新は best effort でよい。
- Auto 更新間隔は設定可能であること。
- 通常操作で Prompt、Generated Image、Human Layer、Snapshot を失わないこと。

## 16. 開発ルール

v0.1 では、本仕様書に書かれていない機能を実装しない。

新しい機能が必要になった場合、先に `docs/sdd/grill.md` の確認手順を通し、仕様書を更新する。

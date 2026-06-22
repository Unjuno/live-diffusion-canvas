# Live Diffusion Canvas 仕様書 v0.1

## 0. 位置づけ

本仕様書は、Live Diffusion Canvas v0.1 のプロダクト仕様である。

Live Diffusion Canvas は、Prompt、Human Layer、Noise Brush、Snapshot を使って、拡散モデルの生成途中状態を人間が探索・介入・仕上げできることを示すプロトタイプである。

## 1. プロダクト定義

Live Diffusion Canvas は、一発で完成画像を生成するツールではない。

目的は、生成途中の状態を探索し、良い中間状態を Snapshot として保存し、そこから復元・分岐・仕上げを行うことである。

基本体験は以下である。

```text
Prompt を設定する
→ 生成ループを開始する
→ Human Layer で人間が方向を与える
→ Noise Brush で生成画像の一部を不確定状態に戻す
→ 生成画像が少しずつ変化する
→ 良い骨格を Snapshot として保存する
→ Snapshot を選び、そこから Finish する
```

本プロトタイプの価値は、画像生成を「Prompt → 完成画像」ではなく、「生成途中状態を人間が操作できる過程」として提示する点にある。

## 2. コアコンセプト

### 2.1 Prompt

Prompt は、生成の方向性を定義する。

Prompt は「何を作るか」「どのような特徴に注意を向けるか」を決める条件である。

例：

```text
simple technical diagram, clean black lines, white background
```

### 2.2 Human Layer

Human Layer は、人間が描く専用レイヤーである。

Human Layer は完成画像そのものではなく、生成過程に対する介入信号として扱う。

Human Layer は、生成処理によって変更されてはならない。

v0.1 では、Human Layer は独立キャンバスとして保持し、生成入力への渡し方は backend 抽象を通して扱う。

### 2.3 Generated Image

Generated Image は、現在の生成状態を表示するキャンバスである。

Auto Mode では、Generated Image が現在状態として保持され、少しずつ更新される。

毎回ゼロから生成するのではなく、現在画像を基準に更新する。

### 2.4 Noise Brush

Noise Brush は、Generated Image の一部を再び不確定状態へ戻すためのブラシである。

これは消しゴムではない。

消す道具ではなく、選択領域を再生成可能な状態へ戻す道具である。

ユーザーの体験は以下である。

```text
この部分が違う
→ Noise Brush で塗る
→ その部分に noiseMask が作られる
→ Prompt と Human Layer の影響下で再生成される
```

### 2.5 Snapshot

Snapshot は、生成途中の状態を保存する機能である。

Snapshot は単なる履歴ではなく、探索の分岐点である。

Snapshot から以下を行える。

- 復元
- 分岐の起点化
- 仕上げ生成

v0.1 では画像 Snapshot による擬似再開でよい。

## 3. MVP の範囲

### 3.1 含める機能

v0.1 では以下を実装対象とする。

- Prompt 入力
- Model 選択
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
- 生成 backend 抽象

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

## 4. 画面構成

ページ構成は以下を基本とする。

```text
上部:
  - アプリ名
  - Model 選択
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

### 5.2 Model 選択

初期モデルは TinySD または同等の軽量拡散モデルを想定する。

モデル選択 UI は存在するが、v0.1 では 1 モデル固定でも許容する。

### 5.3 Human Layer キャンバス

ユーザーは左側のキャンバスに自由に描画できる。

要件：

- 描画は体感即時で反映されること
- Human Layer は Generated Image と分離されること
- 生成処理によって Human Layer が変更されないこと
- Clear 操作で Human Layer を消去できること

### 5.4 Generated Image キャンバス

右側に現在の生成画像を表示する。

Noise Brush はこの Generated Image に対して適用される。

Generated Image は Auto Mode の現在状態として保持される。

### 5.5 Noise Brush

Noise Brush は Generated Image 上で使用する。

設定項目：

- Brush Size
- Noise Strength
- Softness は v0.1 では任意
- 適用対象は Generated Image のみ

Human Layer に Noise Brush を適用する機能は v0.1 では不要である。

### 5.6 Snapshot Timeline

Snapshot Timeline は、保存済み中間状態を横並びで表示する。

各 Snapshot はサムネイルとして表示される。

最低限必要な操作：

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

Branch 用に `parentId` は保持するが、Tree UI は v0.1 では不要である。

## 6. 生成モード

### 6.1 Step Mode

ボタンを押すたびに 1 回だけ生成更新を行う。

目的：

- デバッグ
- 生成設定の確認
- Noise Brush の挙動確認

### 6.2 Auto Mode

一定間隔で生成ループを実行する。

目的：

- リアルタイムに生成が変化している体験を見せる

初期値：

```text
update_interval_ms: 300
steps_per_loop: 1-3
noise_strength: 0.25
cfg: 3.0
```

Auto Mode は停止できなければならない。

生成中に次の生成リクエストが重なる場合、古い結果を破棄する、または新規リクエストを待機させる。

### 6.3 Pause Mode

生成ループを停止する。

Human Layer の描画や Snapshot 操作は可能とする。

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

Finish Mode は、選択した Snapshot から仕上げ生成を行うためのモードである。

推奨初期値：

```text
finish_steps: 12-30
noise_strength: 0.05-0.20
cfg: 3.0-6.0
seed_locked: true
```

Finish Mode では、選択した中間状態の骨格を大きく崩さず、細部を整えることを目的とする。

Finish Mode は Auto Mode とは独立した明示操作として扱う。

## 9. 生成ループ

生成ループは現在の Generated Image を状態として保持し、それを少しずつ更新する。

毎回ゼロから生成しない。

基本処理は以下とする。

```text
現在の Generated Image を取得
→ Noise Mask を取得
→ Noise Mask 領域を次回生成対象にする
→ 少ステップ denoise 相当の生成更新
→ Generated Image を更新
→ 表示
→ Auto Mode なら繰り返す
```

初期状態で Generated Image が存在しない場合は、Prompt から初期画像を生成するか、Mock backend のプレースホルダー画像を生成する。

## 10. Snapshot 仕様

### 10.1 Snapshot の保存内容

v0.1 の Snapshot は最低限以下を保存する。

```ts
type Snapshot = {
  id: string;
  parentId: string | null;
  createdAt: number;

  prompt: string;
  model: string;

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

### 10.2 Snapshot 操作

v0.1 では以下を実装する。

- Save Snapshot
- Restore Snapshot
- Finish from Snapshot

Branch 用に `parentId` は保持するが、Tree UI は v0.1 では不要である。

### 10.3 Latent Snapshot について

本来、拡散過程の途中から正確に再開するには以下が必要である。

- latent state
- timestep
- scheduler state
- seed
- prompt
- generation parameters

ただし v0.1 では、実装速度を優先し、画像 Snapshot からの擬似再開でよい。

後続バージョンで latent snapshot 対応を検討する。

## 11. 生成設定

v0.1 で UI に出す生成設定は以下に限定する。

| 設定 | 意味 | 初期値 |
|---|---|---|
| Model | 使用モデル | TinySD または mock |
| Prompt | 生成方向 | ユーザー入力 |
| Steps | denoise 回数 | Explore: 1-3 / Finish: 12-30 |
| CFG | Prompt の強さ | 3.0 |
| Noise Strength | どれだけ不確定に戻すか | 0.25 |
| Seed | 乱数固定 | ON |
| Update Interval | Auto 更新間隔 | 300ms |
| Brush Size | Noise Brush の大きさ | 32px |

Scheduler は v0.1 では UI に出さず固定でよい。

## 12. Backend 抽象化

生成 backend は差し替え可能にする。

```ts
type GenerationRequest = {
  prompt: string;
  model: string;
  image?: string;
  noiseMask?: string;
  humanLayer?: string;
  seed: number;
  steps: number;
  cfg: number;
  noiseStrength: number;
};

type GenerationResponse = {
  image: string;
  seed: number;
  latencyMs: number;
};
```

v0.1 では、まず Mock backend を実装し、その後 TinySD backend を接続してよい。

Mock backend は、実際の拡散モデルが未接続でも UI 体験と状態遷移を確認できることを目的とする。

## 13. アプリ状態

アプリは最低限以下の状態を持つ。

```ts
type AppState = {
  prompt: string;
  selectedModel: string;

  mode: "step" | "auto" | "pause";
  generationStatus: "idle" | "generating" | "error";

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
};
```

## 14. 受け入れ条件

v0.1 の受け入れ条件は `docs/sdd/acceptance.md` を参照する。

## 15. 非機能要件

### 15.1 パフォーマンス

v0.1 ではハードリアルタイム性能を要求しない。

目標：

```text
Human Layer 描画: 体感即時
生成更新: best effort
Auto 更新間隔: 設定可能
```

### 15.2 安定性

通常操作で以下を失ってはならない。

- Prompt
- Generated Image
- Human Layer
- Snapshot

### 15.3 実装方針

画像品質よりも、体験の成立を優先する。

優先順位：

```text
1. UI が触れる
2. 生成ループが回る
3. Noise Brush が効く
4. Snapshot が使える
5. Finish が使える
6. モデル品質を改善する
```

## 16. 開発ルール

v0.1 では、本仕様書に書かれていない機能を実装しない。

新しい機能が必要になった場合、先に `docs/sdd/grill.md` の確認手順を通し、仕様書を更新する。

## 17. 一文要約

Live Diffusion Canvas v0.1 は、Prompt、Human Layer、Noise Brush、Snapshot を使って、拡散モデルの生成途中状態を人間が探索・介入・仕上げできることを示すプロトタイプである。

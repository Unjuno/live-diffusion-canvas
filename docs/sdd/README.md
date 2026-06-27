# SDD 実装仕様パッケージ

このディレクトリは、Live Diffusion Canvas の v0.1 仕様を固定するための SDD 領域である。

## 対象

```text
Prompt、Guide Canvas、Noise Brush、Snapshot を使って、生成途中状態を人間が探索・介入・仕上げできるプロトタイプ。
```

## 目的

この SDD パッケージの目的は、実装エージェントが以下を曖昧なく判断できる状態にすることである。

- 何を作るか
- 何を作らないか
- どの技術スタックで作るか
- どの順番で実装するか
- どの条件を満たせば完了か
- 仕様変更時に何を確認するか
- 既存ツールを fork / adapter として使ってよい条件

## ファイル構成

| ファイル | 役割 |
|---|---|
| `spec.md` | v0.1 のプロダクト仕様 |
| `runtime.md` | Stateful Diffusion Runtime の仕様。単純な image-to-image 再生成ではなく、拡散 state への介入として定義する |
| `tech_stack.md` | v0.1 の採用技術スタック |
| `implementation_strategy.md` | ゼロ実装、fork、adapter の採用方針 |
| `architecture.md` | UI、状態、backend、Snapshot の実装構造 |
| `tasks.md` | 実装タスク順序 |
| `acceptance.md` | 受け入れ条件 |
| `glossary.md` | 用語定義 |
| `decisions.md` | 設計判断ログ |
| `grill.md` | 仕様レビュー手順 |
| `agent_handoff.md` | 実装エージェントへの短い作業指示 |
| `research/extensions.md` | v0.2 以降の拡張候補。v0.1 の実装範囲ではない |
| `../adr/` | 主要な設計判断の理由を記録する ADR |

## 読む順番

1. `AGENTS.md`
2. `docs/sdd/README.md`
3. `docs/sdd/spec.md`
4. `docs/sdd/runtime.md`
5. `docs/sdd/tech_stack.md`
6. `docs/sdd/implementation_strategy.md`
7. `docs/sdd/architecture.md`
8. `docs/sdd/tasks.md`
9. `docs/sdd/acceptance.md`
10. `docs/sdd/glossary.md`
11. `docs/sdd/decisions.md`
12. `docs/adr/README.md`
13. `docs/sdd/grill.md`
14. `docs/sdd/agent_handoff.md`
15. `docs/sdd/research/extensions.md`

## 採用スタック

```text
Frontend:
  React + Vite + TypeScript

Canvas:
  Konva + react-konva

State:
  Zustand

Snapshot persistence:
  Dexie + IndexedDB

Backend API:
  Python FastAPI

Transport:
  HTTP-first
  WebSocket optional later

Runtime:
  Mock Stateful Runtime first
  Diffusers + TinySD spike second
  ComfyUI adapter later if useful
```

詳細は `docs/sdd/tech_stack.md` を参照する。

## v0.1 の優先順位

```text
1. React + Vite + TypeScript の app scaffold
2. Zustand AppState
3. Guide Canvas が使える
   - Import Image
   - Human Draw Layer
   - Guide Erase Mask
   - Guide Composite
4. Mock Stateful Runtime が動く
5. Run rolling intervention loop が回る
6. Global Exploration Noise で状態が低強度に揺らぎ続ける
7. Noise Brush が押下・ドラッグ中だけ local rejection として効く
8. Dexie + IndexedDB で Snapshot が保存・復元できる
9. Snapshot から Finish できる
10. FastAPI runtime service scaffold
11. Diffusers + TinySD real backend spike
12. 必要なら ComfyUI adapter を検証する
```

画像品質より、生成途中状態を人間が操作できる体験を優先する。

## 明示的な方針

```text
ユーザー向け Step Mode は作らない。
Run / Pause / Resume を中心にする。
Guide Canvas は旧 Human Layer の上位概念とする。
Noise Brush は Generated Image 側の momentary local rejection input とする。
React + Vite + TypeScript / Konva / Zustand / Dexie / FastAPI を v0.1 採用スタックとする。
既存ツールの fork / adapter 利用は許可するが、製品概念を普通の inpainting UI に戻してはならない。
```

## 拡張研究の扱い

`docs/sdd/research/extensions.md` は将来拡張の調査メモである。

v0.1 では実装しない。実装範囲へ入れる場合は、先に `spec.md`、`runtime.md`、`tech_stack.md`、`architecture.md`、`tasks.md`、`acceptance.md`、`decisions.md` を更新する。

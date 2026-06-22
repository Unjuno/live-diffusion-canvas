# SDD 実装仕様パッケージ

このディレクトリは、Live Diffusion Canvas の v0.1 仕様を固定するための SDD 領域である。

## 対象

```text
Prompt、Human Layer、Noise Brush、Snapshot を使って、生成途中状態を人間が探索・介入・仕上げできるプロトタイプ。
```

## 目的

この SDD パッケージの目的は、実装エージェントが以下を曖昧なく判断できる状態にすることである。

- 何を作るか
- 何を作らないか
- どの順番で実装するか
- どの条件を満たせば完了か
- 仕様変更時に何を確認するか

## ファイル構成

| ファイル | 役割 |
|---|---|
| `spec.md` | v0.1 のプロダクト仕様 |
| `architecture.md` | UI、状態、backend、Snapshot の実装構造 |
| `tasks.md` | 実装タスク順序 |
| `acceptance.md` | 受け入れ条件 |
| `glossary.md` | 用語定義 |
| `decisions.md` | 設計判断ログ |
| `grill.md` | 仕様レビュー手順 |
| `agent_handoff.md` | 実装エージェントへの短い作業指示 |
| `research/extensions.md` | v0.2 以降の拡張候補。v0.1 の実装範囲ではない |

## 読む順番

1. `AGENTS.md`
2. `docs/sdd/README.md`
3. `docs/sdd/spec.md`
4. `docs/sdd/architecture.md`
5. `docs/sdd/tasks.md`
6. `docs/sdd/acceptance.md`
7. `docs/sdd/glossary.md`
8. `docs/sdd/decisions.md`
9. `docs/sdd/grill.md`
10. `docs/sdd/agent_handoff.md`
11. `docs/sdd/research/extensions.md`

## v0.1 の優先順位

```text
1. UI が触れる
2. 生成ループが回る
3. Noise Brush が効く
4. Snapshot が保存・復元できる
5. Snapshot から Finish できる
6. モデル品質を改善する
```

画像品質より、生成途中状態を人間が操作できる体験を優先する。

## 拡張研究の扱い

`docs/sdd/research/extensions.md` は将来拡張の調査メモである。

v0.1 では実装しない。実装範囲へ入れる場合は、先に `spec.md`、`architecture.md`、`tasks.md`、`acceptance.md`、`decisions.md` を更新する。

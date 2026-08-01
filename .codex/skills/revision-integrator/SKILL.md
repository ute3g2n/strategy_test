---
name: revision-integrator
description: Integrate readability and source-fidelity review feedback into a final Japanese middle-school explanation. Use when Codex must revise a chapter draft without reintroducing formulas, changing source meaning, or weakening risk warnings.
---

# Revision Integrator

## 1. 目的

読者理解レビューと原文忠実性レビューを反映し、最終版 Markdown を作る。

## 2. 入力

- 数式なしに整えた本文
- Student Review 結果
- Fidelity Review 結果
- 対象章の重要点一覧
- 指定フォーマット

## 3. 出力

保存可能な最終版 Markdown を返す。

## 4. 処理手順

1. 両レビューの `required_fixes` を確認する。
2. 読みにくい表現を中学生向けに直す。
3. 原文の意味が弱くなった箇所を補う。
4. リスク説明を必要に応じて強める。
5. 数式や記号中心の説明を復活させない。
6. 見出し構成を指定フォーマットにそろえる。
7. 章末に「この章のまとめ」を置く。
8. 最終版だけを Markdown として返す。

## 5. 禁止事項

- レビュー指摘を無視しない。
- 修正時に数式を戻さない。
- 原文の意味を変えない。
- 読みやすさのためにリスク説明を削らない。
- 投資をすすめる表現を追加しない。

## 6. 品質チェックリスト

- 必須修正点が反映されている。
- 数式が残っていない。
- 中学生向けの短い文になっている。
- 原文の重要点が残っている。
- リスク説明が弱くなっていない。
- 指定フォーマットに従っている。

## 7. 失敗時の扱い

レビュー指摘が矛盾する、本文が不足して修正できない場合は、次を返す。

```yaml
error: true
reason: revision_integration_failed
message: レビュー反映版を作成できませんでした。
needs_orchestrator_decision: true
```

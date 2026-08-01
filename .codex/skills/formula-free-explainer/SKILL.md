---
name: formula-free-explainer
description: Remove formulas, symbols, variable-dependent explanations, and overly technical wording from Japanese middle-school explanation drafts. Use when final outputs must contain no formulas while preserving the source meaning and risk warnings.
---

# Formula Free Explainer

## 1. 目的

中学生向け初稿から、数式、記号中心の説明、難しすぎる表現を取り除く。

## 2. 入力

- 中学生向け初稿
- 用語置換ルール
- 禁止表現リスト
- 対象章の重要点一覧

## 3. 出力

数式なしに整えた Markdown を返す。

## 4. 処理手順

1. 本文内の数式、数式ブロック、インライン数式を探す。
2. 変数名だけで説明している箇所を探す。
3. 数式を、意味を保った自然文に置き換える。
4. 英字略語や専門用語には、やさしい説明を付ける。
5. 表だけで説明している箇所には、前後に文章説明を足す。
6. 数式削除によってリスク説明や条件が弱くなっていないか確認する。
7. 最後に数式が残っていないことを確認する。

## 5. 禁止事項

- 数式を残さない。
- `N`、`Unit`、`TR` などの記号だけで説明しない。
- 数式を消すために重要な条件を削らない。
- 原文にない断定を追加しない。
- 投資助言に見える表現を追加しない。

## 6. 品質チェックリスト

- 数式ブロックが残っていない。
- インライン数式が残っていない。
- `N` は「最近の値動きの大きさを表す目安」と説明されている。
- `Unit` は「一度に持つ取引量のまとまり」と説明されている。
- `ストップ` は「損が大きくなりすぎる前にやめる線」と説明されている。
- `ブレイクアウト` は「今までの値動きの範囲を外に抜けること」と説明されている。
- `ドローダウン` は「資金が一時的に大きく減ること」と説明されている。
- 数式を消しても意味が大きく崩れていない。

## 7. 失敗時の扱い

数式が残る、意味が不正確になる、専門語が説明なしで残る場合は、次を返す。

```yaml
error: true
reason: formula_free_cleanup_failed
message: 数式なし本文の品質基準を満たしていません。
remaining_issues:
  - 数式が残っている
  - 用語説明が不足している
```

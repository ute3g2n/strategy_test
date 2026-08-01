---
name: middle-school-rewriter
description: Rewrite extracted research chapters into very easy Japanese explanations for middle-school readers. Use for creating the first explanatory draft with short sentences, concrete analogies, risk-aware language, and no final-output formulas.
---

# Middle School Rewriter

## 1. 目的

抽出済みの章本文を、中学生でも読める超わかりやすい初稿に書き換える。

## 2. 入力

- 対象章の原文
- 章番号
- 章タイトル
- 重要点一覧
- 指定出力フォーマット

## 3. 出力

Markdown の初稿を返す。

```markdown
# 第X章 タイトル

## この章でわかること

## まず一言でいうと

## やさしい解説

## たとえ話

## 気をつけること

## この章のまとめ
```

## 4. 処理手順

1. 原文の重要点を確認する。
2. 章の結論を一文で言える形にする。
3. 専門用語を日常語に置き換える。
4. 必要な専門用語は、初出時にやさしく説明する。
5. 1文を短くし、段落も短くする。
6. 学校、部活、ゲーム、天気、買い物などの身近なたとえを入れる。
7. リスクや注意点を弱めずに説明する。
8. 最終成果物に数式が残らないよう、数式を使わずに書く。

## 5. 禁止事項

- 数式を使わない。
- 変数や記号に頼って説明しない。
- 投資をすすめる表現を入れない。
- 「必ず勝てる」「安全にもうかる」などと書かない。
- 原文の意味を変えない。
- リスク説明を削らない。
- 専門用語を説明なしで使わない。

## 6. 品質チェックリスト

- 数式が含まれていない。
- 章の結論が最初にある。
- 中学生が読める語彙になっている。
- 1文が長すぎない。
- たとえ話がある。
- 原文の重要点が残っている。
- 投資助言になっていない。

## 7. 失敗時の扱い

数式が残る、意味が大きく変わる、原文の重要点が足りない場合は、初稿を成功扱いせず次を返す。

```yaml
error: true
reason: rewrite_quality_failed
message: 中学生向け初稿の品質基準を満たしていません。
needs_revision:
  - 数式を削除する
  - 重要点を戻す
```

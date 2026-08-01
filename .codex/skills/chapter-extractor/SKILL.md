---
name: chapter-extractor
description: Extract an exact chapter slice from a UTF-8 Markdown research file. Use when Codex must isolate one numbered chapter, preserve the original text, list section headings, and identify important points for downstream rewriting.
---

# Chapter Extractor

## 1. 目的

Markdown 原文から、指定章の本文を正確に切り出す。

この skill は原文抽出だけを担当する。後続の中学生向け成果物では数式を残さず、投資助言にしない前提で、重要点とリスク説明を落とさず渡す。

## 2. 入力

- 原文ファイルパス
- 対象章番号
- 次章番号
- 章見出し検出ルール

## 3. 出力

```yaml
chapter_number: 3
chapter_title: ボラティリティとポジションサイジング
source_excerpt: |
  # 3. ボラティリティとポジションサイジング
  ...
section_headings:
  - 3.1 True Range
  - 3.2 Nの計算式
important_points:
  - 値動きの大きさに応じて取引量を調整する
  - 1 Unit は最大損失1%という意味ではない
```

## 4. 処理手順

1. 原文を UTF-8 として読む。
2. `# {章番号}.` または同等の章見出しを探す。
3. 対象章の開始見出しから、次章の開始見出し直前までを抽出する。
4. 抽出本文を要約せず、そのまま保持する。
5. `##`、`###` の節見出しを一覧化する。
6. 書き換え時に落としてはいけない重要点を短く列挙する。
7. 文字化け、空抽出、章ずれがないか確認する。

## 5. 禁止事項

- 対象章以外の本文を混ぜない。
- 原文本文を省略しない。
- 原文を勝手に書き換えない。
- 文字化けした本文を成功扱いしない。
- 中学生向け本文を作らない。
- 投資助言になる要約や、数式削除後に必要な重要点を落とす整理をしない。

## 6. 品質チェックリスト

- 対象章の開始位置が正しい。
- 次章直前で抽出が止まっている。
- 章タイトルが正しい。
- 節見出しが抜けていない。
- 重要点が後続の書き換えに使える。

## 7. 失敗時の扱い

章を見つけられない、抽出結果が空、文字化けしている場合は、次を返す。

```yaml
error: true
reason: chapter_extraction_failed
message: 指定章を正しく抽出できませんでした。
chapter_number: 3
```

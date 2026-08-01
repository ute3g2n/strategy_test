---
name: final-output-auditor
description: Audit generated Japanese middle-school chapter explanation files for completeness, format, no formulas, no investment advice, preserved meaning, and safe storage under research. Use after chapter files are written.
---

# Final Output Auditor

## 1. 目的

指定章範囲の最終成果物がすべてそろい、品質基準を満たしているか確認する。

## 2. 入力

- 対象章一覧
- 期待される出力ファイル一覧
- 保存済みファイル一覧
- 原文ファイルパス
- 品質基準

## 3. 出力

```yaml
pass: true
checked_files:
  - research/中学生向け_第03章_ボラティリティとポジションサイジング.md
missing_files: []
files_requiring_revision: []
summary: すべての対象章ファイルが存在し、数式なし、投資助言なし、指定フォーマットで保存されています。
```

## 4. 処理手順

1. 期待される全ファイルが存在するか確認する。
2. 各ファイルが `research` 配下にあるか確認する。
3. 各ファイルの章番号とファイル名が一致するか確認する。
4. 指定フォーマットの見出しがそろっているか確認する。
5. 数式、数式ブロック、記号中心の説明が残っていないか確認する。
6. 投資助言のような表現がないか確認する。
7. リスク説明が極端に弱くなっていないか確認する。
8. 原文ファイルが変更されていないか確認する。
9. 合格、不合格、修正対象を構造化して返す。

## 5. 禁止事項

- ファイル未作成を合格にしない。
- 数式が残っているファイルを合格にしない。
- 投資助言のような表現を見逃さない。
- 原文ファイルの変更を見逃さない。
- 章番号とファイル名の不一致を見逃さない。

## 6. 品質チェックリスト

- 指定範囲の全ファイルが存在する。
- 各ファイルが `research` 配下にある。
- 各ファイルが指定フォーマットに従っている。
- 数式が残っていない。
- 投資助言ではない。
- 原文の意味が大きく変わっていない。
- リスク説明が弱くなっていない。
- 原文ファイルが変更されていない。

## 7. 失敗時の扱い

不足ファイル、不合格ファイル、原文変更がある場合は、次を返す。

```yaml
pass: false
missing_files:
  - research/中学生向け_第04章_エントリールール.md
files_requiring_revision:
  - path: research/中学生向け_第03章_ボラティリティとポジションサイジング.md
    reason: 数式が残っています。
needs_revision_loop: true
```

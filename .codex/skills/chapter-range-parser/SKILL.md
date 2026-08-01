---
name: chapter-range-parser
description: Parse Japanese user instructions that request chapter-based middle-school explanations from research Markdown files. Use when Codex must extract the source file path, requested chapter range, chapter list, and output intent before orchestrating chapter agents.
---

# Chapter Range Parser

## 1. 目的

ユーザー指示から、対象ファイル、開始章、終了章、対象章一覧、実行目的を構造化して取り出す。

この skill は本文生成を行わないが、後続成果物が数式なし、投資助言なし、`research` 保存になるように、実行目的と保存先を固定する。

## 2. 入力

- ユーザー指示文
- デフォルト対象ファイル
- 許可する章範囲
- 既知の章見出し一覧

## 3. 出力

YAML 風の構造化結果を返す。

```yaml
source_file: research/タートルズ・トレンドフォロー戦略.md
start_chapter: 3
end_chapter: 5
chapters:
  - 3
  - 4
  - 5
task: middle_school_explanation
output_dir: research
```

## 4. 処理手順

1. 指示文から Markdown ファイルパスを探す。
2. ファイルパスがない場合は、与えられたデフォルト対象ファイルを使う。
3. `3～5`、`3-5`、`3から5`、`第3章から第5章`、`3章` などの章指定を読む。
4. 開始章と終了章から章番号リストを作る。
5. 許可範囲と既知の章見出しに照らして、存在する章だけを有効にする。
6. 保存先を `research` に固定する。
7. 後続エージェントに渡せる構造化データだけを返す。

## 5. 禁止事項

- 指定されていない章を追加しない。
- 存在しない章を有効扱いしない。
- `research` 以外の保存先を許可しない。
- 章範囲が曖昧なまま実行可能として扱わない。
- 投資判断、解説本文作成、レビュー判断を行わない。
- 数式を残す成果物や投資助言の作成を目的として扱わない。

## 6. 品質チェックリスト

- 対象ファイルが明確である。
- 開始章と終了章が整数である。
- 章一覧が開始章から終了章まで連続している。
- 指定章が許可範囲内である。
- 出力が後続処理で機械的に読める。

## 7. 失敗時の扱い

章指定が読めない、ファイルが不明、範囲外の章が指定された場合は、実行せずに次を返す。

```yaml
error: true
reason: chapter_range_not_parseable
message: 対象章を特定できませんでした。
needed_input: 例: research/タートルズ・トレンドフォロー戦略.md の 3～5 章
```

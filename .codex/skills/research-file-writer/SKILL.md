---
name: research-file-writer
description: Save final Japanese chapter explanation Markdown into the project research directory with UTF-8 encoding. Use when Codex must write validated chapter output files without modifying the original source document.
---

# Research File Writer

## 1. 目的

最終版 Markdown を `research` ディレクトリ配下の指定ファイルに保存する。

保存前に、最終成果物が数式なし、投資助言なし、原文ファイル非変更であることを確認する。

## 2. 入力

- 最終版 Markdown
- 出力ファイルパス
- 対象章番号
- 上書き可否

## 3. 出力

```yaml
written: true
path: research/中学生向け_第03章_ボラティリティとポジションサイジング.md
encoding: UTF-8
```

## 4. 処理手順

1. 出力パスが `research` ディレクトリ配下であることを確認する。
2. 出力ファイル名に対象章番号が含まれることを確認する。
3. 原文ファイルではないことを確認する。
4. Markdown 本文が空でないことを確認する。
5. UTF-8 で保存する。
6. 保存後にファイルの存在とサイズを確認する。
7. 保存結果を構造化して返す。

## 5. 禁止事項

- `research` ディレクトリ外に保存しない。
- 原文ファイルを変更しない。
- 空ファイルを成功扱いしない。
- 指定と異なるファイル名で保存しない。
- 保存前の品質レビューを勝手に省略しない。
- 数式が残っている本文や投資助言に見える本文を保存成功扱いしない。

## 6. 品質チェックリスト

- 保存先が `research` 配下である。
- UTF-8 で保存されている。
- Markdown として読める。
- 対象章番号とファイル名が一致している。
- ファイルサイズが極端に小さくない。
- 数式が残っていない。
- 投資助言になっていない。

## 7. 失敗時の扱い

保存先が不正、本文が空、原文ファイルへの上書きになる場合は、保存せず次を返す。

```yaml
error: true
reason: file_write_blocked
message: research 配下の安全な出力ファイルに保存できませんでした。
written: false
```

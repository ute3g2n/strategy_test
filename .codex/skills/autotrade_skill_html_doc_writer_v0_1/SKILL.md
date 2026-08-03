---
name: autotrade_skill_html_doc_writer_v0_1
description: 単体で読める日本語HTML成果物を作成し、doc/index.htmlへの導線を維持する。
---

# autotrade_skill_html_doc_writer_v0_1

## 目的
設計書、仕様書、検証結果を人間が読みやすい単体HTMLとして出力する。

## 入力
- 文書アウトライン
- 設計判断
- レビュー結果
- 関連リンク

## 出力
- HTML成果物
- `doc/index.html` 更新案

## 禁止事項
- 外部CDN依存
- 正式設計書をMarkdownだけで終えること
- リンク孤立

## 品質チェック
- 文書ID、作成日、状態、入力、判断、Unknown、レビュー履歴を含む
- PCレビュー可読性を優先する
- `doc/index.html` から到達可能にする

## Phase依存パラメータ
- `output_root`
- `artifact_index`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


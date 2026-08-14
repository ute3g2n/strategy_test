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
- 新規または大幅変更時の非hashmetadata、schema、link、path、Secret、状態確認の引き渡し情報

## 禁止事項
- 外部CDN依存
- 正式設計書をMarkdownだけで終えること
- リンク孤立
- metadata/schema/link/Secret確認の結果やUnknownを隠して完了扱いにすること

## 品質チェック
- 文書ID、作成日、状態、入力、判断、Unknown、レビュー履歴を含む
- PCレビュー可読性を優先する
- `doc/index.html` から到達可能にする
- 新規HTML・大幅変更HTMLはmetadata、schema、link、path、Secret、状態の非hash判定対象へ渡し、A95で管理hash再導入を静的判定する
- 非hash確認のPASS、または理由付きBLOCKEDを受領するまで文書作業を完了扱いにしない。管理用hashの一致は完了条件にしない。A95はhashを計算しない。

## Phase依存パラメータ
- `output_root`
- `artifact_index`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`

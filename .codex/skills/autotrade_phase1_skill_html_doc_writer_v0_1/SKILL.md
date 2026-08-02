---
name: autotrade_phase1_skill_html_doc_writer_v0_1
description: Phase 1専用。単体で読める日本語HTML設計書を作成する。
---

# autotrade_phase1_skill_html_doc_writer_v0_1

## 目的
人間がレビューしやすいHTML設計書を、共通テンプレートに従って作成する。

## 入力
- 設計アウトライン
- 要件追跡
- 設計判断
- 未確定事項

## 出力
- 単体HTML設計書
- 相互リンク
- レビュー履歴欄

## 禁止事項
- 外部CDNに依存しない。
- 目次、メタ情報、設計判断、未確定事項、後続Phase引き継ぎを省略しない。
- 正式設計書をMarkdownだけで終わらせない。

## 品質チェック
- UTF-8 HTMLである。
- タイトル、作成日、文書状態がある。
- 長い表も読みやすい。

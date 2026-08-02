---
name: autotrade_phase1_skill_revision_integrator_v0_1
description: Phase 1専用。レビュー指摘を反映し、最終HTML設計書と変更履歴を作成する。
---

# autotrade_phase1_skill_revision_integrator_v0_1

## 目的
整合性レビューとレッドチーム監査の指摘を、設計書へ安全に反映する。

## 入力
- レビュー指摘一覧
- 対象HTML設計書
- 要件追跡マトリクス

## 出力
- 修正版HTML
- レビュー反映履歴
- 保留・却下理由
- Phase完了判定材料

## 禁止事項
- 未解決リスクを削除しない。
- 安全要件を弱めない。
- 指摘の採否理由を省略しない。

## 品質チェック
- 採用、部分採用、保留、却下が記録されている。
- 関連IDとリンクが更新されている。

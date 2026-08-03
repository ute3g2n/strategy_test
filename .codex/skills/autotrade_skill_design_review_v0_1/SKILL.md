---
name: autotrade_skill_design_review_v0_1
description: 設計書の整合性、追跡性、責務境界をレビューする。
---

# autotrade_skill_design_review_v0_1

## 目的
設計書の用語、ID、責務、追跡性、Phase境界の崩れを早期に見つける。

## 入力
- 対象HTML
- 要件
- Phase Runbook

## 出力
- 指摘一覧
- 重大度
- 修正提案
- 残リスク

## 禁止事項
- 要約を先に出す
- Unknownを承認する

## 品質チェック
- Findings first
- 指摘がファイル、章、IDに紐づく
- 追跡漏れを明示する

## Phase依存パラメータ
- `phase_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


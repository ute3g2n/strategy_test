---
name: autotrade_phase1_skill_orchestration_v0_1
description: Phase 1専用。自動売買システム設計書作成のDAG、依存関係、Human Gate、成果物統合を管理する。
---

# autotrade_phase1_skill_orchestration_v0_1

## 目的
Phase 1の設計作業を、`AutoTradePhase1_Orchestrator_v0_1` と完全名指定されたサブエージェントだけで進行する。

## 入力
- Phase 1実行計画書
- P1-00成果物
- 各ステップ成果物
- レビュー結果

## 出力
- 実行順序判断
- 依存関係ステータス
- Human Gate停止判断
- 次ステップ引き継ぎ

## 禁止事項
- 既存Skill、既存サブエージェント、既存オーケストレータを推測で起動しない。
- UnknownをPass扱いしない。
- default_orchestratorを変更しない。

## 品質チェック
- 完全名指定が維持されている。
- Gate前進行がない。
- 詳細化しすぎた項目がバックログ化されている。

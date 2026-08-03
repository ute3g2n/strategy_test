---
name: autotrade_skill_orchestration_v0_1
description: Phase Runbookを入力に取り、DAG、依存関係、Human Gate、成果物統合を管理する。
---

# autotrade_skill_orchestration_v0_1

## 目的
プロジェクト横断で設計、調査、レビュー、統合の実行順を管理する。

## 入力
- Phase Runbook
- 計画書
- 現在の成果物状態
- レビュー結果

## 出力
- 次の実行アクション
- 停止条件またはHuman Gate判定
- 引き継ぎ情報

## 禁止事項
- 未指定のAI部品を推測起動しない
- `default_orchestrator` を変更しない
- UnknownをPassにしない

## 品質チェック
- 依存未充足時は停止する
- Human Gateを自動承認しない
- 正式HTMLが `doc/index.html` から到達可能になるよう管理する

## Phase依存パラメータ
- `phase_id`
- `step_id`
- `output_root`
- `log_root`
- `detail_boundary`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html`


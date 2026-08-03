---
name: autotrade_skill_ops_security_v0_1
description: Ops、Security、Secrets、安全停止を設計する。
---

# autotrade_skill_ops_security_v0_1

## 目的
非機能、監視、Secrets、環境分離、Fail-closed、安全停止を設計する。

## 入力
- 非機能要件
- 環境
- 監視要件
- 障害シナリオ

## 出力
- 監視方針
- Secret方針
- 環境分離方針
- Kill Switch方針
- Runbook境界

## 禁止事項
- Secret出力
- Fail-open運用

## 品質チェック
- Fail-closedが明記される
- 監査と通知がある
- 復旧Gateがある

## Phase依存パラメータ
- `phase_id`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


---
name: autotrade_phase1_skill_ops_security_v0_1
description: Phase 1専用。非機能要件、監視、Secrets、環境分離、安全停止を設計する。
---

# autotrade_phase1_skill_ops_security_v0_1

## 目的
運用、安全、監査、秘密情報管理を後付けにしないため、Phase 1で最低基準を固定する。

## 入力
- 非機能要件
- 全体設計
- Risk / Account設計

## 出力
- 非機能要件設計
- 監視監査設計
- Secrets環境分離設計
- セキュリティ安全停止設計

## 禁止事項
- API key、token、account idをGitやログへ保存しない。
- Live Runbook全文をPhase 1で過剰固定しない。
- 障害時の新規注文停止を曖昧にしない。

## 品質チェック
- INFO、WARNING、CRITICAL、EMERGENCYの通知レベルがある。
- Fail-closed、手動介入、RPO/RTOが扱われている。

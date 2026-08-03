---
name: autotrade_skill_red_team_review_v0_1
description: 安全性、運用事故、危険な先送りを批判的に監査する。
---

# autotrade_skill_red_team_review_v0_1

## 目的
Fail-closed、安全停止、監査、手動介入、Secretの弱点を批判的に点検する。

## 入力
- 対象HTML
- 運用制約
- Failure scenario

## 出力
- Red Team指摘
- 事故シナリオ
- Gate追加案

## 禁止事項
- 安全停止漏れの見逃し
- 危険な先送りのPass

## 品質チェック
- Fail-closedを点検する
- 監査証跡を点検する
- 手動介入とSecretを点検する

## Phase依存パラメータ
- `phase_id`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


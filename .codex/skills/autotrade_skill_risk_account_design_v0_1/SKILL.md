---
name: autotrade_skill_risk_account_design_v0_1
description: Portfolio、Risk、Account、OMSの責務境界を設計する。
---

# autotrade_skill_risk_account_design_v0_1

## 目的
注文、約定、口座、ポジション、Risk判定の責務と正本管理を固定する。

## 入力
- 共通モデル
- 注文、約定、口座要件
- リスク制約

## 出力
- 責務分離
- 正本管理
- Risk override
- 復旧条件

## 禁止事項
- Strategyに口座正本を持たせる
- Riskを任意化する

## 品質チェック
- 正本が明記される
- 停止条件がある
- 手動介入後復旧条件がある

## Phase依存パラメータ
- `phase_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


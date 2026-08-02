---
name: autotrade_phase1_skill_risk_account_design_v0_1
description: Phase 1専用。Portfolio、Risk、Account、OMSの責務境界を設計する。
---

# autotrade_phase1_skill_risk_account_design_v0_1

## 目的
戦略判断、資産配分、口座正本、リスク制御、注文管理を分離する。

## 入力
- Risk要件
- Account要件
- Strategy Interface
- 共通ドメインモデル

## 出力
- Portfolio / Risk / Account / OMS責務境界
- ハードリスクガード方針
- Paper前、Live前の未確定事項

## 禁止事項
- Strategyに口座正本を持たせない。
- Risk GuardよりStrategyを優先しない。
- Live採用値を根拠なしに確定しない。

## 品質チェック
- 最大DD、1Nリスク、日次損失、注文数量上限、Kill Switch中の新規注文禁止が扱われている。

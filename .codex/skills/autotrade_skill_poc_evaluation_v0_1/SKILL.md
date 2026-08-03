---
name: autotrade_skill_poc_evaluation_v0_1
description: PoC評価軸、採点、証拠条件を設計する。
---

# autotrade_skill_poc_evaluation_v0_1

## 目的
PoCの採点軸と必須証拠を明確にし、根拠のない最終決定を防ぐ。

## 入力
- 候補
- 評価軸
- 検証シナリオ
- Human Gate

## 出力
- 採点表
- 証拠条件
- 比較方法
- 決定保留条件

## 禁止事項
- PoCなしの最終決定
- 根拠不明の採点

## 品質チェック
- 採点軸と重みがある
- 必須証拠と失格条件がある
- Human Gate条件がある

## Phase依存パラメータ
- `phase_id`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


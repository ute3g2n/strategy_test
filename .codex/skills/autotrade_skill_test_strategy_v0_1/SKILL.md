---
name: autotrade_skill_test_strategy_v0_1
description: テスト戦略、品質Gate、Failure injectionを設計する。
---

# autotrade_skill_test_strategy_v0_1

## 目的
再現性のある品質Gateを定義し、Human Gateと機械Gateを混ぜない。

## 入力
- 全設計書
- リスク
- Golden test
- Gate方針

## 出力
- テスト分類
- 品質Gate
- 完了条件
- 禁止事項

## 禁止事項
- Human Gateと機械Gateの混同
- 性能追求テスト化

## 品質チェック
- 再現性がある
- Look-ahead防止がある
- Secret漏洩検出がある

## Phase依存パラメータ
- `phase_id`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


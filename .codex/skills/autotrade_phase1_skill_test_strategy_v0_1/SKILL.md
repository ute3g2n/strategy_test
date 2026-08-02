---
name: autotrade_phase1_skill_test_strategy_v0_1
description: Phase 1専用。テスト戦略、品質Gate、Golden test、結合テストを設計する。
---

# autotrade_phase1_skill_test_strategy_v0_1

## 目的
後続Phaseの実装を、安全性、再現性、品質Gateで判定できるようにする。

## 入力
- 各設計書
- Golden test要件
- 移行Gate要件

## 出力
- テスト戦略
- 品質Gate
- Golden test観点
- Human Gateと機械Gateの分離

## 禁止事項
- Look-ahead、Survivorship bias、Data snoopingを許さない。
- 候補別パラメータ最適化をテスト成功条件にしない。
- Gateを曖昧にしない。

## 品質チェック
- Unit、Integration、Replay、Reconciliation、Failure injection、Operational rehearsalが含まれる。

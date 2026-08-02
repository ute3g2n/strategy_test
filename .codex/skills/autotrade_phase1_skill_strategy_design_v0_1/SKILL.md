---
name: autotrade_phase1_skill_strategy_design_v0_1
description: Phase 1専用。Strategy Plugin InterfaceとTurtle戦略比較の境界を設計する。
---

# autotrade_phase1_skill_strategy_design_v0_1

## 目的
戦略ロジックを基盤から分離し、原典版と現代版を同一基盤で比較できるようにする。

## 入力
- 共通ドメインモデル
- Strategy要件
- Turtleルール要件

## 出力
- Strategy Plugin Interface
- OrderIntentまたはTargetPosition定義
- Strategy Config項目
- Strategy非責務

## 禁止事項
- StrategyがBroker接続、口座正本、Kill Switch実行を担当しない。
- 候補別パラメータ最適化を前提にしない。
- 投資助言にしない。

## 品質チェック
- Backtest / Paper / Liveで同じStrategyを使える。
- 原典版と現代版の比較軸が追跡可能である。

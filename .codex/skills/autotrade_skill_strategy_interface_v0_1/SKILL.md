---
name: autotrade_skill_strategy_interface_v0_1
description: Strategy Plugin Interfaceを設計する。
---

# autotrade_skill_strategy_interface_v0_1

## 目的
Backtest、Shadow、Paper、Liveで共通利用できるStrategy Plugin Interfaceを定義する。

## 入力
- 共通モデル
- 戦略要件
- 実行モデル

## 出力
- Interface責務
- 入力イベント
- 出力Intent
- 非責務

## 禁止事項
- Broker接続責務を持たせること
- 口座正本を持たせること
- Risk override責務を持たせること

## 品質チェック
- 4モードで共通利用できる
- 非責務が明示される
- 出力契約が最小十分である

## Phase依存パラメータ
- `phase_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


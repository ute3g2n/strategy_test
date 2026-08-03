---
name: autotrade_skill_turtle_strategy_rules_v0_1
description: Turtle戦略固有ルールを隔離して扱う。
---

# autotrade_skill_turtle_strategy_rules_v0_1

## 目的
Turtle戦略の固有ルールを汎用Strategy Interfaceから分離し、比較可能な形で保持する。

## 入力
- Turtleルール
- 比較軸
- Golden fixture

## 出力
- 固定ルール
- 比較候補
- 未確定事項

## 禁止事項
- 売買推奨
- 資産別の過剰最適化

## 品質チェック
- 原典再現性がある
- 比較軸がある
- Look-ahead防止が明記される

## Phase依存パラメータ
- `phase_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


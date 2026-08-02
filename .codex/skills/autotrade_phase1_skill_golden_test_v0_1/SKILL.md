---
name: autotrade_phase1_skill_golden_test_v0_1
description: Phase 1専用。Turtle戦略のGolden test設計を行う。
---

# autotrade_phase1_skill_golden_test_v0_1

## 目的
N、Donchian、Unit、Stop、Pyramidingなどの計算と状態遷移を、固定入力と期待出力で検証できるようにする。

## 入力
- Turtleルール要件
- Strategy Interface
- 共通ドメインモデル

## 出力
- Golden test一覧
- 固定入力
- 期待出力
- 許容誤差
- 禁止事項

## 禁止事項
- Backtest結果を見て期待値を変更しない。
- 候補別最適化をテストに混ぜない。
- Look-aheadを許さない。

## 品質チェック
- N、True Range、Donchian、0.5N追加、2N Stop、4/6/10/12 Unit上限を含む。
- Gap時の保守的約定が扱われている。

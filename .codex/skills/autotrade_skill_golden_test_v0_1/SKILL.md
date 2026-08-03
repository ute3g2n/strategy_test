---
name: autotrade_skill_golden_test_v0_1
description: Golden testの固定入力、期待出力、許容差を設計する。
---

# autotrade_skill_golden_test_v0_1

## 目的
期待値の後出し変更を防ぎ、戦略や変換ロジックの再現性を担保する。

## 入力
- 仕様
- fixture
- 許容差
- 禁止事項

## 出力
- テストケース
- 期待値
- 許容差
- 変更ルール

## 禁止事項
- 期待値の後出し変更
- 性能追求テスト化

## 品質チェック
- 固定入力がある
- 期待出力がある
- 変更時の承認ルールがある

## Phase依存パラメータ
- `phase_id`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


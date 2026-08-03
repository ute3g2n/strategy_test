---
name: autotrade_skill_adapter_boundary_v0_1
description: BrokerやData Vendor依存をAdapter境界に閉じ込める。
---

# autotrade_skill_adapter_boundary_v0_1

## 目的
外部依存をコアドメインから分離し、変換、再試行、安全停止の責務を境界に集約する。

## 入力
- 外部仕様
- 共通モデル
- 実行モード

## 出力
- Adapter責務
- 変換境界
- IDマッピング
- 障害時挙動

## 禁止事項
- 外部仕様のコア漏れ
- 全API詳細の過剰固定

## 品質チェック
- 外部依存の閉じ込めが明確
- 安全停止が明記される
- 正本との関係が明確

## Phase依存パラメータ
- `phase_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


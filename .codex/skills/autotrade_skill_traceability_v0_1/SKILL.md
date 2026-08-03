---
name: autotrade_skill_traceability_v0_1
description: 要件、設計判断、Unknown、成果物の追跡性を維持する。
---

# autotrade_skill_traceability_v0_1

## 目的
`REQ`、`DEC`、`UNK`、`ART` を軸に、設計活動の追跡性を保つ。

## 入力
- 要件
- 設計書
- Phase Runbook

## 出力
- 追跡マトリクス
- ID対応表
- 未対応一覧

## 禁止事項
- ID重複
- Unknownの握りつぶし
- 出典不明の設計判断

## 品質チェック
- 要件から成果物まで辿れる
- 設計判断に根拠がある
- Unknownに決定タイミングがある

## Phase依存パラメータ
- `phase_id`
- `output_root`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


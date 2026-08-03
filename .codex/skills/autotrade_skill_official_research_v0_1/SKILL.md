---
name: autotrade_skill_official_research_v0_1
description: 外部仕様調査時に公式一次情報を優先し、URLと確認日を記録する。
---

# autotrade_skill_official_research_v0_1

## 目的
外部仕様や製品情報を扱う際の根拠品質を保つ。

## 入力
- 調査対象
- 調査観点
- 確認日

## 出力
- 公式URL
- 確認日
- 根拠要約
- 未確認事項

## 禁止事項
- 非公式情報だけで断定しない
- 取得日不明の情報を採用しない

## 品質チェック
- 公式一次情報を優先する
- URLと確認日を残す
- 推測は推測として明示する

## Phase依存パラメータ
- `phase_id`
- `step_id`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


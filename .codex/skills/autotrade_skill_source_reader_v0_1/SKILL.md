---
name: autotrade_skill_source_reader_v0_1
description: 要件、方針、既存成果物を読み、設計入力として整理する。
---

# autotrade_skill_source_reader_v0_1

## 目的
要求、制約、既存成果物、未確定事項を抜け漏れなく読み取り、後続設計の入力へ変換する。

## 入力
- 要件定義書
- Phase計画書
- 既存HTML成果物
- ログ、台帳、レビュー結果

## 出力
- 入力要約
- 論点一覧
- 制約一覧
- 参照元一覧

## 禁止事項
- 根拠なしに補完しない
- 参照元を曖昧にしない

## 品質チェック
- 参照元ファイルを明示する
- 未確定事項を別出しする
- 後続の追跡ID付与に使える粒度で整理する

## Phase依存パラメータ
- `phase_id`
- `step_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


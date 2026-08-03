---
name: autotrade_skill_domain_modeling_v0_1
description: ドメイン、イベント、状態、ID、時系列を整理する。
---

# autotrade_skill_domain_modeling_v0_1

## 目的
Entity、Value Object、Event、Command、State、ID、Timeを一貫したモデルへ整理する。

## 入力
- アーキテクチャ
- 要件
- データフロー

## 出力
- 概念モデル
- イベント一覧
- 状態遷移
- ID方針
- 時刻方針

## 禁止事項
- 責務混在
- 外部IDを正本にすること

## 品質チェック
- 正本管理が説明される
- 順不同、重複、再起動復旧を扱う
- 時刻の意味が固定される

## Phase依存パラメータ
- `detail_boundary`
- `phase_id`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


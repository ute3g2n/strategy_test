---
name: autotrade_skill_architecture_writer_v0_1
description: 全体構成、モジュール責務、依存方向を設計する。
---

# autotrade_skill_architecture_writer_v0_1

## 目的
アーキテクチャ原則、モジュール責務、依存方向を整理し、過剰詳細化を避けつつ土台を固定する。

## 入力
- 要件
- 制約
- 既存設計
- Phase Runbook

## 出力
- 構成方針
- モジュール責務
- 依存方向
- 非目的

## 禁止事項
- 全クラス設計の固定
- 外部依存をコアへ漏らすこと

## 品質チェック
- 責務境界が明確
- 依存方向が一貫
- 後続Phase詳細化項目が分離される

## Phase依存パラメータ
- `detail_boundary`
- `phase_id`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


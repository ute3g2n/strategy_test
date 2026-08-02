---
name: autotrade_phase1_skill_architecture_writer_v0_1
description: Phase 1専用。全体構成、モジュール責務、依存方向を設計する。
---

# autotrade_phase1_skill_architecture_writer_v0_1

## 目的
自動売買システムの全体アーキテクチャを、後続Phaseの土台として凍結する。

## 入力
- 要件追跡マトリクス
- Phase方針
- 既存要件定義の全体構成

## 出力
- システム全体構成設計
- モジュール責務
- データフロー
- 依存方向

## 禁止事項
- Phase 1で全クラス設計を固定しない。
- BrokerやData Vendor依存をコアへ漏らさない。
- 研究用コードと本番運用コードを混同しない。

## 品質チェック
- モジュラーモノリス、イベント駆動、アダプター方式の理由がある。
- 後続Phaseの詳細化対象が明示されている。

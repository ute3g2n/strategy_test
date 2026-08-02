---
name: autotrade_phase1_skill_adapter_boundary_v0_1
description: Phase 1専用。Broker AdapterとMarket Data Adapterの境界を設計する。
---

# autotrade_phase1_skill_adapter_boundary_v0_1

## 目的
外部BrokerとMarket Data Vendorへの依存をアダプターに閉じ込める。

## 入力
- 全体設計
- 共通ドメインモデル
- 外部仕様の確認事項

## 出力
- Broker Adapter境界
- Market Data Adapter境界
- 外部IDと内部IDの対応方針
- 後続Phase詳細化バックログ

## 禁止事項
- IBKRやDatabentoの全API詳細をPhase 1で固定しない。
- 外部IDをコアドメインへ直接漏らさない。
- AdapterにStrategy判断を持たせない。

## 品質チェック
- Broker依存とMarket Data依存が分離されている。
- Fail-closedにつながるエラー境界がある。

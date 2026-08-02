---
name: autotrade_phase1_skill_execution_model_v0_1
description: Phase 1専用。Backtest、Shadow、Paper、Liveの共通実行モデルを設計する。
---

# autotrade_phase1_skill_execution_model_v0_1

## 目的
履歴イベントリプレイとリアルタイムイベント処理を同じドメインモデルで扱えるようにする。

## 入力
- 全体構成
- 共通ドメインモデル
- Backtest / Paper / Live要件

## 出力
- 共通実行モデル
- 環境差分の扱い
- run id、manifest、データバージョン方針

## 禁止事項
- 証券会社内蔵バックテストへ依存しない。
- Backtest専用設計をLive前提へ無理に流用しない。
- 実資金機能をPhase 1で実装しない。

## 品質チェック
- ReplayとRealtimeのイベント意味が揃っている。
- Shadow、Paper、LiveのGateが明確である。

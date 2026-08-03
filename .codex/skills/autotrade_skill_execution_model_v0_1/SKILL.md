---
name: autotrade_skill_execution_model_v0_1
description: Backtest、Shadow、Paper、Liveの共通実行モデルを設計する。
---

# autotrade_skill_execution_model_v0_1

## 目的
各実行モードで同じイベント意味と戦略契約を維持する。

## 入力
- 共通モデル
- 戦略
- Adapter
- Risk

## 出力
- 実行状態
- イベント処理方針
- ReplayとRealtimeの差分
- Gate

## 禁止事項
- Broker固有Backtest依存
- Live専用設計化

## 品質チェック
- 同じ戦略契約で4モードを説明できる
- Replay/Realtime差分が限定される
- Gateと停止条件がある

## Phase依存パラメータ
- `phase_id`
- `detail_boundary`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


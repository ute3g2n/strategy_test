---
name: autotrade_skill_trading_engine_poc_v0_1
description: 取引エンジン候補のPoC評価を設計する。
---

# autotrade_skill_trading_engine_poc_v0_1

## 目的
取引エンジン候補を、Replay、注文、復旧、Adapter、監視の観点で比較評価する。

## 入力
- 候補エンジン
- 公式情報
- 実行モデル

## 出力
- 候補比較
- 検証シナリオ
- 採用判定Gate

## 禁止事項
- Live接続をPoCへ含めること
- 公式情報なしの断定

## 品質チェック
- Replay検証がある
- 注文と復旧の観点がある
- Adapterと監視の観点がある

## Phase依存パラメータ
- `phase_id`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`


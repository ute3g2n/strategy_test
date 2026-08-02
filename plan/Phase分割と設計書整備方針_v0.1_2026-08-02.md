# Phase分割と設計書整備方針

作成日: 2026-08-02  
対象: タートルズ・トレンドフォロー自動売買システム  
状態: たたき台

## 1. 結論

このプロジェクトでは、Phase 1で全設計書を完全に詳細化してから実装するのではなく、次の方針で進める。

> Phase 1で全体アーキテクチャ、ドメイン分割、品質基準、非機能要件、主要インターフェースを凍結し、詳細設計と実装はPhaseごとに分割して進める。

理由は、自動売買システムではBroker、Market Data、Backtest、Paper Trading、Live Trading、監視、リスク管理が強く相互依存するためである。最初から全詳細設計を固定しすぎると、実Broker/APIやデータ制約にぶつかったときに大きな手戻りが発生する。

## 2. 設計書の分け方

設計書は、次の2階層に分ける。

### 2.1 Phase 1で整備する全体設計

Phase 1では、後続Phaseの土台になる設計を整備する。

- システム全体構成図
- ドメイン分割設計
- 境界づけられたコンテキスト
- モジュール責務
- データフロー
- Strategy差し替え方式
- Broker Adapter設計方針
- Market Data Adapter設計方針
- Backtest / Paper / Live の共通実行モデル
- リスク管理・口座管理の責務境界
- 設定・Secrets・環境分離方針
- ログ、監査証跡、メトリクス、アラート方針
- テスト戦略
- セキュリティ・安全停止方針

Phase 1の成果物は、後続Phaseの「憲法」のように扱う。

### 2.2 各Phaseで整備する詳細設計

詳細設計は、実装対象Phaseに入る直前または同Phase内で整備する。

例:

- Backtest Engineを実装するPhaseで、Backtest詳細設計を作る。
- Market Dataを実装するPhaseで、Databento/代替データの詳細設計を作る。
- IBKR接続を実装するPhaseで、Broker Adapter詳細設計を作る。
- Paper Tradingを実装するPhaseで、注文状態遷移、約定同期、障害復旧の詳細設計を作る。
- Live Tradingへ進むPhaseで、Kill Switch、監視、運用手順、手動介入手順を詳細化する。

## 3. 推奨Phase構成

| Phase | 目的 | 主な成果物 | 実装の有無 |
|---|---|---|---|
| Phase 0 | アセット選定 | 最終候補30件、初期検証候補5件 | 研究用仮実装のみ |
| Phase 1 | 全体設計・技術選定 | 要件定義更新、全体設計、ドメイン設計、非機能要件、ロードマップ | 原則なし。必要ならPoCのみ |
| Phase 2 | データ基盤 | Market Data Adapter、データ保存、品質検査 | あり |
| Phase 3 | 戦略・バックテスト基盤 | Strategy Interface、Turtleロジック、Backtest Engine | あり |
| Phase 4 | Broker/Paper Trading基盤 | Broker Adapter、注文管理、口座同期、Paper実行 | あり |
| Phase 5 | Portfolio/Risk/Account管理 | Unit計算、資金配分、ポジション制限、リスク制御 | あり |
| Phase 6 | Forward Test運用 | Paper Trading、監視、レポート、異常検知 | あり |
| Phase 7 | Live移行準備 | Kill Switch、運用Runbook、監査、最小実資金運用計画 | あり |
| Phase 8 | Live運用 | 実運用、継続監視、改善サイクル | あり |

## 4. Phase 1で詳細化しすぎないもの

Phase 1では、次を完全固定しない。

- IBKR APIの全エンドポイント単位の実装詳細
- Databentoデータ取得の全ジョブ仕様
- Backtest Engineの全クラス設計
- 注文状態遷移の全例外パターン
- Live運用の全Runbook
- 画面・ダッシュボードの細部

これらは、該当Phaseに入った時点で、実API・実データ・実制約を確認しながら詳細化する。

## 5. Phase 1で必ず決めるもの

Phase 1で曖昧にしてはいけないものは次である。

- 本番システムと研究用コードの境界
- Strategy Logicを差し替え可能にするInterface
- Backtest / Paper / Live で共通化するドメインモデル
- Broker依存を閉じ込めるAdapter境界
- Market Data依存を閉じ込めるAdapter境界
- 口座管理、リスク管理、注文管理の責務分離
- 監査ログと再現性の要件
- Secrets管理と環境分離
- 安全停止、手動介入、最大損失制限の方針

## 6. 実装順序の基本方針

実装は、リスクの低い順に進める。

1. ローカルデータで再現可能なBacktest基盤。
2. Market Data取得・保存・品質検査。
3. Strategy InterfaceとTurtleロジック。
4. Paper Trading用Broker Adapter。
5. Portfolio/Risk/Account管理。
6. Forward Test監視。
7. Live Trading最小構成。

実資金を使う機能は最後にする。

## 7. この方針で避けたい失敗

- 最初から巨大な設計書を作り、実API制約で破綻する。
- Backtest専用設計がLive Tradingに流用できない。
- Strategyロジックと基盤が密結合になる。
- BrokerやData Vendorの変更に弱くなる。
- Paper Tradingで発見すべき問題をLiveで初めて発見する。
- 安全停止や監査ログが後付けになる。

## 8. 次にやるべきこと

Phase 1へ進む前に、Phase 1の実行計画と成果物一覧を作る。

その中で、次を明確にする。

- Phase 1で作る設計書。
- Phase 1では作らない詳細設計。
- Phase 2以降に分割する設計書。
- Phase 1完了Gate。
- Phase 2へ進むための承認条件。


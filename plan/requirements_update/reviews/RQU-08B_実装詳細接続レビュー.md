# RQU-08B 実装詳細接続レビュー

## 0. 文書情報

| 項目 | 内容 |
|---|---|
| ステップID | RQU-08B |
| 基準日 | 2026-08-10 |
| 対象 | RQU-07候補のLevel 3/4、横断要件、状態図、追跡表 |
| 使用Orchestrator | `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1` |
| 使用Agent | `AutoTrade_A82_ImplementationDetailDesigner_v0_1`, `AutoTrade_A91_ImplementationDetailReviewer_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1` |
| 使用Skill | `autotrade_skill_implementation_detail_design_v0_1`, `autotrade_skill_implementation_detail_review_v0_1`, `autotrade_skill_design_review_v0_1`, `autotrade_skill_traceability_v0_1` |
| 判定 | `PASS_WITH_LINK_ADOPTION` |

## 1. 実装詳細接続の判定

| 観点 | 確認内容 | 判定 |
|---|---|---|
| Market Data | Catalog、Raw、Normalized、Quality、Manifest、provenanceの順序 | PASS |
| Strategy | ClosedBar、Turtle、SignalEvent、TargetPosition、Snapshot、停止 | PASS |
| Backtest | Manifest、Replay、Calendar、Fill、Cost、Roll、Result、restore | PASS |
| Engine境界 | Core公開契約、Adapter、EngineIdentity、SDK漏れ拒否 | PASS |
| Risk/OMS境界 | TargetPositionとOrderIntentを分離し、外部注文を将来化 | PASS |
| 状態 | Data Gate、Experiment、OrderIntentの正常・異常・再開 | PASS |
| テスト | Golden、Replay、M30、Snapshot、Bias、隔離Gateへの接続 | PASS |
| 詳細化の範囲 | 全API・全フィールドを複製せず、正式詳細設計へ委譲 | PASS |
| Critical | 重大な実装接続漏れ | 0 |
| High | 実装着手を誤らせる接続漏れ | 0 |

## 2. 要件→詳細設計→コード→テストの接続

| 要件領域 | 正式詳細設計 | 主コード | 主テスト・証拠 | 状態 |
|---|---|---|---|---|
| Market Data / 時間足 | `doc/phase3/03_Strategy詳細設計/03_Strategy_Turtle実装詳細設計書.html`、`doc/phase3/04_Backtest詳細設計/04_Backtest_Experiment実装詳細設計書.html` | `src/autotrade/market_data/` | `tests/market_data/`、M30 Run | 接続済み |
| Strategy契約 | Strategy/Turtle詳細設計 | `strategy/contracts.py`、`service.py`、`turtle_rules.py` | `tests/strategy/`、RUN-P3-STR-001 | 接続済み |
| Replay | Backtest/Experiment詳細設計 | `backtest/replay_order.py`、`runner.py` | `tests/backtest/`、RUN-P3-INT-001 | 接続済み |
| Manifest/hash | Backtest詳細設計 | `manifest.py`、`experiment_manifest.py` | manifest/replay evidence | 接続済み |
| Snapshot/restore | Backtest詳細設計 | `snapshot.py` | restore tests | 接続済み |
| Calendar/Fill | Backtest詳細設計 | `calendar_port.py`、`fill_model.py`、`cost_model.py`、`roll_model.py` | Calendar/Fill/Cost tests | 接続済み・実値はUnknown |
| Engine境界 | Engine PoC評価、LEAN固定・offline準備 | `engine_adapter.py` | Engine boundary/PoC tests | 候補・最終未決定 |
| Human Gate/Unknown | Phase 3完了判定・統合台帳 | `doc/00_全Phase残課題Blocked統合台帳.html` | H3-4、RQU-H2/H3記録 | ガバナンス |

## 3. 図と表の整合

| 図 | 矢印・データ | 表の対応 | 判定 |
|---|---|---|---|
| Context Diagram | 利用者→Core、Core→Evidence、Core→将来Broker | Level 1入出力表 | PASS |
| Container Diagram | Market Data→Strategy→Backtest→Adapter→Evidence | Container通信契約表 | PASS |
| Backtest sequence | Manifest→Quality→Strategy→Replay→Evidence | Backtestシーケンス説明 | PASS |
| Paper sequence | Evidence→Human Gate→Risk/OMS→Paper | 移行条件・未承認境界 | PASS |
| Component flow | Catalog→Normalize→Quality→Strategy→Replay→Result | Level 3責務表 | PASS |
| Concept class diagram | MarketEvent、Manifest、Gate、Result、Unknown | Level 4対応表 | PASS |
| State diagrams | STOPPED、再検証、Paper境界 | 安全・移行要件 | PASS |

## 4. N/Aの妥当性

要件定義書で次の項目を全記載しない判断は妥当である。理由を候補本文の詳細境界へ記録し、既存正式詳細設計を参照先とする。

| 項目 | N/A理由 | 参照先 |
|---|---|---|
| 全APIの型定義 | 要件定義書で二重管理しない | P3-D04/P3-D05 |
| 全永続化スキーマ | Level 4は概念データに限定 | P3-D05、実装コード |
| 全例外クラス | 要件上の停止条件を示し、固有例外は詳細設計へ委譲 | P3-D04/P3-D05 |
| 全テストケース | テスト目的と証拠を示し、全ケースはテスト設計を正本とする | P3-D06〜D09 |
| 実装コード例 | 要件定義書の読者と責務を越える | 既存実装・詳細設計 |

## 5. 採用指摘

| 指摘ID | 重要度 | 内容 | 採用先 |
|---|---|---|---|
| `RQU-08B-001` | Medium | 候補HTMLへ正式詳細設計、RQU-03、統合台帳の直接リンクを追加する | RQU-09A |
| `RQU-08B-002` | Low | HTMLにもQ1〜Q30・OD-01〜08の行単位対応を追加し、Markdownと同じ追跡粒度にする | RQU-09A |
| `RQU-08B-003` | Low | `REQ-DATA-005/006`等の意味はRQU-03へのリンクで固定し、候補内で勝手に再定義しない | RQU-09A |

Critical/Highの指摘はない。RQU-09AでMedium/Lowを反映した後、RQU-09Bで再確認する。

## 6. RQU-08B完了判定

- [x] 要件から既存詳細設計、モジュール入出力、状態、異常系、テストへ接続した。
- [x] 要件定義書として不要な実装詳細をN/A理由付きで委譲した。
- [x] 図の矢印とデータ受渡し表の矛盾がない。
- [x] Critical 0 / High 0を確認した。
- [x] RQU-09Aへ採用するリンク・追跡粒度の改善を記録した。

**RQU-08B判定:** `PASS_FOR_RQU-08C`

# RQU-06R Level 3・4 詳細設計接続レビュー

## 0. 文書情報

| 項目 | 内容 |
|---|---|
| ステップID | RQU-06R |
| 基準日 | 2026-08-10 |
| 状態 | `COMPLETED / ACCEPTABLE_FOR_RQU-07` |
| 対象 | `drafts/RQU-06_C4_Level3-4_横断章.md` |
| 使用Orchestrator | `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1` |
| 使用Agent | `AutoTrade_A82_ImplementationDetailDesigner_v0_1`, `AutoTrade_A91_ImplementationDetailReviewer_v0_1` |
| 使用Skill | `autotrade_skill_implementation_detail_design_v0_1`, `autotrade_skill_implementation_detail_review_v0_1`, `autotrade_skill_traceability_v0_1` |

このレビューは、要件定義書を実装詳細設計書へ変えてしまわないことを確認しながら、Level 3・4の記載が既存の正式設計、コード、テストへたどれるかを確認したものである。

## 1. 判定サマリー

| 観点 | 判定 | 根拠 |
|---|---|---|
| モジュール責務 | PASS | Market Data、Strategy、Backtest、Adapter、停止境界を分離 |
| 主要入力・出力 | PASS | ClosedBar、Manifest、TargetPosition、Result、StopReasonを記載 |
| 正常・異常状態 | PASS | Data Gate、Experiment、OrderIntentの状態遷移を記載 |
| 実装名との接続 | PASS | 概念名と主な実装名の対応表を記載 |
| 詳細設計との境界 | PASS | 全フィールド・全メソッドを複製せず、正式HTMLへ接続 |
| テスト接続 | PASS | Golden、Replay、Manifest、Snapshot、M30、停止の証拠へ接続 |
| C4要件との整合 | PASS | Level 3は担当、Level 4は概念・状態に限定 |
| Mermaid構文・SVG生成 | PASS | RQU-05は4/4、RQU-06は10/10のparse/render |
| Critical | 0 | 採用すべきCriticalなし |
| High | 0 | 採用すべきHighなし |

**最終判定:** `PASS_FOR_RQU-07`

## 2. 入出力・責務の追跡

| 要件上の担当 | 主入力 | 主出力 | 異常時 | 既存実装・設計 | 主テスト・証拠 |
|---|---|---|---|---|---|
| Market Data | Raw/DBN、Catalog、source、版 | Normalized MarketEvent、Quality、provenance | 欠損、順序異常、hash不一致で停止 | `src/autotrade/market_data/manifest.py`、`quality.py`、`catalog_resolver.py` | `tests/market_data/`、P3-D04/P3-D05 |
| Strategy | ClosedBar、StrategyConfig、StrategyState | SignalEvent、TargetPosition、状態更新 | future、未確定、時間逆行、M30来歴不足で停止 | `src/autotrade/strategy/contracts.py`、`service.py`、`turtle_rules.py` | `tests/strategy/`、RUN-P3-STR-001、Golden |
| Backtest / Experiment | ExperimentPlan、Manifest、ReplayInput、Calendar | Result、Snapshot、StopReason、Evidence | Manifest、Calendar、Replay、Fill違反で停止 | `src/autotrade/backtest/runner.py`、`contracts.py` | `tests/backtest/`、RUN-P3-INT-001 |
| Engine Adapter | Core型、EngineIdentity、候補Engine結果 | 型付きResult | SDK漏れ、版・digest不一致で停止 | `engine_adapter.py`、P3-D10/P3-D10A | Engine PoC、boundary tests |
| 安全停止 | 不整合、未承認、異常、手動停止 | STOPPED、理由、hash、再開条件 | sticky stopを維持 | `runner.py`、Data Gate、quality gate | P3-AC-06/08、WSL固定4 Gate |

## 3. 概念データと実装名の接続

| 概念 | 接続先 | レビュー結果 |
|---|---|---|
| `MarketEvent` / `ClosedBar` | 正規化データ、`strategy.contracts`、M30 provenance | 要件上の入力として十分。全フィールドはP3-D04/P3-D05へ委譲 |
| `SignalEvent` | `strategy.contracts.SignalEvent`、Turtle判断 | Strategy出力とGoldenへ接続 |
| `TargetPosition` | `strategy.contracts.TargetPosition` | 目標状態であり外部注文ではないことを明記 |
| `OrderIntent` | Risk/OMS境界の将来概念 | 現在のBroker接続と誤認しない注記あり |
| `ExperimentManifest` | `backtest.contracts.ExperimentManifest`、`experiment_manifest.py` | 版・設定・hash・sourceへ接続 |
| `DataGateDecision` | `backtest.contracts.DataGateDecision`、`runner.py` | READY/COMMITTED/STOPPEDの状態へ接続 |
| `BacktestSnapshot` | `backtest.contracts.BacktestSnapshot`、`snapshot.py` | restoreと位置・状態の一致へ接続 |
| `Result` | Backtest result DTO、Evidence | 数値だけでなくStopReasonと証拠を含める境界を確認 |
| `HumanGate` | 統合台帳、P3-D14、RQU-H2/H3 | runtimeデータと混同せず、承認記録として扱う |
| `Unknown` | 統合台帳、`UNK-P3-01/05/07` | 未解消・未PASSとして扱う |

## 4. 状態・例外・再開条件

| 状態・例外 | 要件原稿の表現 | 実装・証拠への接続 | 判定 |
|---|---|---|---|
| Data Gate `STOPPED` | 入力・品質・hash不合格時に停止 | `DataGateDecision`、`runner.py`、Data Gate tests | PASS |
| Replay順序違反 | 重複・時間逆行・未来入力を拒否 | `replay_order.py`、Backtest tests | PASS |
| M30 provenance不足 | 実M1連続30本がない場合に停止 | `service.py`、`runner.py`、M30 fixture/evidence | PASS |
| Snapshot restore不一致 | 新しいRunで再確認し、勝手に再開しない | `snapshot.py`、restore tests | PASS |
| Fill/Calendar不整合 | 契約外の約定・営業日を採用しない | `fill_model.py`、`calendar_port.py` | PASS |
| Human Gate未承認 | 次の段階へ進まず、承認待ちを台帳へ登録 | P3-D14、RQU統合台帳 | PASS |

## 5. AF-D14/16の要件定義書への適用

| 詳細設計標準の項目 | Level 3・4での扱い | 理由 |
|---|---|---|
| ドメイン概要 | 採用 | C4の担当・概念データを理解するために必要 |
| ファイル構成 | 最小採用 | 主要モジュール名と正式詳細設計へのリンクだけを示す |
| Mermaid構造図 | 採用 | 責務、状態、データ関係を中学生向けに示す |
| 型付き全API定義 | N/A（理由付き） | 要件定義書で全APIを複製すると詳細設計との二重管理になるため |
| 全永続化スキーマ | N/A（理由付き） | 概念データだけを示し、保存形式はP3-D05へ委譲するため |
| 全例外クラス | N/A（理由付き） | 要件上の停止条件と再開条件を示し、固有例外は実装詳細へ委譲するため |
| 全テストケース | N/A（理由付き） | テストの目的と証拠リンクを示し、全ケース表はP3-D04〜D09へ委譲するため |
| 実装コード例 | N/A（理由付き） | 要件定義書の読者に不要で、正式詳細設計・コードを正本とするため |

## 6. 指摘一覧と反映

| 指摘ID | 重要度 | 指摘 | 対応 | RQU-06反映箇所 | 再確認 |
|---|---|---|---|---|---|
| `RQU-06R-001` | Low | `OrderIntent`が外部注文と誤解される可能性 | 将来のRisk/OMS承認後だけの候補と明記 | Level 3 Strategy、Level 4状態 | PASS |
| `RQU-06R-002` | Medium | M30の由来条件を概念図だけでなく文章でも固定すべき | 実M1連続30本、M15連結禁止、provenance不足時停止を追記 | Strategy契約、M30節 | PASS |
| `RQU-06R-003` | Low | Human Gateとruntime状態を混同しない注記が必要 | HumanGateをガバナンス記録として対応表へ記載 | Level 4概念表 | PASS |
| `RQU-06R-004` | Medium | 要件定義と詳細設計の境界を明示すべき | AF-D14/16のN/A理由と既存詳細HTMLへの委譲を記載 | AF-D14/16節 | PASS |
| `RQU-06R-005` | Low | Unknownを結果の合格状態と読まない注意が必要 | `APPROVED_DEFERRED_UNKNOWN`、未PASSを明記 | Unknown節、Q/OD表 | PASS |

採用指摘はすべてRQU-06原稿に反映済みである。Critical/Highの採用指摘は0件であり、追加の実装詳細設計書は作成しない。

## 7. RQU-06R完了判定

- [x] モジュール責務、主要入力出力、正常・異常状態を追跡できる。
- [x] 概念名と実装名を対応付けた。
- [x] 詳細が必要な箇所は既存正式詳細設計へ委譲した。
- [x] AF-D14/16の不要項目へN/A理由を付けた。
- [x] 指摘をRQU-06へ反映し、Critical 0 / High 0を確認した。

**RQU-06R判定:** `PASS_FOR_RQU-07`

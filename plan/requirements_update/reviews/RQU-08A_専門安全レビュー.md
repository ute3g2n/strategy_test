# RQU-08A 専門領域・安全境界レビュー

## 0. 文書情報

| 項目 | 内容 |
|---|---|
| ステップID | RQU-08A |
| 基準日 | 2026-08-10 |
| 対象 | RQU-07 Markdown/HTML候補 |
| 使用Orchestrator | `AutoTradeProject_Orchestrator_v0_1` |
| 使用Agent | `AutoTrade_A10_RequirementsCurator_v0_1`, `AutoTrade_A20_ArchitectureDomainArchitect_v0_1`, `AutoTrade_A30_StrategyQaArchitect_v0_1`, `AutoTrade_A40_ExecutionEnginePocArchitect_v0_1`, `AutoTrade_A50_AdapterArchitect_v0_1`, `AutoTrade_A60_RiskAccountArchitect_v0_1`, `AutoTrade_A70_OpsSecurityArchitect_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1` |
| 使用Skill | `autotrade_skill_design_review_v0_1`, `autotrade_skill_red_team_review_v0_1`, `autotrade_skill_traceability_v0_1` |
| 判定 | `PASS_WITH_MEDIUM_LOW_ADOPTIONS` |

## 1. 専門領域別判定

| レビュー担当 | 確認内容 | 判定 | Critical | High |
|---|---|---|---:|---:|
| A10 RequirementsCurator | 現行事実、承認、Unknown、履歴との一致 | PASS | 0 | 0 |
| A20 ArchitectureDomainArchitect | C4階層、責務、依存方向 | PASS | 0 | 0 |
| A30 StrategyQaArchitect | Turtle、ClosedBar、Golden、Bias、品質Gate | PASS | 0 | 0 |
| A40 ExecutionEnginePocArchitect | Backtest、LEAN PoC、Engine最終決定境界 | PASS | 0 | 0 |
| A50 AdapterArchitect | Market Data / Engine / Broker Adapter境界 | PASS | 0 | 0 |
| A60 RiskAccountArchitect | Portfolio、Risk、Account、OMS、OrderIntent | PASS | 0 | 0 |
| A70 OpsSecurityArchitect | Secret、Cloud、監視、Fail-Closed、手動停止 | PASS | 0 | 0 |
| A90 DesignReviewer / Red Team | 過剰一般化、利益保証、先取り、Human Gate | PASS | 0 | 0 |

**合格基準:** Critical 0、High 0を満たした。

## 2. Findings first

| 指摘ID | 重要度 | 指摘 | 採否 | RQU-09Aでの対応 |
|---|---|---|---|---|
| `RQU-08A-001` | Medium | 候補HTMLのQ/OD表はグループ表示であり、MarkdownのQ1〜Q30・OD-01〜08の行単位追跡より短い | 採用 | HTMLへQ1〜Q30とOD-01〜08の行単位表を追加し、旧ID→現行REQ→状態を揃える |
| `RQU-08A-002` | Low | 候補本文には正式詳細設計書のファイル名はあるが、HTML上の相対リンクが十分でない | 採用 | P3-D04/P3-D05/P3-D14、RQU-03、統合台帳へのリンクを候補へ追加 |
| `RQU-08A-003` | Low | 将来Paperの状態図は、図だけを読むと現行機能と誤読される余地がある | 採用 | 「将来・未承認」の凡例、図キャプション、赤い停止境界を再確認し、Paper状態を将来と明記 |
| `RQU-08A-004` | Low | `REQ-DATA-005/006`等の細分類は設計文書間で意味を取り違えやすい | 採用 | 要求ID凡例とRQU-03へのリンクを残し、名称を勝手に再定義しない |

## 3. 事実忠実性チェック

- Phase 3の現在状態を `COMPLETE_WITH_APPROVED_UNKNOWN` とし、`UNK-P3-01/05/07`を未解消・未PASSとして保持している。[REQ-GATE-003]
- H3-4の許可範囲を、Phase 4の計画・境界設計・隔離検証準備に限定している。[REQ-GATE-001][REQ-GATE-003]
- LEANはローカルPoC候補であり、最終Engine採用・Paper接続・Live利用と断定していない。[REQ-EXE-001][REQ-EXE-003]
- P3-ACの固定範囲PASSを利益性、長期頑健性、本番安全性へ一般化していない。[REQ-QA-001][REQ-RISK-001]

## 4. 安全境界チェック

| 危険な誤解 | 候補の対策 | 判定 |
|---|---|---|
| TargetPositionがそのまま注文になる | Risk/OMS/Human Gate後だけOrderIntent候補と明記 | PASS |
| Unknownを承認済みPASSと読む | `APPROVED_DEFERRED_UNKNOWN`と未PASSを併記 | PASS |
| 固定BacktestをLive許可と読む | Broker/Paper/Liveを赤・破線・未承認で表示 | PASS |
| 不明な入力でも処理が進む | Data Gate、STOPPED、hash、再開条件を記載 | PASS |
| Secretが証拠へ漏れる | Secret/Cloudを将来境界、最小権限・非出力として記載 | PASS |
| LEANを最終採用済みと読む | PoC候補、Paper証拠後に別判断と記載 | PASS |
| わかりやすさのため安全警告を削る | 数値、ID、状態、停止条件を保持 | PASS |

## 5. RQU-08A完了判定

- [x] A10〜A70の責務、事実、境界、Unknownを確認した。
- [x] A90/Red Teamで利益保証、過剰一般化、fail-open、Secret/Live先取り、Human Gate漏れを確認した。
- [x] Critical 0 / High 0を確認した。
- [x] Medium 1件、Low 3件をRQU-09Aの採否・反映対象として登録した。

**RQU-08A判定:** `PASS_FOR_RQU-08B`

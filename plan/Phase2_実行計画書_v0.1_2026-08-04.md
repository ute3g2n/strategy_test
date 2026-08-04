# Phase 2 実行計画書

作成日: 2026-08-04  
対象: タートルズ・トレンドフォロー自動売買システム  
対象Phase: Phase 2 Market Data基盤  
状態: v0.2 / 実装詳細設計基盤・P2-03R追補反映済み

参照:

- `doc/requirements/01_自動トレードシステム要件定義書.html`
- `plan/Phase1_実行計画書_v0.1_2026-08-02.md`
- `plan/AI実行基盤整理計画書_v0.1_2026-08-04.md`
- `plan/Phase分割と設計書整備方針_v0.1_2026-08-02.md`
- `doc/phase1/12_統合レビュー/12_Phase1完了判定とPhase2移行承認書.html`
- `doc/phase1/11_ロードマップ/11_詳細設計バックログ.html`
- `doc/phase1/11_ロードマップ/11_Phase2以降ロードマップ.html`
- `doc/phase1/06_アダプター境界/06_Adapter境界設計書.html`
- `doc/phase1/07_実行モデル/07_共通実行モデル設計書.html`
- `doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html`
- `research/asset_selection/13_最終選定/13_Phase0最終レポート_v0.1_2026-08-02.md`
- `research/asset_selection/13_最終選定/13_初期検証候補5件_v0.1_2026-08-02.csv`
- `research/asset_selection/10_頑健性バックテスト/10_Databento取得補助レポート_v0.1_2026-08-02.md`
- `.codex/skills/autotrade_skill_*_v0_1/SKILL.md`
- `.codex/agents/AutoTrade_A*.json`
- `.codex/orchestrators/AutoTradeProject_Orchestrator_v0_1.json`
- `.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json`
- `.codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json`
- `.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json`
- `doc/ai_foundation/14_実装詳細設計書構成標準.html`
- `doc/ai_foundation/15_実装詳細設計AI基盤仕様.html`
- `settings/ai_component_rules.md`

> 本計画書は、Market Data基盤の詳細設計、最小実装、検証、レビュー、レビュー反映を複数ステップで進めるための実行計画である。投資助言、売買推奨、特定商品の推奨を目的としない。

---

## 1. AI部品存在確認

PX-PLAN-00で指定されたAI部品はすべて存在するため、不足部品による停止は不要である。

| 種別 | 完全名 | 確認結果 |
|---|---|---|
| Orchestrator | `AutoTradePhasePlanning_Orchestrator_v0_1` | 存在 |
| Orchestrator | `AutoTradeProject_DesignDocSet_Orchestrator_v0_1` | 存在 |
| Orchestrator | `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1` | 存在 |
| Agent | `AutoTrade_A05_PhaseExecutionPlanner_v0_1` | 存在 |
| Agent | `AutoTrade_A10_RequirementsCurator_v0_1` | 存在 |
| Agent | `AutoTrade_A80_DocumentIntegrator_v0_1` | 存在 |
| Agent | `AutoTrade_A81_DesignDocSetWriter_v0_1` | 存在 |
| Agent | `AutoTrade_A82_ImplementationDetailDesigner_v0_1` | 存在 |
| Agent | `AutoTrade_A90_DesignReviewer_v0_1` | 存在 |
| Agent | `AutoTrade_A91_ImplementationDetailReviewer_v0_1` | 存在 |
| Skill | `autotrade_skill_phase_execution_planning_v0_1` | 存在 |
| Skill | `autotrade_skill_source_reader_v0_1` | 存在 |
| Skill | `autotrade_skill_traceability_v0_1` | 存在 |
| Skill | `autotrade_skill_orchestration_v0_1` | 存在 |
| Skill | `autotrade_skill_html_doc_writer_v0_1` | 存在 |
| Skill | `autotrade_skill_design_doc_set_writer_v0_1` | 存在 |
| Skill | `autotrade_skill_implementation_detail_design_v0_1` | 存在 |
| Skill | `autotrade_skill_implementation_detail_review_v0_1` | 存在 |
| Skill | `autotrade_skill_design_review_v0_1` | 存在 |
| Skill | `autotrade_skill_red_team_review_v0_1` | 存在 |
| Skill | `autotrade_skill_revision_integration_v0_1` | 存在 |

Phase 2専用AI部品は作成しない。理由は、Market Data基盤の計画、設計、実装、レビューは既存または今回追加したプロジェクト汎用Orchestrator、Agent、Skillで扱えるためである。複数HTMLの統合には `AutoTradeProject_DesignDocSet_Orchestrator_v0_1` とA81を、実装着手に用いる詳細設計には `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、A82、A91と詳細設計2 Skillを使用する。既存の `AutoTradePhase1_*` と `autotrade_phase1_skill_*` は参照対象として読むだけにし、実行部品としては起動しない。

---

## 2. Phase 2の目的

Phase 2では、Phase 3のStrategy / Backtest基盤が再現可能なMarketEvent入力を使えるように、Market Data基盤を詳細化し、最小実装と検証を行う。

Phase 2で扱う中心領域は次である。

- Market Data Adapter詳細
- Databentoを第一候補とする外部データ取得仕様
- Raw StoreとNormalized Store
- Instrument Master / Instrument Catalog
- Symbol mapping
- 1分足catalog
- Continuous signal seriesとroll map
- Data quality test
- Replay入力の再現性
- data_versionとRun Manifestへの接続

Phase 2は、Broker接続、Paper発注、Risk最終値、Strategy本体、Backtest Engine本体の完成を目的にしない。

---

## 3. 入力条件

Phase 2開始時点で満たす入力条件は次である。

| 区分 | 条件 |
|---|---|
| Phase 1完了 | `doc/phase1/12_統合レビュー/12_Phase1完了判定とPhase2移行承認書.html` でH1-4承認済み。 |
| Phase 0候補 | 初期検証候補は `MCL`, `M6A`, `MZC`, `MZS`, `MZW`。ただし `MZC/MZS/MZW` は条件付き。 |
| Adapter境界 | D10でMarket Data Adapterの責務、非責務、Raw / Normalized / Tradable / Signal / Derived / Experimentレイヤーが固定済み。 |
| 実行モデル | D11でRun Manifest、data_version、Replay Gate、HealthEventが固定済み。 |
| 品質Gate | D18でReplay test、Data Gate、Failure injection、Secret security testが固定済み。 |
| AI基盤 | 汎用AI部品とPhase Planning Orchestratorが存在し、`default_orchestrator` は変更しない。 |

---

## 4. Phase 2で固定する判断

| ID | 固定する判断 | 根拠 |
|---|---|---|
| DEC-P2-01 | Raw Storeは外部取得データと取得メタデータを上書き不可で保持する。 | D10 DEC-P1-ADP-04 |
| DEC-P2-02 | Normalized Storeは共通schema、UTC時刻、内部InstrumentId、quality_flagsを必須にする。 | 要件8、D10、D11 |
| DEC-P2-03 | Databentoは第一候補Data Vendorとして扱うが、外部SDK型やraw_symbolをCoreへ漏らさない。 | 要件8.4、D10 |
| DEC-P2-04 | 1分足をPhase 2の最小再生単位とし、日足は1分足から生成する。 | 要件8.3、REQ-Q20 |
| DEC-P2-05 | Continuous signal seriesはRawの正本ではなく、Catalogとroll ruleに基づくSignal入力として版管理する。 | REQ-Q19 / REQ-OD03 |
| DEC-P2-06 | データ欠損、重複、時刻逆行、異常価格、checksum不一致はData Gate失敗として扱い、該当範囲のSignal生成を停止する。 | D10 Fail-closed、D18 |
| DEC-P2-07 | 研究用P10ハーネスのDatabento取得補助は参照証跡に限定し、本番Market Data Adapterとして流用しない。 | P10 README、D10境界 |

---

## 5. 後続Phaseへ送る詳細化項目

| ID | 後続Phaseへ送る項目 | 送り先 | Phase 2での扱い |
|---|---|---|---|
| P2-DEFER-01 | Strategy実装、Turtleロジック、Golden fixture本体 | Phase 3 | Data fixtureとReplay入力形式だけ用意する。 |
| P2-DEFER-02 | Backtest Engine本体、取引エンジン最終決定 | Phase 3 | data_versionとManifest接続仕様だけ固定する。 |
| P2-DEFER-03 | IBKR Paper接続、Order/Fill/Position再同期 | Phase 4 | Instrument CatalogにBroker確認予定項目を残す。 |
| P2-DEFER-04 | 1NリスクLive採用値、年率ボラ強制制御 | Phase 5 | 証拠金、契約倍率、最小数量のCatalog項目だけ定義する。 |
| P2-DEFER-05 | Shadowの遅延許容、Push通知サービス、クラウドVM詳細 | Phase 6 | Market data freshnessの測定項目だけ定義する。 |
| P2-DEFER-06 | Live運用Runbook、Kill Switch解除後ウォームアップ | Phase 7 | データ異常時fail-closed証跡だけPhase 2で作る。 |

---

## 6. 成果物

### 6.1 正式HTML成果物

正式HTML成果物は `doc/phase2/` 配下に保存し、追加または更新したHTMLは同じステップ内で `doc/index.html` から到達可能にする。

| ID | 成果物 | 出力先 |
|---|---|---|
| P2-D01 | Phase 2スコープ定義 | `doc/phase2/01_要件追跡/01_Phase2スコープ定義.html` |
| P2-D02 | Phase 2要件追跡マトリクス | `doc/phase2/01_要件追跡/01_Phase2要件追跡マトリクス.html` |
| P2-D03 | Phase 2未確定事項台帳 | `doc/phase2/01_要件追跡/01_Phase2未確定事項台帳.html` |
| P2-D04 | Databento公式仕様確認結果 | `doc/phase2/02_データソース調査/02_Databento公式仕様確認結果.html` |
| P2-D05 | Market Data Adapter実装詳細設計書 | `doc/phase2/03_市場データ詳細設計/05_Market_Data_Adapter詳細設計書.html` |
| P2-D06 | Raw / Normalized Store実装詳細設計書 | `doc/phase2/03_市場データ詳細設計/06_Raw_Normalized_Store詳細設計書.html` |
| P2-D07 | Instrument Catalog実装詳細設計書 | `doc/phase2/03_市場データ詳細設計/07_Instrument_Catalog詳細設計書.html` |
| P2-D15 | 実装詳細設計レビュー・反映記録 | `doc/phase2/03_市場データ詳細設計/08_実装詳細設計レビュー反映記録.html` |
| P2-D08 | Roll Rule / Continuous Signal設計書 | `doc/phase2/04_ロール連続足/04_Roll_Rule_Continuous_Signal設計書.html` |
| P2-D09 | Market Data実装方針とファイル構成 | `doc/phase2/05_実装方針/05_Market_Data実装方針.html` |
| P2-D10 | Data Quality / Replay検証結果 | `doc/phase2/06_検証/06_Data_Quality_Replay検証結果.html` |
| P2-D11 | Phase 2統合レビュー結果 | `doc/phase2/07_統合レビュー/07_Phase2統合レビュー結果.html` |
| P2-D12 | Phase 2レッドチーム監査結果 | `doc/phase2/07_統合レビュー/07_Phase2レッドチーム監査結果.html` |
| P2-D13 | Phase 2レビュー反映履歴 | `doc/phase2/08_完了判定/08_Phase2レビュー反映履歴.html` |
| P2-D14 | Phase 2完了判定とPhase 3移行承認書 | `doc/phase2/08_完了判定/08_Phase2完了判定とPhase3移行承認書.html` |

### 6.2 実装成果物

実装成果物の保存先は、P2-05で最終確認する。計画時点の候補は次である。

| 区分 | 候補保存先 | ルール |
|---|---|---|
| Python実装 | `src/autotrade/market_data/` | 本番候補コードとして扱う。研究用P10コードを直接移植しない。 |
| テスト | `tests/market_data/` | 小さなfixtureだけGit管理する。 |
| fixture | `tests/fixtures/market_data/` | Secret、大容量Raw、実Account情報を含めない。 |
| ローカル取得データ | `data/market_data/` または環境変数で指定する外部パス | 大容量データはGit管理対象外。必要なら `.gitignore` 更新をP2-05で行う。 |

### 6.3 plan配下の成果物

計画書、実行プロンプト、ログ、台帳は `plan/` 配下へ保存する。Phase 2では次を標準保存先にする。

| 区分 | 保存先 |
|---|---|
| 本計画書 | `plan/Phase2_実行計画書_v0.1_2026-08-04.md` |
| 実行ログ | `plan/phase2/ログ/` |
| Human Gate記録 | `plan/phase2/HumanGate/` |
| 作業台帳 | `plan/phase2/台帳/` |
| プロンプト控え | `plan/phase2/プロンプト/` |

---

## 7. Unknown台帳

UnknownはPassにしない。各Unknownには担当ステップ、決定タイミング、未決時の停止または縮退方針を持たせる。

| Unknown ID | 内容 | 担当ステップ | 決定タイミング | 未決時の扱い |
|---|---|---|---|---|
| UNK-P2-01 | OD-01: 初期3-5市場のPhase 2対象確定。`MCL/M6A`を本線、`MZC/MZS/MZW`を条件付きにするか。 | P2-01 | H2-0 | 条件付き銘柄はCatalogにPendingとして残し、Replay Gate対象を分離する。 |
| UNK-P2-02 | OD-03: roll ruleとcontinuous signal方式。出来高最大、期近日、期限前固定日、外部continuousのどれを採用候補にするか。 | P2-04 | H2-1 | Signal seriesを本番入力に昇格しない。 |
| UNK-P2-03 | Databento dataset、schema、stype_in/out、continuous symbology採用範囲。 | P2-02 / P2-03 | P2-03完了時 | Raw取得ジョブ実装をdry-runまたはfixture限定にする。 |
| UNK-P2-04 | `MZC/MZS/MZW` の履歴期間、流動性、Proxy/Fallbackの正式扱い。 | P2-02 / P2-04 | H2-1 | 本線Backtest入力から除外し、条件付きデータセットに隔離する。 |
| UNK-P2-05 | データ品質警告日の扱い。Databento degraded品質警告を除外、警告付き採用、再取得対象のどれにするか。 | P2-06 / P2-08 | P2-08完了時 | 該当日をSignal生成対象外にする。 |
| UNK-P2-06 | Phase 2のテスト実行基盤とレポート形式。 | P2-06 | P2-06完了時 | 最小pytest + JSON/Markdown証跡で開始し、HTML検証結果へ集約する。 |
| UNK-P2-07 | Databento API利用コスト、entitlement、API key利用承認。 | P2-02 / H2-2 | 実取得前 | 外部API実取得を行わず、既存P10サンプルとfixtureだけで検証する。 |
| UNK-P2-08 | `data/market_data/` をリポジトリ内ローカルデータ置場にするか、外部パスにするか。 | P2-05 | P2-05完了時 | 大容量データ生成を停止し、小型fixtureだけ保存する。 |
| UNK-P2-09 | Shadow用Live相当データの遅延許容しきい値。 | P2-03 / P2-10 | Phase 6 | Phase 2では測定項目だけ定義し、合否しきい値は未確定のまま送る。 |
| UNK-P2-10 | P2-D05からP2-D07が実装可能な粒度を満たすか。対象コード、型、保存構造、失敗系、テストの不足を許容しない。 | P2-03R | P2-03R完了時 | A91の再レビューでCritical/HighまたはDD-01からDD-12の未充足が残る場合、P2-04とP2-05を開始しない。 |

---

## 8. Human Gate

| Gate | タイミング | 承認内容 | 未承認時 |
|---|---|---|---|
| H2-0 | P2-01完了後 | Phase 2スコープ、対象候補、Unknown台帳、実装保存先候補。 | P2-02以降へ進めない。 |
| H2-1 | P2-03R・P2-04完了後 | OD-03のPhase 2採用候補、Continuous signal seriesの責務、条件付き銘柄の扱い、P2-D05からP2-D07の実装詳細設計v0.2。 | P2-05の本実装へ進めない。 |
| H2-2 | P2-07開始前 | Databento API実取得の可否、費用、entitlement、Secret取り扱い。 | 外部API実取得を行わずfixture検証のみ行う。 |
| H2-3 | P2-09完了後 | 統合レビュー指摘の採否方針。 | P2-10へ進めない。 |
| H2-4 | P2-10完了後 | Phase 2完了、Phase 3 Strategy / Backtest基盤への移行可否。 | Phase 3へ進めない。 |

---

## 9. 実行DAGと並列化方針

| グループ | ステップ | 並列可否 | 依存 |
|---|---|---|---|
| G0 | P2-01 | シーケンシャル | 本計画書、H1-4 |
| G1 | P2-02, P2-03 | 並列可 | H2-0 |
| G2 | P2-03R | シーケンシャル | P2-03、AF-D14、AF-D15。A91再レビューで実装可能性を確認する。 |
| G3 | P2-04 | シーケンシャル | P2-02, P2-03R |
| G4 | P2-05, P2-06 | 条件付き並列可 | H2-1、P2-03R。P2-06はP2-05の初期構成案を参照してよい。 |
| G5 | P2-07 | シーケンシャル | P2-05, H2-2 |
| G6 | P2-08 | シーケンシャル | P2-05, P2-06, P2-07 |
| G7 | P2-09 | シーケンシャル | P2-01からP2-08、P2-03R |
| G8 | P2-10 | シーケンシャル | P2-09, H2-3 |

---

## 10. 後続ステップ実行プロンプト

### P2-01 Phase 2スコープ、要件追跡、Unknown台帳

```text
ステップID: P2-01
ロール: Phase 2 要件・スコープ整理者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_source_reader_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-01
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-REQ-DOCSET
- detail_boundary: Market Data基盤のスコープ、追跡ID、Unknown、対象候補を固定する。実装詳細やDatabento全APIパラメータは固定しすぎない。
- human_gate_policy: H2-0でPhase 2スコープ、対象候補、Unknown台帳を承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- Phase専用部品は作成しない。必要だと判断した場合は、汎用部品では不足する理由、利用期限、凍結条件を報告して停止する。
- default_orchestrator は変更しない。

入力:
- plan/Phase2_実行計画書_v0.1_2026-08-04.md
- doc/requirements/01_自動トレードシステム要件定義書.html
- doc/phase1/12_統合レビュー/12_Phase1完了判定とPhase2移行承認書.html
- doc/phase1/11_ロードマップ/11_詳細設計バックログ.html
- doc/phase1/11_ロードマップ/11_Phase2以降ロードマップ.html
- doc/phase1/06_アダプター境界/06_Adapter境界設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html
- research/asset_selection/13_最終選定/13_Phase0最終レポート_v0.1_2026-08-02.md
- research/asset_selection/13_最終選定/13_初期検証候補5件_v0.1_2026-08-02.csv
- settings/ai_component_rules.md

タスク:
Phase 2 Market Data基盤のスコープ、入力条件、成果物、要件追跡、Unknown台帳をHTMLで作成してください。

作業:
1. Phase 2で固定する判断と後続Phaseへ送る詳細化項目を分ける。
2. REQ-Q02, REQ-Q19, REQ-Q20, REQ-Q23, REQ-Q29, REQ-OD01, REQ-OD03を中心に追跡マトリクスを作る。
3. 初期候補 `MCL`, `M6A`, `MZC`, `MZS`, `MZW` の本線/条件付き扱いを整理する。
4. UnknownをID付きで台帳化し、決定タイミング、担当ステップ、未決時の停止または縮退方針を記録する。
5. 正式HTMLを `doc/phase2/01_要件追跡/` 配下へ保存し、`doc/index.html` から到達できるように更新する。
6. 実行ログを `plan/phase2/ログ/` へ記録する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、Phase 2スコープ逸脱、UnknownのPass扱い、要件追跡漏れ、Human Gate漏れをレビューする。
- AutoTrade_A80_DocumentIntegrator_v0_1 が、HTMLの読みやすさ、リンク、保存先、doc/index.html更新を確認する。
- 指摘を反映して最終HTMLと変更履歴を更新する。

完了条件:
- P2-D01, P2-D02, P2-D03が存在する。
- doc/index.htmlからP2-D01からP2-D03へ到達できる。
- H2-0で人間が承認すべき項目が明確である。
```

### P2-02 Databento公式仕様確認

```text
ステップID: P2-02
ロール: Market Data公式仕様調査者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_adapter_boundary_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_source_reader_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-02
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-DATASOURCE-DOCSET
- detail_boundary: Databentoのdataset、schema、symbology、metadata、rate limit、品質情報をPhase 2設計に必要な範囲で確認する。外部仕様をCoreへ直結させない。
- human_gate_policy: H2-2で外部API実取得、費用、entitlement、Secret取り扱いを承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/01_要件追跡/01_Phase2スコープ定義.html
- doc/phase1/06_アダプター境界/06_Adapter境界設計書.html
- research/asset_selection/10_頑健性バックテスト/10_Databento取得補助レポート_v0.1_2026-08-02.md
- research/asset_selection/10_頑健性バックテスト/研究用ハーネス/README.md
- settings/ai_component_rules.md

タスク:
Databentoの公式一次情報を確認し、Phase 2 Market Data基盤に必要な外部仕様確認結果をHTMLで作成してください。

作業:
1. Databento Historical API、Python client、dataset、schema、DBN、symbology、definition、statistics、qualityまたはstatus相当の公式情報を確認する。
2. `GLBX.MDP3`, `ohlcv-1m`, futures parent symbology、stype_in/out、instrument_id、raw_symbolの扱いを整理する。
3. `MCL`, `M6A`, `MZC`, `MZS`, `MZW` の取得可能性確認に必要な調査項目を定義する。
4. API keyやentitlementなどSecretに関わる値は出力しない。必要な環境変数名だけを記録する。
5. 確認URL、確認日、要約、未確認事項を記録する。
6. 正式HTMLを `doc/phase2/02_データソース調査/02_Databento公式仕様確認結果.html` に保存し、doc/index.htmlを更新する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、非公式情報だけで断定していないか、外部仕様をCoreへ漏らしていないか、Secret出力がないかをレビューする。
- Red Team観点で、費用、entitlement、rate limit、degraded品質警告、再取得差分を危険な先送りにしていないか確認する。
- 指摘を反映してHTMLを更新する。

完了条件:
- P2-D04が存在する。
- 公式URLと確認日が記録されている。
- H2-2の承認対象が明確である。
```

### P2-03 Market Data Adapter / Store / Catalog詳細設計

```text
ステップID: P2-03
ロール: Market Data基盤詳細設計者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_adapter_boundary_v0_1, autotrade_skill_architecture_writer_v0_1, autotrade_skill_domain_modeling_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-03
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-MARKET-DATA-DESIGN-DOCSET
- detail_boundary: Market Data Adapter、Raw/Normalized Store、Instrument Catalogを実装可能な粒度で詳細化する。Strategyロジック、Broker接続、Backtest Engine本体は対象外。
- human_gate_policy: H2-1でroll/continuous方式と合わせてデータ基盤方式を承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/01_要件追跡/01_Phase2スコープ定義.html
- doc/phase2/01_要件追跡/01_Phase2要件追跡マトリクス.html
- doc/phase2/02_データソース調査/02_Databento公式仕様確認結果.html
- doc/phase1/06_アダプター境界/06_Adapter境界設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- doc/phase1/04_共通モデル/04_共通ドメインモデル設計書.html
- doc/phase1/04_共通モデル/04_イベント注文口座ID時系列設計書.html
- doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html

タスク:
Phase 2 Market Data Adapter、Raw/Normalized Store、Instrument Catalogの詳細設計書をHTMLで作成してください。

作業:
1. Market Data AdapterのPort、入力、出力イベント、エラー分類、HealthEventを定義する。
2. Raw Storeの保存単位、metadata、checksum、source、取得時刻、再取得差分、上書き禁止ルールを定義する。
3. Normalized Storeの必須列、時刻方針、InstrumentId、quality_flags、重複排除、欠損検知を定義する。
4. Instrument Catalogの内部ID、vendor symbol mapping、contract metadata、trading calendar、tick size、contract multiplier、margin placeholderを定義する。
5. Run Manifestのdata_versionへ接続する項目を定義する。
6. 正式HTMLをP2-D05, P2-D06, P2-D07として保存し、doc/index.htmlを更新する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、D10/D11/D18との整合性、責務境界、追跡ID、Unknown扱いをレビューする。
- Red Team観点で、Raw改変、symbol mapping誤り、品質警告の握りつぶし、データ異常時fail-openを確認する。
- AutoTrade_A80_DocumentIntegrator_v0_1 が、リンク、保存先、レビュー履歴を確認する。

完了条件:
- P2-D05, P2-D06, P2-D07が存在する。
- Adapter境界とStore/Catalog責務が分離されている。
- Phase 3がReplay入力を参照できるdata_version構造が説明されている。
```

### P2-03R Market Data実装詳細設計の再設計・専門レビュー・改訂・再レビュー

```text
ステップID: P2-03R
ロール: Market Data基盤 実装詳細設計・改訂者
使用オーケストレータ完全名: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_architecture_writer_v0_1, autotrade_skill_domain_modeling_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_source_reader_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_revision_integration_v0_1, autotrade_skill_orchestration_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-03R
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-MARKET-DATA-IMPLEMENTATION-DETAIL-DOCSET
- detail_boundary: Market Data Adapter、Raw/Normalized Store、Instrument Catalogを実装担当者が追加推測なしで着手できる粒度へ改訂する。Strategyロジック、Broker接続、Backtest Engine本体、未承認のDatabento実取得は対象外。
- human_gate_policy: H2-1でP2-D05からP2-D07の実装詳細設計v0.2とroll/continuous方式を承認する。
- implementation_target: Python 3.11。予定配置は `src/autotrade/market_data/`、`tests/market_data/`、`tests/fixtures/market_data/`。未承認の外部ライブラリ、外部API実呼出し、Secret実値は設計・コード例に含めない。
- document_coverage_matrix: DD-01対象/配置、DD-02モジュール依存、DD-03責務、DD-04型付き入出力、DD-05通常/失敗シーケンス、DD-06物理保存、DD-07疑似コード/コード例、DD-08設定/監査/Health、DD-09テスト、DD-10 Run Manifest/data_version、DD-11追跡/Unknown、DD-12レビュー/改訂/再レビュー。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- Phase専用部品は作成しない。汎用部品で不足すると判断した場合は、不足理由、利用期限、凍結条件を報告して停止する。
- default_orchestrator は変更しない。

入力:
- doc/ai_foundation/14_実装詳細設計書構成標準.html
- doc/ai_foundation/15_実装詳細設計AI基盤仕様.html
- doc/phase2/01_要件追跡/01_Phase2スコープ定義.html
- doc/phase2/01_要件追跡/01_Phase2要件追跡マトリクス.html
- doc/phase2/01_要件追跡/01_Phase2未確定事項台帳.html
- doc/phase2/02_データソース調査/02_Databento公式仕様確認結果.html
- doc/phase2/03_市場データ詳細設計/05_Market_Data_Adapter詳細設計書.html
- doc/phase2/03_市場データ詳細設計/06_Raw_Normalized_Store詳細設計書.html
- doc/phase2/03_市場データ詳細設計/07_Instrument_Catalog詳細設計書.html
- doc/phase1/06_アダプター境界/06_Adapter境界設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html
- README.md、src/、tests/、.gitignore（存在する範囲を確認する。存在しない配置は設計上の予定として明記する。）

タスク:
P2-D05、P2-D06、P2-D07を実装詳細設計書v0.2へ改訂し、専門レビュー、横断/Red Teamレビュー、改訂、専門再レビューを完了してください。P2-D15として、DD-01からDD-12の網羅表、指摘、採否、再レビュー結果を保存してください。

作業:
1. 既存P2-D05からP2-D07の不足をDD-01からDD-12で棚卸しし、要件ID、判断ID、Unknown IDとの対応表を作る。
2. P2-D05に、パッケージ木、Adapter Portと実装クラス、DTO/Event/Error/HealthEventの型付き入出力、Vendor変換境界、取得・正規化・失敗/再試行のシーケンス、擬似コードまたはPythonコード例、fixtureとfailure injectionを追加する。
3. P2-D06に、Raw/Normalizedのファイルまたは表の物理配置、キー、制約、索引相当、チェックサム、追記専用/再取得差分、冪等性、重複/欠損/破損時の処理、data_version生成、保存/読出しコード例とテストを追加する。
4. P2-D07に、Catalogのデータ構造、内部ID生成、vendor symbol mapping、contract metadata、calendar/tick/multiplier/margin placeholder、バージョン/移行、検索API、誤マッピング時のfail-closed、コード例とテストを追加する。
5. 未承認の永続化ライブラリや外部SDKの具体呼出しは固定しない。必要な箇所はPort、Python標準ライブラリ、または擬似コードへ縮退し、Unknown ID、決定タイミング、停止条件を記録する。
6. P2-D05からP2-D07を既存パスでv0.2に更新し、P2-D15を `doc/phase2/03_市場データ詳細設計/08_実装詳細設計レビュー反映記録.html` に作成する。`doc/index.html` の説明とリンクを更新する。
7. 実行ログ、DD網羅台帳、レビュー指摘・採否を `plan/phase2/ログ/` と `plan/phase2/台帳/` に記録する。

レビュー:
- AutoTrade_A91_ImplementationDetailReviewer_v0_1 がDD-01からDD-12を根拠付きでレビューし、実装担当者が追加推測なしに着手できるかをCritical/High/Medium/Lowで判定する。
- AutoTrade_A90_DesignReviewer_v0_1 がD10/D11/D18との整合性、責務境界、要件追跡、Unknown、Phaseスコープをレビューし、Red Team観点でRaw改変、symbol mapping誤り、品質警告の握りつぶし、データ異常時fail-open、Secret漏えいを監査する。
- AutoTrade_A80_DocumentIntegrator_v0_1 と AutoTrade_A81_DesignDocSetWriter_v0_1 が指摘を採否付きで反映し、HTML、相互リンク、保存先、doc/index.html、変更履歴を確認する。
- 反映後、AutoTrade_A91_ImplementationDetailReviewer_v0_1 が再レビューする。CriticalまたはHigh、DD未充足、UnknownのPassが残る場合は完了にしない。

完了条件:
- P2-D05、P2-D06、P2-D07がDD-01からDD-12を根拠付きで満たすv0.2として存在する。
- P2-D15が存在し、初回レビュー、A90監査、採否、改訂、A91再レビュー、残Unknownが記録されている。
- module tree、責務、型付き入出力、物理保存、通常/失敗シーケンス、疑似コードまたはコード例、テスト/fixture/failure injection、data_version/Run Manifest接続を確認できる。
- A91再レビューでCritical/Highが0件、UnknownはPass扱いされず、H2-1で承認すべき実装詳細設計事項が明確である。
- doc/index.htmlからP2-D05、P2-D06、P2-D07、P2-D15へ到達できる。
```

### P2-04 Roll Rule / Continuous Signal設計

```text
ステップID: P2-04
ロール: Roll Rule / Continuous Signal設計者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_adapter_boundary_v0_1, autotrade_skill_strategy_interface_v0_1, autotrade_skill_turtle_strategy_rules_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-04
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-ROLL-SIGNAL-DOCSET
- detail_boundary: Roll rule、continuous signal series、Tradable/Signal分離を固定する。売買ロジックの最終パラメータ最適化はPhase 3以降に送る。
- human_gate_policy: H2-1でOD-03の扱いを承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/03_市場データ詳細設計/05_Market_Data_Adapter詳細設計書.html（P2-03R改訂後）
- doc/phase2/03_市場データ詳細設計/06_Raw_Normalized_Store詳細設計書.html（P2-03R改訂後）
- doc/phase2/03_市場データ詳細設計/07_Instrument_Catalog詳細設計書.html（P2-03R改訂後）
- doc/phase2/02_データソース調査/02_Databento公式仕様確認結果.html
- doc/phase1/05_戦略設計/05_Strategy_Plugin_Interface設計書.html
- doc/phase1/05_戦略設計/05_Turtle_Golden_test設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- research/asset_selection/13_最終選定/13_初期検証候補5件_v0.1_2026-08-02.csv

タスク:
Phase 2のRoll Rule / Continuous Signal設計書を作成し、OD-03の決定候補とHuman Gateを明確にしてください。

作業:
1. 期近、出来高最大、期限前固定日、Databento continuous相当、Proxy/Fallbackの比較軸を定義する。
2. Raw、Normalized、Tradable、Signal、Derivedのどのレイヤーで何を保持するかを定義する。
3. ロール損益、価格差、gap、満期持ち越し禁止、物理決済注意をPhase 3へ渡せる形で整理する。
4. `MCL/M6A` と `MZC/MZS/MZW` の条件付き扱いを分離する。
5. Look-ahead、未来の出来高情報参照、候補別最適化を防ぐGateを定義する。
6. 正式HTMLを `doc/phase2/04_ロール連続足/04_Roll_Rule_Continuous_Signal設計書.html` に保存し、doc/index.htmlを更新する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、D08/D09/D11/D18との整合性、OD-03の決定条件、Look-aheadリスクをレビューする。
- Red Team観点で、未来情報混入、流動性不足のPass、条件付き銘柄の本線混入を確認する。
- 指摘を反映してHTMLを更新する。

完了条件:
- P2-D08が存在する。
- OD-03の採用候補、保留条件、Human Gate承認内容が明確である。
- Phase 3がSignal seriesを使う前のReplay Gate条件が定義されている。
```

### P2-05 Market Data最小実装

```text
ステップID: P2-05
ロール: Market Data基盤実装者
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_adapter_boundary_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-05
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- detail_boundary: Market Data最小実装、設定、fixture、ローカル保存、CLIまたは関数境界を作る。Strategy、Backtest Engine、Broker接続は実装しない。
- human_gate_policy: H2-1承認後に実装を開始する。大容量データ保存先や外部API実取得はH2-2承認に従う。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/03_市場データ詳細設計/05_Market_Data_Adapter詳細設計書.html（P2-03R改訂後）
- doc/phase2/03_市場データ詳細設計/06_Raw_Normalized_Store詳細設計書.html（P2-03R改訂後）
- doc/phase2/03_市場データ詳細設計/07_Instrument_Catalog詳細設計書.html（P2-03R改訂後）
- doc/phase2/04_ロール連続足/04_Roll_Rule_Continuous_Signal設計書.html
- doc/phase1/09_非機能要件/09_設定Secrets環境分離設計書.html
- .gitignore
- package.json
- 既存研究用P10ハーネス一式。ただし参照のみ。

タスク:
Phase 2 Market Data基盤の最小実装を作成してください。

作業:
1. 本番候補コードの保存先を確認し、必要なら `src/autotrade/market_data/` と `tests/market_data/` を作成する。
2. InstrumentId、SymbolMapping、RawDataRef、NormalizedBar、QualityFlag、DataVersion、MarketEventに相当するモデルを実装する。
3. Raw StoreとNormalized Storeの小型ローカル実装を作る。大容量データはGit管理しない。
4. Databento実取得はH2-2未承認なら実行しない。実装はAPI keyを環境変数参照に留め、Secret実値を出力しない。
5. P10研究用CSVを直接本番コードに依存させず、fixture変換入力としてだけ扱う。
6. 実装方針HTML `doc/phase2/05_実装方針/05_Market_Data実装方針.html` を作成し、doc/index.htmlを更新する。
7. 変更が必要な場合は `.gitignore` に大容量データ置場の除外を追加する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、設計書との整合性、責務境界、Secret混入、研究用コード依存をレビューする。
- Red Team観点で、Raw上書き、データ異常時fail-open、API keyログ出力、大容量データ誤コミットを確認する。
- 指摘を反映してコードとHTMLを更新する。

完了条件:
- 最小実装とテスト雛形が存在する。
- Secret実値を要求または出力していない。
- P2-D09が存在し、doc/index.htmlから到達できる。
```

### P2-06 Data Quality / Replayテスト設計

```text
ステップID: P2-06
ロール: Data Quality / Replay QA設計者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_skill_test_strategy_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-06
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-QA-DOCSET
- detail_boundary: Data quality、Replay入力、Manifest証跡のテストを設計する。Strategyの利益評価やBacktest採用判定はPhase 3へ送る。
- human_gate_policy: Data Gate失敗時はSignal生成を停止し、H2-3でレビュー採否を承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/03_市場データ詳細設計/*.html
- doc/phase2/04_ロール連続足/04_Roll_Rule_Continuous_Signal設計書.html
- doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- P2-05で作成された実装案またはテスト雛形

タスク:
Phase 2のData Quality / Replayテスト設計とテスト実装方針を作成してください。

作業:
1. 欠損、重複、時刻逆行、異常価格、異常出来高、checksum不一致、degraded品質警告のテストケースを定義する。
2. 同一data_versionで同一MarketEvent系列を再現するReplay testを定義する。
3. Look-ahead防止、未来のroll情報参照禁止、fixture後出し変更禁止をGate化する。
4. pytest等の最小テスト実行基盤とJSON/Markdown/HTMLレポート形式を決める。
5. P2-05実装に対する最小テストを作成または更新する。
6. 検証結果HTMLの雛形を作り、P2-08で実測値を追記できるようにする。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、D18との整合性、テスト漏れ、Human Gateと機械Gateの混同をレビューする。
- Red Team観点で、データ異常を警告だけで通していないか、Signal生成停止条件が弱くないかを確認する。
- 指摘を反映してテストとHTMLを更新する。

完了条件:
- Data Quality / Replayのテスト観点が実装可能な粒度で定義されている。
- UNK-P2-06のテスト基盤暫定方針が決まっている。
- P2-08が検証を開始できる。
```

### P2-07 Databento取得プロトコル実装

```text
ステップID: P2-07
ロール: Databento取得プロトコル実装者
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_skill_adapter_boundary_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-07
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- detail_boundary: Databento取得プロトコル、dry-run、small fixture取得、metadata保存、Secret非出力を実装する。大規模取得や本番運用スケジュールは対象外。
- human_gate_policy: H2-2が未承認の場合、外部API実取得は行わずdry-runと既存fixtureだけで検証する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/02_データソース調査/02_Databento公式仕様確認結果.html
- doc/phase2/03_市場データ詳細設計/*.html
- doc/phase2/05_実装方針/05_Market_Data実装方針.html
- doc/phase1/09_非機能要件/09_設定Secrets環境分離設計書.html
- H2-2承認記録

タスク:
Databento取得プロトコルの最小実装またはdry-run実装を作成してください。

作業:
1. H2-2承認有無を確認する。
2. 未承認なら外部APIを呼ばず、CLI引数検証、環境変数名検証、リクエスト計画JSON生成、fixture読込だけを実装する。
3. 承認済みなら、Secret実値を出力せず、最小期間・最小シンボルで取得する。取得費用やentitlementに影響する処理は事前ログに明記する。
4. definition、statistics、ohlcv-1m相当のmetadata保存方針を実装またはdry-run出力する。
5. rate limit、認証失敗、権限不足、degraded品質警告をHealthEventまたはData Quality入力へ渡す。
6. 実行ログを `plan/phase2/ログ/` へ保存する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、H2-2未承認の実API呼び出しがないか、Secret混入がないか、公式仕様との対応をレビューする。
- Red Team観点で、費用事故、過剰取得、Secret漏洩、品質警告の握りつぶしを確認する。
- 指摘を反映して実装とログを更新する。

完了条件:
- H2-2状態に応じた安全な取得プロトコルが存在する。
- Secret実値がGit、ログ、HTMLに含まれていない。
- P2-08がData Quality / Replay検証を開始できる。
```

### P2-08 Data Quality / Replay検証

```text
ステップID: P2-08
ロール: Market Data検証者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_skill_execution_model_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-08
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-VALIDATION-DOCSET
- detail_boundary: Phase 2実装のData Quality / Replay検証を行い、Phase 3へ渡せるMarketEvent入力と残Unknownを判定する。Strategy収益評価は行わない。
- human_gate_policy: 検証失敗項目はH2-3のレビュー採否対象にする。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- P2-05実装成果物
- P2-06テスト設計
- P2-07取得プロトコルまたはdry-run成果物
- doc/phase2/03_市場データ詳細設計/*.html
- doc/phase2/04_ロール連続足/04_Roll_Rule_Continuous_Signal設計書.html
- 小型fixtureまたはH2-2承認済み取得データ

タスク:
Data Quality / Replay検証を実行し、検証結果HTMLを作成してください。

作業:
1. テストを実行し、実行コマンド、環境、入力データ、data_version、code_revisionを記録する。
2. 欠損、重複、時刻逆行、異常価格、checksum、degraded品質警告の検出結果を記録する。
3. 同一data_versionで同一MarketEvent系列を再現できるか検証する。
4. 条件付き銘柄を本線データセットへ混入させていないことを確認する。
5. 失敗項目はPassにせず、Unknownまたは修正指示へ送る。
6. `doc/phase2/06_検証/06_Data_Quality_Replay検証結果.html` を作成し、doc/index.htmlを更新する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、検証結果の根拠、失敗項目の扱い、Replay Gate、Data Gateをレビューする。
- Red Team観点で、データ異常の握りつぶし、条件付き銘柄の混入、再現不能な入力の昇格を確認する。
- 指摘を反映してHTMLと修正指示を更新する。

完了条件:
- P2-D10が存在する。
- Data GateのPass/Fail/Unknownが根拠付きで記録されている。
- Phase 3へ渡せるdata_versionまたは渡せない理由が明確である。
```

### P2-09 統合レビューとレッドチーム監査

```text
ステップID: P2-09
ロール: Phase 2統合レビュー・レッドチーム監査者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-09
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-REVIEW-DOCSET
- detail_boundary: Phase 2成果物全体の整合性、安全性、追跡性をレビューする。新規設計や実装を勝手に追加しない。
- human_gate_policy: H2-3でレビュー指摘の採否方針を承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/**/*.html
- P2-05からP2-08の実装、テスト、ログ
- doc/requirements/01_自動トレードシステム要件定義書.html
- doc/phase1/06_アダプター境界/06_Adapter境界設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html

タスク:
Phase 2成果物全体を統合レビューし、レッドチーム監査結果をHTMLで作成してください。

レビュー観点:
1. 要件追跡漏れ。
2. D10/D11/D18との矛盾。
3. Market Data Adapter、Store、Catalog、Signalの責務混線。
4. Raw改変、symbol mapping誤り、未来情報混入。
5. Data Quality Gate失敗のPass扱い。
6. Secret混入、外部API費用事故、過剰取得。
7. `MZC/MZS/MZW` 条件付き扱いの曖昧化。
8. Phase 3へ渡すdata_version、Manifest、Replay入力の不足。
9. doc/index.htmlリンク漏れ。
10. Phase 2スコープ逸脱。

出力形式:
- 指摘ID
- 重要度
- 対象ファイル
- 該当箇所
- 問題内容
- 修正方針
- Human Gate要否

完了条件:
- P2-D11とP2-D12が存在する。
- H2-3で人間が採否判断できる粒度で指摘が整理されている。
```

### P2-10 レビュー反映、完了判定、Phase 3引き継ぎ

```text
ステップID: P2-10
ロール: Phase 2修正統合者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A05_PhaseExecutionPlanner_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_skill_revision_integration_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_phase_execution_planning_v0_1

Phase Runbook:
- phase_id: Phase 2
- step_id: P2-10
- output_root: doc/phase2/
- log_root: plan/phase2/ログ/
- document_set_id: P2-COMPLETION-DOCSET
- detail_boundary: レビュー指摘を反映し、Phase 2完了判定とPhase 3引き継ぎを作成する。Phase 3の実装詳細計画は別Phase計画として扱う。
- human_gate_policy: H2-4でPhase 2完了とPhase 3移行を承認する。

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、不足部品として報告して停止する。
- AutoTradePhase1_* または autotrade_phase1_skill_* は参照対象として読むだけにする。実行部品として起動しない。
- default_orchestrator は変更しない。

入力:
- doc/phase2/07_統合レビュー/07_Phase2統合レビュー結果.html
- doc/phase2/07_統合レビュー/07_Phase2レッドチーム監査結果.html
- doc/phase2/**/*.html
- P2-05からP2-08の実装、テスト、ログ
- H2-3承認記録
- plan/Phase2_実行計画書_v0.1_2026-08-04.md

タスク:
P2-09のレビュー指摘を反映し、Phase 2の最終成果物、レビュー反映履歴、完了判定、Phase 3引き継ぎを作成してください。

作業:
1. 指摘ごとに採用、部分採用、保留、却下を判断し、理由を記録する。
2. 採用・部分採用の指摘を対象HTML、実装、テスト、ログへ反映する。
3. 残UnknownをPhase 3以降へ送る場合は、決定タイミングとGateを明記する。
4. `doc/phase2/08_完了判定/08_Phase2レビュー反映履歴.html` を作成する。
5. `doc/phase2/08_完了判定/08_Phase2完了判定とPhase3移行承認書.html` を作成する。
6. doc/index.htmlを更新する。
7. Phase 3実行計画で使うべき入力一覧とHuman Gate候補をまとめる。

Phase 2完了Gate:
- P2-D01からP2-D15が存在する。
- doc/index.htmlからすべてのPhase 2 HTML成果物へ到達できる。
- Raw / Normalized / Catalog / Signal / Rollの責務境界が矛盾していない。
- Data Quality GateとReplay Gateの結果が根拠付きで記録されている。
- UnknownがPass扱いされず、決定タイミングと担当Phaseを持つ。
- Secret実値、Account ID、API keyがGit、ログ、HTMLに混入していない。
- Phase 3へ渡すdata_version、fixture、Replay入力、未解決事項が明確である。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1 が、修正反映漏れ、残リスク削除、安全要件弱体化、Phase 3引き継ぎ漏れを確認する。
- AutoTrade_A80_DocumentIntegrator_v0_1 が、リンク、保存先、レビュー履歴、doc/index.html更新を確認する。

完了条件:
- P2-D13、P2-D14、P2-D15が存在する。
- H2-4で人間がPhase 2完了とPhase 3移行可否を判断できる。
```

---

## 11. レビュー結果と反映記録

### 11.1 AutoTrade_A90_DesignReviewer_v0_1 観点

| 観点 | 指摘 | 反映 |
|---|---|---|
| ステップ粒度 | 設計、実装、検証、レビュー、反映が1ステップにまとまると実行不能。 | P2-01からP2-10へ分割した。 |
| 依存関係 | Roll設計は公式仕様確認とStore/Catalog設計後に置く必要がある。 | P2-04をP2-02/P2-03依存にした。 |
| 発火制御 | 各プロンプトにAI部品完全名と未存在時停止条件が必要。 | 全プロンプトへ完全名と停止条件を記載した。 |
| Human Gate | 外部API利用とOD-03決定に人間承認が必要。 | H2-1とH2-2を追加した。 |
| Unknown扱い | `MZC/MZS/MZW` とdegraded品質警告をPass扱いにしない。 | UNK-P2-04, UNK-P2-05を追加した。 |
| Phaseスコープ | Strategy / Backtest / Broker / Live Runbookへ踏み込みすぎるリスク。 | 後続Phaseへ送る詳細化項目を分離した。 |

### 11.2 AutoTrade_A80_DocumentIntegrator_v0_1 観点

| 観点 | 指摘 | 反映 |
|---|---|---|
| 読みやすさ | 成果物、DAG、Gate、プロンプトが分かれている必要がある。 | 章を分け、表で整理した。 |
| リンク | 正式HTMLはdoc/index.htmlから到達可能にする必要がある。 | 各ステップの作業と完了条件へdoc/index.html更新を含めた。 |
| 保存先 | 計画、ログ、台帳の保存先が曖昧。 | `plan/phase2/ログ/`, `plan/phase2/HumanGate/`, `plan/phase2/台帳/`, `plan/phase2/プロンプト/` を定義した。 |
| レビュー反映 | 最終版に採否表と変更履歴が必要。 | P2-10でP2-D13を作成するようにした。 |

---

## 12. 完了条件

このPhase 2実行計画書は、次を満たしたため完了とする。

- 後続ステップを本計画書内のプロンプトだけで開始できる。
- 各ステップに、使用オーケストレータ完全名、担当サブエージェント完全名、使用モデル、使用Skill完全名、発火制御、入力、タスク、レビュー、完了条件がある。
- 複数ステップ、並列実行可否、依存関係、レビュー、レビュー反映、Human Gateが含まれる。
- 正式HTML成果物を `doc/phase2/` 配下へ保存し、`doc/index.html` から到達できるルールが含まれる。
- 計画書、プロンプト、ログ、台帳を `plan/` 配下へ保存するルールが含まれる。
- UnknownをPass扱いせず、台帳、決定タイミング、担当ステップが明示されている。
- Phase専用部品は不要と判定し、既存Phase 1専用部品は参照専用にした。
- `default_orchestrator` を変更しない。

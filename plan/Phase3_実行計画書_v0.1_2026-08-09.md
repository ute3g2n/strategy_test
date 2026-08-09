# Phase 3 実行計画書

作成日: 2026-08-09  
対象: タートルズ・トレンドフォロー自動売買システム  
対象Phase: Phase 3 Strategy / Backtest基盤  
状態: v0.1 / 初版

参照:

- `doc/requirements/01_自動トレードシステム要件定義書.html`
- `plan/自動トレードシステム_要件定義書.md`
- `plan/Phase分割と設計書整備方針_v0.1_2026-08-02.md`
- `plan/Phase2_実行計画書_v0.1_2026-08-04.md`
- `doc/00_全Phase残課題Blocked統合台帳.html`
- `doc/phase2/09_実DBN変換/09_実DBN_Replay隔離検証結果.html`
- `tests/evidence/phase2/RUN-P2-DBN-001/automation/run-test-summary.json`
- `doc/phase1/05_戦略設計/05_Strategy_Plugin_Interface設計書.html`
- `doc/phase1/05_戦略設計/05_Turtle_Golden_test設計書.html`
- `doc/phase1/07_実行モデル/07_共通実行モデル設計書.html`
- `doc/phase1/07_実行モデル/07_取引エンジンPoC評価設計書.html`
- `doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html`
- `doc/phase1/11_ロードマップ/11_詳細設計バックログ.html`
- `doc/phase1/11_ロードマップ/11_Phase2以降ロードマップ.html`
- `doc/phase2/04_ロール連続足/04_Roll_Rule_Continuous_Signal設計書.html`
- `doc/phase2/06_検証/06_Data_Quality_Replay検証結果.html`
- `src/autotrade/market_data/`
- `tests/market_data/`
- `.codex/skills/autotrade_skill_*_v0_1/SKILL.md`
- `.codex/agents/AutoTrade_A*.json`
- `.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json`
- `.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json`
- `.codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json`
- `.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json`
- `settings/ai_component_rules.md`

> 本計画は、Phase 2で作成した再現可能なMarketEventを使い、Turtle StrategyとBacktest基盤を同じイベント意味論で実装・検証するための計画である。投資助言、売買推奨、利益保証、特定商品の推奨を目的としない。

> `doc/phase2/08_完了判定/08_Phase2完了判定とPhase3移行承認書.html` の未承認表示は作成時点の履歴である。現在状態は、総合台帳のH2-3/H2-4承認済み記録、P2-12-03最終PASS証跡、実行ID `37da7396f4e84be3b82dfd0aae69a217` を正本とする。

---

## 1. AI部品存在確認

本計画で指定する汎用AI部品はすべて存在する。Phase 3専用のOrchestrator、Agent、Skillは作成しない。Strategy、Golden test、Backtest、PoC、実装、レビューは既存の汎用部品で扱えるためである。

| 種別 | 完全名 | 確認結果 |
|---|---|---|
| Orchestrator | `AutoTradePhasePlanning_Orchestrator_v0_1` | 存在 |
| Orchestrator | `AutoTradeProject_DesignDocSet_Orchestrator_v0_1` | 存在 |
| Orchestrator | `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1` | 存在 |
| Orchestrator | `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1` | 存在 |
| Orchestrator | `AutoTradeProject_Orchestrator_v0_1` | 存在 |
| Agent | `AutoTrade_A05_PhaseExecutionPlanner_v0_1` | 存在 |
| Agent | `AutoTrade_A10_RequirementsCurator_v0_1` | 存在 |
| Agent | `AutoTrade_A20_ArchitectureDomainArchitect_v0_1` | 存在 |
| Agent | `AutoTrade_A30_StrategyQaArchitect_v0_1` | 存在 |
| Agent | `AutoTrade_A40_ExecutionEnginePocArchitect_v0_1` | 存在 |
| Agent | `AutoTrade_A70_OpsSecurityArchitect_v0_1` | 存在 |
| Agent | `AutoTrade_A80_DocumentIntegrator_v0_1` | 存在 |
| Agent | `AutoTrade_A81_DesignDocSetWriter_v0_1` | 存在 |
| Agent | `AutoTrade_A82_ImplementationDetailDesigner_v0_1` | 存在 |
| Agent | `AutoTrade_A90_DesignReviewer_v0_1` | 存在 |
| Agent | `AutoTrade_A91_ImplementationDetailReviewer_v0_1` | 存在 |
| Agent | `AutoTrade_A110_PythonTestEngineer_v0_1` | 存在 |
| Agent | `AutoTrade_A120_PythonImplementer_v0_1` | 存在 |
| Agent | `AutoTrade_A130_VerificationEngineer_v0_1` | 存在 |
| Agent | `AutoTrade_A140_DebugEngineer_v0_1` | 存在 |
| Agent | `AutoTrade_A150_PythonCodeReviewer_v0_1` | 存在 |
| Agent | `AutoTrade_A160_TradingSecurityReviewer_v0_1` | 存在 |
| Skill | `autotrade_skill_phase_execution_planning_v0_1` | 存在 |
| Skill | `autotrade_skill_strategy_interface_v0_1` | 存在 |
| Skill | `autotrade_skill_turtle_strategy_rules_v0_1` | 存在 |
| Skill | `autotrade_skill_golden_test_v0_1` | 存在 |
| Skill | `autotrade_skill_execution_model_v0_1` | 存在 |
| Skill | `autotrade_skill_trading_engine_poc_v0_1` | 存在 |
| Skill | `autotrade_skill_poc_evaluation_v0_1` | 存在 |
| Skill | `autotrade_skill_test_strategy_v0_1` | 存在 |
| Skill | `autotrade_skill_python_implementation_v0_1` | 存在 |
| Skill | `autotrade_skill_python_test_quality_v0_1` | 存在 |
| Skill | `autotrade_skill_python_code_review_v0_1` | 存在 |

既存の `AutoTradePhase1_*` と `autotrade_phase1_skill_*` は、D08、D09、D11、D12、D18の作成根拠として読むだけにする。実行部品として起動しない。`default_orchestrator` は変更しない。

---

## 2. Phase 3の目的

Phase 3では、Phase 2のMarketEvent系列を入力に、StrategyとBacktestの本番候補コードを実装し、同じ入力・設定・コード版で同じSignal、Intent、状態、約定結果を再現できる状態を作る。

中心領域は次のとおりである。

- Strategy Pluginの型付き契約と状態遷移
- Turtle原典System 1 / System 2のN、True Range、Donchian、Entry、Exit、0.5N追加、2N Stop
- 原典版と比較候補の設定分離
- 決定的な履歴イベント再生
- 約定、取引コスト、スリッページ、Gap、Roll損益の明示
- Golden fixture、Replay test、Look-ahead防止、Bias Gate
- Experiment Manifestと再現可能な実験結果
- Holdout / Walk-forwardの分割契約
- NautilusTraderとLEAN系の取引エンジンPoC証拠
- Phase 4へ渡すOrderIntent、実行モデル、未確定事項

Phase 3ではBroker接続、IBKR Paper発注、Broker再同期、実資金注文、Live用Risk最終値、クラウド運用、Secret投入を実装しない。

---

## 3. 開始条件と現在の入力状態

| 区分 | 現在の条件 |
|---|---|
| Phase 2移行承認 | 総合台帳でH2-3、H2-4は2026-08-09承認済み。 |
| 実データReplay | P2-12-03は実DBN 4件を読取り、通常先物3件をMarketEvent化し、spread 1件を除外して固定4 Gate PASS。 |
| 再現性 | 入力hash前後一致、同一Replay系列一致、data_version `dv_780568eab89680cfc758`。 |
| Strategy仕様 | D08でStrategyの責務、非責務、ライフサイクル、OrderIntent境界を定義済み。 |
| Golden仕様 | D09でGT-TUR-001〜012、Look-ahead防止、fixture後出し変更禁止を定義済み。 |
| 実行モデル | D11でEvent Envelope、Run Manifest、Backtest / Shadow / Paper / Liveの共通意味論を定義済み。 |
| PoC評価 | D12で候補、採点、除外条件、証拠条件を定義済み。 |
| 品質 | D18とPhase 2実装でReplay、Data Gate、fail-closedの基礎が存在。 |
| 長期評価データ | P2-12-03の実DBNは4件、研究用5銘柄CSVは主に2026年7月1か月であり、55日Channelや本格Walk-forwardには不足する。利益評価の合格根拠にはまだ使わない。 |

---

## 4. Phase 3で固定する判断

| ID | 固定する判断 | 理由 |
|---|---|---|
| DEC-P3-01 | StrategyはMarketEventと限定Viewを読み、SignalEvent、OrderIntentまたはTargetPositionまでを出す。 | Risk最終判定、OMS、Broker責務を混ぜないため。 |
| DEC-P3-02 | Golden testは利益を判定せず、ルール、時刻、状態遷移、出力の再現性を判定する。 | 結果を見てfixtureや期待値を変える過剰最適化を防ぐため。 |
| DEC-P3-03 | 未確定バー、未来のroll、holdout結果、後続バーをStrategyへ渡さない。 | Look-aheadを防ぐため。 |
| DEC-P3-04 | 同じdata_version、Catalog版、Strategy Config、Experiment Manifest、code revision、engine版で同じ順序付き出力を再現する。 | 実験の追跡性を保つため。 |
| DEC-P3-05 | 約定モデル、コスト、スリッページ、Gap、RollはStrategy外のBacktest実行モデルへ置く。 | StrategyをBacktest専用化しないため。 |
| DEC-P3-06 | Holdoutはパラメータ決定に使わず、結果確認後に分割、fixture、期待値を変更しない。 | data snoopingを防ぐため。 |
| DEC-P3-07 | Market Data品質方針はPhase 2の `quality-warning-except-missing-duplicate-time-v1` を入力条件として保持する。 | Phase間で品質意味論を変えないため。 |
| DEC-P3-08 | 大容量データと実験結果は `E:\strategy_test_data\phase3\` 配下へ保存し、Gitには小型fixture、Manifest、要約証跡だけを置く。 | ユーザーが決定した保存方針に従うため。 |
| DEC-P3-09 | Phase 3のPoCはローカルBacktest適合を評価し、Broker Paper接続はPhase 4へ送る。OD-02の最終確定範囲はH3-2で明示承認する。 | D12の全PoC証拠にはPhase 4項目が含まれるため。 |
| DEC-P3-10 | Critical / High、Unknown、Manifest不一致、未来情報混入、再現不一致がある場合はPhase 3を完了扱いにしない。 | 安全側に停止するため。 |

---

## 5. 後続Phaseへ送る項目

| ID | 項目 | 送り先 | Phase 3での扱い |
|---|---|---|---|
| P3-DEFER-01 | IBKR Paper接続、部分約定の実Broker意味論、Open Order / Fill / Position再同期 | Phase 4 | PortとPoC期待値だけを固定する。 |
| P3-DEFER-02 | 1NのLive用金額、証拠金、最小数量、4/6/10/12 Unitの最終Risk判定 | Phase 4/5 | Strategyは計算根拠とHintを出すが、注文可否を決めない。 |
| P3-DEFER-03 | Shadow / Paperの運用日数、通知サービス、クラウドVM | Phase 5/6 | 測定項目とHealthEventだけを定義する。 |
| P3-DEFER-04 | Live向けSecret、Kill Switch、Broker-native Stop、復旧Runbook | Phase 4〜7 | BacktestにSecretや実注文能力を持ち込まない。 |
| P3-DEFER-05 | 長期実績に基づくパラメータ採用、資金配分、利益目標 | 後続の研究・承認Gate | Phase 3ではルール再現性とBias防止を優先し、短期データから採用判断しない。 |

---

## 6. 成果物

### 6.1 正式HTML成果物

正式HTMLは `doc/phase3/` 配下へ保存し、追加・更新と同じステップで `doc/index.html` から到達可能にする。指摘内容と修正方針には、同じセル内で中学生でも分かる説明を併記する。

| ID | 成果物 | 出力先 |
|---|---|---|
| P3-D01 | Phase 3スコープ定義 | `doc/phase3/01_要件追跡/01_Phase3スコープ定義.html` |
| P3-D02 | Phase 3要件追跡・Unknown対応表 | `doc/phase3/01_要件追跡/01_Phase3要件追跡マトリクス.html` |
| P3-D03 | 取引エンジン公式仕様・PoC前提確認 | `doc/phase3/02_エンジン調査/02_取引エンジン公式仕様確認結果.html` |
| P3-D04 | Strategy / Turtle実装詳細設計書 | `doc/phase3/03_Strategy詳細設計/03_Strategy_Turtle実装詳細設計書.html` |
| P3-D05 | Backtest / Experiment実装詳細設計書 | `doc/phase3/04_Backtest詳細設計/04_Backtest_Experiment実装詳細設計書.html` |
| P3-D06 | Golden / Biasテスト設計・fixture凍結記録 | `doc/phase3/05_テスト設計/05_Golden_Biasテスト設計書.html` |
| P3-D07 | Strategy実装・検証結果 | `doc/phase3/06_実装検証/06_Strategy実装検証結果.html` |
| P3-D08 | Backtest実装・再現性検証結果 | `doc/phase3/06_実装検証/07_Backtest再現性検証結果.html` |
| P3-D09 | Cost / Roll / Gap / Holdout検証結果 | `doc/phase3/07_頑健性検証/08_Cost_Roll_Gap_Holdout検証結果.html` |
| P3-D10 | 取引エンジンPoC評価結果 | `doc/phase3/08_エンジンPoC/09_取引エンジンPoC評価結果.html` |
| P3-D11 | Phase 3統合レビュー結果 | `doc/phase3/09_統合レビュー/10_Phase3統合レビュー結果.html` |
| P3-D12 | Phase 3レッドチーム監査結果 | `doc/phase3/09_統合レビュー/11_Phase3レッドチーム監査結果.html` |
| P3-D13 | レビュー反映・Phase 4引継ぎ | `doc/phase3/10_完了判定/12_Phase3レビュー反映履歴.html` |
| P3-D14 | Phase 3完了判定とPhase 4移行承認書 | `doc/phase3/10_完了判定/13_Phase3完了判定とPhase4移行承認書.html` |

### 6.2 実装・テスト成果物

| 区分 | 保存先 | ルール |
|---|---|---|
| Strategy実装 | `src/autotrade/strategy/` | 外部SDK、Broker、Secret、ファイルI/O、現在時刻へ直接依存しない。 |
| Backtest実装 | `src/autotrade/backtest/` | MarketEventを順序どおり再生し、約定・コスト・ManifestをStrategy外で扱う。 |
| 共通契約 | `src/autotrade/execution/` または既存共通型 | P3-D04/P3-D05のA91レビューで配置を確定するまで、先に新設しない。 |
| Strategyテスト | `tests/strategy/` | GT-TUR-001〜012を固定fixtureで実装する。 |
| Backtestテスト | `tests/backtest/` | Replay、cost、roll、gap、Manifest、Bias Gateを検証する。 |
| 小型fixture | `tests/fixtures/strategy/`, `tests/fixtures/backtest/` | hash固定。成績を見た後の変更は禁止。 |
| 実行証跡 | `tests/evidence/phase3/<run-id>/` | JSON/Markdown、Manifest、レビュー、固定Gate結果を保存する。 |

### 6.3 大容量データ

Phase 3で作る大容量データは次へ保存する。バックアップ、保存期限、暗号化、専用ACL、容量上限を設けないというユーザー決定を継承する。消失時に復元できないリスクは受容済みである。

- `E:\strategy_test_data\phase3\datasets\`
- `E:\strategy_test_data\phase3\experiments\`
- `E:\strategy_test_data\phase3\manifests\`
- `E:\strategy_test_data\phase3\engine_poc\`
- `E:\strategy_test_data\phase3\reports\`
- `E:\strategy_test_data\phase3\tmp\`

既存の研究用CSVは入力候補として検査するが、Phase 2のdata_version、Catalog、品質報告、連続足規則へ接続できない場合は、正式な合格証拠に使わない。

### 6.4 plan・ログ

| 区分 | 保存先 |
|---|---|
| 本計画書 | `plan/Phase3_実行計画書_v0.1_2026-08-09.md` |
| 実行ログ | `plan/phase3/ログ/` |
| プロンプト控え | `plan/phase3/プロンプト/` |
| 作業メモ | `plan/phase3/台帳/` |
| Human Gate証跡 | `tests/evidence/phase3/<run-id>/human-gate/` |

---

## 7. Unknown台帳

現在状態の正本は `doc/00_全Phase残課題Blocked統合台帳.html` とする。本表はPhase 3内の担当と期限を示す計画上の写しであり、状態変更時は総合台帳全体も同時に点検する。

| Unknown ID | 内容 | 担当 | 決定時期 | 未決時の扱い |
|---|---|---|---|---|
| UNK-P3-01 | 55日Channel、Holdout、Walk-forwardに足る履歴期間と市場数がまだない。 | P3-01, P3-02, P3-10 | H3-2まで | Goldenとsynthetic Replayだけ進め、利益・頑健性を合格扱いしない。 |
| UNK-P3-02 | Golden fixture形式、Decimal精度、丸め、許容差、最小ケース数。 | P3-03, P3-05 | H3-1 | Strategy実装を開始しない。 |
| UNK-P3-03 | NautilusTrader / LEANの固定版、ライセンス、ローカル実行方式、依存hash。 | P3-02, P3-09 | H3-2 | 外部依存を導入せず、自作の最小決定的runnerで契約検証だけ行う。 |
| UNK-P3-04 | OD-02をPhase 3のBacktest証拠だけで最終決定するか、Phase 4のPaper再同期証拠まで条件付きにするか。 | P3-02, P3-09 | H3-2 | Phase 3候補選定に限定し、プロジェクト全体の最終決定と書かない。 |
| UNK-P3-05 | 市場別手数料、スリッページ、Gap約定の実測値。 | P3-04, P3-08 | P3-10 | 保守的な明示設定で比較し、実値や利益保証と呼ばない。 |
| UNK-P3-06 | 1NのLive用金額、証拠金、最小数量、Risk最終値。 | P3-03, P3-11 | Phase 4/5 | StrategyはSignalとUnit Hintまでに限定し、注文可否を決めない。 |
| UNK-P3-07 | 取引時間、休日、セッション境界の正式Calendar。 | P3-04, P3-08 | P3-10 | 固定テストCalendarだけで検証し、Live適合を主張しない。 |
| UNK-P3-08 | 原典版と比較候補で固定するパラメータ集合、学習区間、検証区間。 | P3-01, P3-05, P3-10 | H3-1 / H3-2 | 結果を見て候補を増減せず、比較結果を採用判断に使わない。 |

---

## 8. 人による承認

| Gate | タイミング | 承認してもらう内容 | 未承認時 |
|---|---|---|---|
| H3-0 | P3-01完了後 | Phase 3の対象、非対象、Strategy候補、成果物、Unknown、Phase 4への境界。 | P3-02の読取調査だけ可能。詳細設計・実装を開始しない。 |
| H3-1 | P3-05完了後 | Golden fixture、期待出力、hash、丸め、Look-ahead/Biasテスト、変更規則を凍結する。 | P3-06以降の本実装を開始しない。 |
| H3-2 | P3-02/P3-05完了後 | 取引エンジン固定依存の導入、必要な長期履歴データの取得・利用、OD-02のPhase 3決定範囲。 | 外部取得・依存導入・実エンジンPoCを行わず、synthetic契約検証に限定する。 |
| H3-3 | P3-11完了後 | 統合レビューとレッドチーム指摘の採否、残Unknownの送り先。 | P3-12の完了判定へ進めない。 |
| H3-4 | P3-12完了後 | Phase 3完了、Backtest結果の利用範囲、Phase 4 Broker / Paper基盤への移行。 | Phase 4へ進めない。 |

H3-2は外部データや外部依存を使う許可であり、Secret投入、Broker接続、実注文、Live運用の許可ではない。

---

## 9. 実行DAG

| グループ | ステップ | 並列 | 依存 |
|---|---|---|---|
| G0 | P3-01 | 不可 | H2-4、本計画書 |
| G1 | P3-02 | 不可 | P3-01。読取調査はH3-0前でも可能、依存導入は不可。 |
| G2 | P3-03, P3-04 | 並列可 | H3-0、P3-01、P3-02の調査結果 |
| G3 | P3-05 | 不可 | P3-03、P3-04 |
| G4 | P3-06, P3-07 | 並列可 | H3-1、P3-05 |
| G5 | P3-08 | 不可 | P3-06、P3-07 |
| G6 | P3-09 | 不可 | H3-2、P3-02、P3-07、P3-08 |
| G7 | P3-10 | 不可 | P3-06〜P3-09。長期データ未承認時は契約・synthetic検証に縮退し、UNK-P3-01を残す。 |
| G8 | P3-11 | 不可 | P3-01〜P3-10 |
| G9 | P3-12 | 不可 | H3-3、P3-11 |

---

## 10. 後続ステップ実行プロンプト

### P3-01 Phase 3スコープ・要件追跡・Unknown整理

```text
ステップID: P3-01
ロール: Phase 3要件・スコープ整理者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_source_reader_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_strategy_interface_v0_1, autotrade_skill_turtle_strategy_rules_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_orchestration_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_design_review_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-01
- output_root: doc/phase3/
- log_root: plan/phase3/ログ/
- detail_boundary: Strategy / Backtest / Golden / PoCを対象とし、Broker、Paper、Live、Secret、Risk最終値を含めない。
- human_gate_policy: P3-01成果物作成後、H3-0承認まで詳細設計・実装を開始しない。

発火制御:
- 上記完全名のAI部品だけを使用する。
- 不足部品があれば代替せず報告して停止する。
- AutoTradePhase1_* と autotrade_phase1_skill_* は参照専用とし起動しない。
- default_orchestratorは変更しない。

入力:
- plan/Phase3_実行計画書_v0.1_2026-08-09.md
- doc/00_全Phase残課題Blocked統合台帳.html
- doc/requirements/01_自動トレードシステム要件定義書.html
- doc/phase1/05_戦略設計/05_Strategy_Plugin_Interface設計書.html
- doc/phase1/05_戦略設計/05_Turtle_Golden_test設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- doc/phase1/07_実行モデル/07_取引エンジンPoC評価設計書.html
- doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html
- doc/phase1/11_ロードマップ/11_詳細設計バックログ.html
- doc/phase2/09_実DBN変換/09_実DBN_Replay隔離検証結果.html

タスク:
Phase 3のスコープ、要件追跡、Unknown、成果物、Phase 4境界を正式HTMLへ整理してください。

作業:
1. H2-3/H2-4承認済みとP2-12-03 PASSを確認する。
2. D08/D09/D11/D12/D18とBL-P3-01/02をPhase 3成果物へ対応付ける。
3. 原典System 1/2、比較候補、Backtest、Cost/Roll/Gap、Holdout/Walk-forward、取引エンジンPoCを対象化する。
4. Broker/Paper/Live/Secret/Risk最終判定を対象外として明記する。
5. UNK-P3-01〜08を総合台帳へ登録し、関連する全行・件数・最新状態を全体点検する。
6. H3-0〜H3-4を日本語で明記する。
7. P3-D01/P3-D02を作成しdoc/index.htmlへリンクする。

レビュー:
- A90がPhase逸脱、Unknownの合格扱い、Phase 4責務混入を確認する。
- A30がTurtle/Goldenの範囲、A40がPoC/OD-02の決定時期を確認する。
- 指摘内容と修正方針には中学生でも分かる説明を同じ欄へ併記する。

完了条件:
- P3-D01/P3-D02が作成され、doc/index.htmlから到達できる。
- H3-0の承認対象が具体的である。
- 現在の全Unknownが総合台帳へ反映されている。
```

### P3-02 取引エンジン公式仕様・PoC前提調査

```text
ステップID: P3-02
ロール: 取引エンジン公式仕様・PoC前提調査者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_trading_engine_poc_v0_1, autotrade_skill_poc_evaluation_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-02
- output_root: doc/phase3/02_エンジン調査/
- log_root: plan/phase3/ログ/
- detail_boundary: 公式仕様、版、ライセンス、ローカルBacktest、再現性、Manifest接続を調査する。依存導入や実行はしない。
- human_gate_policy: H3-2前に外部パッケージ、Docker image、.NET tool、データを導入しない。

発火制御:
- 指定AI部品だけを使用する。不足時は停止する。
- 外部仕様は公式一次情報だけを根拠にし、URLと確認日を記録する。
- default_orchestratorは変更しない。

入力:
- P3-D01, P3-D02
- doc/phase1/07_実行モデル/07_取引エンジンPoC評価設計書.html
- doc/phase1/07_実行モデル/07_共通実行モデル設計書.html
- doc/phase2/09_実DBN変換/09_実DBN_Replay隔離検証結果.html
- pyproject.toml

タスク:
NautilusTraderとLEAN系について、Phase 3のローカルBacktest PoCを安全かつ再現可能に実行する前提を公式情報で確認してください。

作業:
1. 現在の安定版、Python/.NET/Docker要件、ライセンス、ローカル実行方法を確認する。
2. MarketEvent、Strategy、OrderIntent、Manifest、deterministic replayへ接続する最小Adapter境界を比較する。
3. 外部データ取得、クラウド利用、Broker接続をPoC必須条件にしない。
4. wheel/package/image hash固定、offline再実行、キャッシュ保存先を設計する。
5. POC-01〜05のうちPhase 3で実行する項目とPhase 4へ送る項目を分ける。
6. OD-02をPhase 3で最終決定できる範囲と、Phase 4証拠が必要な範囲を明示する。
7. P3-D03を作成し、H3-2の承認材料を作る。

レビュー:
- A40が比較の公平性とPoC再現性を確認する。
- A70が外部依存、実行権限、ネットワーク、Secret、ライセンスを確認する。
- A90が候補名だけで採用していないかを監査する。

完了条件:
- 公式URL、確認日、固定候補版、導入物、PoC縮退方針が明確である。
- H3-2前に外部導入を行っていない。
- UNK-P3-03/04の解決材料が総合台帳へ反映されている。
```

### P3-03 Strategy / Turtle実装詳細設計

```text
ステップID: P3-03
ロール: Strategy / Turtle実装詳細設計者
使用オーケストレータ完全名: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_strategy_interface_v0_1, autotrade_skill_turtle_strategy_rules_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_domain_modeling_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_revision_integration_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-03
- output_root: doc/phase3/03_Strategy詳細設計/
- log_root: plan/phase3/ログ/
- detail_boundary: Strategyの計算、状態、Signal/Intentまで。約定、Risk最終判定、OMS、Brokerは対象外。
- human_gate_policy: H3-0承認済みを確認する。H3-1前にGolden期待値を確定扱いしない。

発火制御:
- 指定部品だけを使用し、不足時は停止する。
- Phase 1専用部品は参照のみ。
- A91初回レビュー、改訂、A91再レビューまで完了しない限り設計完了としない。

入力:
- P3-D01〜P3-D03
- D08 Strategy Plugin Interface
- D09 Turtle Golden test
- D11 共通実行モデル
- Phase 2 MarketEvent / Catalog / data_version実装

タスク:
Strategy / Turtleを実装者が判断を補わず実装できる詳細設計へ更新してください。

作業:
1. ファイル構成、型付きAPI、状態、snapshot、reason code、例外を定義する。
2. True Range、N、Donchian、System 1/2 Entry/Exit、勝ちブレイクフィルター、0.5N追加、2N Stopを時系列順に定義する。
3. Decimal精度、丸め、warmup、確定バー、同時刻イベント順を固定する。
4. Strategy Configに原典版と比較候補を分離し、銘柄別後付け最適化を禁止する。
5. OrderIntent/TargetPosition、StrategyState、StrategySnapshot、Healthの全フィールドを定義する。
6. Risk/OMS/Broker/約定/現在時刻/外部I/OをStrategyから排除する。
7. GT-TUR-001〜012と追加異常系を全テスト表へ対応させる。
8. AF-D14/16の構成、日本語説明、Mermaid図、受渡し表を満たすP3-D04を作る。

レビュー:
- A91が型、時系列、例外、全テスト、実装可能性をFindings firstで確認する。
- A30が原典ルールとLook-aheadを確認する。
- A90がRisk/OMS責務混入とBacktest専用化を監査する。

完了条件:
- A91再レビューでCritical/Highが0件。
- UNK-P3-02/06/08が明示され、未決値をPassにしていない。
- P3-D04がdoc/index.htmlから到達できる。
```

### P3-04 Backtest / Experiment実装詳細設計

```text
ステップID: P3-04
ロール: Backtest / Experiment実装詳細設計者
使用オーケストレータ完全名: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_trading_engine_poc_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_revision_integration_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-04
- output_root: doc/phase3/04_Backtest詳細設計/
- log_root: plan/phase3/ログ/
- detail_boundary: 履歴Event再生、Strategy接続、仮想約定、cost/roll/gap、Manifest、結果保存。Broker接続なし。
- human_gate_policy: H3-0承認済みを確認し、外部engine依存はH3-2まで導入しない。

発火制御:
- 指定部品だけを使用する。
- A91再レビュー前に実装開始可としない。
- 外部接続、Secret、Broker、可変現在時刻を設計へ入れない。

入力:
- P3-D01〜P3-D04
- D11 共通実行モデル
- D12 取引エンジンPoC評価
- D18 テスト品質Gate
- Phase 2 MarketEvent, DataVersionManifest, Replay証跡

タスク:
決定的なBacktestとExperiment Manifestの実装詳細設計を作成してください。

作業:
1. MarketEvent順序、clock、queue、Strategy呼出し、状態保存、結果確定の処理順を定義する。
2. FillModel、CostModel、SlippageModel、GapModel、RollPnLModelをPortとして分離する。
3. 同一時刻、Gap、Stop飛越し、価格上限下限、欠損、roll境界の保守的規則を定義する。
4. Experiment Manifestへdata_version、fixture/data hash、Catalog、Strategy Config、engine版、cost設定、分割、code revisionを束縛する。
5. Holdout/Walk-forwardの期間分割、学習/検証情報のアクセス禁止を定義する。
6. Eドライブの大容量出力とGit管理証跡の境界を定義する。
7. Nautilus/LEAN AdapterをCoreから分離し、外部型をStrategyへ漏らさない。
8. 全テスト表、Mermaid構造/処理図、異常系、復旧、監査を含むP3-D05を作る。

レビュー:
- A91が実装可能性、永続化、例外、全テストを確認する。
- A40がengine非依存CoreとPoC接続を確認する。
- A70/A90が未来情報、Manifest改ざん、外部I/O、危険な理想約定を監査する。

完了条件:
- A91再レビューでCritical/Highが0件。
- UNK-P3-01/03/05/07が明示される。
- P3-D05がdoc/index.htmlから到達できる。
```

### P3-05 Golden / Biasテスト設計とRED固定

```text
ステップID: P3-05
ロール: Strategy / Backtestテスト設計者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_test_quality_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_turtle_strategy_rules_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_python_code_review_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-05
- output_root: doc/phase3/05_テスト設計/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-GOLD-001
- detail_boundary: 固定fixtureと期待値を先に作り、未実装APIをREDで固定する。利益の良し悪しは判定しない。
- human_gate_policy: fixture hashと期待値をH3-1で承認するまで実装を開始しない。

発火制御:
- 指定部品だけを使用する。
- trusted scope登録前に新Run IDを実行しない。
- 実市場の結果を見てfixtureや期待値を変えない。
- 外部接続、Secret、Brokerを使わない。

入力:
- P3-D04, P3-D05
- D09 Golden test
- D18 テスト品質Gate
- tests/fixtures/market_data/
- tests/evidence/phase2/RUN-P2-DBN-001/
- scripts/quality_gate/trusted_scopes.json

タスク:
Golden、Replay、Bias、Manifest、異常系のfixtureとREDテストを先に作成してください。

作業:
1. GT-TUR-001〜012を実装可能なJSON fixtureへ固定する。
2. TR/N/Donchian、Entry/Exit、勝ちブレイク、0.5N追加、2N Stop、snapshot/restoreを覆う。
3. 未確定バー、未来roll、holdout参照、現在時刻、fixture後出し変更を拒否する。
4. Backtestの同時刻順序、Gap保守約定、cost、roll、Manifest改ざん、再ReplayをRED化する。
5. fixture schema、Decimal表現、期待Signal/Intent/State、hashを証跡へ固定する。
6. RUN-P3-GOLD-001のtarget_paths、固定4 Gate、Manifest、証跡先をtrusted scopeへ登録する。
7. P3-D06を作成し、RED/GREEN内訳と未実装境界を記録する。

レビュー:
- A150がテスト漏れ、脆いassert、可変時刻、外部I/Oを確認する。
- A160がLook-ahead、data snooping、未知値の合格扱い、理想約定を監査する。
- 問題内容と修正方針へ中学生向け説明を併記する。

完了条件:
- 固定fixture、期待値、hash、変更規則がH3-1の承認材料として明確。
- 未実装APIはRED、既存MarketEvent契約はGREENとして区別される。
- Golden testを利益評価に使っていない。
```

### P3-06 Strategy / Turtle最小実装

```text
ステップID: P3-06
ロール: Strategy / Turtle Python実装者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_implementation_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_strategy_interface_v0_1, autotrade_skill_turtle_strategy_rules_v0_1, autotrade_skill_golden_test_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-06
- output_root: src/autotrade/strategy/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-STR-001
- detail_boundary: 承認済みP3-D04とRED範囲の最小実装。Risk/OMS/Broker/Fillは実装しない。
- human_gate_policy: H3-1承認済みfixture hashを確認する。

発火制御:
- 指定部品だけを使用する。
- テストをGREENにするためfixture/期待値を変更しない。
- Critical/High、未知入力、未来参照があれば停止する。

入力:
- 承認済みP3-D04/P3-D06
- tests/strategy/
- tests/fixtures/strategy/
- src/autotrade/market_data/store_contracts.py
- RUN-P3-GOLD-001証跡

タスク:
承認済み詳細設計とGolden REDに限定してStrategy / Turtleを最小実装してください。

作業:
1. 型、indicator、state、System 1/2、Signal/Intent、snapshot/restoreを実装する。
2. Decimal、UTC、確定バー、warmup、同時刻順を固定する。
3. 外部I/O、現在時刻、Broker型、SDK型、Risk最終判定を入れない。
4. REDを順にGREEN化し、失敗時はA140の上限付き回復を使う。
5. ruff format/check、mypy、pytest、coverage、固定Gateを実行する。
6. A150/A160レビューのCritical/Highを解消する。
7. P3-D07とRUN-P3-STR-001証跡を作る。

レビュー:
- A150がPython品質、型、純粋性、保守性を確認する。
- A160がLook-ahead、隠れ状態、Unknown通過、Signal責務を監査する。
- A30が原典ルールとGolden一致を確認する。

完了条件:
- GT-TUR-001〜012がGREEN。
- 同一入力でSignal/Intent/Stateが一致する。
- Critical/Highが0件で、P3-D07がdoc/index.htmlから到達できる。
```

### P3-07 Backtest Core / Experiment Manifest最小実装

```text
ステップID: P3-07
ロール: Backtest Core Python実装者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_implementation_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_trading_engine_poc_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-07
- output_root: src/autotrade/backtest/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-BT-001
- detail_boundary: 決定的Event replay、Strategy接続、Manifest、最小仮想約定。外部engine SDKはH3-2まで使わない。
- human_gate_policy: H3-1承認済みを確認する。

発火制御:
- 指定部品だけを使用する。
- Golden fixtureを変更しない。
- 外部接続、Broker、Secret、可変現在時刻を使わない。

入力:
- 承認済みP3-D05/P3-D06
- src/autotrade/strategy/
- src/autotrade/market_data/
- tests/backtest/
- tests/fixtures/backtest/

タスク:
決定的なBacktest CoreとExperiment Manifestを最小実装してください。

作業:
1. Event queue、simulated clock、Strategy lifecycle、結果収集を実装する。
2. data_versionとMarketEvent順序を改変せず入力する。
3. Manifestへ全入力版/hash/config/codeを束縛し、不一致を拒否する。
4. snapshot/restore後も重複Signal/Intentを作らない。
5. 最小Fill Portを実装し、cost/roll/gapの詳細はP3-08へ分離する。
6. 固定GateとA150/A160レビューを通す。
7. P3-D08とRUN-P3-BT-001証跡を作る。

レビュー:
- A150が決定性、型、例外、永続化、競合を確認する。
- A160がManifest差替え、未来情報、入力改ざん、理想約定を監査する。
- A40が外部engine Adapter境界を確認する。

完了条件:
- 同一Manifestで同一順序のSignal/Intent/結果になる。
- ManifestやMarketEvent差替えをfail-closedで拒否する。
- Critical/Highが0件。
```

### P3-08 Cost / Roll / Gap / Holdout契約実装

```text
ステップID: P3-08
ロール: Backtest頑健性モデル実装者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_implementation_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_golden_test_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-08
- output_root: src/autotrade/backtest/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-BIAS-001
- detail_boundary: 約定、費用、Gap、Roll、期間分割とBias防止。利益採用判断はしない。
- human_gate_policy: H3-1承認済みfixtureを使う。長期実データはH3-2承認範囲だけ使用する。

発火制御:
- 指定部品だけを使用する。
- 実測値がUnknownなら明示設定を使い、実際の手数料・利益と呼ばない。
- holdout結果を見た後の設定変更を禁止する。

入力:
- P3-D05〜P3-D08
- Phase 2 Roll / Continuous設計
- tests/backtest/
- tests/fixtures/backtest/

タスク:
Cost、Slippage、Gap、Roll、Holdout/Walk-forwardの実行契約を実装してください。

作業:
1. commission、slippage、保守的Stop/Gap fill、roll PnLを設定駆動で実装する。
2. 理想価格約定、負のコスト、未来close参照を拒否する。
3. train/validation/holdoutの期間をManifestで固定し、Strategyからholdout情報を隠す。
4. 同一入力で同一partitionと結果を再現する。
5. 短期データでは頑健性合格としない証跡を残す。
6. P3-D09を更新可能な検証骨格として作る。

レビュー:
- A150がモデル境界、型、テストを確認する。
- A160が楽観約定、後付け最適化、holdout漏洩、roll二重計上を監査する。

完了条件:
- cost/roll/gapを無視した結果を正式結果として出せない。
- Holdout漏洩テストがGREEN。
- UNK-P3-01/05/07が未解消なら明示的に残る。
```

### P3-09 取引エンジンPoC

```text
ステップID: P3-09
ロール: 取引エンジンPoC実行・評価者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_trading_engine_poc_v0_1, autotrade_skill_poc_evaluation_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-09
- output_root: doc/phase3/08_エンジンPoC/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-POC-001
- detail_boundary: ローカルBacktest PoC。Broker、Paper、Live、Secretは対象外。
- human_gate_policy: H3-2で承認された版、依存hash、入力、実行方式だけを使う。

発火制御:
- 指定部品だけを使用する。
- H3-2未承認なら実engine依存を導入せず、BLOCKED証跡を作って停止する。
- 公式配布元、固定hash、offline再実行条件を検証する。
- 外部接続、クラウドQuantConnect、Broker、Secretを使わない。

入力:
- P3-D03, P3-D05, P3-D07〜P3-D09
- D12 取引エンジンPoC評価設計
- H3-2承認記録
- RUN-P3-STR-001, RUN-P3-BT-001

タスク:
NautilusTraderとLEAN系を、同じ固定入力・Strategy意味論・採点表で比較してください。

作業:
1. 承認済み固定依存をoffline環境へ導入し、hashと版を証跡化する。
2. 1市場20日breakout、1分足Replay、Entry/Add/Stop/Exit、snapshot/restoreを実行する。
3. 同一Manifestで再実行し、イベント・Signal・Intent・結果差を比較する。
4. 外部型、engine固有ID、暗黙clockをCoreへ漏らさないAdapterを使う。
5. D12採点表と除外条件で評価し、失敗も保存する。
6. Phase 4 Paper証拠が無い項目は未検証とし、OD-02の決定範囲を明示する。
7. P3-D10を作成し、総合台帳のUNK-P3-03/04を更新する。

レビュー:
- A150がAdapter実装と再現性を確認する。
- A160/A70が依存供給元、実行権限、外部通信、Secret、証跡改ざんを監査する。
- A40が採点の公平性と除外条件を確認する。

完了条件:
- 両候補または承認済み縮退候補を同一条件で比較している。
- Broker/Paper未検証を合格扱いしていない。
- P3-D10がdoc/index.htmlから到達できる。
```

### P3-10 統合Replay / Golden / Bias検証

```text
ステップID: P3-10
ロール: Phase 3統合検証者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_test_quality_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-10
- output_root: doc/phase3/06_実装検証/, doc/phase3/07_頑健性検証/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-INT-001
- detail_boundary: 全Strategy/Backtest/PoC証跡の統合検証。短期データから利益採用を決めない。
- human_gate_policy: 承認済みfixture、入力、依存だけを使用する。

発火制御:
- 指定部品だけを使用する。
- trusted scopeとManifestにないコード、入力、コマンドを実行しない。
- WSL実機Gateが必要ならWindows側を正本としてcommit/push後、AI委譲済みのwsl.exe + git pull --ff-onlyで同期する。force/reset/コピーは禁止する。

入力:
- P3-D04〜P3-D10
- RUN-P3-GOLD-001, RUN-P3-STR-001, RUN-P3-BT-001, RUN-P3-BIAS-001, RUN-P3-POC-001
- scripts/quality_gate/trusted_scopes.json
- E:\strategy_test_data\phase3\（承認済み入力のみ）

タスク:
Phase 3のGolden、Replay、Manifest、Bias、Cost/Roll/Gap、PoCを統合検証してください。

作業:
1. GT-TUR-001〜012、Look-ahead、fixture hash、Manifest tamper、Replay一致を検証する。
2. 原典System 1/2と比較候補を同一入力・同一cost条件で実行する。
3. holdout漏洩、未来roll、survivorship、結果後の設定変更を拒否する。
4. 実データ期間が不足する場合、契約検証PASSと頑健性UNKNOWNを分離する。
5. 全RunのHEAD、target hash、fixture/data hash、tool版、execution IDを照合する。
6. P3-D07〜P3-D10を最終実測へ更新する。

レビュー:
- A150が証跡と最終コードのrevision一致を確認する。
- A160が利益を良く見せる漏洩、楽観約定、Unknown隠しを監査する。
- A30/A40がStrategyとengine結果の意味論一致を確認する。

完了条件:
- 再現性・Golden・Bias GateのPass/Fail/Unknownが明確。
- UNK-P3-01が残る場合、Phase 3完了に与える影響を明記する。
- stale証跡を最終PASSに使わない。
```

### P3-11 統合レビュー・レッドチーム監査

```text
ステップID: P3-11
ロール: Phase 3統合レビュー・レッドチーム監査者
使用オーケストレータ完全名: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-11
- output_root: doc/phase3/09_統合レビュー/
- log_root: plan/phase3/ログ/
- detail_boundary: 要件、設計、コード、テスト、証跡、Unknown、Phase 4境界を横断監査する。
- human_gate_policy: 指摘採否はH3-3で人が承認する。Critical/Highを承認だけで無効化しない。

発火制御:
- 指定部品だけを使用する。
- Findings firstで重大度、証拠、影響、修正方針を記録する。
- 問題内容と修正方針の同じ欄に中学生向け説明を併記する。

入力:
- P3-D01〜P3-D10
- src/autotrade/strategy/, src/autotrade/backtest/
- tests/strategy/, tests/backtest/
- tests/evidence/phase3/
- doc/00_全Phase残課題Blocked統合台帳.html

タスク:
Phase 3の統合レビューとレッドチーム監査を実施してください。

作業:
1. 要件追跡、責務境界、Golden、Replay、Bias、Manifest、PoCを横断する。
2. Look-ahead、data snooping、survivorship、楽観約定、roll二重計上、stale証跡を攻撃的に確認する。
3. StrategyがRisk/OMS/Brokerを持たないか確認する。
4. 外部engine固有型、Secret、可変時刻、未固定依存の漏出を確認する。
5. OD-02、長期データ、実測cost、CalendarのUnknownを合格扱いしていないか確認する。
6. P3-D11/P3-D12を作成し、全Findingを総合台帳へ根本原因で統合する。

レビュー:
- A90が全体整合性、A150がコード品質、A160が取引安全、A30/A40がStrategy/PoCを独立判定する。

完了条件:
- Critical/High/Medium/Low、採否、修正条件、証拠先が明確。
- H3-3で承認すべき事項が日本語で具体的に示される。
- P3-D11/P3-D12がdoc/index.htmlから到達できる。
```

### P3-12 レビュー反映・完了判定・Phase 4引継ぎ

```text
ステップID: P3-12
ロール: Phase 3修正統合・完了判定者
使用オーケストレータ完全名: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_revision_integration_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_orchestration_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_doc_set_writer_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-12
- output_root: doc/phase3/10_完了判定/
- log_root: plan/phase3/ログ/
- detail_boundary: H3-3採用指摘を反映し、Phase 3完了とPhase 4入力を判定する。
- human_gate_policy: H3-3承認済みを確認し、最終移行はH3-4承認まで行わない。

発火制御:
- 指定部品だけを使用する。
- Critical/High、未解決の完了必須Unknown、証跡revision不一致があれば完了判定をFAIL/BLOCKEDにする。
- 人による承認だけでMachine Gateを省略しない。

入力:
- P3-D01〜P3-D12
- H3-3承認記録
- 全Phase 3コード、テスト、Run証跡
- doc/00_全Phase残課題Blocked統合台帳.html

タスク:
レビュー指摘を反映し、再レビュー、Phase 3完了判定、Phase 4引継ぎを作成してください。

作業:
1. H3-3採用指摘をコード、テスト、設計、証跡へ反映する。
2. A91/A150/A160の再レビューを行いCritical/Highを確認する。
3. Golden、Replay、Bias、cost/roll/gap、PoCの最終Gateを再実行する。
4. OD-02の決定範囲とPhase 4で必要なPaper証拠を明示する。
5. Phase 4へ渡すStrategy/Backtest契約、OrderIntent、Manifest、Unknown、禁止事項を整理する。
6. P3-D13/P3-D14を作成しdoc/index.htmlへ追加する。
7. H3-4の承認対象を、専門用語だけにせず具体的な日本語で示す。
8. 総合台帳全体を点検し、Human Gate、Blocked、Unknown、件数、最新状態、履歴を整合させる。

レビュー:
- A91が詳細設計と最終実装の整合性を確認する。
- A150/A160が最終コードと証跡を再監査する。
- A90/A81が全成果物、リンク、台帳、Phase 4引継ぎを確認する。

完了条件:
- Critical/Highが0件。
- 必須Unknownを合格扱いしていない。
- P3-D13/P3-D14がdoc/index.htmlから到達できる。
- H3-4でユーザーが何を承認すべきか超具体的に説明されている。
```

---

## 11. 計画レビュー結果

### 11.1 ステップ粒度

設計、RED、Strategy実装、Backtest実装、頑健性モデル、engine PoC、統合検証、レビュー、反映を分離した。Golden期待値を実装後に変更できない順序になっている。

### 11.2 Phase境界

Broker、Paper、Live、Secret、Risk最終判定をPhase 3から除外した。Phase 3はOrderIntentとBacktest証拠までを作り、Phase 4へBroker接続と再同期を渡す。

### 11.3 現在の最大Unknown

長期評価データが不足している。P2-12-03の4件と研究用1か月CSVだけでは、55日Channelや本格Walk-forwardの利益・頑健性を証明できない。このため、Golden/Replay契約の実装と、長期実績の評価を別Gateにした。

### 11.4 AI部品

全ステップを既存の汎用AI部品で実行できる。Phase 3専用部品の新設や `default_orchestrator` の変更は不要である。

---

## 12. Phase 3完了条件

Phase 3を完了扱いにするには、少なくとも次を満たす。

1. P3-D01〜P3-D14が作成され、`doc/index.html` から到達できる。
2. GT-TUR-001〜012が固定fixtureでPASSする。
3. Look-ahead、未来roll、holdout漏洩、fixture後出し変更を拒否する。
4. 同一Experiment Manifestで同一順序のSignal、Intent、状態、Backtest結果を再現する。
5. cost、slippage、Gap、Rollを無視した結果を正式結果にできない。
6. StrategyがRisk、OMS、Broker、Secret、外部SDK型を所有しない。
7. 取引エンジンPoCのPass/Fail/UnknownとOD-02の決定範囲が明確である。
8. 長期データ不足時は、Golden/Replay契約のPASSと、利益・頑健性のUNKNOWNを分離する。
9. A91、A150、A160の最終レビューでCritical/Highが0件である。
10. H3-3とH3-4が明示承認される。

H3-4が未承認の場合、Phase 3成果物は研究・検証候補として保持し、Phase 4のBroker / Paper基盤へ引き渡さない。

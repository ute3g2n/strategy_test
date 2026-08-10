# Phase 3 実行計画書

作成日: 2026-08-09  
対象: タートルズ・トレンドフォロー自動売買システム  
対象Phase: Phase 3 Strategy / Backtest基盤  
状態: v1.0 / H3-0、H3-1、H3-1R、H3-2、H3-5承認済み。H3-1R改訂により、v2は履歴として保持し、v3では実M1を連続30本必須・不足M30を停止する。P3-06のStrategy実装・固定4 GateはPASS（2026-08-09）。P3-07R-01〜05でCore範囲を受入可へ更新し、P3-08のRUN-P3-BIAS-001も機械Gate・WSL隔離・独立レビュー・Human Gateを完了した。P3-08Aはユーザーの追加待機指示後、公式LEAN固定digest、artifact hash、ライセンス、network none/read-onlyのLocal preflight、固定4 Gate、レビューを完了してPASS。P3-09は実行要求を受領したが、専用実行入口・Run Manifest・LEAN/Core parity期待出力が未確定のためBLOCKED。Broker、Paper、Liveは対象外のままとする。

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
| DEC-P3-09 | Phase 3のPoCはローカルBacktest適合と候補選定までを評価し、Broker Paper接続とOD-02最終決定はPhase 4へ送る。この境界はH3-2で承認済みである。 | D12の全PoC証拠にはPhase 4項目が含まれるため。 |
| DEC-P3-10 | Critical / High、Unknown、Manifest不一致、未来情報混入、再現不一致がある場合はPhase 3を完了扱いにしない。 | 安全側に停止するため。 |
| DEC-P3-11 | 1分足を正本入力とし、15分・30分・1時間・4時間・日足は版管理した決定的なTimeframe Aggregatorで生成する。LEAN内蔵集約を使う場合も同じfixtureに対する出力一致を必須にする。 | engineを交換しても時間足の意味とManifestを変えないため。 |
| DEC-P3-12 | 4時間足と日足は単純なUTC固定分割にせず、固定Calendar、取引セッション、時間帯、夏冬時間規則で区切る。同時に複数足が確定した場合の配信順も固定する。 | 取引所時間と未来情報の誤りを防ぐため。 |
| DEC-P3-13 | Strategyの今回判断用Channel Viewと、現在足を取り込んだ次回用Indicator Stateを別型にする。 | 現在足をDonchian窓へ先に混ぜるLook-aheadを構造的に防ぐため。 |
| DEC-P3-15 | LEANを主PoC候補とする。LEANが固定合格条件を満たせない場合だけ、失敗証跡を残してNautilusTraderへ縮退する。 | 2候補を無条件に二重実装せず、比較可能性と撤退経路を両立するため。 |
| DEC-P3-14 | 30分足（M30）を追加する。M30は15分足を連結せず、固定Calendarのsession anchorから数えた連続30本の確定1分足を直接集約して作る。 | 途中の15分足を二重に使うと、欠損・復元・丸めの扱いが実装ごとに分かれるため。 |

### H3-2承認後の取引エンジン方針とPoC合格条件

ユーザーは2026-08-09に、提案した方針によりH3-2を承認した。Phase 3では **LEANを主PoC候補** とし、NautilusTraderはLEANが下記の合格条件を満たせない場合の比較・代替候補として残す。これは「LEANを本番で最終採用する」決定ではない。OD-02の最終決定は、Phase 3のPoC結果とPhase 4のPaper接続・再同期の証拠を確認してから行う。

| ID | PoC合格条件 | 設計を固定するまで | 実装・単体検証を終えるまで | LEAN PoCとして実証するまで | Phase 4へ送る部分 |
|---|---|---|---|---|---|
| P3-AC-01 | 1分足から15分・30分・1時間・4時間・日足を決定的に作れる | P3-04、P3-05、P3-05R | P3-07R | P3-09、P3-10（原則LEAN、縮退時はNautilusTrader） | 取引所別の実運用Calendar確認 |
| P3-AC-02 | 未完成の上位時間足をStrategyへ渡さず、未来を見ない | P3-03〜P3-05、P3-05R | P3-06、P3-07R | P3-09、P3-10 | なし（Phase 3完了必須） |
| P3-AC-03 | セッション境界・夏冬時間・同時closeの順序が正しい | P3-04、P3-05、P3-05R | P3-07R、P3-08 | P3-09、P3-10 | 実取引所の正式Calendarと運用変更追随 |
| P3-AC-04 | 同じManifestから同じSignal / Intentを再現できる | P3-04、P3-05、P3-05R | P3-07R | P3-09、P3-10 | なし（Phase 3完了必須） |
| P3-AC-05 | 取引エンジン固有型をCoreへ漏らさないAdapter境界 | P3-03、P3-04 | P3-06、P3-07R | P3-09、P3-11 | Broker Adapterとの接続 |
| P3-AC-06 | 固定ローカル入力だけで、外部通信なしに再実行できる | P3-04、P3-05 | P3-07R、P3-08A | P3-09、P3-10 | Paper環境での別途隔離確認 |
| P3-AC-07 | 3〜5市場を現実的な時間で処理できる | P3-04、P3-05 | P3-07Rで計測口と証跡拒否を実装 | P3-09、P3-10 | 20〜40市場のPaper負荷・連続運用はPhase 4 |
| P3-AC-08 | Python戦略のGolden、snapshot復元、Look-ahead防止が成立する | P3-05、H3-1、P3-05R、H3-1R | P3-06、P3-07R | P3-09、P3-10 | なし（Phase 3完了必須） |

やさしい説明: P3-03〜P3-05で「何を正解にするか」を先に決めます。P3-06〜P3-08で自作部分を作り、P3-08AでLEANの版と中身を固定します。P3-09でLEANに同じ問題を解かせ、P3-10で全部の答えが矛盾しないか確認します。20〜40市場を何日も動かす試験と実際の取引所につなぐ試験は、Paper取引を扱うPhase 4の仕事です。

---

## 5. 後続Phaseへ送る項目

| ID | 項目 | 送り先 | Phase 3での扱い |
|---|---|---|---|
| P3-DEFER-01 | IBKR Paper接続、部分約定の実Broker意味論、Open Order / Fill / Position再同期 | Phase 4 | PortとPoC期待値だけを固定する。 |
| P3-DEFER-02 | 1NのLive用金額、証拠金、最小数量、4/6/10/12 Unitの最終Risk判定 | Phase 4/5 | Strategyは計算根拠とHintを出すが、注文可否を決めない。 |
| P3-DEFER-03 | Shadow / Paperの運用日数、通知サービス、クラウドVM | Phase 5/6 | 測定項目とHealthEventだけを定義する。 |
| P3-DEFER-04 | Live向けSecret、Kill Switch、Broker-native Stop、復旧Runbook | Phase 4〜7 | BacktestにSecretや実注文能力を持ち込まない。 |
| P3-DEFER-05 | 長期実績に基づくパラメータ採用、資金配分、利益目標 | 後続の研究・承認Gate | Phase 3ではルール再現性とBias防止を優先し、短期データから採用判断しない。 |
| P3-DEFER-06 | 実取引所Calendarの継続追随、Broker Adapter接続、Paper隔離再実行、20〜40市場の連続負荷運用 | Phase 4 | Phase 3では固定Calendar、engine非依存Adapter、完全オフライン、3〜5市場性能を必ず検証し、実環境でしか確認できない部分だけを送る。 |

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
| 時間足集約実装 | `src/autotrade/backtest/timeframe/` またはP3-D05で確定した同等配置 | engine非依存。1分足から15分・30分・1時間・4時間・日足を決定的に生成する。 |
| 取引エンジンAdapter | `src/autotrade/backtest/engine_adapters/` またはP3-D05で確定した同等配置 | CoreはProtocolだけを参照し、LEAN/Nautilus固有型を外へ出さない。 |
| 時間足・Calendarテスト | `tests/backtest/timeframe/` | DST、セッション、同時close、未完成bar、欠損1分足を固定fixtureで検証する。 |
| LEANオフライン準備証跡 | `tests/evidence/phase3/RUN-P3-LEAN-PREP-001/` | 公式配布元、版、image/package digest、ライセンス、取得時通信、オフライン再実行条件を保存する。 |

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
| UNK-P3-01 | 55日Channel、Holdout、Walk-forwardに足る履歴期間と市場数がまだない。H3-2で利用許可は得たが、十分なデータの存在・品質は未確認。 | P3-08, P3-10 | P3-10 | Golden、固定Calendar、5市場×2暦年synthetic Replayは進め、実データの利益・頑健性を合格扱いしない。 |
| UNK-P3-02 | Golden fixture形式、Decimal精度、丸め、許容差、最小ケース数。 | P3-03, P3-05 | 解決済み（H3-1、2026-08-09） | H3-1で承認済みの値を使う。30分足追加によるfixture/hash変更はP3-05R後のH3-1Rで再承認するまで実装しない。 |
| UNK-P3-03 | LEANの固定版、ライセンス、ローカル実行方式、image/package完全hash。NautilusTraderは縮退時だけ同様に固定する。 | P3-02, P3-08A | P3-08A完了時 | 完全hashとオフライン再実行条件を固定できるまでP3-09を開始しない。 |
| UNK-P3-04 | OD-02の決定時期。 | P3-02, H3-2 | 解決済み | Phase 3はローカルPoC候補選定まで、最終決定はPhase 4のPaper接続・再同期証拠後とする。 |
| UNK-P3-05 | 市場別手数料、スリッページ、Gap約定の実測値。 | P3-04, P3-08 | P3-10 | 保守的な明示設定で比較し、実値や利益保証と呼ばない。 |
| UNK-P3-06 | 1NのLive用金額、証拠金、最小数量、Risk最終値。 | P3-03, P3-11 | Phase 4/5 | StrategyはSignalとUnit Hintまでに限定し、注文可否を決めない。 |
| UNK-P3-07 | 取引時間、休日、セッション境界の正式Calendar。 | P3-04, P3-08 | P3-10 | 固定テストCalendarだけで検証し、Live適合を主張しない。 |
| UNK-P3-08 | 原典版と比較候補で固定するパラメータ集合、学習区間、検証区間。 | P3-01, P3-05, P3-10 | 解決済み（H3-1、2026-08-09） | 承認済みfixtureで比較し、結果を見て候補を増減しない。30分足に伴うfixture/hash変更はH3-1Rで再承認する。 |
| UNK-P3-09 | 原典の日中突破を、確定1分足または確定15分足のどちらで近似するか。どちらも原典そのものではなく、近似方式として名前を分ける。 | P3-03, P3-05 | 解決済み（H3-1、2026-08-09） | 承認済みの `M15_CLOSE_CONFIRMED_V1` を使う。30分足は日中突破の近似方式を変えず、時間足入力を増やすだけとする。 |

---

## 8. 人による承認

| Gate | タイミング | 承認してもらう内容 | 未承認時 |
|---|---|---|---|
| H3-0 | P3-01完了後 | Phase 3の対象、非対象、Strategy候補、成果物、Unknown、Phase 4への境界。 | P3-02の読取調査だけ可能。詳細設計・実装を開始しない。 |
| H3-1 | 承認済み（2026-08-09） | Golden fixture、時間足・Calendar fixture、期待出力、hash、丸め、同時close順序、TargetPosition、日中突破の `M15_CLOSE_CONFIRMED_V1` 近似、Look-ahead/Biasテスト、3〜5市場性能fixtureと合格値、変更規則を凍結する。 | `RES-P3-H3-1`。30分足を追加するため、P3-05Rで変わるfixture/hashはH3-1Rで再承認するまで本実装へ使わない。 |
| H3-1R | 承認済み（2026-08-09） | 30分足を含む改訂fixture、期待OHLCV、session境界、同時close順、Manifest/timeframe rule版、新hash、追加REDテストを凍結する。改訂承認により、v2は履歴として保持し、v3では実M1を連続30本必須・不足M30を停止する。 | `RES-P3-H3-1R-REVISION`。P3-06/P3-07はv3を正本として実装・GREEN化する。既存15分〜日足の承認済み範囲は変更しない。 |
| H3-2 | 承認済み（2026-08-09） | LEANを主PoC候補として、固定版・hash・公式配布元をP3-09開始前に証跡化して導入する。必要な長期履歴は `E:\strategy_test_data\phase3\datasets\` に限る。OD-02はPhase 3では候補選定まで、最終決定はPhase 4のPaper証拠後とする。 | Broker、Secret、実注文、Live運用は引き続き許可しない。固定版・hashを記録できない導入は行わない。 |
| H3-3 | P3-11完了後 | 統合レビューとレッドチーム指摘の採否、残Unknownの送り先。 | P3-12の完了判定へ進めない。 |
| H3-4 | P3-12完了後 | Phase 3完了、Backtest結果の利用範囲、Phase 4 Broker / Paper基盤への移行。 | Phase 4へ進めない。 |

H3-2は外部データや外部依存を使う許可であり、Secret投入、Broker接続、実注文、Live運用の許可ではない。

---

## 9. 実行DAG

| グループ | ステップ | 並列 | 依存 |
|---|---|---|---|
| G0 | P3-01 | 不可 | H2-4、本計画書 |
| G1 | P3-02 | 不可 | P3-01。読取調査はH3-0前でも可能、依存導入は不可。 |
| G2 | P3-03 | 不可 | H3-0、P3-01、P3-02の調査結果 |
| G3 | P3-04 | 不可 | P3-03、P3-D04 |
| G4 | P3-05 | 不可 | P3-03、P3-04 |
| G5 | H3-1 | 不可 | P3-05。Golden、時間足、Calendar、性能fixtureと期待値を凍結する。 |
| G6 | P3-05R | 不可 | H3-1。30分足の設計・RED固定を行う。 |
| G7 | H3-1R | 不可 | P3-05R。30分足の改訂fixture/hashを再承認する。 |
| G8 | P3-06 | 不可 | H3-1、H3-1R、P3-05、P3-05R |
| G9 | P3-07 | 可能（Core範囲） | P3-07R-05、固定4 Gate PASS、WSL隔離、fixture hash一致、Human Gate承認。実エンジン接続・正式性能は後続範囲。 |
| G9R | P3-07R-01〜05 | 完了 | P3-07差戻し、P3-D05/P3-D06/P3-D08、H3-1/H3-1R/H3-2承認済み。RUN-P3-BT-001を登録入口で再実行し、固定4 GateとHuman Gateを完了。 |
| G10 | P3-08 | 完了・受入済み | RUN-P3-BIAS-001のWSL隔離、fixture hash、formatter/lint/type/testの固定4 Gate、独立レビュー、H3-5 Human Gate承認を確認。P3-08Aを開始し、P3-09はP3-08A完了まで開始しない。 |
| G11 | P3-08A | 完了・受入済み | H3-2、P3-02、P3-04、P3-05R、P3-08。`RUN-P3-LEAN-PREP-001`の固定digest、artifact hash、LICENSE、network none/read-only Local preflight、固定4 Gate、レビューを確認。P3-09は別Gateで実行する。 |
| G12 | P3-09 | BLOCKED（2026-08-10） | P3-08AはPASS。ただしP3-09専用実行入口、Run Manifest、LEAN/Core parity期待出力が未確定で、trusted scopeは`execution_allowed=false`。実engineは未起動。 |
| G13 | P3-10 | 不可 | P3-03〜P3-09。長期データ不足時は利益・頑健性だけUNKNOWNとし、P3-AC-01〜08のPhase 3範囲は省略しない。 |
| G14 | P3-11 | 不可 | P3-01〜P3-10 |
| G15 | P3-12 | 不可 | H3-3、P3-11 |

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
- acceptance_conditions: P3-AC-02, P3-AC-05, P3-AC-08

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
15分・1時間・4時間・日足を同時利用でき、未完成barやengine固有型を受け取らないStrategy / Turtleを、実装者が判断を補わず実装できる詳細設計へ更新してください。

作業:
1. ファイル構成、型付きAPI、状態、snapshot、reason code、例外を定義する。
2. True Range、N、Donchian、System 1/2 Entry/Exit、勝ちブレイクフィルター、0.5N追加、2N Stopを時系列順に定義する。
3. Decimal精度、丸め、warmup、確定バー、同時刻イベント順を固定する。
4. Strategy Configに原典版と比較候補を分離し、銘柄別後付け最適化を禁止する。
5. OrderIntent/TargetPosition、StrategyState、StrategySnapshot、Healthの全フィールドを定義する。
6. Risk/OMS/Broker/約定/現在時刻/外部I/OをStrategyから排除する。
7. GT-TUR-001〜012と追加異常系を全テスト表へ対応させる。
8. AF-D14/16の構成、日本語説明、Mermaid図、受渡し表を満たすP3-D04を作る。
9. Strategyが参照できる時間足をConfigで明示し、各barの`timeframe`、`bar_open_time`、`bar_close_time`、`is_closed`、Calendar版を必須入力にする。未完成barは型境界または入力検証で拒否する。
10. 同一時刻に15分・1時間・4時間・日足が確定した場合、全ての確定barをViewへ反映した後にStrategy判断を一回だけ行う契約を定義する。
11. snapshotへ時間足別warmup、直近確定時刻、indicator状態を保存し、復元直後の重複Signalと欠落Signalを禁止する。
12. Strategy、Signal、Intent、snapshot、fixtureの公開型にLEAN、QuantConnect、NautilusTrader固有型やIDを含めない。

レビュー:
- A91が型、時系列、例外、全テスト、実装可能性をFindings firstで確認する。
- A30が原典ルールとLook-aheadを確認する。
- A90がRisk/OMS責務混入とBacktest専用化を監査する。
- A20とA90が、engine Adapterを交換してもStrategy APIが変わらないことを確認する。担当一覧にないA40はこのStepでは発火しない。

完了条件:
- A91再レビューでCritical/Highが0件。
- UNK-P3-02/06/08が明示され、未決値をPassにしていない。
- P3-D04がdoc/index.htmlから到達できる。
- P3-AC-02/05/08について、入力型、停止条件、全テストケース、P3-04/P3-05への受渡しが実装可能な粒度で定義される。
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
- human_gate_policy: H3-0/H3-2承認済みを確認する。このステップでは外部engineをまだ導入せず、engine非依存契約だけを設計する。
- acceptance_conditions: P3-AC-01〜P3-AC-07

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
決定的な複数時間足生成、Calendar、Backtest、Experiment Manifest、engine Adapter、性能計測の実装詳細設計を作成してください。

作業:
1. MarketEvent順序、clock、queue、Strategy呼出し、状態保存、結果確定の処理順を定義する。
2. FillModel、CostModel、SlippageModel、GapModel、RollPnLModelをPortとして分離する。
3. 同一時刻、Gap、Stop飛越し、価格上限下限、欠損、roll境界の保守的規則を定義する。
4. Experiment Manifestへdata_version、fixture/data hash、Catalog、Strategy Config、engine版、cost設定、分割、code revisionを束縛する。
5. Holdout/Walk-forwardの期間分割、学習/検証情報のアクセス禁止を定義する。
6. Eドライブの大容量出力とGit管理証跡の境界を定義する。
7. Nautilus/LEAN AdapterをCoreから分離し、外部型をStrategyへ漏らさない。
8. 全テスト表、Mermaid構造/処理図、異常系、復旧、監査を含むP3-D05を作る。
9. 1分足を正本入力として、15分・1時間・4時間・日足を生成する`TimeframeAggregator`の型、状態、API、Decimal規則、欠損時停止、重複拒否、snapshot/restoreを定義する。
10. 4時間足・日足の開始位置を固定Calendarのsession anchorで決める。UTC固定分割を禁止し、米国夏冬時間の切替、休日、短縮日、日次休場をfixtureで表現する。
11. 同一close時刻は「1分足確定→15分→1時間→4時間→日足の順にView更新→Strategy判断を一回」の順序へ固定し、並び順をManifest材料に含める。
12. 未完成barはStrategyへ渡さず、終了時に残った端数barは明示的に破棄するか`PARTIAL_BAR_REJECTED`で停止する。どちらを採用するかを設計とテストで一意にする。
13. `EngineAdapter` Protocolを定義し、入力をproject共通MarketEvent/Manifest、出力を共通Signal/Intent/Resultへ限定する。LEAN/Nautilus固有型、暗黙clock、固有IDをCoreへ出さない。
14. Experiment Manifestへtimeframe rule版、Calendar版/hash、同時close順序版、Adapter版、engine版/digest、入力hash、性能fixture hashを束縛する。
15. P3-AC-07の固定性能試験を「5市場×2暦年のsynthetic 1分足、4種の派生足、Strategy Replay、同一端末で初回と再実行、30分以内、peak RSS 8GiB以下」と定義する。端末情報、CPU、RAM、OS、実測時間、peak RSSを証跡化する。
16. 外部通信なしを機械確認するpreflight/postflight、ローカル入力限定、Eドライブ保存先、オフライン再実行の設計を定義する。

レビュー:
- A91が実装可能性、永続化、例外、全テストを確認する。
- A40がengine非依存CoreとPoC接続を確認する。
- A70/A90が未来情報、Manifest改ざん、外部I/O、危険な理想約定を監査する。
- A30が複数時間足のStrategy判断時点、A40がLEAN Adapterと性能試験の実装可能性を確認する。

完了条件:
- A91再レビューでCritical/Highが0件。
- UNK-P3-01/03/05/07が明示される。
- P3-D05がdoc/index.htmlから到達できる。
- P3-AC-01〜07の全項目について、正常系、異常系、証跡、Pass/Fail判定が全テスト表へ一対一で割り当てられる。
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
- acceptance_conditions: P3-AC-01〜P3-AC-08

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
Golden、複数時間足、Calendar、Replay、Bias、Manifest、Adapter境界、オフライン、性能のfixtureとREDテストを先に作成してください。

作業:
1. GT-TUR-001〜012を実装可能なJSON fixtureへ固定する。
2. TR/N/Donchian、Entry/Exit、勝ちブレイク、0.5N追加、2N Stop、snapshot/restoreを覆う。
3. 未確定バー、未来roll、holdout参照、現在時刻、fixture後出し変更を拒否する。
4. Backtestの同時刻順序、Gap保守約定、cost、roll、Manifest改ざん、再ReplayをRED化する。
5. fixture schema、Decimal表現、期待Signal/Intent/State、hashを証跡へ固定する。
6. RUN-P3-GOLD-001のtarget_paths、固定4 Gate、Manifest、証跡先をtrusted scopeへ登録する。
7. P3-D06を作成し、RED/GREEN内訳と未実装境界を記録する。
8. 1分足から15分・1時間・4時間・日足へ変換する固定入力と、各OHLCV、開始・終了時刻、件数、hashの期待値を作る。同一入力の二回実行でbyte同一になることを要求する。
9. 未完成15分/1時間/4時間/日足、入力欠損、重複、時刻逆行、セッション外、Calendar不一致を拒否するREDを作る。
10. 米国夏時間開始日・終了日、通常日、休日、短縮日、日次休場を含むCalendar fixtureを作り、4時間足と日足のsession anchorを固定する。
11. 同一時刻に複数時間足がcloseするfixtureを作り、全View更新後にStrategyが一回だけ呼ばれ、Signal/Intentが重複しない期待値を固定する。
12. 同一Manifestの二回実行一致と、timeframe rule、Calendar、順序版、engine digest、Adapter版、code revisionのどれか一つを変えた場合のManifest/DataVersion差をRED化する。
13. LEAN固有型・IDをCore公開APIへ渡す実装、ネットワーク有効状態、未固定依存、ローカル外入力、可変現在時刻を拒否する境界テストを作る。
14. P3-AC-07用に5市場×2暦年の決定的synthetic 1分足生成器と期待件数/hashを固定し、30分・8GiBの合格値、端末情報記録schemaをH3-1承認対象へ含める。
15. P3-AC-01〜08それぞれに、テストID、fixture、期待結果、証跡キー、実装担当Stepを割り当てた合格条件追跡表をP3-D06へ作る。未割当が1件でもあればP3-05を未完了とする。

レビュー:
- A150がテスト漏れ、脆いassert、可変時刻、外部I/Oを確認する。
- A160がLook-ahead、data snooping、未知値の合格扱い、理想約定を監査する。
- 問題内容と修正方針へ中学生向け説明を併記する。

完了条件:
- 固定fixture、期待値、hash、変更規則がH3-1の承認材料として明確。
- 未実装APIはRED、既存MarketEvent契約はGREENとして区別される。
- Golden testを利益評価に使っていない。
- P3-AC-01〜08のPhase 3範囲すべてにREDまたは既存GREENテストがあり、H3-1で凍結すべきhashと期待値が欠けていない。
```

### P3-05R 30分足追加計画・設計改訂・RED再凍結

```text
ステップID: P3-05R
ロール: 複数時間足の設計改訂・Golden再凍結責任者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1, AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_domain_modeling_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_python_code_review_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-05R
- output_root: doc/phase3/01_要件追跡/, doc/phase3/03_Strategy詳細設計/, doc/phase3/04_Backtest詳細設計/, doc/phase3/05_テスト設計/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-M30-001
- detail_boundary: 30分足（M30）を既存の15分・1時間・4時間・日足と同じ確定足として追加する。1分足からの決定的集約、Strategy入力、Calendar、Snapshot、Manifest、Golden/Biasテスト、品質Gate、証跡までを改訂する。Risk、OMS、Broker、実engine、利益採用判断は対象外。
- human_gate_policy: H3-1は2026-08-09に承認済み。ただしM30追加でfixture/hash/期待値を変更するため、P3-05R完了後のH3-1R再承認前にM30の本実装・GREEN化を開始しない。
- acceptance_conditions: P3-AC-01, P3-AC-02, P3-AC-03, P3-AC-04, P3-AC-08

発火制御:
- 指定した完全名のAI部品だけを使用する。存在しない部品は代替せず報告して停止する。
- `default_orchestrator` は変更しない。Phase 1専用部品は読取専用とし、実行部品として起動しない。
- 既にH3-1で承認されたv1 fixtureを上書きしない。M30用はv2 fixture・別Run・別hashとして追加し、旧証跡は履歴として残す。
- 外部接続、実市場データ、Broker、Secret、実engine、可変な現在時刻を使わない。
- 30分足は15分足を二つ結合して作らない。固定Calendarのsession anchorから連続した確定1分足30本を直接集約し、1本でも欠ける、重複する、時刻が逆行する、範囲外ならM30を作らずfail-closedで止める。

入力:
- plan/Phase3_実行計画書_v0.1_2026-08-09.md
- doc/phase3/03_Strategy詳細設計/03_Strategy_Turtle実装詳細設計書.html（P3-D04）
- doc/phase3/04_Backtest詳細設計/04_Backtest_Experiment実装詳細設計書.html（P3-D05）
- doc/phase3/05_テスト設計/05_Golden_Biasテスト設計書.html（P3-D06）
- doc/phase3/01_要件追跡/01_Phase3要件追跡マトリクス.html（P3-D02）
- tests/fixtures/strategy/turtle_golden_v1.json
- tests/fixtures/strategy/multi_timeframe_v1.json
- tests/fixtures/phase3/run_p3_gold_fixture_manifest.json
- tests/strategy/, tests/backtest/, scripts/quality_gate/, scripts/quality_gate/trusted_scopes.json
- src/autotrade/market_data/store_contracts.py, src/autotrade/market_data/quality.py
- tests/evidence/phase3/RUN-P3-GOLD-001/
- doc/00_全Phase残課題Blocked統合台帳.html

タスク:
既存のP3-05までで凍結した15分・1時間・4時間・日足の意味を壊さず、30分足をM30として追加してください。P3-D02/P3-D04/P3-D05/P3-D06、fixture、REDテスト、trusted scope、証跡、Phase 3実行計画、doc/index、総合台帳を同じ改訂版へそろえ、H3-1Rで人が確認できる材料を作ってください。

作業:
1. 現状棚卸しを行う。Phase 2の`MarketEvent`は1分足の事実を運ぶ型であり、timeframeを増やして破壊しない。P3の`Timeframe`、`ClosedBarView`、`ClosedBarBatch`、`StrategyConfig`、`IndicatorState`、Snapshot、Timeframe Aggregator、Experiment Manifest、Result、既存fixture/testのどこを変更するかを表にする。
2. M30の意味を固定する。時間区間はCalendarのsession anchorからの半開区間`[open, close)`、30本すべてが確定済み、`bar_open_time_utc < bar_close_time_utc`、OHLCVは1分足列から直接算出する。open=最初、high=最大、low=最小、close=最後、volume=合計とする。DST、休日、短縮日、日次休場、session終端の端数は固定Calendarで判断し、端数は`PARTIAL_BAR_REJECTED`としてStrategyへ渡さない。
3. 同時close順を`M1 → M15 → M30 → H1 → H4 → D1`へ改訂し、同じDecisionPointでは全ての該当Viewを更新してからStrategyを一回だけ呼ぶ。M30が無効なConfig、未完成、未来、重複競合、Calendar版不一致、Snapshot文脈不一致はSignal/Directive 0件・停止にする。
4. P3-D04を改訂する。`Timeframe`、enabled/trigger/indicator/entry/exit binding、Batch正規順、warmup、State、Snapshot、reason code、公開DTO、Mermaid図、全テスト表へM30を明記する。M30を使うかはConfigで明示し、指定しない戦略の既存M15/H1/H4/D1挙動は変えない。
5. P3-D05を改訂する。`TimeframeAggregator`、`PartialBarState`、`AggregatorSnapshot`、Replay order、Calendar、Manifestの`timeframe_rule_version`、Performance/Result/Snapshotのhash材料、正常・異常の擬似コード、BT表へM30を明記する。M30の出力をM15出力から導出する実装、端数の黙殺、同bar新規約定、未来Calendar/Rollの利用は禁止する。
6. P3-D06と新規v2 fixtureを作る。既存v1を保持したまま、M30 normal、M30+M15、M30+H1、M30+H1+H4+D1の同時close、欠損1分、重複、時刻逆行、DST、短縮日端数、休日、復元、Manifest/timeframe rule差替えを固定する。GT-TUR-036〜040、BT-038〜042を追加し、全ケースで入力・操作・期待値・合否・証跡を表にする。
7. `RUN-P3-M30-001`をtarget-only scopeとして登録する。対象はP3の設計/fixture/テスト/品質Gateだけとし、親Manifestで全v2子fixtureのhashを束縛する。formatter、lint、mypy、固定P3 pytestを4 Gateとして設計する。H3-1R未承認の間はscopeをBLOCKEDにし、REDを品質GateのPASSと呼ばない。
8. v2 REDを先に実行して通常失敗として記録する。既存v1 GREEN/REDの意味を変えない。既存P2 MarketEvent契約はGREENのまま分離して確認し、未実装のStrategy/Backtest APIだけをREDとして記録する。
9. A90/A91/A150/A160の指摘を、問題内容と修正方針の直下に中学生でも分かる説明を付けて記録する。Critical/Highを0件にしてからP3-05Rを完了扱いにする。
10. P3-D02のP3-AC-01〜04/08、timeframe前提、test/Run追跡表をM30へ更新する。`doc/index.html`、Phase 3実行計画、総合台帳、P3-05R実行ログを全件確認して更新する。H3-1は承認済みとして履歴を残し、M30改訂分だけをH3-1R承認待ちとして登録する。既存の残課題と同じ根本原因なら新しい残課題行を増やさない。

レビュー:
- A20がMarketEventとP3の時間足DTOの責務分離、M30の直接集約、Catalog/Calendar版の意味を確認する。
- A30がM30を含む同時close一回判断、Strategyのwarmup、Look-ahead、Golden期待値を確認する。
- A82/A91がP3-D04/P3-D05を、型、永続化、復元、擬似コード、全テスト表まで実装可能な粒度で確認する。
- A90が時間順・DST・端数・DecisionPointの横断整合を確認する。
- A150がfixture hash、Pythonテスト、skip/xfail、可変時刻、外部I/Oを確認する。
- A160が未来情報、欠損/重複の通過、端数barの黙殺、M30を使った有利な仮想約定を監査する。

完了条件:
- M30の生成規則、Calendar境界、OHLCV、同時close順、Snapshot/Manifest hash材料、停止コードがP3-D04/P3-D05に一意に定義されている。
- GT-TUR-036〜040、BT-038〜042を含むv2 fixture/hashと通常REDが存在し、旧v1 fixture/hashは変更されていない。
- H3-1Rで承認してもらう項目と、承認前に開始してはいけないM30実装範囲がP3-D06と総合台帳で日本語で分かる。
- P3-AC-01〜04/08のM30追加分が追跡表へ割り当てられ、Critical/Highが0件、P3-D04/P3-D05/P3-D06がdoc/index.htmlから到達できる。
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
- human_gate_policy: H3-1承認済みfixture hashと、P3-05R後にH3-1Rで再承認したM30 fixture hashを確認する。
- acceptance_conditions: P3-AC-02, P3-AC-05, P3-AC-08

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
8. 15分・30分・1時間・4時間・日足の確定済みViewを同時に参照できるStrategy入力を実装し、`is_closed=false`、未知timeframe、Calendar版不一致をfail-closedで拒否する。M30をConfigで無効にした場合は、既存時間足の意味を変えない。
9. 同一close時刻で複数時間足が更新されても、Backtest Coreが発行する一つの判断点につきStrategy判断を一回だけ行い、`M1 → M15 → M30 → H1 → H4 → D1`の全View更新後に重複Signal/Intentを生成しない。
10. 時間足別warmup、最終確定時刻、indicator状態をsnapshotへ保存し、復元前後でSignal/Intent/Stateの順序付き系列を一致させる。
11. 公開API、例外、証跡、snapshotを静的検査し、LEAN/QuantConnect/NautilusTraderのimport、型、ID、文字列表現がStrategy Coreへ漏れていないことを証明する。
12. `RUN-P3-STR-001`のtarget_paths、固定4 Gate、fixture hash、Manifest、証跡先をtrusted scopeへ登録してから実行する。

レビュー:
- A150がPython品質、型、純粋性、保守性を確認する。
- A160がLook-ahead、隠れ状態、Unknown通過、Signal責務を監査する。
- A30が原典ルールとGolden一致を確認する。

完了条件:
- GT-TUR-001〜012がGREEN。
- 同一入力でSignal/Intent/Stateが一致する。
- Critical/Highが0件で、P3-D07がdoc/index.htmlから到達できる。
- P3-AC-02/05/08の全凍結テストがGREENで、未完成bar、未来bar、復元重複、engine型漏出のいずれも通過しない。
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
- detail_boundary: 決定的な複数時間足生成、Event replay、Strategy接続、Manifest、EngineAdapter Port、最小仮想約定。外部engine SDKはP3-08Aまで使わない。
- human_gate_policy: H3-1承認済みと、P3-05R後のH3-1RでM30 fixture/hashが再承認済みであることを確認する。
- acceptance_conditions: P3-AC-01〜P3-AC-08

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
決定的なTimeframe Aggregator、Calendar、Backtest Core、EngineAdapter Port、Experiment Manifest、性能計測口を最小実装してください。

作業:
1. Event queue、simulated clock、Strategy lifecycle、結果収集を実装する。
2. data_versionとMarketEvent順序を改変せず入力する。
3. Manifestへ全入力版/hash/config/codeを束縛し、不一致を拒否する。
4. snapshot/restore後も重複Signal/Intentを作らない。
5. 最小Fill Portを実装し、cost/roll/gapの詳細はP3-08へ分離する。
6. 固定GateとA150/A160レビューを通す。
7. P3-D08とRUN-P3-BT-001証跡を作る。
8. 1分足から15分・30分・1時間・4時間・日足を作る純粋な`TimeframeAggregator`を実装し、M30はsession anchorからの確定1分足30本を直接集約する。OHLCV、件数、開始・終了時刻、欠損・重複・逆行、端数barの規則を凍結fixtureどおりにする。
9. 固定Calendarとsession anchorを実装し、通常日、夏時間開始・終了、休日、短縮日、日次休場の4時間足・日足境界を凍結fixtureどおりにする。OSの現在時間帯設定へ依存しない。
10. 同一close時刻では、1分→15分→30分→1時間→4時間→日足をViewへ反映した後にDecisionPointを一回発行する。順序違反や二重DecisionPointを拒否する。
11. `EngineAdapter` Protocol、project共通入力/output DTO、engine変換エラーを実装する。外部engine packageはimportせず、synthetic fake adapterで契約テストをGREENにする。
12. Manifestにtimeframe rule版、Calendar hash、同時close順序版、Adapter版、engine placeholder、性能fixture hashを追加し、値欠落・差替え・再構築不一致を拒否する。
13. ネットワークなし、ローカル入力限定、明示clockのみを検査するpreflight interfaceと、wall time・peak RSS・event件数を記録するperformance recorderを実装する。
14. 5市場×2暦年のsynthetic fixtureで出力hash、Signal/Intent順序を二回一致させる。P3-07では計測値を記録し、正式な30分・8GiB判定はLEANを含むP3-09で行う。
15. `RUN-P3-BT-001`のtarget_paths、固定4 Gate、fixture hash、Manifest、証跡先をtrusted scopeへ登録してから実行する。

レビュー:
- A150が決定性、型、例外、永続化、競合を確認する。
- A160がManifest差替え、未来情報、入力改ざん、理想約定を監査する。
- A40が外部engine Adapter境界を確認する。

完了条件:
- 同一Manifestで同一順序のSignal/Intent/結果になる。
- ManifestやMarketEvent差替えをfail-closedで拒否する。
- Critical/Highが0件。
- P3-AC-01〜08のうちCore/Strategy実装で担当する全テストがGREENで、LEAN実機だけがP3-09の未検証項目として明示される。
```

### P3-07R Backtest Core再実装・再現性修復

P3-07Rは、P3-07の履歴を改変せず、レビュー差戻しを修復するための追加実装計画である。目的は「個別の真偽値を返すテスト用関数」を増やすことではない。Phase 2の`MarketEvent`から、決定的なReplay、Strategy一回呼出し、仮想約定、Snapshot、改ざん検知つきResult公開までを**実際に一本接続**し、同じ入力から同じ監査可能な結果だけを公開することである。

#### P3-07Rの固定境界

- H3-1、H3-1R、H3-2の承認済み内容、既存v1/v2/v3 Golden fixtureのbytes、期待出力、M30の「実M1連続30本」規則を変更しない。修復のために期待値をテスト内で上書き、`skip`/`xfail`化、常時PASSの分岐、自己申告のboolを追加してはならない。
- Broker、Secret、実注文、外部engine SDK、外部ネットワーク、可変現在時刻は対象外である。P3-07RのEngineAdapterは、外部SDKをimportしない共通DTOと`FakeEngineAdapter`までに限る。LEANの取得・固定・実行はP3-08A以降である。
- 大容量の正式Run出力だけを`E:\strategy_test_data\phase3\backtests\runs\`に原子的に公開する。Gitには小型fixture、Manifestの要約/hash、テスト、実行証跡だけを置く。ユーザー決定どおり、バックアップ、暗号化、保存期限、容量上限、専用ACLは追加の合格条件にしない。
- P3-07Rの各工程は、前工程のREDまたはレビュー指摘を消さずに証跡化してからGREENへ進む。設計と凍結済み期待値に矛盾が出た場合だけは、安全に停止し、P3-07をPASSとせずに差分を報告する。

| 修復対象 | P3-07Rでの閉じ方 | 主な完了証跡 |
|---|---|---|
| BLK-P3-008: 実ReplayからResult公開まで未接続 | 型付き`BacktestRunner`を唯一の正本経路にし、Replay→Calendar/集約→Strategy→次bar約定→Snapshot→Commitを実行する。 | 順序違い、重複、改ざん、中断復旧、二回Replayの統合テストとresult hash。 |
| Manifest / fixtureの改ざん検知不足 | strict canonical JSON、全必須hash、親Manifestの固定子集合、独立した期待値oracleを用いる。 | 欠落、未知field、NaN/Infinity、子fixture差替え、hash差替えがSTOPPEDとなるテスト。 |
| ResultStoreの任意root、symlink、偽造marker | 固定Eドライブroot、run ID、regular path、staging、hash再計算、commit marker、no-overwriteを実装する。 | path traversal / reparse / marker偽造 / 部分commit / 二重publishの拒否テスト。 |
| BLK-P3-009: Offline / Engine / 性能が自己申告 | 実入力と実出力から証跡を作るPreflight/Postflight、共通Engine DTO、Fake Adapter parity、性能測定器を実装する。 | 通信・Secret・依存・hash・端末情報の欠落をPASSにできないテストとmachine-readable evidence。 |

#### P3-07R-01 実行契約の補強と敵対的RED固定

```text
ステップID: P3-07R-01
ロール: Backtest実行契約・敵対的テスト固定者
使用オーケストレータ完全名: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1, AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_trading_engine_poc_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-07R-01
- run_id: RUN-P3-BT-REPAIR-001
- output_root: doc/phase3/04_Backtest詳細設計/, tests/backtest/, tests/fixtures/phase3/, tests/evidence/phase3/RUN-P3-BT-REPAIR-001/
- detail_boundary: P3-D05を置換せず、P3-07差戻しを閉じる実行契約・型・失敗コード・REDケースを補足する。外部engine、Broker、実データ取得は対象外。
- human_gate_policy: 新しい設計判断は作らない。H3-1/H3-1R/H3-2の承認済み値を読むだけであり、既存fixture/expectedの変更は禁止する。
- acceptance_conditions: P3-AC-01, P3-AC-02, P3-AC-03, P3-AC-04, P3-AC-05, P3-AC-06, P3-AC-08。P3-AC-07は「偽造できない測定口」の契約だけを扱う。

入力:
- P3-D04、P3-D05、P3-D06、P3-D08、P3-06実装とP3-07のA150/A160/A40レビュー証跡
- src/autotrade/market_data/store_contracts.py のMarketEvent / DataVersionManifest正本
- H3-1/H3-1R承認済みfixtureとRUN-P3-BT-001の既存証跡

タスク:
1. P3-D05にP3-07R補足節を追加し、以下をフィールド名、Python型、必須/nullable、正規化、失敗コード、冪等性まで固定する。`ReplayInput`、`ReplayOrderKey`、`DataGateDecision`、`ExperimentManifest`、`BacktestRunRequest`、`BacktestRunResult`、`BacktestSnapshot`、`ResultRow`、`CommitMarker`、`EngineIdentity`、`EngineRunRequest`、`EngineRunResult`、`EngineAdapter` Protocol、`OfflineEvidence`、`PerformanceEvidence`。
2. 唯一の正本経路を `BacktestRunner.run(request) -> BacktestRunResult` と固定する。公開APIが「caller suppliedのPASS bool」だけで合格を返すことを禁止し、既存のdict predicateは削除するか、実DTOを呼び出す薄い互換入口に限定する。
3. 実行順を擬似コードで固定する。strict Manifest検証 → P2 MarketEvent/Data Gate検証 → Replay正規化/重複処理 → 各1分Eventで既存protective stopとeligible pendingだけを処理 → Calendar/Timeframe集約 → 同一close cohortを全更新 → Strategy一回 → 新Directiveを次bar用pendingへ追加 → Snapshot/Result append → marker commit → atomic publish、の順以外を許可しない。
4. 親fixture Manifestは、P3-07Rで読む全子fixtureの「完全な相対path集合、sha256、schema version」を列挙する。テストは親Manifestから期待値を読むだけにせず、テストコード側の固定期待hash/不変条件とも突き合わせる。絶対path、UNC、`..`、symlink/junction/reparse、重複子、未列挙子、hash形式不正を拒否する。
5. 次の通常REDを、既存のBT-001〜042とH3 fixtureのbytesを変えずに追加する。欠落/未知Manifest値、非有限Decimal/float、未知Data Gate flag、品質停止、未来Event、BAR_1M以外、event_id欠落、同じinstrument・同じ1分区間の別payload、同じevent_id再送/競合、M30のM1 30本以外、future Calendar/Roll、同bar新規Fill、遅い別市場barへのFill、Snapshot改ざん/欠落、偽造commit marker、path escape/reparse、engine identity未固定、offline/performance証跡欠落、Secret形状のResultRow。
6. `pytest`は実装前に通常REDであることを記録する。失敗理由は未実装APIまたは既存stubのfail-openに限り、fixture/期待値/テストを都合よく弱めない。A91がCritical/High 0となるまで、本実装へ進めない。

レビュー:
- A150/A160/A40は、REDが実処理を要求し、自己申告・常時PASS・fixture自己参照では通らないことを独立確認する。
- A91は、補足節だけでA120が追加判断なく実装できることを確認する。

完了条件:
- P3-D05補足、独立oracle、RED証跡、P3-AC→テスト→証跡対応表が揃う。
- 既存承認fixture/hashを変更せず、全新規安全テストが「現在のP3-07実装ではRED」である。
- A91/A150/A160/A40のCritical/Highが0件で、P3-07R-02にのみ引き渡す。
```

#### P3-07R-02 型付きReplay・Strategy接続・保守的仮想約定の実装

```text
ステップID: P3-07R-02
ロール: 決定的Backtest Core実装者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_implementation_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_turtle_strategy_rules_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-07R-02
- run_id: RUN-P3-BT-REPAIR-002
- output_root: src/autotrade/backtest/, tests/backtest/, tests/evidence/phase3/RUN-P3-BT-REPAIR-002/
- detail_boundary: P3-07R-01で固定したCore実行経路、Replay、Calendar/時間足接続、Strategy一回呼出し、次barだけの最小仮想約定。Cost/Slippage/Roll/Gapの数値モデルはP3-08のまま分離する。
- human_gate_policy: H3-1/H3-1Rの固定値を実装するだけであり、再承認を要求しない。

入力:
- P3-07R-01の受入済み補足・RED・親fixture Manifest
- P2の型付きMarketEvent/DataVersionManifest、P3-06のStrategy Core、P3-D05のCalendar/ClosedBarBatch/ConfirmedExecutionView契約

タスク:
1. public entryを型付き・不変DTOだけにする。入力Mapping/JSONは境界で厳格復元し、未知field、欠落field、非UTC/naive時刻、float、非有限Decimal、未承認timeframeを固定BacktestFailureへ正規化して、Signal/Directive/Fill/Resultを0件にする。
2. Replay順序を `(bar_close_time_utc, instrument_id, event_id)` とし、同一event_idかつcanonical payload同一は一回だけ採用、同一event_idで内容違い、または同一instrument・同一BAR_1M区間で内容違いは`DUPLICATE_1M_CONFLICT`でsticky停止する。P2のdata_version、quality decision、Catalog/Calendar/Manifest bindingのどれかが欠けても開始しない。
3. P3-D05のTimeframeAggregatorとCalendarを実行経路へ接続する。M30は実M1 30本、session anchor、source ID、OHLCV、品質、Calendar版を再計算して一致した場合だけ作る。15分・30分・1時間・4時間・日足の端数、DST、休日、短縮日、休場、欠損、重複、逆行は`PARTIAL_BAR_REJECTED`等で停止する。
4. 同一close cohortは固定順 `M1_TRIGGER → M15 → M30 → H1 → H4 → D1` で全Viewを更新してから、P3-06 Strategyを一回だけ呼ぶ。到着順の全permutationで、Signal、TargetPosition、State hash、Batch hashが一致することを実行テストにする。
5. `ScheduledDirective` / `SimulatorState`を実装する。新規Entry/Add/Channel Exitはdecisionより後の、同一tradable instrumentの最初のeligible 1分barだけで評価する。既存保有のprotective stopだけは設計どおり現barで評価できる。別市場、未到達、同bar、過去bar、時刻形式不正、Replay終端のpendingを明確に`PENDING`/`UNFILLED`/`NO_ELIGIBLE_BAR`へし、二重Fillを許可しない。
6. `TARGET_POSITION`出力はP3-06契約を保持する。Entry/Addは正のstrategy unit hint、Exit/2N Stopは`FLAT`と0 hintであり、Broker quantity、Margin、実注文、外部engine IDを混ぜない。
7. 全REDをGREEN化し、既存P3-06/P3-07テストを含む対象scopeを通す。A140は失敗時に最小修正を行うが、仕様・fixture・期待値を変更して合格扱いにしない。

レビュー:
- A150は実ReplayがStrategy、Fill、状態へ接続されていることをコード実行で確認する。
- A160は未来情報、品質抜け、同bar Fill、M30偽装、重複/順序を入力改ざんで監査する。

完了条件:
- P3-AC-01/02/03/08のCore範囲が実入力の統合テストでGREEN。
- 「入力boolを返すだけ」のReplay/Simulator APIが正本経路から除去され、全失敗は構造化STOPPEDかつ出力0件になる。
- A150/A160のCritical/Highが0件でP3-07R-03へ進む。
```

#### P3-07R-03 Manifest・Snapshot・EドライブResult公開と復旧の実装

```text
ステップID: P3-07R-03
ロール: 実験証跡・原子的公開・復旧実装者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_implementation_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-07R-03
- run_id: RUN-P3-BT-REPAIR-003
- output_root: src/autotrade/backtest/, E:\strategy_test_data\phase3\backtests\runs\, tests/evidence/phase3/RUN-P3-BT-REPAIR-003/
- detail_boundary: canonical Manifest、Snapshot、append-only Result、commit/recovery、Eドライブpath境界。バックアップ・暗号化・保存期限・容量制限はユーザー決定どおり実装しない。
- human_gate_policy: 保存方針は承認済み。AIはEドライブ外への正式結果公開、UNC/WSLコピー、既存Run上書きを行わない。

タスク:
1. strict canonical JSONを一箇所に実装する。UTF-8、sorted key、Decimal正規文字列、UTC RFC3339 `Z`、Enum code、固定collection順だけを許可し、float、NaN、Infinity、set、任意object、unknown fieldを拒否する。SHA-256はcanonical bytesだけから再計算する。
2. ExperimentManifestはraw/normalized/MarketEvent列、data/catalog/calendar/timeframe/ordering/config/code、quality、split、cost profile、adapter/engine、fixture、input/output hashを全て必須にする。P3-07ではEngineIdentityを全field `ENGINE_NOT_USED` の固定値にする。read/restore/publishのたびにManifestと全hashを再構築照合し、欠落・差替え・未知schemaは`MANIFEST_INTEGRITY_VIOLATION`で公開しない。
3. ResultStoreは固定root `E:\strategy_test_data\phase3\backtests\runs\` のregular directoryだけを受ける。run IDをallow-list正規表現で検証し、相対/絶対混在、UNC、`..`、symlink/junction/reparse、root自身、存在済みrun、root外pathを拒否する。テストは一時rootを明示注入して同じ規則を実測する。
4. `staging/<run_id>`へ immutable Manifest → canonical result rows → Snapshot → commit marker の順に書く。各write後にhashとflushを確認し、markerにはmanifest/result/snapshot/last committed event/offset/hashを束縛する。marker内容を再読込・再hashしてから一回だけatomic renameし、公開済みRunの上書き、二度目publish、外部から置換したstaging、偽造markerを拒否する。
5. SnapshotにはManifest、Replay/aggregator/strategy/simulator state、pending directives、consumed fingerprints、execution/campaign watermarks、result offset、input/output hashを束縛する。中断注入後はcommit済みeventだけを再生し、同じSignal/Fill/ResultRowを二度作らない。missing/tampered/newer schema/context mismatchは復旧せずSTOPPEDとする。
6. ResultRowは許可fieldだけを持ち、Secretらしいkey/value、engine/broker固有ID、非canonical数値を拒否またはredact reason付きSTOPPEDにする。ResultStoreはCoreの外側のpublish adapterとし、Strategy/Replay/Engine DTOからfilesystem objectを漏らさない。
7. path/reparse差替え、marker差替え、部分書込み、同一run再実行、Snapshot改ざん、同一event再配送、途中停電相当のfailure injectionをGREENにする。実験結果が公開されない失敗も監査証跡へ一意に残す。

レビュー:
- A150はcanonical hash、commit順、復旧水位、ResultRow schemaをレビューする。
- A160はpath traversal、Windows reparse point、TOCTOU、marker偽造、Secret混入、任意rootを実証的に監査する。

完了条件:
- BLK-P3-008の「実Replay→Snapshot→ResultStore→復旧」が実行テストで一体化される。
- hash、path、marker、Snapshotの一つでも不一致ならResultは公開されず、Signal/Fillの追加生成は0件。
- A150/A160のCritical/Highが0件でP3-07R-04へ進む。
```

#### P3-07R-04 Engine境界・Offline・性能証跡の実装

```text
ステップID: P3-07R-04
ロール: Engine Adapter境界・ローカル実行証跡実装者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_implementation_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_trading_engine_poc_v0_1, autotrade_skill_ops_security_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-07R-04
- run_id: RUN-P3-BT-REPAIR-004
- output_root: src/autotrade/backtest/, scripts/quality_gate/, tests/quality_gate/, tests/backtest/, tests/evidence/phase3/RUN-P3-BT-REPAIR-004/
- detail_boundary: SDKなしのEngineAdapter共通契約、Core referenceとのFake Adapter parity、外部通信なしの実行証跡、性能測定口。LEAN/Nautilusの取得・import・実行はしない。
- human_gate_policy: H3-2は既に承認済みだが、このStepは外部engine依存を導入しない。EngineIdentityの実digestはP3-08Aまで捏造しない。

タスク:
1. `EngineIdentity`、`EngineAdapter` Protocol、`EngineRunRequest`、`EngineRunResult`、`EngineFailure`を実装する。engine/adapter/runtime/artifact digestの全fieldを必須にし、P3-07は`ENGINE_NOT_USED`だけを許可する。tag単独、空、unknown、型違い、SDK型/ID/例外の公開型・Snapshot・Manifest漏出はSTOPPEDにする。
2. `FakeEngineAdapter`は同じ凍結Replay/Manifest/Strategy Configを受け、Core referenceが一度だけ作った順序付きSignal/Directive/virtual fill/state/result hashと比較する。差異は`ENGINE_PARITY_MISMATCH`で結果を採用しない。Fake Adapter自身がStrategyを二度実行することを禁止する。
3. OfflinePreflight/Postflightを実測値から作る。許可input root、実際に読んだinput hash、実際に書いたresult hash、許可依存hash、禁止import走査、Secret key/value scan、外向き通信遮断/試行0、Broker/Cloud URL 0をmachine-readable evidenceへ記録する。欠落、型違い、未知値、観測不能は`OFFLINE_PREFLIGHT_UNPROVEN`または`OFFLINE_POLICY_VIOLATION`で停止し、caller boolだけでPASSにしない。
4. P3用品質Gate入口は登録済みtarget pathsだけを実行し、対象scopeのnetwork guardを必ず有効にする。直接pytestによる最終証跡代用、外部path、実DBN、Secret、engine SDKを拒否する。既存P2入口・証跡を変更しない。
5. PerformanceEvidenceは決定的5市場×2暦年synthetic inputのgenerator/schema/seed/hash、派生bar hash、Manifest、CPU/RAM/OS/ストレージ、monotonic elapsed、peak RSS測定器/版/単位、二回の実結果hashを記録する。計測なし/不正値/形だけの`sha256:`/limit超過/二回不一致はPASSにしない。P3-07では「計測口と証跡の正しさ」だけをGREENとし、30分/8GiBの正式性能判定はP3-09であると記録する。
6. Fake Adapter成功、SDK漏出、identity不一致、parity差、通信試行、禁止依存、Secret/URL、外部path、測定値/host/hash欠落の全ケースをGREENにする。

レビュー:
- A40は共通DTO、Core一回実行、identity、Fake parity、P3-08A/P3-09への境界を確認する。
- A160はOffline/Secret/SDK/import/path/evidenceの自己申告抜けを監査する。
- A150はProtocolの型、例外正規化、Evidence hashの決定性を確認する。

完了条件:
- P3-AC-05/06のCore範囲が、SDKなしの実DTO・Fake parity・機械証跡でGREEN。
- P3-AC-07は測定口の偽造拒否までGREENであり、未実行の正式閾値をPASSと主張しない。
- A40/A150/A160のCritical/Highが0件でP3-07R-05へ進む。
```

#### P3-07R-05 RUN-P3-BT-001再実行・最終受入

```text
ステップID: P3-07R-05
ロール: Backtest再現性の最終検証・証跡統合者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-07R-05
- run_id: RUN-P3-BT-001
- output_root: tests/evidence/phase3/RUN-P3-BT-001/, doc/phase3/06_実装検証/07_Backtest再現性検証結果.html, doc/00_全Phase残課題Blocked統合台帳.html
- detail_boundary: P3-07の同じRun IDを、P3-07R-01〜04で固定したscope/fixture/hash/APIで再実行して受入可否を更新する。P3-08、P3-08A、P3-09、Broker、Paper、Liveを開始しない。
- human_gate_policy: 新しい設計承認は不要。既存H3-1/H3-1R/H3-2を再確認する。実行入口が別途人のRun承認を要求した場合だけは、その状態を偽造せず停止して正確なRun IDと確認対象をユーザーへ提示する。

タスク:
1. `trusted_scopes.json`、P3 local test wrapper、親fixture Manifest、target paths、fixture hash、Evidence schemaを最終実装と完全一致させる。対象外worktree差分、P2 scope、WSL、外部pathを最終合否へ混ぜない。
2. `RUN-P3-BT-001`で、formatter、lint、type、P3許可pytestの固定4 Gateを実行する。直接pytestの結果だけを最終証跡にせず、preflight/postflight、fixture integrity、input/output hash、二回Replay、failure injection、ResultStore復旧、Fake Adapter parity、performance evidence状態を同じRunへ保存する。
3. A150、A160、A40に最終コードと実行証跡を独立レビューさせる。前回の全Critical/Highに対し「どのテスト・どの実装・どの証跡で閉じたか」をP3-D08の表に一対一で記録する。未解消Critical/High、skip/xfail、期待値改変、自己申告PASS、外部I/O、Result公開不整合が一件でもあれば`REVIEW_RETURNED`のままにする。
4. 全条件を満たした場合だけP3-D08をP3-07受入可へ更新し、BLK-P3-008を解決済みにする。BLK-P3-009は「P3-07 Coreの自己申告問題は解消、実LEAN依存の固定・実行はP3-08A/P3-09待ち」と範囲を縮小する。総合台帳の最新状態、件数、Human Gate、Phase表示、履歴、P3-08前提を全件検索して同期する。
5. 最終判定は「P3-07 PASS（Core範囲）」と「P3-09で初めて判定するLEAN実機・30分/8GiB正式性能」を明確に分ける。未実施の外部engine/実取引所Calendar/Paper/LiveをPASSと書かない。

完了条件:
- 固定4 Gate、対象Core統合テスト、二回Replay、改ざん/中断復旧、Fake Adapter parityが全てPASS。
- A150/A160/A40の最終Critical/Highが0件で、P3-D08・総合台帳・実行計画の現在状態が一致する。
- P3-07が受入可へ戻り、P3-08のみ開始可能になる。P3-08A/P3-09/Phase 4は依然として後続Gateのままである。
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
- human_gate_policy: P3-07R-05でP3-07が受入可へ戻った後だけ、H3-1/H3-1R承認済みfixtureを使う。長期実データはH3-2承認範囲だけ使用する。
- acceptance_conditions: P3-AC-01, P3-AC-02, P3-AC-03, P3-AC-04, P3-AC-08

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
7. 欠損1分足、セッション途中の入力終了、rollと4時間足closeの同時発生、Gap直後の複数時間足更新をfailure injectionし、部分barや未来rollをStrategyへ渡さない。
8. Calendar/timeframe ruleをholdout結果確認後に変更できないようManifestへ束縛し、変更したRunを別Experimentとして扱う。
9. snapshot/restoreをCost/Roll/Gap適用前後で実行し、二重cost、二重roll、重複Signal/Intentが発生しないことを検証する。
10. `RUN-P3-BIAS-001`のtarget_paths、固定4 Gate、fixture hash、Manifest、証跡先をtrusted scopeへ登録してから実行する。

レビュー:
- A150がモデル境界、型、テストを確認する。
- A160が楽観約定、後付け最適化、holdout漏洩、roll二重計上を監査する。

完了条件:
- cost/roll/gapを無視した結果を正式結果として出せない。
- Holdout漏洩テストがGREEN。
- UNK-P3-01/05/07が未解消なら明示的に残る。
- P3-AC-01〜04/08の頑健性テストがGREENで、実取引所Calendarの継続追随だけをPhase 4へ分離する。

実行結果（2026-08-10）:
- `tests/backtest tests/strategy` は265件PASS、skip/xfailは0件。
- WSL隔離下でformatter、lint、type、testの固定4 Gate、fixture前後hash、networking mode `none` をPASS。
- `RUN-P3-BIAS-001` はユーザーのH3-5承認によりPASS。P3-08Aを開始し、P3-09はP3-08A完了まで開始しない。
```

### P3-08A LEAN固定依存・オフライン実行環境準備

実行結果（2026-08-10）: **PASS**。初回約60分ではDocker展開・登録が完了しなかったが、ユーザーの追加待機指示後、同じ公式固定digestで取得を継続し、完成イメージ登録、Eドライブtar保存、全hash、LICENSE、network none/read-only Local preflight、固定4 Gate、独立レビューを完了した。P3-09は別Gateであり、まだ開始しない。証跡: `tests/evidence/phase3/RUN-P3-LEAN-PREP-001/`。

```text
ステップID: P3-08A
ロール: LEAN依存固定・オフライン実行準備者
使用オーケストレータ完全名: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_trading_engine_poc_v0_1, autotrade_skill_poc_evaluation_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_python_test_quality_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1

Phase Runbook:
- phase_id: Phase 3
- step_id: P3-08A
- output_root: E:\strategy_test_data\phase3\engine_poc\lean\, tests/evidence/phase3/RUN-P3-LEAN-PREP-001/
- log_root: plan/phase3/ログ/
- run_id: RUN-P3-LEAN-PREP-001
- detail_boundary: LEAN公式依存の取得、完全hash固定、ライセンス記録、オフライン起動確認まで。Strategy評価、Broker、Paper、Live、Secretは対象外。
- human_gate_policy: H3-2承認済み範囲だけを使用する。LEAN主候補の準備が安全に完了できない場合はPoCを開始せず、縮退条件を記録する。
- acceptance_conditions: P3-AC-05, P3-AC-06

発火制御:
- 指定部品だけを使用する。
- 公式QuantConnect/LEAN配布元以外からpackage、Docker image、source、dataを取得しない。
- 取得時だけ必要最小限の外部通信を許可し、接続先、時刻、取得物、版、digestを記録する。Broker、QuantConnect Cloud backtest、API key、Secret、データ自動購入を使わない。
- 可変tagだけで固定せず、Docker image digestまたはsource commitと全artifact hashを記録する。
- 大容量取得物はEドライブへ置き、GitにはManifest、hash、ライセンス、要約証跡だけを保存する。

入力:
- H3-2承認記録
- P3-D03, P3-D05, P3-D06, P3-D08, P3-D09
- scripts/quality_gate/trusted_scopes.json
- E:\strategy_test_data\phase3\engine_poc\

タスク:
LEANをP3-09で完全オフライン再実行できるよう、公式依存を一度だけ取得し、版・digest・ライセンス・実行入口・ネットワーク遮断条件を固定してください。

作業:
1. 公式一次情報を再確認し、確認日、公式URL、LEAN commit/tag、Docker image digest、CLI/.NET/Python/Docker版、ライセンスを記録する。
2. 原則として公式LEAN Docker imageをdigest固定して取得する。利用不能な場合だけ公式sourceの固定commit buildへ縮退し、理由と全build artifact hashを記録する。
3. image/package/cacheを`E:\strategy_test_data\phase3\engine_poc\lean\`へ保存し、Git追跡・staged・Secret混入が0件であることを確認する。
4. 取得完了後にネットワークを遮断し、固定ローカルfixtureだけでLEANが起動できるpreflightを実行する。データ自動取得、Cloud、Broker接続要求が発生した場合はBLOCKEDにする。
5. `RUN-P3-LEAN-PREP-001`のManifestへ全hash、実行入口、必要volume、read/write範囲、環境変数名、ネットワーク禁止、復元手順を固定する。Secret値は記録しない。
6. LEAN project/AdapterのCore側import境界を静的検査し、engine固有型が`src/autotrade/strategy/`とengine非依存Coreへ漏れていないことを確認する。
7. NautilusTraderへの縮退条件を「LEANがP3-AC-01〜08のいずれかをengine固有理由で満たせず、二回の限定修正後も再現する場合」と固定する。縮退準備は`RUN-P3-NT-PREP-001`、縮退PoCは`RUN-P3-POC-NT-001`とし、同じfixture・期待値・合格値、公式版/hashを固定する。
8. P3-D03、総合台帳、doc/index.htmlを更新し、現在の正本版とP3-09で使う唯一のexecution manifestを明示する。
9. `RUN-P3-LEAN-PREP-001`と`RUN-P3-POC-001`のtarget_paths、固定4 Gate、入力hash、image/package digest、証跡先をtrusted scopeへ登録する。縮退Runは縮退条件成立後に別scopeとして登録する。

レビュー:
- A70/A160が供給元、digest、権限、外部通信、Secret、書込範囲を監査する。
- A150がAdapter import境界と実行入口を確認する。
- A40/A130がオフライン起動とP3-09への再現可能な受渡しを確認する。

完了条件:
- 公式配布元、固定版、完全digest/hash、ライセンス、ローカル実行入口が一意に記録される。
- ネットワーク遮断後の起動preflightがPASSし、Cloud、Broker、Secret、データ自動取得を使っていない。
- Critical/Highが0件で、P3-AC-05/06の準備GateがPASSする。
- 条件を満たせない場合はP3-09を開始せず、BLOCKED理由とNautilusTrader縮退可否を総合台帳へ記録する。
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
- human_gate_policy: H3-2で承認され、P3-08Aで固定したLEAN版、完全digest/hash、入力、実行方式だけを使う。
- acceptance_conditions: P3-AC-01〜P3-AC-08

発火制御:
- 指定部品だけを使用する。
- RUN-P3-LEAN-PREP-001がPASSでない場合は実engineを起動せず、BLOCKED証跡を作って停止する。
- P3-08Aで固定したdigest/hashを実行前後に検証する。
- 外部接続、クラウドQuantConnect、Broker、Secretを使わない。
- LEAN失敗後に期待値、fixture、Calendar、性能合格値を変更しない。

入力:
- P3-D03, P3-D04, P3-D05, P3-D06, P3-D07, P3-D08, P3-D09
- D12 取引エンジンPoC評価設計
- H3-2承認記録
- RUN-P3-STR-001, RUN-P3-BT-001
- RUN-P3-BIAS-001, RUN-P3-LEAN-PREP-001
- P3-AC-01〜08の凍結fixture、期待値、合格条件追跡表

タスク:
LEANを主候補として、同じ固定入力・Strategy意味論・Manifestで複数時間足、再現性、Adapter境界、オフライン、性能をPoCしてください。LEANが固定縮退条件に該当した場合だけNautilusTraderを同じ条件で評価してください。

作業:
1. 実行前にP3-08AのLEAN digest/hash、ローカル入力hash、Calendar hash、timeframe rule版、Adapter版、code revisionを再照合する。一つでも違えば開始しない。
2. ネットワークを遮断し、QuantConnect Cloud、Broker、Secret、自動データ取得を無効化した状態を機械確認してからLEANを起動する。
3. P3-AC-01として、固定1分足から15分・30分・1時間・4時間・日足を生成し、project Timeframe Aggregatorの期待OHLCV、件数、開始・終了時刻、順序、hashと一致させる。
4. P3-AC-02/03として、未完成bar拒否、通常日、夏時間開始・終了、休日、短縮日、日次休場、4時間session anchor、同時close時の一回判断を実行する。
5. P3-AC-04/08として、Entry/Add/Stop/Exit、snapshot/restoreを同一Manifestで二回実行し、MarketEvent、派生bar、Signal、Intent、State、結果の順序付き系列を一致させる。
6. P3-AC-05として、LEAN固有型・ID・例外をAdapter内で共通型へ変換し、Strategy/Core公開API、snapshot、Manifest、証跡へ漏れていないことを静的・動的に確認する。
7. P3-AC-06として、二回目のPoCを完全オフライン、固定ローカル入力だけで再実行する。外部接続要求や未固定依存要求が一件でもあればFAILとする。
8. P3-AC-07として、5市場×2暦年のsynthetic 1分足、5派生時間足、Strategy Replayを実行し、30分以内、peak RSS 8GiB以下、二回の出力hash一致を確認する。端末情報と測定方法を保存する。
9. 各P3-ACを個別にPASS/FAIL/BLOCKEDで記録し、利益率を合否基準にしない。失敗時も入力、ログ、hash、原因を保存する。
10. LEANがengine固有理由でいずれかのP3-ACに失敗した場合、限定修正を最大二回行う。なお失敗する場合だけP3-08Aの縮退契約に従いNautilusTraderを`RUN-P3-POC-NT-001`で同じfixture・期待値・合格値により評価する。
11. P3-D10を作成し、LEAN採用候補/条件付き/不採用、Nautilus縮退の有無、Phase 4未検証部分、OD-02の決定範囲、総合台帳のUNK-P3-03/04を更新する。

レビュー:
- A150がAdapter実装と再現性を確認する。
- A160/A70が依存供給元、実行権限、外部通信、Secret、証跡改ざんを監査する。
- A40が採点の公平性、複数時間足意味論、縮退条件を確認する。

完了条件:
- LEANについてP3-AC-01〜08のPhase 3範囲が全てPASSしている。または固定縮退条件に従い、LEANの失敗証跡が存在し、NautilusTraderが同じP3-AC-01〜08を全てPASSしている。
- 5市場×2暦年の性能試験が30分以内・peak RSS 8GiB以下で、二回の出力hashが一致する。
- ネットワーク遮断、固定ローカル入力、固定digest/hashの実行前後一致が証跡化される。
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
- acceptance_conditions: P3-AC-01〜P3-AC-08のPhase 3最終Gate

発火制御:
- 指定部品だけを使用する。
- trusted scopeとManifestにないコード、入力、コマンドを実行しない。
- WSL実機Gateが必要な場合はWindows側を正本とし、ユーザー委譲済みの可逆同期手順を使う。AIは対象WSL cloneのbranch/origin/HEAD/statusを確認し、dirty変更をリポジトリ外アーカイブへ保存して`git stash push --include-untracked`で退避した後、clean確認済みcloneへ`git pull --ff-only`を実行する。reset、clean、force、rebase、checkout、stash drop/pop、UNCコピー、未コミット変更の上書きは行わず、同期後にHEAD、clean状態、trusted scope、fixture hashを再確認してから実機Runを行う。

入力:
- P3-D04〜P3-D10
- RUN-P3-GOLD-001, RUN-P3-STR-001, RUN-P3-BT-001, RUN-P3-BIAS-001, RUN-P3-POC-001
- RUN-P3-LEAN-PREP-001。縮退条件成立時だけRUN-P3-NT-PREP-001とRUN-P3-POC-NT-001
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
7. P3-AC-01〜08の追跡表を機械的に集計し、各条件について設計行、テストID、実装path、Run証跡、レビュー結果、最終状態が全て存在することを確認する。
8. 1分→15分/1時間/4時間/日足の期待bar系列とLEAN実測系列、project Aggregator系列を三者比較し、順序・値・hashの差分0件を確認する。
9. 通常日、夏時間開始・終了、休日、短縮日、日次休場、同時close、未完成barの全fixtureについて、未来情報参照0件とStrategy判断回数一致を確認する。
10. snapshot/restore前後、オフライン再実行前後、同一Manifest二回、5市場性能二回のSignal/Intent/State/結果hashを比較する。
11. P3-AC-01/02/04/05/06/08は一件でもFAIL/BLOCKEDならPhase 3完了不可とする。P3-AC-03は固定Calendar試験PASSを必須とし、実取引所Calendar継続追随だけPhase 4へ送る。P3-AC-07は3〜5市場PASSを必須とし、20〜40市場連続運用だけPhase 4へ送る。
12. `p3-acceptance-summary.json`と中学生向け説明を含むMarkdown/HTML要約を作り、総合台帳へ最終状態を反映する。

レビュー:
- A150が証跡と最終コードのrevision一致を確認する。
- A160が利益を良く見せる漏洩、楽観約定、Unknown隠しを監査する。
- A30/A40がStrategyとengine結果の意味論一致を確認する。

完了条件:
- 再現性・Golden・Bias GateのPass/Fail/Unknownが明確。
- UNK-P3-01が残る場合、Phase 3完了に与える影響を明記する。
- stale証跡を最終PASSに使わない。
- `p3-acceptance-summary.json`でP3-AC-01〜08のPhase 3必須部分が全てPASSし、未割当、未実行、根拠なしのPASSが0件である。
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
- acceptance_conditions: P3-AC-01〜P3-AC-08の独立監査

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
7. P3-AC-01〜08を一件ずつ独立再監査し、設計、RED、実装、PoC、統合証跡の五段階が途切れていないか確認する。
8. 4時間session anchor、夏時間、同時close、未完成bar拒否、snapshot復元、Adapter型漏出、オフライン、5市場性能を重点的にfailure injectionする。
9. LEANが主候補に選ばれた理由が性能や利益の印象ではなく固定合格条件の証拠で説明できるか確認する。Nautilus縮退を行った場合は同じ条件だったか確認する。
10. Phase 4へ送るP3-AC-03の実取引所Calendar追随、P3-AC-05のBroker Adapter接続、P3-AC-06のPaper隔離、P3-AC-07の20〜40市場連続運用を、総合台帳の独立した残課題へ追跡する。

レビュー:
- A90が全体整合性、A150がコード品質、A160が取引安全、A30/A40がStrategy/PoCを独立判定する。

完了条件:
- Critical/High/Medium/Low、採否、修正条件、証拠先が明確。
- H3-3で承認すべき事項が日本語で具体的に示される。
- P3-D11/P3-D12がdoc/index.htmlから到達できる。
- P3-AC-01〜08のPhase 3必須部分にCritical/Highまたは証拠欠落が0件で、Phase 4送りが現在のPASSと混同されていない。
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
- acceptance_conditions: P3-AC-01〜P3-AC-08の最終受入

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
9. P3-AC-01〜08の最終表を再生成し、全Phase 3必須部分がPASSであること、Phase 4送りの4項目が独立登録されていることを確認する。
10. LEANの固定digest/hash、Adapter版、Calendar hash、timeframe rule版、性能fixture hash、最終code revisionと全Run証跡を照合する。
11. P3-AC-03/07の境界を明示し、固定Calendarと3〜5市場試験はPhase 3でPASS、実取引所Calendar継続追随と20〜40市場連続運用はPhase 4未検証と記載する。

レビュー:
- A91が詳細設計と最終実装の整合性を確認する。
- A150/A160が最終コードと証跡を再監査する。
- A90/A81が全成果物、リンク、台帳、Phase 4引継ぎを確認する。

完了条件:
- Critical/Highが0件。
- 必須Unknownを合格扱いしていない。
- P3-D13/P3-D14がdoc/index.htmlから到達できる。
- H3-4でユーザーが何を承認すべきか超具体的に説明されている。
- P3-AC-01〜08のPhase 3必須部分が全てPASSし、一件でもFAIL/BLOCKED/証拠欠落ならP3-D14をPhase 3完了PASSにしない。
```

---

## 11. 計画レビュー結果

### 11.1 ステップ粒度

Strategy設計、Backtest/時間足設計、RED、H3-1、Strategy実装、Backtest/時間足実装、頑健性モデル、LEAN固定依存準備、engine PoC、統合検証、レビュー、反映を直列化した。後続ステップが前段成果物を入力にする矛盾を除き、Golden・時間足・Calendar・性能期待値を実装後に変更できない順序にした。

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
2. P3-AC-01: 同じ1分足から同じ15分・30分・1時間・4時間・日足が生成され、project Aggregatorと採用候補engine（原則LEAN、縮退時はNautilusTrader）の値・順序・hashが一致する。
3. P3-AC-02: 未完成の上位足、未来roll、後続bar、holdout情報、可変現在時刻をStrategyへ渡さない。
4. P3-AC-03: 固定Calendarで通常日、夏時間開始・終了、休日、短縮日、日次休場、4時間session anchor、同時close順序がPASSする。実取引所Calendarの継続追随はPhase 4へ独立登録する。
5. P3-AC-04: 同一Experiment Manifestで同一順序のMarketEvent、派生bar、Signal、Intent、State、Backtest結果を再現する。
6. P3-AC-05: Strategyとengine非依存CoreがLEAN/Nautilus固有型・ID・例外を所有せず、Adapter境界テストがPASSする。
7. P3-AC-06: 固定digest/hashと固定ローカル入力だけで、ネットワーク遮断後に二回再実行できる。
8. P3-AC-07: 5市場×2暦年のsynthetic 1分足と5派生時間足を30分以内、peak RSS 8GiB以下で処理し、二回の出力hashが一致する。20〜40市場連続運用はPhase 4へ独立登録する。
9. P3-AC-08: GT-TUR-001〜012、複数時間足Golden、snapshot/restore、Look-ahead防止が固定fixtureでPASSする。
10. cost、slippage、Gap、Rollを無視した結果を正式結果にできず、利益・頑健性UNKNOWNと契約PASSを分離する。
11. `p3-acceptance-summary.json`にP3-AC-01〜08の設計、テスト、実装、Run、レビュー根拠があり、未割当・未実行・根拠なしPASSが0件である。
12. A91、A150、A160の最終レビューでCritical/Highが0件である。
13. H3-3とH3-4が明示承認される。

H3-4が未承認の場合、Phase 3成果物は研究・検証候補として保持し、Phase 4のBroker / Paper基盤へ引き渡さない。

# Phase 5 実行計画書 v0.1

- 計画ID: `P5-PLAN-001`
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- 対象Phase: Phase 5 市場データ運用化と実証
- 作成日: 2026-08-12（Asia/Tokyo）
- 状態: `P5-02_COMPLETE_WITH_FALLBACK_REVIEW`
- 前Phase: Phase 4 Product/Application・Backtest（`P4-PLAN-001`）
- 前Phase承認: `P4-H2=APPROVED`。P4-H2はPhase 5の実装、外部Data取得、Secret投入、外部I/Oを承認しない。
- 計画作成標準: `AutoTradePhasePlanning_Orchestrator_v0_1`、`AutoTrade_A05_PhaseExecutionPlanner_v0_1`、`autotrade_skill_phase_execution_planning_v0_1`
- AI部品変更標準: `AutoTradeComponentLifecycle_Orchestrator_v0_1`、`AutoTrade_A06_AiComponentEngineer_v0_1`、`autotrade_skill_ai_component_lifecycle_v0_1`
- 起動契約版: `RDC-PHASE-PLAN-0.2`、`RDC-AI-COMPONENT-0.2`

## 1. 結論

Phase 5は、P4で作成したProduct/ApplicationのData接続点を引き継ぎ、初期5候補（MCL、M6A、MZC、MZS、MZW）の市場Dataを、対象・契約・来歴・品質・Calendar・Cost／Slippage／Gap・長期期間・Holdout／Walk-forwardまで再現可能なEvidenceへ変換するPhaseである。

ただし、P4-H2はP5開始承認ではない。この計画を作成した時点では、外部Providerへの接続、費用発生、Secret参照、外部I/O、実Data取得、Broker／Paper／Live、実資金、Cloudを開始しない。P5-H0、P5-H1、P5-DATA-G1、P5-H2を分離し、承認範囲を越える発火を禁止する。

本計画の直接実行プロンプトは、Orchestrator／Agent／Skillの名前を列挙するだけでは完了扱いにしない。各Promptへ、実ランタイムのOrchestrator spawn、指定Agent全件の個別spawn、固定model受理、wait完了、受領証跡、起動不能時の継続Fallbackを埋め込む。起動不能は単独の停止条件にしないが、未起動を起動済み・独立レビュー済みと偽らない。Human Gate、外部I/O、Secret、UnknownのPass、Critical／High、必須Evidenceの欠落はFail-closedで停止する。

## 2. Phase 5の目的と非目的

### 2.1 目的

- 論理IDから実Symbol、取引所、限月、Roll、単位、Provider対応をEvidence付きで対応付ける。
- 初期5候補と4資産種類の対象範囲、D1／H4／H1／M30／M15の時間足を固定する。
- Raw／Normalized／Quality／Manifest／Calendar／Provenance／hashの責務と保存境界を確定する。
- 欠損、重複、時刻逆行、異常値、DST、休場、短縮日、Roll、未来Data、Look-aheadをFail-closedで検出する。
- 固定仮定と実測Cost／Slippage／Gapを分離し、長期期間、train／validation／holdout、Walk-forwardの再現可能な分割を作る。
- P6のRisk／Portfolio／OMSが参照できるData contract、Calendar版、Cost／Gap版をEvidence付きで引き渡す。

### 2.2 非目的

- 利益性の採用、投資助言、銘柄推奨、Live適合性の承認。
- Broker注文、Paper／Live、実資金、実Account、実Risk値、Cloud公開。
- 未承認Provider、未承認Secret、契約不明の再配布、対象拡大。
- P4 Core本体の無承認変更、P4 metadata DBへのData保存単位の無断追加。
- 外部Data取得Worker、Provider SDK、依存、migration、実Data保存を推測で新設すること。

## 3. 発火制御と開始状態

- `P5-H0` 未承認の間は、P5-01〜P5-05の計画・読み取り・設計・レビュー候補の範囲だけを実行できる。外部I/O、Secret、費用、依存導入、実Data取得はしない。
- `P5-H0` はPhase 5計画と設計開始範囲だけを承認する。P5-H1、P5-DATA-G1、P5-H2を自動承認しない。
- `P5-H1` はレビュー済みData詳細設計、RED、Run Manifest、ローカル固定ダミー実装・品質確認の範囲を承認する。外部Data取得は含めない。
- `P5-DATA-G1` は市場Data Provider専用の別Gateである。対象Symbol／期間／時間足、契約・権限、費用上限、endpoint、rate、通信範囲、Secret参照・mask・失効、Raw／Normalized／Quality／Manifest／Evidence保存、保持・再配布を一括承認する。Broker／Paper用のP7 Gateとは別である。
- `P5-H2` はP5の実証EvidenceとP6へのData contract引渡しだけを承認する。利益性、Broker、Paper、Live、実資金は承認しない。
- 既存台帳でP5 Gateが解決済みと確認できない限り、外部I/O、Secret、費用発生、本線引渡しを実行しない。

## 4. 正本入力

| 入力 | 用途 | 制約 |
|---|---|---|
| `plan/phase4/Phase5計画入力一覧_2026-08-12.md` | P4-10の完了値、P5目的、Unknown、開始Gate | P5開始承認ではない |
| `doc/phase4/05_完了/07_Phase4完了判定・Phase5計画引渡し.html` | P4最終coverage、P4-H2、引渡し境界 | P5外部Dataへ一般化しない |
| `plan/requirements_update/RQV2_Phase4以降再編ロードマップ_2026-08-11.md` | Phase間DAG、P5の目的、非対象、Gate | P5内のStep順は本計画が正本 |
| `plan/requirements_update/01_自動トレードシステム要件定義書_v2.md` | 正式REQ、Data／Calendar／Quality／Traceability | Unknownを補完しない |
| `plan/requirements_update/RQV2_要件UIテスト追跡マトリクス_2026-08-11.md` | REQ／UC／Screen／Test／Evidenceの母集団 | P5対象を根拠付きで切り出す |
| `doc/phase4/02_実装詳細設計/03_ProductApplication_Backtest実装詳細設計書.html` | P4 Data／Manifest／保存／品質接続点 | CoreとApplicationの責務を混同しない |
| `doc/phase4/02_実装詳細設計/04_ProductApplication_API詳細設計書.html` | P4 API-P4-IDとData境界 | P5 APIを無断追加しない |
| `doc/phase4/02_実装詳細設計/05_ProductApplication_DB_Persistence詳細設計書.html` | P4 metadata／Result／Evidence／file境界 | Data保存をP4 DBへ無断追加しない |
| `doc/phase4/02_実装詳細設計/06_ProductApplication_UI全21画面詳細設計書.html` | Catalog／Quality／Evidence表示のUI境界 | UIモックを実Data証拠と扱わない |
| `doc/00_全Phase残課題Blocked統合台帳.html` | Gate、Blocked、Unknownの唯一の現在正本 | P5 Gate行を同期する |
| `.codex/config.json`、`.codex/orchestrators/`、`.codex/agents/`、`.codex/skills/` | 使用部品、固定model、Skillの正本 | 推測起動しない |

## 5. 引継ぎ基準線と責務境界

| 項目 | P4引渡し値 | P5での扱い |
|---|---|---|
| P4 Run | `RUN-P4-04D-001` | 固定local品質のEvidence。外部Data Runではない |
| P4 fixture | SHA-256 `aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4` | 実Dataの代用にしない |
| P4 Core | 36 source files、P4終端差分0 | 凍結。変更が必要なら別設計・RED・Gate |
| P4 Application quality | formatter／lint／mypy PASS、pytest 17 passed | P5 Data adapter／qualityの別Gateを作る |
| P4 UI | 21/21設計、13画面×10状態×2 viewport、42 screenshots、axe Critical／Serious 0 | 実Data／実運用Evidenceと混同しない |
| P4境界 | metadata DB、Core ResultStore、CSV／file、Evidenceを分離 | Raw／Normalized／Quality／Manifestの保存先はP5設計で定義し、P4 DBへ無断追加しない |

## 6. 成果物配置

| 区分 | 保存先 |
|---|---|
| 実行計画 | `plan/Phase5_実行計画書_v0.1_2026-08-12.md` |
| 計画作成・AI部品変更ログ | `plan/phase5/ログ/` |
| Phase 5正式HTML | `doc/phase5/` |
| Phase 5機械Evidence | `tests/evidence/phase5/<RunId>/` |
| P5の現在Gate・Unknown | `doc/00_全Phase残課題Blocked統合台帳.html` |
| Phase 5索引 | `doc/index.html` |

正式HTMLは、文書ID、作成日、状態、入力、REQ／DEC／UNK／ART、平易な概要、図、受渡し表、レビュー履歴、採否、関連リンクを持ち、`doc/index.html`から到達できる。Secret、API key、Account ID、実Dataの認証値をHTML・ログ・Evidenceへ出力しない。

## 7. Step一覧と依存関係

| Step | 内容 | 前提 | Gate | 外部I/O | 主成果物 |
|---|---|---|---|---|---|
| P5-01 | 入力・P4接続点・Data対象・REQ追跡 | P5-H0 | P5-H0 | 不可 | 入力・追跡HTML、ログ |
| P5-02 | Catalog／Provider／Data contract設計 | P5-01 | P5-H0 | 不可 | Data契約詳細設計HTML、ログ |
| P5-03 | Raw／Normalized／Quality／Calendar／Provenance／保存設計 | P5-02 | P5-H0 | 不可 | Data運用詳細設計HTML、ログ |
| P5-04 | Cost／Slippage／Gap／長期／Holdout／Walk-forward／Test設計 | P5-02、P5-03 | P5-H0 | 不可 | 品質・Run Manifest設計HTML、ログ |
| P5-05 | 詳細設計レビュー、改訂、再レビュー、P5-H1候補 | P5-01〜04 | P5-H0 | 不可 | 統合レビューHTML、ログ |
| P5-H1 | ローカル固定ダミー実装・品質の開始承認 | P5-05 | 人間承認 | 不可 | 承認記録 |
| P5-06 | 固定local Data contract／QualityのRED→GREEN・品質Gate | P5-H1 | P5-H1 | 不可 | 実装ログ、local Evidence |
| P5-07 | 外部Data Gate準備、承認対象表、台帳同期 | P5-06 | P5-H1 | 不可 | Data Gate申請HTML、ログ |
| P5-DATA-G1 | Provider専用の外部Data Gate | P5-07 | 人間承認 | 承認前不可 | 承認記録、台帳同期 |
| P5-08 | 承認範囲内の限定Data取得・Raw／Normalized Evidence | P5-DATA-G1 | P5-DATA-G1 | 条件付き可 | Data取得Evidence |
| P5-09 | Quality／Calendar／Cost／Gap／期間分割／Holdout実証 | P5-08 | P5-DATA-G1 | 条件付き可 | 実証Report、Evidence |
| P5-10 | 統合・独立レビュー、Unknown再分類、P5-H2候補 | P5-06、P5-09 | P5-DATA-G1 | 不可 | 完了候補HTML、ログ |
| P5-H2 | P5完了・P6引渡し承認 | P5-10 | 人間承認 | 不可 | 承認記録 |
| P5-11 | 完了記録、台帳同期、P6入力引渡し | P5-H2 | P5-H2 | 不可 | 完了HTML、引渡し一覧、ログ |

P5-01とP5-02はP5-01完了後にP5-02を開始する。P5-03、P5-04はP5-02の契約骨子を前提に逐次実行する。P5-05でレビューを閉じるまでP5-H1へ進まない。P5-08／09はP5-DATA-G1承認後だけ発火する。P5-10は実証Evidenceが不足している場合、UnknownをPassにせずP5-H2候補を作らない。

## 8. 使用AI部品と固定model

Orchestratorのmodelは、現行汎用定義JSONに従いすべて `gpt-5.6-terra` とする。Agentのmodelは下表を正本とし、直接実行時にJSONから再読して `model` 引数へ明示する。利用不能時に代替model、代替Agent、`default_orchestrator`へ置換しない。

| 完全名 | 固定model | 主Skill |
|---|---|---|
| `AutoTrade_A05_PhaseExecutionPlanner_v0_1` | `gpt-5.6-luna` | `autotrade_skill_phase_execution_planning_v0_1` |
| `AutoTrade_A10_RequirementsCurator_v0_1` | `gpt-5.6-luna` | `autotrade_skill_source_reader_v0_1` |
| `AutoTrade_A20_ArchitectureDomainArchitect_v0_1` | `gpt-5.6-luna` | `autotrade_skill_architecture_writer_v0_1` |
| `AutoTrade_A30_StrategyQaArchitect_v0_1` | `gpt-5.6-luna` | `autotrade_skill_strategy_interface_v0_1` |
| `AutoTrade_A40_ExecutionEnginePocArchitect_v0_1` | `gpt-5.6-luna` | `autotrade_skill_execution_model_v0_1` |
| `AutoTrade_A50_AdapterArchitect_v0_1` | `gpt-5.6-luna` | `autotrade_skill_adapter_boundary_v0_1` |
| `AutoTrade_A70_OpsSecurityArchitect_v0_1` | `gpt-5.6-luna` | `autotrade_skill_ops_security_v0_1` |
| `AutoTrade_A80_DocumentIntegrator_v0_1` | `gpt-5.1` | `autotrade_skill_html_doc_writer_v0_1` |
| `AutoTrade_A81_DesignDocSetWriter_v0_1` | `gpt-5.6-luna` | `autotrade_skill_design_doc_set_writer_v0_1` |
| `AutoTrade_A82_ImplementationDetailDesigner_v0_1` | `gpt-5.6-luna` | `autotrade_skill_implementation_detail_design_v0_1` |
| `AutoTrade_A90_DesignReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_design_review_v0_1` |
| `AutoTrade_A91_ImplementationDetailReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_implementation_detail_review_v0_1` |
| `AutoTrade_A110_PythonTestEngineer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_test_quality_v0_1` |
| `AutoTrade_A120_PythonImplementer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_implementation_v0_1` |
| `AutoTrade_A130_VerificationEngineer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_test_quality_v0_1` |
| `AutoTrade_A140_DebugEngineer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_debug_recovery_v0_1` |
| `AutoTrade_A150_PythonCodeReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_code_review_v0_1` |
| `AutoTrade_A160_TradingSecurityReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_code_review_v0_1` |

P5-08の外部Data取得用に、既存の実行可能な外部I/O Worker／Runnerを推測してはならない。現在の `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1` はnetwork禁止であり、A120も外部API禁止である。P5-DATA-G1後に使用する具体的な取得Runner、固定コマンド、target scope、Evidence rootが別途承認・登録されない場合、P5-08は `P5-EXTERNAL-WORKER-UNKNOWN` として停止し、P5-09以降を外部Data PASSとして扱わない。

## 9. Unknown・Blocked・後続Phase

| ID | 状態 | 決定者／期限 | Evidence | 未決時の扱い |
|---|---|---|---|---|
| `UNK-P3-01` | 未解消 | P5 Data owner／P5-DATA-G1後 | 長期Data、期間、本数、市場数、Provenance、Quality | 固定fixtureを実市場PASSにしない。P6へ再分類 |
| `UNK-P3-05` | 未解消 | P5 Data／Execution owner | 市場別Cost／Slippage／Gap、固定仮定との差分 | 推測補完しない。P6へ再分類 |
| `UNK-P3-07` | 未解消 | P5 Calendar owner | 公式Calendar、version、hash、DST／Roll／休場 | Calendar不一致でData／Signal停止 |
| `Q-243` | 後続Gate | Product／Architecture／運用者 | 安全境界、初期候補、実行可能性、性能 | 4項目を分離し、未決をPassにしない |
| `RQV2-BLK-001` | operator override履歴 | Requirements／Document control | `tests/evidence/phase1/`欠落と適用範囲 | 機械PASSへ一般化しない |
| `UNK-P4-04B-001〜005` | 未解消 | Persistence／Ops／DB Gate前 | retention、backup、SQLite version、concurrency、migration | P5 DB作成・migrationへ流用しない |
| `UNK-P4-04D-004` | 未解消 | Ops／Security | host outbound isolation | 外部Data実証前に方式とEvidenceをGateで固定 |
| `UNK-P4-UI-002` | 未解消 | UI QA／Ops | font／OS／DPR／browser baseline | P5 UI表示をformal pixel PASSにしない |
| `EXTERNAL-DATA-PROVIDER-SECRET` | 未承認 | 運用者／Data／Security | 契約、費用、Secret mask、通信、保存境界 | P5-DATA-G1未承認なら外部I/O禁止 |
| `P5-EXTERNAL-WORKER-UNKNOWN` | 未定義 | Architecture／Ops／期限はP5-DATA-G1前 | 取得Runner、固定command、scope、hash、Evidence | 推測起動せず、実証完了を宣言しない |

## 10. 完了条件

P5-H2へ提出できるのは、次をすべて満たした場合だけである。

- 対象5候補、4資産種類、5時間足、Symbol／取引所／限月／Roll／単位の対応がCatalog version付きで再現できる。
- Raw／Normalized／Quality／Manifest／Calendar／Provenance／hashの保存境界、相対path、再生成が一致する。
- 欠損、重複、時刻逆行、異常値、未来Data、Calendar不一致、Look-ahead、Survivorshipの停止Evidenceがある。
- 固定仮定と実測Cost／Slippage／Gapが分離され、P4 syntheticから実測値を推定していない。
- 長期期間、本数、市場数、train／validation／holdout、Walk-forward分割とhashが一致する。
- 外部通信、Provider契約、費用、Secret、保持・再配布、rate、失効、監査の承認範囲がP5-DATA-G1と台帳で一致する。
- P6へ渡すData contract、Calendar、Cost／Gap version、未解消Unknown、停止条件、Evidence indexが揃う。
- `Critical=0`、`High=0`。起動不能Fallbackがあった場合は、独立実行済みと偽らず、Fallbackの責務チェックリストと自己レビューを記録する。

## 11. 共通実ランタイム起動契約（各直接実行Promptへ埋込み）

以下をP5-01〜P5-11の各直接実行Promptへ適用する。名前の列挙、JSON読込、Skill適用、ルートAgentの自己レビューは起動証跡ではない。

1. ルート実行Agentは、最初に `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` の利用可否を確認する。利用可能なら、Prompt記載のOrchestrator JSON path、`model=gpt-5.6-terra`、Phase／Step、入力・出力境界、Agents、Skillsを渡してCoordinatorを1体spawnする。
2. CoordinatorはPromptのAgents欄にある全Agentを一体ずつspawnする。各Agent JSON pathと定義JSONの固定modelを `model` 引数へ明示し、Orchestrator JSONの `agents` map外のAgentも省略しない。各Agentをwaitし、完了statusと出力参照を取得する。
3. 実Agentとして扱えるのは、`agent_id`、JSON path、固定model、受付status、完了status、出力参照が揃ったAgentだけである。`orchestrator_agent_id`とCoordinatorの受付／完了も保存する。
4. spawn／waitが使えない、固定modelを受理できない、Coordinatorが子Agentを起動できない、または出力を取得できない場合は、先に `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`dispatch_mode=LOCAL_FALLBACK_NO_SUBAGENTS`、未起動Agent、理由、確認時刻、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`をログへ記録する。その後、ルート実行Agentが当該Agentの責務をチェックリストで順次適用して継続する。
5. Fallbackで行った確認を独立Agentの実行結果、独立レビュー、固定model実行済みと書かない。実行ログにruntime backend、親／子ID、全試行Agent、JSON path、model、Skills、start／end、status、出力参照、独立性、review mode、入力hash、成果物hash、finding hashを記録する。
6. 起動不能は単独の停止条件にしない。Human Gate未承認、外部I/O／Secret／費用／実資金の範囲逸脱、UnknownのPass、Core境界違反、必須成果物／Evidence／追跡表の欠落、Critical／High未解決、default_orchestrator変更は、Fallback中も停止する。

## 12. Step別の直接実行Prompt

以下のコードブロックは、一つずつ順番に実行する。各Promptは、最初に入力文書、統合台帳、Git状態、対象JSON／Skillを再読し、dispatch receiptを保存してから作業する。P5-H0、P5-H1、P5-DATA-G1、P5-H2の承認を推測してはならない。

### P5-01 入力・P4接続点・Data対象・REQ追跡

```text
Step ID: P5-01
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。Agentは各定義JSONのmodelをmodel引数へ明示する（A10/A20/A81/A90=gpt-5.6-luna、A80=gpt-5.1）。代替model・代替Agent・default_orchestratorは禁止。
Skills: autotrade_skill_source_reader_v0_1, autotrade_skill_architecture_writer_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_orchestration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H0=APPROVEDを統合台帳で確認する。設計・読み取り・HTML・ログだけを更新し、外部Data、Provider、Secret、費用、外部I/O、依存、実Run、Core、P4 DBを変更しない。
入力: Phase5計画入力一覧、RQV2正式要件、RQV2ロードマップ、P4完了HTML、P4-03〜P4-04D、P4 Evidence、統合台帳、doc/index.html、指定AI部品JSON／SKILL.md。
実施: P4から受け取ったData／Manifest／保存／Quality接続点を再照合し、MCL/M6A/MZC/MZS/MZW、4資産種類、D1/H4/H1/M30/M15、Catalog／Calendar／Quality／Cost／Gap／HoldoutのREQ→UC→Data object→Test→Evidence→Gateを行単位で追跡する。P5対象外のBroker／Paper／Live／実資金／実Risk／Cloudを別表に固定する。doc/phase5/01_要件追跡/01_Phase5入力・Data対象・REQ追跡.html、plan/phase5/ログ/P5-01_入力・Data対象・REQ追跡_2026-08-12.mdを作成し、doc/index.htmlへ導線を追加する。
レビュー: A90がFindings firstで入力欠落、P4契約の誤一般化、UnknownのPass化、Gate漏れ、リンク不足をレビューする。A80/A81の責務チェックリストも適用し、Critical/Highを同Stepで反映する。
完了条件: P5対象・非対象、P4接続点、REQ／UC／Test／Evidence／Gate、Unknown、停止条件、dispatch receiptが相互に一致し、Critical/High=0。
停止条件: P4接続点不明、対象・時間足不明、P4 syntheticを実市場Evidenceへ一般化、P5-H0未承認、外部I/O／Secret混入、必須receipt欠落、Critical/High未解決。
```

### P5-02 Catalog／Provider／Data contract詳細設計

```text
Step ID: P5-02
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。Agent固定modelはA10/A20/A40/A50/A70/A82/A90/A91=gpt-5.6-luna、A80=gpt-5.1。各JSONのmodelを再読し、model引数へ明示する。A70はOrchestrator JSONのagents map外だが省略しない。
Skills: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_architecture_writer_v0_1, autotrade_skill_domain_modeling_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_orchestration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H0=APPROVED、P5-01完了を確認する。Provider候補の公式仕様読解は許可するが、アカウント、Secret、endpoint接続、費用発生、外部Data取得、依存導入はしない。
入力: P5-01正式HTML／ログ、正式要件、P4 Data接続点、DB／file境界、統合台帳、公式一次情報（必要な場合）、AF-D14/AF-D16/AF-D17、doc/index.html。
実施: Catalog version、論理ID→実Symbol／取引所／限月／Roll／単位、4資産種類、5時間足、Provider／schema／契約範囲、Data request、Raw／Normalized／Quality／Manifest／Evidenceの境界、relative path、hash、再生成、保持・削除・再配布、Secret参照・mask・失効・監査、外部通信の許可・禁止、Fail-closed条件を設計する。Providerは識別子と契約条件の設計に留め、推測値や実接続を入れない。doc/phase5/02_データ詳細設計/02_Data_Catalog_Provider_DataContract詳細設計書.html とログを作成し、doc/index.htmlへ導線を追加する。
レビュー: A82/A91が型、入出力、境界、例外、全テスト、AF-D16適合を監査し、A50がAdapter境界、A70がSecret／外部I/O／停止、A90がREQ／Unknown／Gateを監査する。Critical/Highは反映・再レビューする。
完了条件: Catalog／契約／外部境界／保存境界／Secret境界／Evidence／TestがP5-03、P5-04、P5-DATA-G1へ一対一以上で接続され、Critical/High=0。
停止条件: 実Symbol等を推測、Provider権限・費用・再配布不明、Secret値を出力、外部接続を実行、P5-01未完了、Unknownを仮決定、receipt欠落、Critical/High未解決。
```

### P5-03 Raw／Normalized／Quality／Calendar／Provenance詳細設計

```text
Step ID: P5-03
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A20/A30/A40/A50/A70/A82/A90/A91=gpt-5.6-luna、A80=gpt-5.1。各Agent JSONの固定modelをmodel引数へ明示する。A30/A70はmap外でも省略しない。
Skills: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_domain_modeling_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H0=APPROVED、P5-02完了を確認する。設計書とログだけを更新し、DB／migration／repository／fixture／Application／UIソース、依存、実Run、外部I/O、Coreは変更しない。
入力: P5-02 Data contract、P5-01追跡、P4 Result／Evidence／CSV境界、正式要件、既存DBN decoder／Raw／Normalized契約、統合台帳、AF-D16/AF-D17。
実施: Raw保持、正規化、timestamp／timezone／unit、来歴、source／request／content hash、Manifest、相対path、再生成、Calendar version／hash、DST／休場／短縮日／Roll、欠損／重複／逆行／異常値／未来Data／Look-ahead／Survivorshipの判定とFail-closed停止を、実装者が判断なく実装できる粒度で設計する。P4 metadata DBにData本文を複製しない。doc/phase5/02_データ詳細設計/03_Data_Raw_Normalized_Quality_Calendar_Provenance詳細設計書.html とログを作成し、Mermaid構造図・正常／失敗flow直後の受渡し表、全テストを含める。
レビュー: A91がモジュール、型、保存、処理順、例外、全試験を監査する。A50が外部ID／変換境界、A30/A40がReplay／Strategy入力／Look-ahead、A70がSecret／path／fail-closed、A90がREQ／Core／Unknownを監査する。Critical/Highを反映して再レビューする。
完了条件: Raw／Normalized／Quality／Calendar／Provenanceの責務、保存境界、停止、再生成、Test／Evidence、P5-08／09の入力が一致し、Critical/High=0。
停止条件: 来歴・hash・Calendar・timezone・停止条件・保存境界が未定義、P4 DBへ無断追加、実Data取得、依存導入、Core変更、receipt欠落、Critical/High未解決。
```

### P5-04 Cost／Gap／長期／Holdout／Walk-forward／品質Test設計

```text
Step ID: P5-04
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
Agents: AutoTrade_A30_StrategyQaArchitect_v0_1, AutoTrade_A40_ExecutionEnginePocArchitect_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A30/A40/A50/A70/A82/A90/A91=gpt-5.6-luna、A80=gpt-5.1。各JSONの固定modelをmodel引数へ明示する。A30/A70はmap外でも省略しない。
Skills: autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_execution_model_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_golden_test_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H0=APPROVED、P5-02/P5-03完了を確認する。固定local dummyの設計とTest設計だけを行い、外部Data、費用、Secret、実測取得、実Run、Core変更は発火しない。
入力: P5-02/P5-03正式設計、P4実装詳細、P4 fixed fixture、正式要件、統合台帳、既存Cost／Roll／Gap／Holdout契約、trusted scope規則。
実施: 市場別Cost／Slippage／Gapを実測値と固定仮定に分け、保守側境界、roll／spread、欠損、長期期間、本数、市場数、train／validation／holdout、Walk-forward、look-ahead監査、再現hashを設計する。schema／contract／replay／failure injection／manifest mismatch／calendar mismatch／cost provenance／holdout再利用拒否をTEST-P5-DATA-IDとして入力・操作・期待・停止条件・Evidenceで定義する。doc/phase5/03_品質設計/04_Phase5_DataQuality_Cost_Holdout_Test_RunManifest設計.html とログを作り、P5-06、P5-08、P5-09、P5-H2へ結ぶ。
レビュー: A91が実装可能性と試験網羅性、A30/A40がLook-ahead／Replay／split、A50がsource／provider boundary、A70が外部I/O／Secret／隔離、A90がREQ／Gate／Unknownを監査する。Critical/Highを同Stepで反映・再レビューする。
完了条件: TEST-P5-DATA-IDがData contract、Calendar、Cost／Gap、期間分割、P5-DATA-G1、Evidenceへ一対一以上で接続し、Critical/High=0。
停止条件: 実測と仮定の混同、期間／分割／未来参照不明、P4 syntheticからの推測、外部I/O、receipt欠落、Critical/High未解決。
```

### P5-05 詳細設計統合レビュー・改訂・P5-H1候補

```text
Step ID: P5-05
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
Agents: AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A82_ImplementationDetailDesigner_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A91_ImplementationDetailReviewer_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1
Model: Orchestrator=gpt-5.6-terra。A81/A82/A90/A91/A70=gpt-5.6-luna、A80=gpt-5.1。固定modelをJSONから再読して渡す。A70はmap外でも省略しない。
Skills: autotrade_skill_implementation_detail_review_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_implementation_detail_design_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_revision_integration_v0_1, autotrade_skill_traceability_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H0=APPROVED、P5-01〜P5-04完了を確認する。設計書、レビュー、改訂、ログ、doc/index.htmlだけを更新し、外部I/O、Secret、依存、実装、実Run、Core変更は発火しない。
入力: P5-01〜P5-04正式HTML／ログ、統合台帳、正式要件、P4設計、AF-D14/AF-D16/AF-D17、AI部品JSON／Skill。
実施: A91の実装詳細レビュー、A90の横断／Red Teamレビュー、A70の外部境界監査、A80/A81の改訂統合を行う。Findings first、採否表、Critical／High閉鎖、REQ／DEC／UNK／ART、P5-H1の承認対象（local dummyのみ）を記録する。P5-DATA-G1の未承認をP5-H1で承認したように書かない。doc/phase5/04_レビュー/05_Phase5詳細設計レビュー・改訂記録.html とログを作成する。
レビュー: A90とA91は相互に独立した観点で網羅表を確認し、A80/A81が反映後のリンク・index・履歴を確認する。起動できなかったAgentはFallbackチェックリストで再確認し、独立性をfalseにする。
完了条件: P5-02〜04の設計にCritical/Highがなく、P5-H1へ提出するlocal scope、RED、Run Manifest、停止条件、Unknown、Evidence構造が揃う。
停止条件: Critical/High、設計書間不一致、外部Data承認の混入、Unknownの仮決定、必須receipt欠落、doc/index.html導線欠落。
```

### P5-H1 ローカル固定Data contract実装・品質開始承認

```text
Step ID: P5-H1
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
発火制御: P5-05のレビュー済みHTML、Critical/High=0、対象path、fixture hash、Run Manifest、外部I/O=0を確認し、運用者がP5-H1を明示承認するまで開始しない。P5-H1承認は外部Data、Secret、費用、Provider、Broker、Paper、Liveを含まない。
記録: 承認後、対象Run ID、HEAD、change hash、fixture hash、trusted scope、承認文言、承認範囲、除外範囲を `tests/evidence/phase5/<RunId>/human-gate-p5-h1.md` と統合台帳へ記録する。承認がない場合は `HUMAN_GATE_REQUIRED` としてP5-06を開始しない。
```

### P5-06 固定local Data contract／Quality RED→GREEN

```text
Step ID: P5-06
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
Agents: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A120_PythonImplementer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。全Agent=gpt-5.6-luna。各JSONの固定modelをmodel引数へ明示する。
Skills: autotrade_skill_python_test_quality_v0_1, autotrade_skill_python_implementation_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_orchestration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。A110→A120→A130→A140（必要時）→A150/A160の順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H1=APPROVED、trusted scope登録、host outbound isolation条件、fixture hashを確認する。固定local dummy、承認済みtarget_paths、既存P4境界内だけを対象とし、network、Provider、Secret、実Data、Core、P4 DB、未登録Runを変更しない。
入力: P5-02〜05のレビュー済み設計、P5-H1承認記録、Run Manifest、trusted_scopes.json、P4 fixture、既存Data contract／decoder。
実施: A110がTEST-P5-DATA-IDのlocal固定dummy REDを作り、A120が承認範囲の最小実装、A130が検証、A140が上限付き原因別修正、A150/A160がコード／安全レビューを行う。欠損／重複／逆行／hash mismatch／calendar mismatch／look-aheadをfail-closedで確認する。外部通信0をEvidenceへ記録する。
完了条件: RED→GREEN、固定fixture hash一致、target-only、外部通信0、Critical/High=0、A150/A160のレビュー、Evidence indexが揃う。P5-DATA-G1を承認済みと扱わない。
停止条件: Run未登録、target外変更、外部通信、Secret、fixture改変、test skip／削除、Critical/High、host isolation未確認、receipt欠落。
```

### P5-07 外部Data Gate準備・台帳同期

```text
Step ID: P5-07
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A50/A70/A81/A90=gpt-5.6-luna、A80=gpt-5.1。各Agent JSONの固定modelを渡す。A50/A70はmap外でも省略しない。
Skills: autotrade_skill_source_reader_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_traceability_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H1=APPROVED、P5-06完了を確認する。Gate申請書と台帳だけを更新し、Providerへの接続、Secret参照、費用発生、外部I/O、取得Runner起動はしない。
入力: P5-02〜06、P5-H1承認、統合台帳、正式要件、Provider候補の公式一次情報、対象候補、保存・再配布・費用・Secret・通信の設計。
実施: P5-DATA-G1の承認対象を空欄・仮値なしで列挙する。対象Symbol／期間／時間足、Provider／契約／権限、endpoint／rate、費用上限、Secret参照・mask・失効、通信方式、Raw／Normalized／Quality／Manifest／Evidenceの保存、保持・再配布、停止条件、取得Runnerの固定command、Run ID、target_paths、Data hash、host isolation、再現手順を記載する。doc/phase5/05_実証/06_Phase5外部Data_Gate申請・範囲表.html とログを作り、未承認を統合台帳へ登録する。
レビュー: A50がProvider／外部ID境界、A70がSecret／通信／費用／停止、A90がREQ／Gate／Unknown、A80/A81が文書・index・台帳導線を監査する。
完了条件: 運用者がP5-DATA-G1で判断できる完全な申請表と、取得Runnerが未定義ならP5-EXTERNAL-WORKER-UNKNOWNとして停止する記録がある。
停止条件: 対象・費用・契約・Secret・通信・保存・Runner・Evidenceが不明、P5-H1未承認、外部I/Oが発火、Unknownを仮決定、receipt欠落。
```

### P5-DATA-G1 市場Data Provider専用Human Gate

```text
Step ID: P5-DATA-G1
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
発火制御: P5-07の申請表を読み、運用者がP5-DATA-G1を明示承認するまで外部I/O、Secret、費用発生、実Data取得を禁止する。P4-H2、P5-H0、P5-H1の承認で代用しない。
承認対象: 市場Data Providerだけの対象Symbol／期間／時間足、契約・利用権限、費用上限、endpoint／rate／通信方式、Secret参照・mask・失効・監査、Raw／Normalized／Quality／Manifest／Evidence保存、保持・削除・再配布、停止・再試行・再生成、Run ID、target_paths、Data hash、host isolation、取得Runnerの固定command。
承認除外: Broker／Paper／Live／実資金、実Risk値、利益性、対象拡大、別Provider、別endpoint、Secret用途変更、Cloud、未登録Runner。
記録: 明示承認を `tests/evidence/phase5/<RunId>/human-gate-p5-data-g1.md` に保存し、統合台帳のP5-DATA-G1行、承認範囲、期限、再開条件、Evidence先を更新する。不承認・空欄・条件付き未確定は `HUMAN_GATE_REQUIRED` とし、P5-08を開始しない。
```

### P5-08 承認範囲内の限定Data取得・Raw／Normalized Evidence

```text
Step ID: P5-08
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A90_DesignReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A50/A70/A90=gpt-5.6-luna。固定modelを各JSONから読み、model引数へ明示する。
Skills: autotrade_skill_source_reader_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_orchestration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。外部I/Oより前に完了させる。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-DATA-G1=APPROVED、承認されたRun ID／target_paths／固定command／Secret参照／host isolationをすべて検証する。承認範囲外のData、endpoint、費用、Secret、対象拡大、Broker、Paper、Liveは発火しない。取得Runnerが実在・固定・承認済みでない場合はP5-EXTERNAL-WORKER-UNKNOWNとして外部I/Oをせず記録する。
入力: P5-02〜07正式設計、P5-DATA-G1承認記録、固定取得Runner／command、Run Manifest、target scope、Provider契約、固定対象、Evidence root、統合台帳。
実施: 承認対象を変更せず、Raw受信時刻、source／request／content hash、Manifest、Normalized変換、timezone／unit、相対path、Secret非出力、通信監査、停止・再試行・再生成を記録する。欠損、重複、逆行、hash不一致、Calendar不一致、未来Dataは推測補完せずFail-closedで停止する。tests/evidence/phase5/<RunId>/へsanitized Evidenceを保存する。
レビュー: A50が変換・外部ID、A70がSecret／通信／費用／path、A90が承認範囲・停止・Evidence・Unknownをレビューする。外部I/Oの正式実行結果とAgent起動結果を混同しない。
完了条件: 承認範囲、Raw／Normalized hash、Manifest、provenance、通信・費用・Secret監査、停止条件、dispatch receiptが一致し、Critical/High=0。
停止条件: Gate不一致、Runner不明、承認範囲外、Secret平文、費用上限超過、hash不一致、欠損補完、未来Data、host isolation不明、Critical/High、receipt欠落。
```

### P5-09 Quality／Calendar／Cost／Gap／期間分割／Holdout実証

```text
Step ID: P5-09
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
Agents: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A90_DesignReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A110/A130/A140/A150/A160/A90=gpt-5.6-luna。各JSONの固定modelをmodel引数へ明示する。A90はQuality Orchestrator map外でも省略しない。
Skills: autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_design_review_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-DATA-G1=APPROVED、P5-08完了、trusted scope、host isolation、Run Manifest、Data／Calendar hashを確認する。承認範囲内のDataだけを対象とし、Broker、Paper、Live、実資金、Core変更、未登録Runは発火しない。
入力: P5-04品質設計、P5-08 Raw／Normalized Evidence、Data／Calendar／Manifest hash、Cost／Gap provenance、期間分割、holdout／walk-forward定義、trusted scope。
実施: 欠損、重複、逆行、異常値、DST、休場、Roll、Calendar不一致、未来参照、Look-ahead、Survivorship、Cost／Slippage／Gapの実測／仮定分離、長期期間、本数、市場数、train／validation／holdout、Walk-forward再現を固定入力で検証する。結果、停止一覧、再生成手順、hash、Evidence indexを作成する。利益性・Live適合を判定しない。
レビュー: A130が検証、A140が上限付き復旧、A150/A160が安全・コード、A90がData contract／Gate／Unknown／Evidenceをレビューする。未実行、条件外、font／OS未固定をPASSにしない。
完了条件: 対象ごとのQuality／Calendar／Cost／Gap／期間分割／holdout Evidence、再現hash、停止証跡、レビュー、dispatch receiptが揃い、Critical/High=0。
停止条件: hash不一致、Calendar未確認、欠損補完、未来Data、実測／仮定混同、holdout汚染、Gate不一致、Unknown PASS化、host isolation不明、Critical/High、receipt欠落。
```

### P5-10 統合・独立レビュー・P5-H2候補

```text
Step ID: P5-10
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A50/A70/A81/A90=gpt-5.6-luna、A80=gpt-5.1。固定modelをJSONから明示する。A50/A70はmap外でも省略しない。
Skills: autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_source_reader_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_revision_integration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-DATA-G1=APPROVED、P5-08/P5-09完了を確認する。外部I/O、Secret、追加取得、Provider変更、実注文、実資金、Core変更は発火しない。
入力: P5-01〜09正式HTML／ログ、P5-DATA-G1承認、Evidence index／hash、統合台帳、REQ／UC／Test／Evidence追跡、Unknown一覧。
実施: Data contract、Catalog、Raw／Normalized、Quality、Calendar、Cost／Gap、期間分割、holdout、P5-DATA-G1承認、停止／再生成、外部通信／Secret監査、P6引渡しを統合し、REQ→Evidenceのcoverageを再照合する。未解消Unknownは根本原因、owner、期限、再開条件、後続Phaseへ再分類する。doc/phase5/04_レビュー/07_Phase5統合品質・P6引渡し候補.html とログを作成する。
レビュー: A90がFindings firstで外部I/O、Data／Calendar／Cost／Gap、Look-ahead、Gate、Unknown、P6境界を監査する。A80/A81がHTML、index、相互リンク、採否、履歴を確認する。Critical/Highは反映・再レビューし、P5-H2候補に残さない。
完了条件: REQ／UC／Test／Evidenceが追跡可能、実証Evidence hash一致、未解消Unknown明示、P6 Data contractが揃い、Critical/High=0。利益性・Broker・Paper・Live PASSを記載しない。
停止条件: Evidence欠落／hash不一致、Gate証拠不一致、UnknownのPass、外部範囲逸脱、P6境界不明、receipt欠落、Critical/High未解決。
```

### P5-H2 Phase 5完了・P6引渡し承認

```text
Step ID: P5-H2
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
発火制御: P5-10の完了候補、Evidence hash、REQ／UC／Test追跡、P5-DATA-G1範囲、未解消Unknown、P6引渡し表を読み、運用者がP5-H2を明示承認するまでP5-11を開始しない。
承認対象: P5で実証したData contract、対象範囲、Quality／Calendar／Cost／Gap／期間分割／holdout Evidence、P6への引渡し、未解消Unknownと停止条件。
承認除外: 利益性の採用、実Risk、Broker、Paper、Live、実資金、Cloud、対象拡大、未承認Secret。
記録: 承認文言を `tests/evidence/phase5/<RunId>/human-gate-p5-h2.md` に保存し、統合台帳のP5-H2行を更新する。不承認・条件不明・Critical/High残存は `HUMAN_GATE_REQUIRED` または `BLOCKED` として完了を宣言しない。
```

### P5-11 完了記録・台帳同期・P6計画入力引渡し

```text
Step ID: P5-11
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A81/A90=gpt-5.6-luna、A80=gpt-5.1。各JSONの固定modelを明示する。
Skills: autotrade_skill_source_reader_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_revision_integration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H2=APPROVEDを統合台帳と承認Evidenceで確認する。完了HTML、P6計画入力、ログ、台帳、doc/index.htmlだけを更新し、外部I/O、実Data追加取得、Provider変更、Broker、Paper、Live、実資金、Core、DB migrationは発火しない。
入力: P5-10正式HTML／ログ、P5-H2承認、全Evidence hash、Data contract／Calendar／Cost／Gap version、Unknown、P6ロードマップ、統合台帳。
実施: doc/phase5/06_完了/08_Phase5完了判定・Phase6計画引渡し.html、plan/phase5/Phase6計画入力一覧_2026-08-12.md、plan/phase5/ログ/P5-11_完了・P6引渡し_2026-08-12.mdを作成する。P5の実証範囲、未承認範囲、Unknown、P6へ渡すData contract／Calendar／Cost／Gap／停止条件を行単位で記録し、doc/index.htmlと統合台帳を同期する。
レビュー: A90が完了範囲の過大一般化、UnknownのPass、P6外部副作用混入を監査し、A80/A81がリンク、index、改訂履歴、台帳同期を確認する。Fallbackの場合は独立完了と記載しない。
完了条件: P5-H2承認、完了HTML、P6入力、Evidence index／hash、台帳、doc/index.html、dispatch receiptが一致し、P6の開始条件とP5非対象が明確である。
停止条件: P5-H2未承認、Evidence不一致、P6入力欠落、Unknown PASS化、外部I/O／Broker／Paper／Live混入、receipt欠落、Critical/High未解決。
```

## 13. レビューと受入判定

P5-05、P5-10では、Findings firstの順にCritical／Highを先に列挙し、採否表と修正後の再レビューを残す。設計AgentとReviewerが起動できた場合は実AgentのID・固定model・完了statusをEvidenceへ保存する。起動できなかった場合は `SELF_REVIEW_FALLBACK` と明記し、独立レビュー済みという表現を使わない。

Phase 5の完了判定は、外部Dataの実証範囲に限定する。P4の固定fixture、P5のData Quality、利益性、Broker接続、Paper、Live、実資金を同じPASSへ混ぜない。P5-DATA-G1の承認がないP5-08／09は開始できず、P5-EXTERNAL-WORKER-UNKNOWNが解消されない場合は、P5-H2を完了扱いにしない。

## 14. 計画作成時の実行記録

- 計画作成の読み取り専用助言Coordinator: `019ff44d-da57-79d0-a9af-331c5590b046`（Cicero）。
- 実行方式: `ADVISORY_RUNTIME_SPAWN`。実行対象はPhase5ではなく、計画のStep／Gate／起動契約レビューだけ。
- 変更: 助言Agentはファイル変更、外部I/O、依存導入、Phase5 Runを行っていない。
- 限界: 呼出し元ランタイムから `.codex` の完全名・固定modelを実行コンポーネントとして束縛したことは、Agent IDだけでは証明できない。そのため本計画の直接Promptは、実行時にJSON path、固定model、spawn／wait receiptを再取得する契約を必須とする。

## 15. 変更履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-08-12 | v0.1 | P4-10引渡しを基に、Phase5を入力追跡、Data契約、Raw／Normalized／Quality／Calendar、Cost／Gap、長期／Holdout、local固定品質、Data Provider専用Gate、限定外部Data実証、統合レビュー、P6引渡しへ分割した。全直接PromptへRDC-PHASE-PLAN-0.2、起動不能時Fallback、固定model、receipt、Unknown／Gate停止を追加した。 |

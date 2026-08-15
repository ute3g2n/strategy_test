# Phase 5 実行計画書 v0.1

- 計画ID: `P5-PLAN-001`
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- 対象Phase: Phase 5 市場データ運用化と実証
- 作成日: 2026-08-12（Asia/Tokyo）
- 状態: `P5-11_BLOCKED_P5_H2_NOT_APPROVED`
- 前Phase: Phase 4 Product/Application・Backtest（`P4-PLAN-001`）
- 前Phase承認: `P4-H2=APPROVED`。P4-H2はPhase 5の実装、外部Data取得、Secret投入、外部I/Oを承認しない。
- 計画作成標準: `AutoTradePhasePlanning_Orchestrator_v0_1`、`AutoTrade_A05_PhaseExecutionPlanner_v0_1`、`autotrade_skill_phase_execution_planning_v0_1`
- AI部品変更標準: `AutoTradeComponentLifecycle_Orchestrator_v0_1`、`AutoTrade_A06_AiComponentEngineer_v0_1`、`autotrade_skill_ai_component_lifecycle_v0_1`
- 起動契約版: `RDC-PHASE-PLAN-0.2`、`RDC-AI-COMPONENT-0.2`

## 1. 結論

Phase 5は、P4で作成したProduct/ApplicationのData接続点を引き継ぎ、市場Dataを対象・契約・来歴・品質・Calendar・Cost／Slippage／Gap・長期期間・Holdout／Walk-forwardまで再現可能なEvidenceへ変換するPhaseである。計画作成時の初期5候補（MCL、M6A、MZC、MZS、MZW）は履歴として保持するが、2026-08-14の運用者指示により初期運用候補から外し、Binance Data VisionのCrypto暫定対象（BTCUSDT、ETHUSDT）へスコープを変更した。

ただし、P4-H2はP5開始承認ではない。この計画を作成した時点では、外部Providerへの接続、費用発生、Secret参照、外部I/O、実Data取得、Broker／Paper／Live、実資金、Cloudを開始しない。P5-H0、P5-H1、P5-DATA-G1、P5-H2を分離し、承認範囲を越える発火を禁止する。2026-08-13の旧P5-DATA-G1（Databento範囲）は履歴として保持し、2026-08-14のProvider変更後はBinance用の新しいP5-DATA-G1 amendmentが必要である。費用事前見積り必須ルールは廃止済みだが、Runner・対象・利用条件・外部Run Evidence不足のためP5-08以降は停止中である。

### 1.1 2026-08-14 Binance Data Visionスコープ改訂

- ProviderをBinance Data Visionの公開アーカイブへ変更する。
- 旧初期候補 `MCL`、`M6A`、`MZC`、`MZS`、`MZW` は初期運用候補から外し、履歴として保存する。
- 入力履歴で具体的に名前があるCryptoだけを採用し、暫定対象を `BTCUSDT`、`ETHUSDT` とする。
- `Binance Spot`、Spot Kline `1m`、UTC、24/7 Calendarを推奨暫定値とする。Futures、Funding、Liquidation、他のアルトコインは別Gateとする。
- 既存Databentoの承認・request・RunnerをBinanceへ読み替えない。新しい申請表、request、Runner、Evidence root、保護対象のchecksum／hash検証がP5-08再開条件である。管理用hash検証は再開条件にしない。
- 詳細は `doc/phase5/06_方針転換/02_Binance_Data_Vision方針転換・Crypto暫定対象.html` と `plan/phase5/ログ/P5-08_Binance_Data_Vision方針転換・Crypto暫定対象_2026-08-14.md` を正本とする。

### 1.2 P5-08以降の現行実行範囲

| 項目 | 現行の計画値 | 実行前の扱い |
|---|---|---|
| Provider／接続先 | Binance Data Vision公開アーカイブ、`https://data.binance.vision/` | 新しいP5-DATA-G1 amendmentで許可URLと取得方法を固定する。Binance REST APIへ自動拡張しない |
| 市場・対象 | `asset_type=crypto`、`market_segment=spot`、`BTCUSDT`／`ETHUSDT` | Spotは暫定対象。Futures、Funding、Liquidation、他のsymbolは対象外で、別Gateなしに追加しない |
| 基底Data | Spot Kline `1m` の月次ZIP。日次ZIPは境界照合が承認された場合だけ使う | Tick、Order book、Trade stream、REST APIページングをP5-08の主経路にしない |
| 期間 | `2025-02-24T00:00:00Z` 以上、`2026-08-01T00:00:00Z` 未満を旧P5からの比較用暫定継承 | Binance用Gateで再承認されるまで確定値と扱わない。全履歴へ勝手に拡張しない |
| 時刻・Calendar | UTC、`CRYPTO_24_7_UTC`。2025-01-01以降のSpot timestampはmicroseconds想定 | unitを検査してManifestへ記録する。DST、CME休場、短縮日、限月、RollはCrypto Spotへ適用せず、該当性を`N/A`として記録する |
| 取得認証 | API key／Secretを使用しない。既存環境変数のキーも読まない | 公開アーカイブのHTTPS allowlistだけを使う。Secret metadataを入力・ログ・Evidenceへ持ち込まない |
| 費用 | Provider公開Data費用 `0 USD`。保存・通信・実行の内部budgetは別管理 | 事前費用見積りは開始条件にしないが、内部上限と実行後usage／保存量の監査は残す |
| 成果物 | Raw ZIP／`.CHECKSUM`／展開CSV、Normalized、Quality、Catalog、Calendar適用表、Provenance、Evidence index | `.CHECKSUM`やData内容のchecksumはデータ完全性・再現性のためだけに扱う。文書管理用hash、manifest hash、receipt hashは作らない |

本計画の直接実行プロンプトは、Orchestrator／Agent／Skillの名前を列挙するだけでは完了扱いにしない。各Promptへ、実ランタイムのOrchestrator spawn、指定Agent全件の個別spawn、固定model受理、wait完了、受領証跡、起動不能時の継続Fallbackを埋め込む。起動不能は単独の停止条件にしないが、未起動を起動済み・独立レビュー済みと偽らない。Human Gate、外部I/O、Secret、UnknownのPass、Critical／High、必須Evidenceの欠落はFail-closedで停止する。

## HASH-FUTURE-01〜08／Step 05 現行運用ルール

- 本計画および本計画から派生するStep／Phaseの完了、受入、handoff、retry、BLOCKED判定では、管理用hash（差分hash、変更hash、Worktree／Baseline／Manifest／Evidenceのfingerprint、入力・成果物・findingの管理hash）を取得、保存、比較、再計算しない。これらの管理チェックは、ユーザーが明示的に与えた権限によりフローから完全に除外する。
- 安全・データ・再現性に直接結び付く保護hashだけを、所有する実行基盤の内部で目的、入力範囲、失敗時の停止条件とともに扱う。例は固定fixture、実Data／Raw／Calendar／Replay、依存供給網などのidentityであり、保護hash不一致はFail-closedで停止する。
- 過去の計画・ログに残る管理hashは履歴としてのみ参照し、現行の受入条件、再試行条件、BLOCKED条件、承認条件へ再利用しない。管理hashの代替としてUUID、mtime、fingerprint、別名checksumを導入しない。
- このルールは本計画の全Prompt、スクリプト、Run Manifest、Evidence受渡し、統合台帳更新へ継承する。管理hashの記載が必要になった場合は、計算せず `HASH_MANAGEMENT_DISABLED` として扱い、保護対象か不明なhashはUnknown／Human Gateへ送る。

## 2. Phase 5の目的と非目的

### 2.1 目的

- 論理IDから実Symbol、quote asset、market segment、Provider path、timestamp unit、数量単位をEvidence付きで対応付ける。旧先物の取引所・限月・Rollは現行Crypto Spotでは`N/A`として明示する。
- 現行暫定Crypto対象（BTCUSDT／ETHUSDT）、旧5候補の履歴境界、4資産種類、D1／H4／H1／M30／M15の時間足を固定する。
- Raw／Normalized／Quality／Catalog／Calendar適用表／Provenance／Evidence indexの責務と保存境界を確定する。Raw archiveの`.CHECKSUM`とData内容のidentityは、データ完全性・再現性に直接必要な範囲だけを保護する。
- 欠損、重複、時刻逆行、timestamp unit誤り、OHLCV異常、Spot／Futures混入、未来Data、Look-aheadをFail-closedで検出する。DST、休場、短縮日、限月、RollはCrypto Spotでは適用外として誤検出しない。
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
- `P5-DATA-G1` はBinance Data Vision公開アーカイブ専用の別Gateである。`BTCUSDT`／`ETHUSDT`、Spot、1m、UTC、期間、許可URL、Raw／Normalized／Quality／Evidence保存、利用・保持条件、内部budget、host isolation、固定Runnerを承認する。公開Data取得はAPI key／Secretを使わず、Secret参照・mask・失効を実行経路へ追加しない。Broker／Paper用の後続Gateとは別である。
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
| P5-06 | 固定local Data contract／QualityのRED→GREEN・品質Gate | P5-H1 | `PASS` | 不可 | 正式4 Gate、host isolation、fixture pre/postの保護hash一致、wrapper exit 0 |
| P5-07 | 外部Data Gate準備、承認対象表、台帳同期 | P5-06 | 申請表完了・P5-DATA-G1待ち | 不可 | `P5-EXTERNAL-WORKER-UNKNOWN`を保持。外部I/OはP5-DATA-G1承認まで開始しない |
| P5-DATA-G1 | Binance Data Vision Provider専用外部Data Gate amendment | P5-07 | 新しい人間承認 | `BINANCE_AMENDMENT_REQUIRED` | 旧Databento承認は履歴。`BTCUSDT`／`ETHUSDT`、Spot、1m、UTC、24/7、公開Data費用0、API key／Secret非使用、固定Runner／request／allowlistを新Gateで固定 |
| P5-08 | Binance暫定対象の限定Data取得・Raw／Normalized Evidence | Binance用P5-DATA-G1 amendment、運用者waiver | `RAW_AND_EXPANDED_CSV_ACQUIRED` | 実施済み（36件） | `RUN-P5-08-BINANCE-001`に月次Spot Kline 1m ZIP、`.CHECKSUM`、展開CSVを保存。Provider条件とhost isolation通信証拠はこのRunの開始前提から除外したが、事実はUNKNOWN／NOT_VERIFIEDのまま。Normalized／QualityはP5-09で実施 |
| P5-09 | Crypto Spot Quality／Calendar適用／Cost／Gap／期間分割／Holdout実証 | P5-08 Binance Raw Evidence | `QUALITY_EVIDENCE_COMPLETE_WITH_OPEN_UNKNOWN` | 実施済み（local quality evidence） | `RUN-P5-09-BINANCE-001`で2銘柄各753,120本、gap／重複／補間0、UTC D1／H4／H1／M30／M15、Cost／Gap、Holdout分割を記録。Provider条件、P5-08 host isolation、child Agent未起動はUnknownとして未解消 |
| P5-10 | Binance対象の統合・独立レビュー、Unknown再分類、P5-H2候補 | P5-08、P5-09 | `INTEGRATED_REVIEW_COMPLETE_WITH_OPEN_UNKNOWN` | 不可 | REQ/UC/Test/Evidenceを統合し、機械品質・Calendar・splitを再照合。Provider条件、P5-08 host isolation、child Agent未起動、未測定execution costをOpenとして保持し、P5-H2候補は不成立 |
| P5-H2 | Binance対象P5完了・P6引渡し承認 | P5-10 | `HUMAN_GATE_REQUIRED` | 不可 | P5-10のP6引渡し候補は作成済みだが、Open Unknownと人間の明示承認がないため承認対象は未成立 |
| P5-11 | Binance対象の完了記録、台帳同期、P6計画入力引渡し | P5-H2 | `BLOCKED` | 不可 | P5-H2未承認。P5-10候補は承認前の文書に留まり、P5-11の完了HTML・P6計画入力は作成しない |

P5-01とP5-02はP5-01完了後にP5-02を開始する。P5-03、P5-04はP5-02の契約骨子を前提に逐次実行する。P5-05でレビューを閉じるまでP5-H1へ進まない。P5-08は`P5-DATA-G1-BINANCE-AMENDMENT-001=APPROVED`、固定Runner、request、allowlist、運用者waiverが揃った後に発火する。Provider利用条件の事前確認と実行前後host-isolation通信証拠は、`RUN-P5-08-BINANCE-001`の開始前提から除外した。P5-09はP5-08のBinance Raw／展開CSVを入力にlocal quality evidenceを生成済みである。P5-10は統合レビューを完了したが、残るUnknownをPassへ再分類せず、P5-H2候補は不成立とした。

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
| `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1` | `gpt-5.6-luna` | `autotrade_skill_protected_hash_policy_guard_v0_1`, `autotrade_skill_traceability_v0_1` |
| `AutoTrade_A91_ImplementationDetailReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_implementation_detail_review_v0_1` |
| `AutoTrade_A110_PythonTestEngineer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_test_quality_v0_1` |
| `AutoTrade_A120_PythonImplementer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_implementation_v0_1` |
| `AutoTrade_A130_VerificationEngineer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_test_quality_v0_1` |
| `AutoTrade_A140_DebugEngineer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_debug_recovery_v0_1` |
| `AutoTrade_A150_PythonCodeReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_code_review_v0_1` |
| `AutoTrade_A160_TradingSecurityReviewer_v0_1` | `gpt-5.6-luna` | `autotrade_skill_python_code_review_v0_1` |

P5-08〜P5-11の新規・大幅変更成果物では、A95を各StepのPromptへ含め、保護対象のData完全性・再現性identityと管理用hashの境界を静的に判定する。A95はhash値、Manifest、stale、fingerprint、receipt hashを計算・保存・比較・retryせず、管理用hashの導入を許可しない。

P5-08の外部Data取得用に、既存の実行可能な外部I/O Worker／Runnerを推測してはならない。現在の `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1` はnetwork禁止であり、A120も外部API禁止である。P5-DATA-G1後に使用する具体的な取得Runner、固定コマンド、target scope、Evidence rootが別途承認・登録されない場合、P5-08は `P5-EXTERNAL-WORKER-UNKNOWN` として停止し、P5-09以降を外部Data PASSとして扱わない。

## 9. Unknown・Blocked・後続Phase

| ID | 状態 | 決定者／期限 | Evidence | 未決時の扱い |
|---|---|---|---|---|
| `UNK-P3-01` | 未解消 | P5 Data owner／P5-DATA-G1後 | 長期Data、期間、本数、市場数、Provenance、Quality | 固定fixtureを実市場PASSにしない。P6へ再分類 |
| `UNK-P3-05` | 未解消 | P5 Data／Execution owner | 市場別Cost／Slippage／Gap、固定仮定との差分 | 推測補完しない。P6へ再分類 |
| `UNK-P3-07` | 未解消 | P5 Calendar owner | `CRYPTO_24_7_UTC`の適用、配布欠落と市場欠損の区別、version／保護対象identity | Calendar適用不明、または欠損をゼロ埋めした場合はData／Signal停止 |
| `Q-243` | 後続Gate | Product／Architecture／運用者 | 安全境界、初期候補、実行可能性、性能 | 4項目を分離し、未決をPassにしない |
| `RQV2-BLK-001` | operator override履歴 | Requirements／Document control | `tests/evidence/phase1/`欠落と適用範囲 | 機械PASSへ一般化しない |
| `UNK-P4-04B-001〜005` | 未解消 | Persistence／Ops／DB Gate前 | retention、backup、SQLite version、concurrency、migration | P5 DB作成・migrationへ流用しない |
| `UNK-P4-04D-004` | 解消済み（P5-06 formal local host Evidence） | Ops／Security | 固定local harnessのhost outbound isolation | 外部Data実行へ一般化せず、P5-DATA-G1後の外部Runで再確認 |
| `P5-06_BLOCKED` | 解消 | Ops／Security／Human Gate | P5-06正式WSL隔離品質Gateでhost isolation CONFIRMED、4 Gate PASS | P5-06正式EvidenceをP5-07へ引き渡し |
| `UNK-P4-UI-002` | 未解消 | UI QA／Ops | font／OS／DPR／browser baseline | P5 UI表示をformal pixel PASSにしない |
| `EXTERNAL-DATA-PROVIDER-TERMS` | 実行前確認待ち | 運用者／Data／Security | Binance公開アーカイブの利用・保持・再配布条件、許可URL、内部budget、通信、保存境界。API key／Secretは使用しない | Gateの承認範囲と実行前Evidenceが揃わない限り外部I/O禁止 |
| `UNK-P5-BINANCE-001` | 未解消 | P5-DATA-G1／運用者 | Spotを暫定採用すること、Futuresへ拡張しないこと | Spot範囲を新Gateへ固定。Futuresを現行対象へ追加しない |
| `UNK-P5-BINANCE-002` | 未解消 | 運用者／銘柄選定 | 「主要アルトコイン」の具体symbolが未入力 | `BTCUSDT`／`ETHUSDT`以外を推測追加せず、別Gateへ送る |
| `UNK-P5-BINANCE-003` | 未解消 | P5-08／Data owner | 対象月の実ファイル、最初・最後のtimestamp、欠損、timestamp unit | URL、`.CHECKSUM`、件数、範囲、欠損を実Evidenceで確認するまで下流へ渡さない |
| `UNK-P5-BINANCE-004` | 未解消 | P5-08／Security | archive update、月次／日次差、利用・再配布条件 | 取得時のsource URL、checksum、更新情報、利用条件を記録し、UnknownをPassにしない |
| `P5-EXTERNAL-WORKER-UNKNOWN` | 未定義 | Architecture／Ops／期限はP5-DATA-G1前 | Binance用取得Runner、固定command、scope、allowlist、Evidence root、host isolation | 推測起動せず、`RUN-P5-08-BINANCE-001`を実行しない |

## 10. 完了条件

P5-H2へ提出できるのは、次をすべて満たした場合だけである。

- `BTCUSDT`／`ETHUSDT`、Crypto Spot、D1／H4／H1／M30／M15、symbol／quote asset／market segment／timestamp unitの対応がCatalogとData Evidenceで再現できる。旧先物の取引所・限月・Rollは現行対象外として明示される。
- Raw ZIP／`.CHECKSUM`／展開CSV、Normalized、Quality、Calendar適用表、Provenance、Evidence indexの保存境界と相対pathが一致する。データ完全性・再現性に直接必要な保護対象identityだけを扱い、管理用hashは扱わない。
- timestamp unit、UTC単調性、欠損、重複、OHLCV異常、Spot／Futures混入、未来Data、Look-ahead、Survivorshipの停止Evidenceがある。
- `CRYPTO_24_7_UTC`を適用し、DST、CME休場、短縮日、限月、RollをCrypto Spotへ誤適用しない。無データ区間を自動ゼロ埋めしていない。
- Provider公開Data費用0、内部保存・通信・実行usage、Spot fee／slippage仮定と実測値の区別、Gap分類がEvidence付きで分離される。P4 syntheticから実測値を推定していない。
- 承認済み期間（暫定継承範囲を含む）、本数、対象symbol、train／validation／holdout、Walk-forwardの分割が再現できる。holdout汚染がない。
- 許可URL、API key／Secret非使用、利用・保持条件、通信、保存、Runner、host isolationの承認範囲がP5-DATA-G1と台帳で一致する。
- P6へ渡すBinance Data contract、`CRYPTO_24_7_UTC`適用、Cost／Gap version、未解消Unknown、停止条件、Evidence indexが揃う。
- `Critical=0`、`High=0`。起動不能Fallbackがあった場合は、独立実行済みと偽らず、Fallbackの責務チェックリストと自己レビューを記録する。

## 11. 共通実ランタイム起動契約（各直接実行Promptへ埋込み）

以下をP5-01〜P5-11の各直接実行Promptへ適用する。名前の列挙、JSON読込、Skill適用、ルートAgentの自己レビューは起動証跡ではない。

1. ルート実行Agentは、最初に `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` の利用可否を確認する。利用可能なら、Prompt記載のOrchestrator JSON path、`model=gpt-5.6-terra`、Phase／Step、入力・出力境界、Agents、Skillsを渡してCoordinatorを1体spawnする。
2. CoordinatorはPromptのAgents欄にある全Agentを一体ずつspawnする。各Agent JSON pathと定義JSONの固定modelを `model` 引数へ明示し、Orchestrator JSONの `agents` map外のAgentも省略しない。各Agentをwaitし、完了statusと出力参照を取得する。
3. 実Agentとして扱えるのは、`agent_id`、JSON path、固定model、受付status、完了status、出力参照が揃ったAgentだけである。`orchestrator_agent_id`とCoordinatorの受付／完了も保存する。
4. spawn／waitが使えない、固定modelを受理できない、Coordinatorが子Agentを起動できない、または出力を取得できない場合は、先に `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`dispatch_mode=LOCAL_FALLBACK_NO_SUBAGENTS`、未起動Agent、理由、確認時刻、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`をログへ記録する。その後、ルート実行Agentが当該Agentの責務をチェックリストで順次適用して継続する。
5. Fallbackで行った確認を独立Agentの実行結果、独立レビュー、固定model実行済みと書かない。実行ログにはruntime backend、親／子ID、全試行Agent、JSON path、model、Skills、start／end、status、出力参照、独立性、review modeを記録する。入力・成果物・findingの管理hashは記録せず、保護hashが直接の安全・データ・再現性条件である場合だけ所有ランタイムの記録に限定する。
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
実施: P4から受け取ったData／Manifest／保存／Quality接続点を再照合し、Binance Data Vision、BTCUSDT／ETHUSDT、旧5候補の履歴境界、4資産種類、D1/H4/H1/M30/M15、Catalog／Calendar／Quality／Cost／Gap／HoldoutのREQ→UC→Data object→Test→Evidence→Gateを行単位で追跡する。P5対象外のBroker／Paper／Live／実資金／実Risk／Cloudを別表に固定する。doc/phase5/01_要件追跡/01_Phase5入力・Data対象・REQ追跡.html、plan/phase5/ログ/P5-01_入力・Data対象・REQ追跡_2026-08-12.mdを作成し、doc/index.htmlへ導線を追加する。
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
実施: Catalog version、論理ID→実Symbol／取引所／限月／Roll／単位、4資産種類、5時間足、Provider／schema／契約範囲、Data request、Raw／Normalized／Quality／Manifest／Evidenceの境界、relative path、保護対象のhash、再生成、保持・削除・再配布、Secret参照・mask・失効・監査、外部通信の許可・禁止、Fail-closed条件を設計する。Providerは識別子と契約条件の設計に留め、推測値や実接続を入れない。doc/phase5/02_データ詳細設計/02_Data_Catalog_Provider_DataContract詳細設計書.html とログを作成し、doc/index.htmlへ導線を追加する。
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
実施: Raw保持、正規化、timestamp／timezone／unit、来歴、source／request／contentの保護hash、Manifest、相対path、再生成、Calendar version／hash、DST／休場／短縮日／Roll、欠損／重複／逆行／異常値／未来Data／Look-ahead／Survivorshipの判定とFail-closed停止を、実装者が判断なく実装できる粒度で設計する。管理用Manifest／Evidence hashは設計しない。P4 metadata DBにData本文を複製しない。doc/phase5/02_データ詳細設計/03_Data_Raw_Normalized_Quality_Calendar_Provenance詳細設計書.html とログを作成し、Mermaid構造図・正常／失敗flow直後の受渡し表、全テストを含める。
レビュー: A91がモジュール、型、保存、処理順、例外、全試験を監査する。A50が外部ID／変換境界、A30/A40がReplay／Strategy入力／Look-ahead、A70がSecret／path／fail-closed、A90がREQ／Core／Unknownを監査する。Critical/Highを反映して再レビューする。
完了条件: Raw／Normalized／Quality／Calendar／Provenanceの責務、保存境界、停止、再生成、Test／Evidence、P5-08／09の入力が一致し、Critical/High=0。
停止条件: 来歴・保護hash・Calendar・timezone・停止条件・保存境界が未定義、P4 DBへ無断追加、実Data取得、依存導入、Core変更、receipt欠落、Critical/High未解決。管理用hashの不一致は停止条件にしない。
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
実施: 市場別Cost／Slippage／Gapを実測値と固定仮定に分け、保守側境界、roll／spread、欠損、長期期間、本数、市場数、train／validation／holdout、Walk-forward、look-ahead監査、再現性に直接結び付く保護hashを設計する。schema／contract／replay／failure injection／Manifest構造／Calendar mismatch／cost provenance／holdout再利用拒否をTEST-P5-DATA-IDとして入力・操作・期待・停止条件・Evidenceで定義する。管理用Manifest hashの不一致は停止条件にしない。doc/phase5/03_品質設計/04_Phase5_DataQuality_Cost_Holdout_Test_RunManifest設計.html とログを作り、P5-06、P5-08、P5-09、P5-H2へ結ぶ。
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
発火制御: P5-05のレビュー済みHTML、Critical/High=0、対象path、保護対象のfixture hash、Run Manifest、外部I/O=0を確認し、運用者がP5-H1を明示承認するまで開始しない。P5-H1承認は外部Data、Secret、費用、Provider、Broker、Paper、Liveを含まない。
記録: 承認後、対象Run ID、HEAD、target_paths、保護対象のfixture hash、trusted scope、承認文言、承認範囲、除外範囲を `tests/evidence/phase5/<RunId>/human-gate-p5-h1.md` と統合台帳へ記録する。管理用change hashは記録しない。承認がない場合は `HUMAN_GATE_REQUIRED` としてP5-06を開始しない。
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
実施: A110がTEST-P5-DATA-IDのlocal固定dummy REDを作り、A120が承認範囲の最小実装、A130が検証、A140が上限付き原因別修正、A150/A160がコード／安全レビューを行う。欠損／重複／逆行／保護対象のinput／fixture hash mismatch／calendar mismatch／look-aheadをfail-closedで確認する。管理用hashは計算・比較・再試行しない。外部通信0をEvidenceへ記録する。
完了条件: RED→GREEN、固定fixtureの保護hash一致、target-only、外部通信0、Critical/High=0、A150/A160のレビュー、Evidence indexが揃う。P5-DATA-G1を承認済みと扱わない。
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
実施: P5-DATA-G1の承認対象を空欄・仮値なしで列挙する。対象Symbol／期間／時間足、Provider／契約／権限、endpoint／rate、費用上限、Secret参照・mask・失効、通信方式、Raw／Normalized／Quality／Manifest／Evidenceの保存、保持・再配布、停止条件、取得Runnerの固定command、Run ID、target_paths、Data内容の保護hash、host isolation、再現手順を記載する。管理用Manifest／Evidence hashは記載しない。doc/phase5/05_実証/06_Phase5外部Data_Gate申請・範囲表.html とログを作り、未承認を統合台帳へ登録する。
レビュー: A50がProvider／外部ID境界、A70がSecret／通信／費用／停止、A90がREQ／Gate／Unknown、A80/A81が文書・index・台帳導線を監査する。
完了条件: 運用者がP5-DATA-G1で判断できる完全な申請表と、取得Runnerが未定義ならP5-EXTERNAL-WORKER-UNKNOWNとして停止する記録がある。
停止条件: 対象・費用・契約・Secret・通信・保存・Runner・Evidenceが不明、P5-H1未承認、外部I/Oが発火、Unknownを仮決定、receipt欠落。
```

### P5-DATA-G1 市場Data Provider専用Human Gate

```text
Step ID: P5-DATA-G1
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
発火制御: P5-07のBinance amendment申請表を読み、運用者が`P5-DATA-G1-BINANCE-AMENDMENT-001`を明示承認するまで外部I/O、Secret、費用発生、実Data取得を禁止する。P4-H2、P5-H0、P5-H1、旧Databento承認で代用しない。
承認対象: Binance Data Vision公開アーカイブの許可URL、`BTCUSDT`／`ETHUSDT`、Spot、1m、承認期間、UTC、`CRYPTO_24_7_UTC`、月次ZIPと`.CHECKSUM`、Raw／Normalized／Quality／Evidence保存、利用・保持・再配布条件、内部budget、停止・再生成、`RUN-P5-08-BINANCE-001`、target paths、データ完全性・再現性に直接必要なchecksum／identity、host isolation、固定Runner／command。公開アーカイブ取得にAPI key／Secret／entitlementは使用しない。文書管理用hashは承認対象にしない。
承認除外: Binance Futures、Funding、Liquidation、Tick、Order book、REST API主経路、Broker／Paper／Live／実資金、実Risk値、利益性、対象拡大、別Provider、別URL、API key／Secret用途、Cloud、未登録Runner。
記録: 明示承認を `tests/evidence/phase5/<RunId>/human-gate-p5-data-g1.md` に保存し、統合台帳のP5-DATA-G1行、承認範囲、期限、再開条件、Evidence先を更新する。不承認・空欄・条件付き未確定は `HUMAN_GATE_REQUIRED` とし、P5-08を開始しない。
```

### P5-08 承認範囲内の限定Data取得・Raw／Normalized Evidence

```text
Step ID: P5-08
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A50/A70/A90/A95=gpt-5.6-luna。固定modelを各JSONから読み、model引数へ明示する。
Skills: autotrade_skill_source_reader_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_official_research_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_protected_hash_policy_guard_v0_1, autotrade_skill_orchestration_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。外部I/Oより前に完了させる。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: `P5-DATA-G1-BINANCE-AMENDMENT-001=APPROVED`、`RUN-P5-08-BINANCE-001`の登録、承認されたtarget paths／固定command／HTTPS allowlist／API key・Secret非使用／運用者waiverを検証する。Provider利用条件の事前確認と実行前後host-isolation通信証拠は、このRunの開始条件にはしない。事前費用見積りは開始条件としない。Provider公開Data費用0、内部budget control、実行後usage／保存監査は記録する。承認範囲外のsymbol、market segment、endpoint、期間、追加取得、Broker、Paper、Liveは発火しない。取得Runnerが実在・固定・waiver範囲確認済みでない場合は`P5-EXTERNAL-WORKER-UNKNOWN`として外部I/Oをせず記録する。
入力: P5-02〜07正式設計、Binance方針文書、P5-DATA-G1承認・変更記録、固定取得Runner／command、`request.json`、`BTCUSDT`／`ETHUSDT`、Spot、1m、承認期間、Data Vision URL template、対象月、Evidence root、統合台帳。公開アーカイブ取得に不要なentitlement、API key、Secret metadata、既存環境変数のキーは入力にしない。
実施: 承認対象を変更せず、まずlocal dry-runでURL template、対象月、相対path、checksum取得方法、保存先、停止条件を検証する。Gate後は月次Spot Kline 1m ZIPだけを対象期間内で取得し、REST API、Futures、Tick、Order book、Funding、Liquidationへ拡張しない。取得後、ZIPと同じ場所の`.CHECKSUM`を使ってSHA-256を検証し、Raw ZIP、checksum文書、展開CSV、Normalized、Quality、Provenanceを同じRunへ束ねる。checksumとData内容のidentityはデータ完全性・再現性を守るためだけに扱い、文書管理用hash、Manifest hash、Evidence hash、receipt hashは計算・保存・比較・retryしない。timestamp unit、UTC、symbol、OHLCV、1分間隔、重複、欠損、未来Dataを検査し、欠損を推測補完しない。取得URL、取得時刻、相対path、外部I/O実施有無、Secret非出力、実行後usage監査を保存する。実行前後のhost-isolation通信証拠は取得しない。
レビュー: A50がBinance symbol／CSV列／Normalized変換、A70がHTTPS allowlist／Secret非使用／budget／保存path、A90が承認範囲・停止・Evidence・Unknownをレビューする。外部I/Oの正式実行結果とAgent起動結果を混同しない。
完了条件: `BTCUSDT`／`ETHUSDT` Spotの承認範囲、Raw ZIP／`.CHECKSUM`／展開CSV／Normalized、timestamp unit／UTC、Quality、provenance、通信・費用・Secret監査、停止条件、dispatch receiptが一致し、Critical/High=0。
停止条件: Gate不一致、Runner不明、target scope不明、URL allowlist逸脱、運用者waiver欠落又はscope不一致、承認範囲外、API key／Secret読取、checksum不一致、timestamp unit不明、Spot／Futures混入、欠損補完、未来Data、実行後usage監査不明、Critical/High、receipt欠落。Provider terms=UNKNOWNとhost isolation=NOT_VERIFIEDは、このRunでは単独の停止条件にしない。文書管理用hash不一致は停止条件にしない。事前見積りの不存在だけでは停止しない。
```

### P5-09 Quality／Calendar／Cost／Gap／期間分割／Holdout実証

```text
Step ID: P5-09
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
Agents: AutoTrade_A110_PythonTestEngineer_v0_1, AutoTrade_A130_VerificationEngineer_v0_1, AutoTrade_A140_DebugEngineer_v0_1, AutoTrade_A150_PythonCodeReviewer_v0_1, AutoTrade_A160_TradingSecurityReviewer_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
Model: Orchestrator=gpt-5.6-terra。A110/A130/A140/A150/A160/A90/A95=gpt-5.6-luna。各JSONの固定modelをmodel引数へ明示する。A90はQuality Orchestrator map外でも省略しない。
Skills: autotrade_skill_python_test_quality_v0_1, autotrade_skill_debug_recovery_v0_1, autotrade_skill_python_code_review_v0_1, autotrade_skill_test_strategy_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_protected_hash_policy_guard_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: `P5-DATA-G1-BINANCE-AMENDMENT-001=APPROVED`、`RUN-P5-08-BINANCE-001`完了、`RUN-P5-09-BINANCE-001`のtrusted scope、host isolation、Raw／Normalized／Quality Evidence、source checksumを確認する。承認範囲内の`BTCUSDT`／`ETHUSDT` Spotだけを対象とし、Broker、Paper、Live、実資金、Core変更、未登録Runは発火しない。
入力: P5-04品質設計、Binance用Crypto適用表、P5-08 Raw ZIP／`.CHECKSUM`／展開CSV／Normalized／Provenance、Manifest構造、Cost／Gap provenance、承認期間、train／validation／holdout／walk-forward定義、trusted scope。P5-04に残るCME futures固有のDST／休場／Roll規則は、そのまま適用せず、Crypto Spotでは`N/A`とする適用判断を入力へ固定する。
実施: 次の順で検証する。①symbol、quote asset、Spot階層、CSV列、timestamp unit、UTC、1分間隔、単調性、重複、OHLCV整合、`.CHECKSUM`を確認する。②1m RawからD1／H4／H1／M30／M15をUTC境界で生成し、各足のClose、OHLCV集計、欠損・重複・再生成を検査する。③`CRYPTO_24_7_UTC`を適用し、DST、CME休場、短縮日、限月、Rollは適用外として記録する。無データ区間はゼロ埋めせず、市場欠損、配布欠落、対象外時間を分類する。④Provider公開Data費用0、内部保存・通信・実行usage、Spot fee／slippage仮定と実測値、Gap分類を分離する。⑤未来参照、Look-ahead、Survivorship、期間境界、train／validation／holdout、Walk-forward再現を検証する。結果、停止一覧、再生成手順、Data完全性・再現性に直接必要なidentity、Evidence indexを作成する。文書管理用Manifest／Evidence hashは計算・比較・再試行しない。利益性・Live適合を判定しない。
レビュー: A130が検証、A140が上限付き復旧、A150/A160が安全・コード、A90がData contract／Gate／Unknown／Evidenceをレビューする。未実行、条件外、font／OS未固定をPASSにしない。
完了条件: `BTCUSDT`／`ETHUSDT`ごとのQuality、`CRYPTO_24_7_UTC`適用、Cost／Gap、期間分割、holdout Evidence、source checksum、Data完全性・再現性identity、停止証跡、レビュー、dispatch receiptが揃い、Critical/High=0。
停止条件: `.CHECKSUM`またはData完全性identity不一致、timestamp unit／UTC未確認、Spot／Futures混入、Calendar適用不明、欠損補完、未来Data、実測／仮定混同、holdout汚染、Gate不一致、Unknown PASS化、host isolation不明、Critical/High、receipt欠落。文書管理用hash不一致は停止条件にしない。
```

### P5-10 統合・独立レビュー・P5-H2候補

```text
Step ID: P5-10
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A50_AdapterArchitect_v0_1, AutoTrade_A70_OpsSecurityArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A50/A70/A81/A90/A95=gpt-5.6-luna、A80=gpt-5.1。固定modelをJSONから明示する。A50/A70はmap外でも省略しない。
Skills: autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_source_reader_v0_1, autotrade_skill_adapter_boundary_v0_1, autotrade_skill_ops_security_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_revision_integration_v0_1, autotrade_skill_protected_hash_policy_guard_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: `P5-DATA-G1-BINANCE-AMENDMENT-001=APPROVED`、`RUN-P5-08-BINANCE-001`と`RUN-P5-09-BINANCE-001`の完了、実証Evidenceの状態を確認する。追加の外部I/O、Secret、追加取得、Provider変更、symbol追加、実注文、実資金、Core変更は発火しない。
入力: P5-01〜09正式HTML／ログ、Binance方針・決定ログ、P5-DATA-G1 amendment承認、`BTCUSDT`／`ETHUSDT` SpotのCatalog／Data contract、Raw／Normalized／Quality／Calendar適用／Cost／Gap／Holdout Evidence、Evidence index／状態、統合台帳、REQ／UC／Test／Evidence追跡、Unknown一覧。文書管理用Evidence hashは入力にしない。
実施: `BTCUSDT`／`ETHUSDT` Spot、1m→D1／H4／H1／M30／M15、UTC／`CRYPTO_24_7_UTC`、source checksum、Raw／Normalized、Quality、Cost／Gap、期間分割、holdout、P5-DATA-G1承認、停止／再生成、外部通信／Secret非使用監査、P6引渡しを統合し、REQ→Evidenceのcoverageを再照合する。旧Databento／CME 5候補のEvidenceを現行Binanceの実証Evidenceへ読み替えない。未解消Unknownは根本原因、owner、期限、再開条件、後続Phaseへ再分類する。`doc/phase5/04_レビュー/07_Phase5統合品質・P6引渡し候補.html`とログを作成する。
レビュー: A90がFindings firstで外部I/O、Data／Calendar／Cost／Gap、Look-ahead、Gate、Unknown、P6境界を監査する。A80/A81がHTML、index、相互リンク、採否、履歴を確認する。Critical/Highは反映・再レビューし、P5-H2候補に残さない。
完了条件: REQ／UC／Test／Evidenceが`BTCUSDT`／`ETHUSDT` Spot範囲で追跡可能、実証Evidenceの存在・構造・状態が確認でき、source checksumとData完全性・再現性identityの目的が明示され、未解消Unknown、P6 Binance Data contractが揃い、Critical/High=0。利益性・Broker・Paper・Live PASSを記載しない。
停止条件: Evidence欠落・構造不備・状態不一致、保護対象のGate証拠不一致、UnknownのPass、外部範囲逸脱、P6境界不明、receipt欠落、Critical/High未解決。管理用Evidence hash不一致は停止条件にしない。
```

### P5-H2 Phase 5完了・P6引渡し承認

```text
Step ID: P5-H2
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
発火制御: P5-10の完了候補、`BTCUSDT`／`ETHUSDT` SpotのEvidenceの存在・構造・状態、REQ／UC／Test追跡、`P5-DATA-G1-BINANCE-AMENDMENT-001`の範囲、未解消Unknown、P6引渡し表を読み、運用者がP5-H2を明示承認するまでP5-11を開始しない。文書管理用Evidence hashは発火条件にしない。
承認対象: Binance Data VisionのSpot Kline 1mを基底とするData contract、`CRYPTO_24_7_UTC`適用、`BTCUSDT`／`ETHUSDT`、承認期間、Quality、source checksum、Cost／Gap、期間分割／holdout Evidence、P6への引渡し、未解消Unknownと停止条件。
承認除外: 他のsymbol、Futures、Funding、Liquidation、利益性の採用、実Risk、Broker、Paper、Live、実資金、Cloud、未承認Secret。
記録: 承認文言を `tests/evidence/phase5/<RunId>/human-gate-p5-h2.md` に保存し、統合台帳のP5-H2行を更新する。不承認・条件不明・Critical/High残存は `HUMAN_GATE_REQUIRED` または `BLOCKED` として完了を宣言しない。
```

### P5-11 完了記録・台帳同期・P6計画入力引渡し

```text
Step ID: P5-11
Phase ID: PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12
Plan: P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md
Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
Agents: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A81_DesignDocSetWriter_v0_1, AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
Model: Orchestrator=gpt-5.6-terra。A10/A81/A90/A95=gpt-5.6-luna、A80=gpt-5.1。各JSONの固定modelを明示する。
Skills: autotrade_skill_source_reader_v0_1, autotrade_skill_design_doc_set_writer_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_revision_integration_v0_1, autotrade_skill_protected_hash_policy_guard_v0_1
実ランタイム起動契約（このPrompt単体で適用）:
1. rootはmulti_agent_v1__spawn_agent／multi_agent_v1__wait_agentの可用性を確認し、指定Orchestratorの実在するJSON pathと固定modelを渡してspawnし、wait後にroot receiptを保存する。
2. CoordinatorはこのPromptに列挙された全Agentを一体ずつspawnする。Orchestrator JSONのagents map外のAgentも省略せず、各Agent JSONの固定modelをmodel引数へ渡し、全員をwaitしてchild receiptを保存する。Promptに順序制約がある場合はその順序を守る。
3. Agent名の列挙、JSON／Skillの読込、または自己レビューはspawn済みの証拠にしない。実spawn、agent_id、wait status、出力参照を必須とする。
4. spawn／waitが使えない場合は作業前にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、時刻、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、責務チェックリストで継続する。child起動不能だけでは停止しない。
5. 起動していないAgentを独立実行済み・独立レビュー済みと記載しない。receiptにはOrchestrator／Agent名、JSON path、固定model、agent_id、spawn／wait status、output_ref、fallback_reason、independent、review_modeを含める。
発火制御: P5-H2=APPROVEDを統合台帳と承認Evidenceで確認する。完了HTML、P6計画入力、ログ、台帳、doc/index.htmlだけを更新し、外部I/O、実Data追加取得、Provider変更、symbol追加、Broker、Paper、Live、実資金、Core、DB migrationは発火しない。
入力: P5-10正式HTML／ログ、P5-H2承認、`BTCUSDT`／`ETHUSDT` Spotの全Evidence記録・状態、Binance Data contract、`CRYPTO_24_7_UTC`適用、Cost／Gap version、source checksumの来歴、Unknown、P6ロードマップ、統合台帳。文書管理用Evidence hashは入力にしない。
実施: `doc/phase5/06_完了/08_Phase5完了判定・Phase6計画引渡し.html`、`plan/phase5/Phase6計画入力一覧_2026-08-12.md`、`plan/phase5/ログ/P5-11_完了・P6引渡し_2026-08-12.md`を作成する。P5のBinance／Crypto Spot実証範囲、旧Databento履歴、未承認範囲、Unknown、P6へ渡すData contract／Calendar適用／Cost／Gap／停止条件を行単位で記録し、P6が自動的にFutures、Broker、Paper、Liveへ拡張しないことを明記して、doc/index.htmlと統合台帳を同期する。
レビュー: A90が完了範囲の過大一般化、UnknownのPass、P6外部副作用混入を監査し、A80/A81がリンク、index、改訂履歴、台帳同期を確認する。Fallbackの場合は独立完了と記載しない。
完了条件: P5-H2承認、完了HTML、P6入力、Evidence index・存在・構造・状態、台帳、doc/index.html、dispatch receiptが一致し、P6の開始条件とP5非対象が明確である。
停止条件: P5-H2未承認、Evidence欠落・構造不備・状態不一致、P6入力欠落、Unknown PASS化、外部I/O／Broker／Paper／Live混入、receipt欠落、Critical/High未解決。管理用Evidence hash不一致は停止条件にしない。
```

## 13. レビューと受入判定

P5-05、P5-10では、Findings firstの順にCritical／Highを先に列挙し、採否表と修正後の再レビューを残す。設計AgentとReviewerが起動できた場合は実AgentのID・固定model・完了statusをEvidenceへ保存する。起動できなかった場合は `SELF_REVIEW_FALLBACK` と明記し、独立レビュー済みという表現を使わない。

Phase 5の完了判定は、Binance Data Visionの`BTCUSDT`／`ETHUSDT` Spot Historical実証範囲に限定する。P4の固定fixture、P5のData Quality、利益性、Broker接続、Paper、Live、実資金を同じPASSへ混ぜない。`P5-DATA-G1-BINANCE-AMENDMENT-001`の承認と`RUN-P5-08-BINANCE-001`の固定Runner／waiverがないP5-08は開始できず、P5-08のRaw取得済みだけではP5-09 Quality／P5-H2を完了扱いにしない。P5-09はlocal quality evidenceを生成済みだが、Provider条件・host isolation・child dispatchのUnknownを残すためP5-H2候補にはしない。`P5-EXTERNAL-WORKER-UNKNOWN`は固定Runner実行済み、Raw／Normalized／Quality evidence生成済みへ更新する。

## 14. 計画作成時の実行記録

- 計画作成の読み取り専用助言Coordinator: `019ff44d-da57-79d0-a9af-331c5590b046`（Cicero）。
- 実行方式: `ADVISORY_RUNTIME_SPAWN`。実行対象はPhase5ではなく、計画のStep／Gate／起動契約レビューだけ。
- 変更: 助言Agentはファイル変更、外部I/O、依存導入、Phase5 Runを行っていない。
- 限界: 呼出し元ランタイムから `.codex` の完全名・固定modelを実行コンポーネントとして束縛したことは、Agent IDだけでは証明できない。そのため本計画の直接Promptは、実行時にJSON path、固定model、spawn／wait receiptを再取得する契約を必須とする。

## 15. 変更履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-08-12 | v0.1 | P4-10引渡しを基に、Phase5を入力追跡、Data契約、Raw／Normalized／Quality／Calendar、Cost／Gap、長期／Holdout、local固定品質、Data Provider専用Gate、限定外部Data実証、統合レビュー、P6引渡しへ分割した。全直接PromptへRDC-PHASE-PLAN-0.2、起動不能時Fallback、固定model、receipt、Unknown／Gate停止を追加した。 |
| 2026-08-14 | v0.2 scope amendment | 運用者の決定を受領し、ProviderをBinance Data Visionへ変更、旧CME Micro futures 5件を初期運用候補から外し、BTCUSDT／ETHUSDTを暫定対象へ変更。旧Databento Gateを履歴化し、Binance用P5-DATA-G1 amendment、request、Runner、checksum／hash EvidenceをP5-08再開条件へ追加した。 |
| 2026-08-15 | v0.3 execution-plan amendment | P5-08〜P5-11の実行条件をBinance Spot／BTCUSDT・ETHUSDT／1m月次ZIP／UTC／`CRYPTO_24_7_UTC`へ具体化。API key／Secret非使用、公開Data費用0、`.CHECKSUM`のデータ完全性検証、CryptoではDST／休場／限月／Rollを適用外とする品質判定、Binance専用Run ID／Evidence、P6引渡し範囲を明記した。各直接PromptへA95の固定model／Skill指定を追加し、管理用hashは受入条件から除外した。 |
  | 2026-08-15 | v0.4 P5-08 operator-waiver execution | 運用者決定により、`RUN-P5-08-BINANCE-001`の開始前提からProvider利用条件の事前確認と実行前後host-isolation通信証拠を除外した。事実はUNKNOWN／NOT_VERIFIEDのまま保持し、固定RunnerでBTCUSDT／ETHUSDTの18月分、Raw ZIP／`.CHECKSUM`／展開CSV 36件を取得した。Normalized／Quality／Calendar／Cost／Gap／HoldoutはP5-09へ残した。 |
| 2026-08-15 | v0.5 P5-10 integrated review | P5-08/09のBinance Evidenceを統合し、REQ/UC/Test/Evidence、UTC Calendar、Cost/Gap、期間分割/Holdout、P6境界を再照合した。Provider条件、P5-08 host isolation、child dispatch、未測定execution costをOpenで保持し、P5-H2候補は作成しなかった。 |
  | 2026-08-15 | v0.5 P5-09 quality-evidence execution | `RUN-P5-09-BINANCE-001`でP5-08展開CSVを入力に、schema／timestamp／OHLCV／単調性／重複／gap、UTC D1／H4／H1／M30／M15、`CRYPTO_24_7_UTC`、Cost／Gap、train／validation／holdoutをlocal検証した。機械Gateは完了したが、Provider条件、P5-08 host isolation、子Agent未起動をUnknownとして保持し、P5-10統合レビュー待ちとした。 |

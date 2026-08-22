# Phase 5R2 実行計画書 v0.2 — 要件v4正式化後の後続実行

> Artifact ID: `P5R2-PLAN-002`
> Version: `v0.2`
> 作成日: `2026-08-22`
> 状態: `CURRENT_PLAN / P5R2-HREQ_APPROVED / P5R2-06A_COMPLETE / P5R2-H1_APPROVED_LOCAL_ONLY / P5R2-12_RED_CONFIRMED / P5R2-13_GREEN_CONFIRMED / P5R2-14_GREEN_CONFIRMED / P5R2-15_GREEN_CONFIRMED / P5R2-16_GREEN_CONFIRMED / P5R2-17_PACKET_READY / P5R2-DATA-G1_APPROVED_BOUNDED / P5R2-18_LOCAL_GREEN / P5R2-18_EXTERNAL_BLOCKED_HOST_ISOLATION / P5R2-19_LOCAL_UI_VERIFIED_RUNTIME_FALLBACK / P5R2-20_COMPLETE / P5R2-DELETE-G1_APPROVED_BOUNDED_P5R2_21 / P5R2-21_LOCAL_GREEN / P5R2-22_LOCAL_GREEN_CANDIDATE / P5R2-23_LOCAL_GREEN / P5R2-H2_UNAPPROVED / P6_PAUSED`
> 旧計画: [`Phase5R2_実行計画書_v0.1_2026-08-21.md`](./Phase5R2_実行計画書_v0.1_2026-08-21.md)（要件確定前の履歴。上書きしない）

## 1. この計画の結論

ユーザーの明示承認を受領したため、P5R2-HREQを承認済みとして扱い、要件v4を正式化した。本書は、その正式要件を入力に、P5R2-07以降の後続実行を再編した現在の計画入口である。

この承認で許可されたのは、次の2点だけである。

1. v4要件を正式な現在正本として公開すること。
2. v4を入力に、後続の実行計画を再作成すること。

P5R2-H1は2026-08-22に、利用者から移譲されたHuman Gate承認権限に基づき、承認packetの範囲で承認済みである。P5R2-DATA-G1は2026-08-23に、P5R2-18のbounded pilotだけを承認した。P5R2-20でDELETE-G1 packetを作成し、root CodexはP5R2-21の実装と新規一時fixture受入だけを承認した。P5R2-H2は未承認である。したがって、DATA-G1承認は他Provider・他銘柄・他期間への拡張、Provider login／契約／API call、Secret、費用、Data再配布の許可ではなく、DELETE-G1承認も既存Data／Run／CSV／Audit／Evidenceの削除、P6開始の許可ではない。

要件v4の現在正本は [`doc/requirements/01_自動トレードシステム要件定義書_v4.html`](../doc/requirements/01_自動トレードシステム要件定義書_v4.html) である。v3、P5R旧完了、P5R手順書v0.5、v4 candidate、P5R2-06 HREQ packetは、履歴または入力証拠として保持する。

## 2. 4領域と8件の承認済みRequirement

4領域は分類であり、8件は人が承認したatomicなRequirement単位である。以降の設計、実装、Test、Manual、Evidenceは8件を直接追跡する。

| 領域 | atomic Requirement | 実装・検証への主な展開 |
|---|---|---|
| 時間足 | `P5R2-CREQ-TF-001` | Single Backtestの戦略時間足を15m／30m／1h／4h／1dから1つ選択。1mはsource。 |
| 時間足 | `P5R2-CREQ-TF-002` | 1m sourceから上位足を生成。不足時は生成画面へ遷移。品質警告と使用禁止を分離。 |
| 時間足 | `P5R2-CREQ-TF-003` | legacy、UTC、指定期間／有効期間を新規Run入力から分離。 |
| Historical Data | `P5R2-CREQ-HD-001` | UIからDownload要求、生成要求、Job状態、取消、失敗、再試行を扱う。実ProviderはDATA-G1後。 |
| Historical Data | `P5R2-CREQ-HD-002` | 銘柄別Data Catalog、時間足、期間、quality、usable、identity、merge／replace、dedupe、conflict、promotionを扱う。 |
| Backtest Run操作 | `P5R2-CREQ-RUN-001` | 実行一覧・進捗・結果サマリーの3画面から、QUEUED／RUNNINGだけを取消する。二重押下と再送を安全に扱う。 |
| Backtest Run操作 | `P5R2-CREQ-RUN-002` | 保持したい結果を残し、不要なterminal result Artifactだけを物理削除する。CSV、Historical Data、Run、監査、Evidenceは保護する。 |
| 手順書 | `P5R2-CREQ-DOC-001` | `01_バックテスト手順書`を実装・Test・画像・Evidenceが揃った操作だけで改訂する。 |

詳細Requirement、Acceptance、回答原文、旧候補との差分は、[`AT-REQ-004 v4`](../doc/requirements/01_自動トレードシステム要件定義書_v4.html)、[`P5R2-ART-03`](../doc/phase5R2/02_要件候補/03_P5R2候補Requirement・Acceptance・追跡表.html)、[`P5R2-ART-04`](../doc/phase5R2/02_要件候補/04_バックテスト手順書改訂要件.html)を参照する。

## 3. P5Rの旧完了範囲とP5R2の対象を分ける

### 3.1 P5Rの履歴として保持する範囲

- P5Rが当時の限定Scopeで完了した事実、P5R-H2、P5RのEvidence、既存Manual v0.5。
- P5Rで作成した既存の1m／M30保存Data、Run、結果、CSV、再起動復元の履歴。
- P5Rの旧テスト、固定fixture、既存Quality Gateの実行証跡。
- P5Rの「P6引渡し」は、当時の履歴として保持するが、P5R2を飛ばす現在の開始条件にはしない。

### 3.2 P5R2で新たに扱う範囲

- 利用者向け戦略時間足を15m／30m／1h／4h／1dへ是正すること。
- 1m sourceとderived timeframeを分離し、銘柄ごとの生成済み時間足・期間・品質・usable状態を管理すること。
- UIからHistorical Data Download要求とlocal timeframe generation要求を作成し、JobとDataSetを分けること。
- 同一identityの非重複期間の利用者開始merge／replace、完全一致dedupe、値競合時の明示replace、影響Run／結果の確認を扱うこと。
- 実行一覧・進捗・結果サマリーからのRun取消と、不要なterminal result Artifactの物理削除を分けること。
- Export済みCSV、Historical Data、Run本体、監査、Evidenceを保護すること。
- `01_バックテスト手順書`を、実装・検証済みの現行機能に追従させること。

### 3.3 P5R2で扱わない範囲

- P5R2-H1前のソース変更、RED／GREEN、test subprocess、Playwright。
- P5R2-DATA-G1前のProvider login、契約、API call、外部Data download、Secret、費用、外部通信。
- P5R2-DELETE-G1前の既存実Data、既存Run、Evidence、監査記録の削除。
- Broker、注文、実資金、Paper、Live、P6のRisk／OMS実装。
- 管理用hash、manifest、checksum receipt、fingerprint、stale、hash retryを完了条件へ追加することは禁止する。

## 4. Gate、Unknown、現在の停止条件

| Gate／Unknown | 現在状態 | この計画での扱い | 未承認中の禁止 |
|---|---|---|---|
| `P5R2-HREQ` | `APPROVED (2026-08-22)` | v4正式化とP5R2-07計画再編の根拠。 | HREQ前の状態へ戻さない。承認範囲をH1へ拡張しない。 |
| `P5R2-H1` | `APPROVED_BY_DELEGATED_AUTHORITY` | 承認packetの範囲で、詳細設計、RED、target paths、fixture、Quality Gate、local実装範囲を承認済み。 | DATA-G1前の外部Data、DELETE-G1前の既存物理削除、H2前の完了宣言、P6開始。 |
| `P5R2-UNK-TF-004` | `H1_DECISION_CONFIRMED / LOCAL_EVIDENCE / H2_REVIEW` | H1で確定した単一内部欠損の補間条件をP5R2-13の実装・negative test・provenanceへ反映した。P5R2-23で最終追跡する。 | 条件外Dataをusable／Run入力へ昇格しない。 |
| `P5R2-UNK-TF-006` | `H1_DECISION_CONFIRMED / LOCAL_EVIDENCE / H2_REVIEW` | Catalog時点のclosedかつquality承認済みsourceの最小〜最大時刻を既定値とするH1判断をP5R2-13／14／22で実装・確認した。P5R2-23で最終追跡する。 | sourceなし、品質未承認、境界不明の期間を推測して表示・送信しない。 |
| `P5R2-UNK-QG-001` | `RESOLVED_LOCAL / EXTERNAL_SEPARATE` | `phase5R2` namespace、固定入口、scope登録、WSL host outbound isolationのEvidenceをP5R2-18 local Runで確認した。 | External Runのhost-level isolation確認へ読み替えない。未登録Run、固定入口外のtest実行は禁止。 |
| `P5R2-UNK-QG-002` | `RESOLVED_LOCAL_READONLY` | 既存protected fixtureのpath/name/version/記録済みprotected identityをread-only参照し、固定Gate Evidenceへ記録した。 | 既存protected identityの置換、新規管理hash、identity不一致のPass扱いは禁止。 |
| `P5R2-UNK-QG-003` | `OPEN / EXTERNAL_RUN_BLOCKED` | P5R2-18 external Runのhost-level isolation。process-level allowlistと独立host証拠を分け、現在は`NOT_VERIFIED`としてexecute／promotionを停止する。 | host-level allow-only環境のpre/post証拠なしの外部接続、既存P5 waiverの流用、proxy／別host／別期間への拡張。 |
| `P5R2-DATA-G1` | `APPROVED_BOUNDED_P5R2_18 (2026-08-23)` | Binance Data Vision public archive、Spot BTCUSDT／ETHUSDT、source 1m、UTC 2025-02-24以上2025-03-01未満、最大4 archive objects、local derived 15m／30m／1h／4h／1d、Run／Evidence／保存先をP5R2-18へ限定する。 | 承認範囲外のProvider・host・symbol・期間・interval、login、契約、API call、Secret、費用、Data再配布、実削除、P6開始。 |
| `P5R2-DELETE-G1` | `APPROVED_BOUNDED_P5R2_21_FIXTURE_ONLY (2026-08-23)` | terminal ResultArtifactだけの物理削除実装と、新規一時fixtureだけの受入を承認した。CSV／Historical Data／Run／Audit／Evidence、一括purge、restore、P6は対象外。 | 既存実Data、既存Run、既存CSV、既存Audit、既存Evidenceへの物理操作。承認範囲外のpath・ID・Data・Run。 |
| `P5R2-H2` | `UNAPPROVED` | 全Acceptance、Manual、Open Unknown、P6再引渡しをpacket化し、人の承認を得る。 | P5R2完了宣言、P6開始。 |
| `P5R2-UNK-HD-004` | `USER_APPROVED_LIMITED / NO_HASH_FLOW` | 管理用hashを導入しない。保護対象hashが必要になったときだけ別Gateへ送る。 | hash値、manifest、checksum、fingerprint、stale、retry、hash receiptの作成・要求。 |

P5R2-HREQ承認後も、上表のH1、DATA-G1、DELETE-G1、H2の4つの人判断は残る。H1、DATA-G1、DELETE-G1は、それぞれの承認packet、Acceptance、境界、Unknown、権限移譲記録に基づきroot Codexが限定承認した。DATA-G1はP5R2-18のbounded pilotだけ、DELETE-G1はP5R2-21の実装と新規一時fixture受入だけに有効である。H2は未承認のままであり、計画を作ったことや、設計を書いたことを承認とみなさない。

## 5. 入力、対象path、既存入口

### 5.1 必読入力

1. `doc/requirements/01_自動トレードシステム要件定義書_v4.html`
2. `doc/requirements/01_自動トレードシステム要件定義書_v3.html`（履歴・継承確認）
3. `doc/phase5R2/01_要件追跡/01_P5R2現状差分・根因・要求追跡.html`
4. `doc/phase5R2/01_要件追跡/02_P5R2ヒアリング回答・決定台帳.html`
5. `doc/phase5R2/02_要件候補/03_P5R2候補Requirement・Acceptance・追跡表.html`
6. `doc/phase5R2/02_要件候補/04_バックテスト手順書改訂要件.html`
7. `doc/phase5R2/03_HREQ/05_P5R2-HREQ承認packet.html`
8. `plan/phase5R2/requirements/drafts/01_自動トレードシステム要件定義書_v4_candidate.md`
9. `plan/Phase5R2_実行計画書_v0.1_2026-08-21.md`とP5R2-00〜06Aのログ／receipt
10. `doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html`
11. `doc/phase5R/02_実装詳細設計/03_再起動後バックテスト履歴復元実装詳細設計書.html`
12. `doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html`
13. `doc/phase5R/07_運用手順/01_バックテスト手順書.html`
14. `src/autotrade/application/`、`src/autotrade/backtest/`、`src/autotrade/market_data/`、`src/autotrade/strategy/`
15. `ui/mock/src/`、`ui/mock/tests/`、`tests/application/`、`tests/backtest/`、`tests/phase5R/`、`scripts/phase5r/`
16. `scripts/quality_gate/trusted_scopes.json`、`scripts/wsl_quality_gate/run_test.ps1`、`scripts/wsl_quality_gate/run_isolated_p2.ps1`
17. `.codex/orchestrators/*.json`、`.codex/agents/*.json`、`.codex/skills/*/SKILL.md`、`settings/language.md`、`settings/ai_component_rules.md`

### 5.2 現在確認できている実装入口

| 責務 | 現在の入口 | P5R2での扱い |
|---|---|---|
| Product API | `src/autotrade/application/api.py`、`http_server.py` | endpoint／DTO／状態判定を詳細設計で再定義。 |
| Backtest実行 | `src/autotrade/application/backtest_product.py`、`run_service.py`、`job_service.py` | 1m固定拒否、Run状態、取消、Job境界を要件v4へ追従。 |
| Persistence | `src/autotrade/application/persistence.py`、`history_catalog.py`、`storage_paths.py` | DataSet、Job、Artifact、Audit、OperationGuardの責務を設計。 |
| Core／時間足 | `src/autotrade/backtest/timeframe_aggregator.py`、`runner.py`、`src/autotrade/strategy/contracts.py` | source／derived／strategyを分離し、closed bar／UTC／品質を固定。 |
| Market Data | `src/autotrade/market_data/`、`scripts/phase5_external_data/` | local fake providerと実Providerを分離。実ProviderはDATA-G1後。 |
| UI | `ui/mock/src/P5RBacktestScreen.tsx`、`backtestApi.ts` | 実Application APIに接続するUI変更はA172で行い、固定ダミーUIの責務と混ぜない。 |
| UI検証 | `ui/mock/tests/`、`playwright.config.ts`、`package.json` | 実画面のassert後にdesktop/mobile、axe、request監視、Manual画像を取得。 |
| 固定品質入口 | `scripts/wsl_quality_gate/run_test.ps1` | `phase[0-9]+`制約とP5R2 Evidence namespaceをH1前に解消またはGateへ送る。 |

既存ファイルを実装対象と確定するのはH1後である。上表はread-onlyの現在入口であり、v0.2作成時点の変更許可ではない。

## 6. 成果物配置とDAG

### 6.1 成果物配置

| ID | 成果物 | 保存先 | 現在状態 |
|---|---|---|---|
| `AT-REQ-004` | 正式要件v4 | `doc/requirements/01_自動トレードシステム要件定義書_v4.html` | current |
| `P5R2-HREQ-PACKET-001` | HREQ承認packet | `doc/phase5R2/03_HREQ/05_P5R2-HREQ承認packet.html` | approved history |
| `P5R2-PLAN-002` | 本計画v0.2 | `plan/Phase5R2_実行計画書_v0.2_2026-08-22.md` | current |
| `P5R2-ART-DD` | 実装詳細設計セット | `doc/phase5R2/04_実装詳細設計/` | P5R2-09以降で作成 |
| `P5R2-ART-QG` | Quality／RED／Run scope | `plan/phase5R2/quality/`、`tests/evidence/phase5R2/<RunId>/` | P5R2-12 RED confirmed |
| `P5R2-ART-MAN` | 改訂済みBacktest手順書 | `doc/phase5R/07_運用手順/01_バックテスト手順書.html` | P5R2-22改訂候補・実画像／a11y／link確認済み、P5R2-23統合レビューLOCAL_GREEN、H2待ち |
| `P5R2-ART-DELETE-G1` | DELETE-G1承認packet | `doc/phase5R2/08_DELETE-G1/08_P5R2-DELETE-G1承認packet.html` | bounded承認済み／P5R2-21受入済み |
| `P5R2-ART-H2` | H2 packet／完了判定 | `doc/phase5R2/06_完了/`、`plan/phase5R2/ログ/` | 全Acceptance後 |

### 6.2 直列・条件分岐・並列

```text
P5R2-06A(v4正式化)
  -> P5R2-07(本計画v0.2)
  -> P5R2-08(read-only入力・部品再利用)
  -> P5R2-09(実装詳細設計)
  -> P5R2-10(設計レビュー・改訂・再レビュー)
  -> P5R2-H1(人判断)
  -> P5R2-11(QG互換確認・scope・RED設計)
  -> P5R2-12(RED)
  -> P5R2-13(時間足実装)
  -> P5R2-14(Historical Data local実装)
  -> P5R2-15(Run取消・結果Artifact削除guard実装)
  -> P5R2-16(local統合・migration・recovery)
  -> P5R2-17(DATA-G1 packet作成)
  -> P5R2-DATA-G1(packet -> 人判断)
  -> P5R2-18(承認時だけ実Provider受入)
  -> P5R2-19(UI統合・a11y・visual・E2E)
  -> P5R2-20(DELETE-G1 packet作成)
  -> P5R2-DELETE-G1(packet確認 -> 人判断)
  -> P5R2-21(承認時だけ物理削除受入)
  -> P5R2-22(01_バックテスト手順書改訂・実画像)
  -> P5R2-23(統合・Security・Code・Manualレビュー)
  -> P5R2-24(H2 packet作成)
  -> P5R2-H2(packet -> 人判断)
  -> P5R2-25(H2後完了判定・P6再引渡し)
```

P5R2-13、P5R2-14、P5R2-15の設計入力はP5R2-10後に分離するが、同じ共有Persistence／state／Audit契約を変更するため、実装は同一作業ツリーで並列に編集しない。独立したread-onlyレビューだけを並列に行う。P5R2-DATA-G1、P5R2-DELETE-G1、H1、H2は直列のHuman Gateである。

## 7. 全Step共通の実行契約

以下の契約を、下記の各直接実行Promptへ必ず埋め込む。完全名を列挙するだけではspawn／waitの証拠にならない。

### RDC-P5R2-0.2

1. rootは`multi_agent_v1__spawn_agent`で指定Coordinatorを実spawnし、`multi_agent_v1__wait_agent`で完了を待つ。
2. CoordinatorはPromptに列挙された全Agentを一体ずつspawnし、各Agent JSONの固定model、JSON path、Skillを明示してwaitする。map外の明示Agentも省略しない。
3. receiptに`runtime_backend`、`dispatch_mode`、`orchestrator_name`、`orchestrator_json_path`、`orchestrator_model`、`orchestrator_agent_id`、`agent_name`、`agent_json_path`、`agent_model`、`agent_id`、`accepted_status`、`completion_status`、`output_reference`、`independent`、`review_mode`を保存する。
4. spawn／wait不能時は、先に`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`LOCAL_FALLBACK_NO_SUBAGENTS`、未起動Agent、理由、UTC時刻、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`をログへ保存する。その後にrootの責務チェックリストで継続する。
5. fallbackは独立レビューと呼ばない。未起動Agentを実行済みと書かない。Critical／High、Human Gate、Unknown、外部I/Oの境界はfallbackでも緩めない。
6. A95は静的な管理hash再導入判定だけを行い、hash値、manifest、checksum receipt、fingerprint、stale、hash retryを計算・保存・比較しない。
7. 各Stepの作業者は、既存ユーザー変更を上書きせず、編集は`apply_patch`、正式HTMLは`doc/`、計画・ログは`plan/`、品質Evidenceは`tests/evidence/{phase_id}/{run_id}/`に保存する。
8. Gate未承認、外部I/O、Secret、費用、対象外path、未解消Unknown、Critical／Highがあればfail-closedで停止する。

### 共通の完了・停止条件

- 成果物、receipt、Finding、Unknown、Gate状態を参照リンク付きで保存する。
- `doc/index.html`と`doc/00_全Phase残課題Blocked統合台帳.html`の現在状態を同期する。
- P5R2-H1前は設計・計画のread-only成果物だけを作り、実装・Test subprocess・Playwrightを開始しない。
- P5R2-DATA-G1前はlocal fake provider以外を実行しない。
- P5R2-DELETE-G1前は一時fixtureの設計・REDだけに限定し、既存実Data／Run／Evidence／監査を削除しない。
- P5R2-H2前はP5R2を完了扱いにせず、P6へ再引渡ししない。

## 8. P5R2-07以降の直接実行Prompt

以下は、各Stepを個別に開始するためのPromptである。開始条件を満たさないPromptを前倒し実行してはならない。

### P5R2-07 — 後続実行計画v0.2を再作成する

```text
step_id=P5R2-07。
開始条件は、ユーザーのP5R2-HREQ明示承認、P5R2-06Aのv4正式公開、AT-REQ-004がdoc/index.htmlから到達可能であること。今回のStepは計画作成だけであり、実装Stepではない。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1（.codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

全Step共通実行契約RDC-P5R2-0.2を適用する。spawn／wait不能時はRUNTIME_DISPATCH_FALLBACK_REQUIREDとfallback receiptを先に保存し、独立実行済みと書かない。

作業:
1. AT-REQ-004、ART-01〜04、HREQ承認記録、P5R2-00〜06Aログ、v0.1、P5R成果物、AI部品定義を読む。
2. 4領域と8件を別軸でcoverage表にする。各atomic RequirementからUI、API、Persistence、state、Test、Manual、Evidence、Gateを直接追跡する。
3. P5Rの旧完了範囲とP5R2の現行要件を混ぜず、v0.1を履歴として残す。
4. P5R2-08からP5R2-25まで、詳細設計、H1、QG、RED、時間足、Data、Run操作、DATA-G1、UI、DELETE-G1、Manual、レビュー、H2、P6再引渡しの全Promptを欠番なく作る。
5. 各Promptに、開始条件、対象path、非対象path、Human Gate、固定model、Agent JSON path、Skill、RDC receipt、成果物、Acceptance、Negative Test、停止条件、rollback／recovery、次Step入力を全文で入れる。
6. 01_バックテスト手順書の改訂を独立した後続Stepとして含め、実装済み・検証済み操作だけを記載する停止条件を入れる。
7. run_test.ps1のphase namespace制約、trusted scope、fixture identity、外部I/O境界、管理hash禁止をUnknown／停止条件へ入れる。
8. 新規／大幅変更の本計画、Prompt、Acceptance、receiptをA95へ静的に渡す。A95はhashを計算しない。

出力:
- plan/Phase5R2_実行計画書_v0.2_2026-08-22.md
- plan/phase5R2/ログ/P5R2-07_後続実行計画再作成_2026-08-22.md
- plan/phase5R2/ログ/runtime-receipt-P5R2-07.json と .md
- 必要なdoc/index.html／統合台帳更新

完了条件:
- v0.1を上書きせず、v0.2が現在の実行入口である。
- 最終StepのP5R2-H2後完了判定・P6再引渡しまで直接実行Promptがある。
- Critical／High=0、H1／DATA-G1／DELETE-G1／H2の状態、P6停止、外部I/O禁止が矛盾なく読める。
- ソース実装、Test subprocess、Playwright、外部Data、Secret、費用、実削除を行っていない。
```

### P5R2-08 — 要件v4の入力読解と既存部品再利用判定

```text
step_id=P5R2-08。開始条件はP5R2-07完了。read-onlyの入力整理と既存部品再利用判定だけを行う。H1前のため、ソース、Test、UI、Playwright、外部I/O、Secret、実削除を変更・実行しない。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1（.codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用し、Coordinator、指定Agent全件、wait、receiptを実行する。起動不能はfallbackとして記録し、独立レビューと呼ばない。

作業:
1. v4の8 atomic Requirementと詳細Requirementのcoverageを作成する。
2. P5Rの既存application／backtest／market_data／strategy／UI／Test／Manualを読み、再利用可能、変更候補、責務不足、対象外に分ける。
3. `P5R2-UNK-TF-004`、`P5R2-UNK-TF-006`、`P5R2-UNK-QG-001`、`P5R2-UNK-QG-002`の決定期限、owner、停止範囲、Evidence先を更新する。
4. ComponentLifecycleが必要かを、名前ではなくJSONの責務とSkillで判定する。必要でもこのStepで部品を作らず、別Stepを計画する。
5. P5R2-H1で人が判断する設計対象、target paths、fixture、固定入口候補を列挙する。

出力:
- plan/phase5R2/ログ/P5R2-08_入力・部品再利用判定_2026-08-22.md
- plan/phase5R2/requirements/P5R2-08_requirement-coverage.md
- plan/phase5R2/requirements/P5R2-08_component-reuse.md
- 統合台帳のP5R2-UNK-QG-001／002更新案（人Gate未承認のまま）

Acceptance:
- 8件すべてに下位Requirement、既存実装入口、設計入力、後続Step、Manual、Gateがある。
- P5R旧完了とP5R2変更を混同しない。
- 未確認のpath、command、fixtureを確定事項と書かない。
```

### P5R2-09 — 実装詳細設計書セットを作成する

```text
step_id=P5R2-09。開始条件はP5R2-08完了。P5R2-H1未承認のため、実装詳細設計の作成だけを許可し、ソース実装、RED／GREEN、test subprocess、Playwright、外部I/O、実削除を禁止する。

CoordinatorはAutoTradeProject_ImplementationDesign_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A20_ArchitectureDomainArchitect_v0_1（.codex/agents/AutoTrade_A20_ArchitectureDomainArchitect_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A40_ExecutionEnginePocArchitect_v0_1（.codex/agents/AutoTrade_A40_ExecutionEnginePocArchitect_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A50_AdapterArchitect_v0_1（.codex/agents/AutoTrade_A50_AdapterArchitect_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A81_DesignDocSetWriter_v0_1（.codex/agents/AutoTrade_A81_DesignDocSetWriter_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A82_ImplementationDetailDesigner_v0_1（.codex/agents/AutoTrade_A82_ImplementationDetailDesigner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A91_ImplementationDetailReviewer_v0_1（.codex/agents/AutoTrade_A91_ImplementationDetailReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_implementation_detail_design_v0_1、autotrade_skill_implementation_detail_review_v0_1、autotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。AF-D16（doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html）とAF-D17（doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html）を使う。

設計対象:
1. timeframe contract／1m source／derived cache／UTC／closed bar／partial／補間／preflight／legacy。
2. HistoricalDownloadJob、TimeframeGenerationJob、DataSet Catalog、identity、coverage、quality、provenance、staging、promotion、orphan、recovery。
3. Run list／progress／summaryの状態判定、cancel request、OperationGuard、terminal操作、ResultArtifact、CSV registry、監査。
4. 物理削除は論理Artifact IDから固定許可rootを解決し、symlink／reparse／traversal／TOCTOU／別ID／保護対象を拒否する。H1／DELETE-G1未承認中は実unlinkを設計上のfail-closed境界に置く。
5. SQLite／file storageのmigration、restart、partial failure、rollback、recovery、既存legacy。
6. UI/API DTO、error code、dialog、input handoff、keyboard／focus／a11y、Manual／Evidenceの接続。

各HTMLには、目的の平易な説明、Mermaid構造図、module-to-module data handoff表、typed contract、永続化schema、正常／異常sequence、transaction、例外、recovery、全Test case、Requirement／Manual／Gate追跡、Unknown、レビュー履歴を含める。

出力:
- doc/phase5R2/04_実装詳細設計/01_P5R2時間足・Preflight設計書.html
- doc/phase5R2/04_実装詳細設計/02_P5R2HistoricalDataJob・Catalog設計書.html
- doc/phase5R2/04_実装詳細設計/03_P5R2Run操作・ResultArtifact設計書.html
- doc/phase5R2/04_実装詳細設計/04_P5R2Persistence・Migration・Recovery設計書.html
- doc/phase5R2/04_実装詳細設計/05_P5R2UI・Manual・Evidence接続設計書.html
- plan/phase5R2/ログ/P5R2-09_実装詳細設計作成_2026-08-22.md

Acceptance:
- A82/A91が実装者の判断余地を残さない粒度で、endpoint、schema、state、処理順、例外、Testを記載する。
- F-001／F-002／F-003／F-004／F-006／F-007の現行契約と旧候補が混在しない。
- UnknownをPassにせず、H1／DATA-G1／DELETE-G1で止まる境界が設計にある。
```

### P5R2-10 — 詳細設計をFindings firstでレビュー・改訂・再レビューする

```text
step_id=P5R2-10。開始条件はP5R2-09の設計HTMLセットとcoverage matrixが存在し、doc/index.htmlから到達可能であること。実装・Test・Playwright・外部I/O・実削除は行わない。

CoordinatorはAutoTradeProject_ImplementationDesign_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A91_ImplementationDetailReviewer_v0_1（.codex/agents/AutoTrade_A91_ImplementationDetailReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A81_DesignDocSetWriter_v0_1（.codex/agents/AutoTrade_A81_DesignDocSetWriter_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A82_ImplementationDetailDesigner_v0_1（.codex/agents/AutoTrade_A82_ImplementationDetailDesigner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_implementation_detail_review_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。A91はmodule／API／Persistence／sequence／exception／Testの欠落、A90はPhase境界・安全・Unknown・責務矛盾、A80/A81は導線・状態・改訂履歴、A95は管理hash再導入だけを確認する。

作業:
1. Findings firstでCritical／High／Medium／Lowを出し、各FindingにID、path／section、事故シナリオ、修正、受入Evidenceを付ける。
2. 特に、1mとstrategy timeframeの混同、30mの除外、全期間未定義、DownloadとGenerationの混同、merge後の勝手な削除、CSV cascade、削除対象のpath差し替え、OperationGuardの再起動、stagingのpartial promotion、QG namespaceを確認する。
3. 採用／部分採用／Later Gate／却下を理由付きで統合し、改訂後にA91とA90を再実行する。
4. Critical／Highが残る場合はH1 packetへ進めず、P5R2-DESIGN_BLOCKEDとして停止する。

出力:
- plan/phase5R2/ログ/P5R2-10_詳細設計レビュー・改訂・再レビュー_2026-08-22.md
- 設計HTMLの改訂版、review finding、採否表、再レビュー結果
- runtime-receipt-P5R2-10.json と .md

Acceptance:
- A91とA90の再レビューでCritical／High=0。
- すべての設計書がdoc/index.htmlから到達し、Unknown／Gate／非対象が保持される。
- H1承認なしに実装・Test subprocessへ進まない。
```

### P5R2-H1 — 詳細設計・RED・local実装範囲を人が承認する

```text
step_id=P5R2-H1。人判断Stepである。P5R2-10の再レビューがCritical／High=0でない場合、またはQG namespace／fixture identityの不整合が解消されない場合は、承認packetを作らずP5R2-H1_UNREADYで停止する。

人が確認する対象:
1. AT-REQ-004の8 atomic Requirement coverage。
2. P5R2-09/10の詳細設計、RED、state matrix、negative test、recovery、Manual／Evidence接続。
3. 実装対象pathと除外path。最低限、src/autotrade/application、src/autotrade/backtest、src/autotrade/market_data、src/autotrade/strategy、ui/mock、tests、scriptsの具体的な範囲を表にする。
4. trusted scope、Run ID、fixture、Evidence root、固定入口、host outbound isolation、P5R2 Evidence namespaceの互換。
5. H1後もDATA-G1前はlocal fake providerのみ、DELETE-G1前は一時fixtureのguard／REDのみとする境界。

出力:
- doc/phase5R2/05_H1/06_P5R2-H1承認packet.html
- plan/phase5R2/ログ/P5R2-H1_承認判断_2026-08-22.md
- 統合台帳のP5R2-H1行（APPROVED_BY_DELEGATED_AUTHORITY）

承認packetの範囲に含まれない操作は、該当する後続Gateの承認がない限り実行しない。P5R2-11以降は各Stepの開始条件、scope登録、host isolation、外部I/O／削除境界を満たしてから進める。
```

### P5R2-11 — H1後のQuality Scope互換確認・RED実行設計

```text
step_id=P5R2-11。開始条件はP5R2-H1承認packetが`APPROVED_BY_DELEGATED_AUTHORITY`として記録されていること。承認記録がなければ、Scope登録、Test subprocess、Playwright、ソース変更を行わず停止する。DATA-G1前の外部I/O、DELETE-G1前の実Data削除は引き続き禁止する。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_test_quality_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とImplementationQualityのRDC-GENERIC-0.2を適用する。H1承認の証拠、target_only、excluded_paths、fixture identity、evidence root、network isolationをreceiptへ保存する。

作業:
1. `scripts/wsl_quality_gate/run_test.ps1`の`phase[0-9]+`制約をread-onlyで確認し、P5R2 Evidence namespaceと互換しない場合はP5R2-UNK-QG-001として停止する。既存phase5RのRunをP5R2へ無断流用しない。
2. `scripts/quality_gate/trusted_scopes.json`のschemaと固定4 Gateを確認し、H1承認対象pathだけのtarget_only scope案を作る。
3. 新規fixtureの保護対象値が必要かを確認する。必要なら管理hashを作らず、保護対象hashの別Human Gateへ送る。
4. RED対象を時間足、Data Job／Catalog、Run cancel、ResultArtifact delete guard、audit、restart、path safety、UI DTOへ分ける。
5. Scope登録自体はH1承認範囲内で行うが、test subprocessはこのStepでは開始しない。登録できない場合はQUALITY_GATE_BLOCKEDで停止する。

出力:
- plan/phase5R2/quality/P5R2-11_scope・RED設計.md
- plan/phase5R2/quality/P5R2-11_run-manifest.json（管理hashを含めない。protected fixtureが必要ならHuman Gate待ちと明記）
- 必要なtrusted scope更新案、更新ログ、runtime receipt

Acceptance:
- P5R2-H1承認範囲外のpath、command、fixtureをScopeへ入れない。
- `P5R2-UNK-QG-001/002`を解消済みと偽らない。
- 外部network、Secret、費用、実Data削除が0である。
```

### P5R2-12 — REDテストを作成する

```text
step_id=P5R2-12。開始条件はP5R2-H1承認、P5R2-11のScope登録、fixture／Evidence rootの確認、host outbound isolation Evidence、scopeの`execution_allowed=true`確認。RED作成だけを行い、GREEN実装は同じStepで行わない。DATA-G1前はlocal fake providerのみ、DELETE-G1前は一時fixtureのみ。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_test_quality_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality orchestratorの固定Run contractを適用する。REDが本当に失敗したことをEvidenceへ保存し、skip、xfail、threshold弱化でPassにしない。

作業:
1. TF: 5選択肢、1m拒否、30m許可、legacy拒否、UTC boundary、effective end、closed bar、欠損1本warning、端点／2本以上／未来値／逆転拒否、全期間未確定停止。
2. HD: DownloadJob／GenerationJobのID・state分離、staging、validation、atomic promotion、orphan、recovery、identity違い、dedupe、conflict、merge preview、明示replace、影響Run／結果確認。
3. RUN: 3画面共通state、QUEUED／RUNNING cancel、terminal state不変、UI二重押下、再送、別tab、OperationGuard、CSV保護、active Run拒否、path traversal／symlink／reparse拒否。
4. Audit／Manual: 操作者、理由、target、旧／新state、依存数、request／correlation ID、失敗理由、Manual registryの未実装拒否。
5. restart／partial failure／保存先不一致／migration failureをfailure injectionにする。

出力:
- tests/application/、tests/backtest/、tests/phase5R/、ui/mock/tests/内のP5R2 REDテスト（対象pathはH1 packetとscopeに従う）
- tests/evidence/phase5R2/<RunId>/P5R2-12_RED.json と実行ログ
- plan/phase5R2/ログ/P5R2-12_RED作成_2026-08-22.md

Acceptance:
- 各8 atomic Requirementに少なくとも1つの失敗条件がある。
- RED結果が期待どおり失敗し、未実装をPass扱いしない。
- 外部I/O、Secret、既存実Data／Run／Evidence削除がない。

実績（2026-08-22〜2026-08-23）:
- `RED_CONFIRMED`。固定WSL入口でformatter／lint／typeはPASS、testは期待REDとしてFAILした。
- `tests/evidence/phase5R2/RUN-P5R2-11-LOCAL-001/P5R2-12_RED.json` に8件のfailure condition、対応test、runtime／禁止操作境界を記録した。
- P5R2-13を完了し、時間足正規化、Preflight、Run／Sweepのstrict boundary、1m source／derived identity、gap／coverage／provenance検査をGREEN確認した。固定WSL品質Gateはformatter／lint／type／testの4項目すべてPASS（49 tests）。Critical／Highなし、A95は新規管理hashフローなしとしてALLOW判定した。実Provider、外部Data、Secret、費用、実削除、Playwrightは実施していない。
- P5R2-14の開始条件を満たした。local fake provider／既存fixtureだけでHistorical Data Job・Catalog・時間足生成を実装し、DATA-G1未承認境界を維持する。
```

### P5R2-13 — 時間足・Preflight・legacy境界を実装する

```text
step_id=P5R2-13。P5R2-12のRED_CONFIRMED（2026-08-22）を開始条件として確認済み。H1承認範囲内、Dataはlocal fixture／fake providerだけ。実Provider、Secret、費用、実Data削除、P6は不可。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A120_PythonImplementer_v0_1（.codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A140_DebugEngineer_v0_1（.codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とImplementationQualityのfixed Run contractを適用する。A110のRED確認前にA120を開始しない。Failureは仮説ごと最大2回までで、外部接続は禁止する。

対象候補:
- src/autotrade/backtest/timeframe_aggregator.py、runner.py、contracts.py
- src/autotrade/application/preflight.py、contracts.py、backtest_product.py、history_catalog.py
- src/autotrade/strategy/contracts.py、service.py、snapshot.py
- 対応するtestsとui/mockのDTOはH1 target scope内だけ

実装契約:
1. 利用者選択は15m／30m／1h／4h／1dのみ。1mはsource属性としてのみ保持する。
2. 1m sourceとderived Dataをidentityで分離し、UTC 00:00 anchor、closed bar、指定終了／有効終了を保存する。
3. 内部欠損1本は候補方式PREVIOUS_CLOSED_BAR、OHLC同値、Volume 0、warning／provenance。端点・2本以上・未来値・逆転・provenance欠落はUNUSABLE。
4. 必要Data不足時はRunを作成・開始せず、理由と生成確認を返し、銘柄を引き継いだ生成画面DTOへ遷移できるようにする。
5. legacy 1m／M30を新規Runに自動使用しない。

完了:
- RED→GREENの対象Test、format／lint／type、固定Quality Gate、A150／A160レビュー、A95判定をEvidenceへ保存。
- Critical／High、network、Secret、対象外path、未承認Gateがあれば停止。
```

P5R2-13実行結果（2026-08-23）:
- `GREEN_CONFIRMED`。固定4 Gateはformatter／lint／type／testすべてPASS。最終testは49件PASS、既存application／backtest回帰は174件PASS・43件deselected。
- 固定WSL入口 `RUN-P5R2-13-LOCAL-001` はhost outbound isolation確認を含めてPASS。対象はlocal-onlyであり、DATA-G1／DELETE-G1／H2／P6の承認状態は変更していない。
- 実装はP5R2-13の時間足・Preflight契約に限定した。Requested Project Coordinator／Agentsの独立runtime dispatchは成立していないため、runtime receiptでは`NOT_DISPATCHED`／`independent=false`／`SELF_REVIEW_FALLBACK`として記録し、実行済みと偽っていない。別途実施した最終レビューprobeは証跡上分離した。
- 証拠: [`P5R2-13 GREEN`](../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/P5R2-13_GREEN.json)、[`verification`](../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/verification.json)、[`A95 policy`](../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/P5R2-13_A95_policy.json)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-13.md)。

### P5R2-14 — Historical Data Job・Catalog・local generationを実装する

```text
step_id=P5R2-14。開始条件はP5R2-13のlocal時間足GREEN、P5R2-H1承認、P5R2-DATA-G1未承認。local fake provider／既存fixtureだけを使い、実Provider接続・login・契約・API call・download・Secret・費用は行わない。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A120_PythonImplementer_v0_1（.codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A140_DebugEngineer_v0_1（.codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_adapter_boundary_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。A50のProvider Adapter境界をlocal fake providerだけへ閉じる。

実装契約:
1. HistoricalDownloadJobとTimeframeGenerationJobをjob_type、ID、state、input、output、retry_ofで分ける。
2. UI入力は銘柄、複数時間足、期間。既定期間は、P5R2-UNK-TF-006の設計規則に従い、未確定なら停止理由を返す。
3. Jobはstaging→validation→atomic promotion。partial、FAILED、CANCELLED、RECOVERY_REQUIRED、ORPHAN_STAGINGをusable DataSetへ昇格しない。
4. Data identityはProvider、market、symbol、Data timeframe、normalized schemaで判定する。identity違いを自動mergeしない。
5. 同一timestamp完全一致はdedupe。値競合はpreviewと旧値／新値を示し、利用者がreplaceを明示しない限りCONFLICTで停止する。
6. 非重複期間はmerge previewでcoverage、追加、dedupe、conflict、影響Run／Artifact／CSVを示し、確認後にpromotionする。過去Run結果の変更可能性を理由にmergeを拒否しない。
7. Catalogは銘柄別に時間足、期間、quality、usable、legacy、provenance、current stateを表示する。

完了:
- local fake providerで開始・取消・失敗・再試行・restart・partial failure・merge／replace・dedupe／conflictをRED→GREEN確認。
- 外部host、Secret、費用、実Data削除が0であることをEvidenceへ記録。
```

実績（2026-08-23）:
- `P5R2-14_GREEN_CONFIRMED`。固定WSL入口 `RUN-P5R2-14-LOCAL-001` はformatter／lint／type／testの4 GateすべてPASS（52 tests）で、host outbound isolationを確認した。対象回帰33 testsもPASSした。
- Job snapshotのserver ownership／CAS、Catalog staging tokenのJob再検証、preview操作束縛、Result owner、exclusive writeを実装し、追加read-only監査でin-scope Critical／High=0を確認した。
- 指定Project Coordinator／Agentsの独立dispatchは成立していないため、runtime receiptでは`NOT_DISPATCHED`／`independent=false`／`SELF_REVIEW_FALLBACK`として記録した。P5R2-16へJob永続化・migration・統合recoveryを引き継ぐ。
- 証拠: [`P5R2-14 GREEN`](../tests/evidence/phase5R2/RUN-P5R2-14-LOCAL-001/P5R2-14_GREEN.json)、[`verification`](../tests/evidence/phase5R2/RUN-P5R2-14-LOCAL-001/verification.json)、[`A95 policy`](../tests/evidence/phase5R2/RUN-P5R2-14-LOCAL-001/P5R2-14_A95_policy.json)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-14.md)。

実績（P5R2-15、2026-08-23）:
- `P5R2-15_GREEN_CONFIRMED`。Run取消のserver-owned OperationGuard、HTTP経路、terminal不変、同一token再送、revision競合、最終bar取消、queued checkpoint／resume競合を実装した。
- ResultArtifactはDELETE-G1前のfail-closed guardまでを実装した。既存Data／Run／Audit／Evidence／CSVの実削除、unlink、tombstone、cascadeは実行していない。
- Windows固定pytest 42件、WSL固定pytest 42件、対象storage／Backtest／cancel guard／non-hash境界回帰24件、品質Gate契約11件、固定WSL4 GateをPASS。host outbound isolationはCONFIRMED、修正後の独立レビューでin-scope Critical／High／Medium／Lowはすべて0件となった。
- 証拠: [`P5R2-15 GREEN`](../tests/evidence/phase5R2/RUN-P5R2-15-LOCAL-001/P5R2-15_GREEN.json)、[`verification`](../tests/evidence/phase5R2/RUN-P5R2-15-LOCAL-001/verification.json)、[`修正後コードレビュー`](../tests/evidence/phase5R2/RUN-P5R2-15-LOCAL-001/P5R2-15_code_review_final_after_storage_fix.json)、[`A95 policy`](../tests/evidence/phase5R2/RUN-P5R2-15-LOCAL-001/P5R2-15_A95_policy_review_final.json)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-15.md)。

### P5R2-15 — Run取消・結果Artifact削除guard・OperationGuardを実装する

```text
step_id=P5R2-15。開始条件はP5R2-14のlocal Data GREEN、H1承認。P5R2-DELETE-G1は未承認なので、既存実Data／Run／Evidence／監査の物理削除は行わない。DELETE-G1前は一時fixtureの削除guard、拒否、RED／GREENだけを扱い、実unlinkは実行禁止とする。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A120_PythonImplementer_v0_1（.codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A140_DebugEngineer_v0_1（.codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。

実装契約:
1. 実行一覧・進捗・結果サマリーの3画面で同じRun state判定を返す。
2. QUEUED／RUNNINGだけcancel requestを受付。terminal／RECOVERY_REQUIRED／LEGACY_RESULT_ONLY／PARTIAL_FAILEDはRun state不変で理由とauditを保存する。
3. UIのin-flight disableを前提に、Serverはtarget ID、operation kind、operation token、current state、CAS versionを再確認する。同一token再送は保存済み結果、別tokenは現在状態を返し、二度目の状態変更を拒否する。
4. ResultArtifactはPRESENT／DELETE_PENDING／RESULT_DELETED／DELETE_FAILED、CSVはNONE／EXPORTING／EXPORTED／EXPORT_FAILEDで分離する。EXPORTING中は拒否する。
5. 削除APIはpathを受けず論理Artifact IDだけを受ける。固定root、台帳ID、Run、Artifact種別、canonical path、symlink／reparse、traversal、TOCTOUをfail-closedで検査する。
6. DELETE-G1前の物理unlinkは常に拒否し、保護対象（CSV、Historical Data、Run本体、Audit、Evidence）をcascadeしない。

Acceptance:
- cancel／deleteの二重クリック、再送、別tab、restart、state競合、active Run、CSV、traversal、symlink／reparse、別IDを個別にNegative Test。
- 物理削除未承認の状態をendpointとUIで誤表示しない。
```

### P5R2-16 — local統合・migration・restart／recoveryを検証する

```text
step_id=P5R2-16。開始条件はP5R2-13〜15のlocal unit GREEN、各review Critical／High=0、H1承認。外部Provider、Secret、費用、実Data／Run削除、P6は不可。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A140_DebugEngineer_v0_1（.codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。失敗原因ごとのDebug試行は最大2回まで。

作業:
1. legacy 1m／M30の閲覧、new 30mの選択、source／derived Catalog、Run参照を同時に確認する。
2. Job staging、promotion、Catalog current pointer、Run固定DataSet、merge／replace、影響結果、CSV保護を統合する。
3. API／Windows再起動、Job途中停止、promotion途中停止、OperationGuard再起動、未完了Run、破損／不一致をRECOVERY_REQUIREDへ遷移させる。
4. migrationは既存P5R履歴を消さず、legacy／currentを別表示する。rollbackと未掲載stagingを確認する。
5. 固定4 Gate、UI build／unit、local API、request外部0の検証計画をEvidenceへ保存する。

出力:
- tests/evidence/phase5R2/<RunId>/P5R2-16_local-integration/
- plan/phase5R2/ログ/P5R2-16_local統合・recovery_2026-08-22.md
- migration／recovery結果、open Unknown更新

未解消Critical／High、network isolation不足、実Data削除検出、Gate逸脱があればP5R2-LOCAL_INTEGRATION_BLOCKEDで停止する。
```

実績（P5R2-16、2026-08-23）:
- `P5R2-16_GREEN_CONFIRMED`。Job registry、staging／promotion、Catalog current pointer、Run固定DataSet、merge／replace、restart、migration、promotion途中停止、OperationGuard復元、CSV／path安全を統合確認した。
- 固定WSL入口 `RUN-P5R2-16-LOCAL-001` はformatter／lint／type／testの4 GateすべてPASS（108 tests）。host outbound isolationは`CONFIRMED`、`networking_mode=none`、wrapper exit 0である。Windowsの同一固定対象も108 tests PASSした。
- read-onlyレビューで検出されたHigh相当論点を修正し、Critical／High=0とした。指定roster全員の独立dispatchは成立していないため、runtime receiptには実際のagent、未起動、A95 static fallbackを分離して記録した。
- 外部Provider、login、契約、API call、Data download、Secret、費用、実Data／Run／Audit／Evidence／CSV削除、Playwright、P6開始、新規管理hashは行っていない。
- 証拠: [`P5R2-16 GREEN`](../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/P5R2-16_local-integration/P5R2-16_GREEN.json)、[`verification`](../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/verification.json)、[`host isolation`](../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/host-isolation.json)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-16.md)。

P5R2-16は完了し、P5R2-17 DATA-G1 packet作成へ移行可能とする。DATA-G1／DELETE-G1／H2は未承認のまま保持する。

### P5R2-17 — DATA-G1承認packetを作成する

```text
step_id=P5R2-17。開始条件はP5R2-16 local統合・recoveryが完了し、P5R2-DATA-G1は未承認であること。これはGate packet作成だけであり、外部host、login、契約、API call、Data download、Secret、費用を行わない。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A50_AdapterArchitect_v0_1（.codex/agents/AutoTrade_A50_AdapterArchitect_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_adapter_boundary_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。A50はProvider／host／通信境界だけを設計し、実接続をしない。A95は管理hashを追加しない。

作業:
1. P5R2-REQ-HD-001／002、DATA-G1、P5R2-UNK-HD-004、P5R2-UNK-QG-001／002を直接追跡する。
2. provider、host、market、symbol、source interval、UTC期間、保存先、allowlist、redirect／proxy、rate limit、再試行、cancel、失敗、費用、Secret、外部Dataからusableへの昇格条件を表にする。
3. 実Provider受入Run ID、Evidence root、host outbound isolation、外部I/Oの開始・停止・失敗条件をpacket化する。
4. 公式一次情報は、許可された公開文書のread-only閲覧だけに限定し、login、契約、API call、Data downloadを行わない。未確認事項はUnknownへ残す。

出力:
- doc/phase5R2/07_DATA-G1/07_P5R2-DATA-G1承認packet.html
- plan/phase5R2/ログ/P5R2-17_DATA-G1_packet作成_2026-08-22.md
- 統合台帳更新案（DATA-G1はUNAPPROVEDのまま）

Acceptance:
- packetだけで人が外部I/Oの対象、費用、Secret、保存先、停止条件を判断できる。
- HREQ承認、P5R2-17完了、公式公開文書の閲覧をDATA-G1承認と読み替えない。
```

実績（P5R2-17、2026-08-23）:
- `P5R2-17_PACKET_READY`。Binance Data Vision public archiveを推奨候補とし、Spot BTCUSDT／ETHUSDT、source 1m、UTCのbounded pilot（2025-02-24以上2025-03-01未満）、allowlist、保存先、費用上限、Secret境界、停止／rollback、usable昇格条件をpacketへ集約した。
- 公式一次情報は、Binance Public Data README、Data Collection入口、Spot API docs、Terms entryをread-only閲覧した。公式READMEのコードライセンスを市場Dataの再配布許諾へ拡張せず、保持・再配布条件、対象期間の完全性、外部host-level isolationはUnknownとして残した。
- 外部host、login、契約、API call、Data download、Secret、費用は0。P5R2-DATA-G1は未承認のままで、packet作成や公式文書閲覧を承認と読み替えていない。
- 証拠: [`DATA-G1 packet`](../doc/phase5R2/07_DATA-G1/07_P5R2-DATA-G1承認packet.html)、[`packet Evidence`](../tests/evidence/phase5R2/RUN-P5R2-17-PACKET-001/packet-evidence.json)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-17.json)。

P5R2-17は完了し、P5R2-DATA-G1は2026-08-23にbounded pilotとして承認済みである。承認範囲外の外部I/O、Secret、費用、Data再配布、実削除、P6開始は引き続き禁止する。

実績（P5R2-DATA-G1、2026-08-23）:
- `APPROVED_BOUNDED_P5R2_18`。P5R2-17 packet、P5R2-16 local GREEN、対象範囲、停止条件、rollback条件、Unknownを確認し、P5R2-18の実Provider受入だけを承認した。
- 承認範囲はBinance Data Vision public archive、Spot BTCUSDT／ETHUSDT、source 1m、UTC 2025-02-24以上2025-03-01未満、matching monthly archiveとsibling `.CHECKSUM`の最大4 object、local derived 15m／30m／1h／4h／1d、`RUN-P5R2-18-EXTERNAL-001`、`E:\\strategy_test_data\\autotrade\\historical\\spot\\klines\\1m`へのstaging／atomic promotionである。
- provider fee capは0 USD、redirect reject、proxy disabled、API key／Secret／login／REST／WebSocket／Authorizationなしとした。retention／redistribution terms、archive completeness、host-level isolationはUnknownとして保持し、host-level isolation未確認時は`NOT_VERIFIED`で停止する。
- 承認Evidence: [`承認判断ログ`](./phase5R2/ログ/P5R2-DATA-G1_承認判断_2026-08-23.md)、[`Human Gate Evidence`](../tests/evidence/phase5R2/RUN-P5R2-DATA-G1-P5R2-001/human-gate-p5r2-data-g1.md)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-DATA-G1.json)。

P5R2-18へ移行する。承認範囲外の外部I/O、Secret、費用、Data再配布、実削除、P6開始は引き続き禁止する。

### P5R2-DATA-G1 — 実Provider／外部Data境界を人が承認する

```text
step_id=P5R2-DATA-G1。人判断Step。P5R2-16のlocal検証が完了していない、またはpacketに対象範囲がない場合は承認依頼を出さず停止する。

人が確認する対象:
1. Provider名、公式host、market、symbol、source interval、期間、UTC範囲、保存先。
2. 公開文書、利用条件、再配布条件、rate limit、通信allowlist、proxy／redirectの扱い。
3. 認証・Secretが必要か、必要ならどのSecretをどの境界で読むか。未承認のSecretは0件。
4. 費用上限、容量、download回数、失敗時の停止、再試行、cancel、外部Dataをusableへ昇格する条件。
5. `HistoricalDownloadJob`と`TimeframeGenerationJob`の境界、実Provider受入Run ID、Evidence root、host outbound isolation。
6. 保護対象hashを使う場合の目的・対象・比較時点・不一致時停止・再取得条件。目的不明ならNO_HASH_FLOWのままにする。

出力:
- doc/phase5R2/07_DATA-G1/07_P5R2-DATA-G1承認packet.html
- 承認時は plan/phase5R2/ログ/P5R2-DATA-G1_承認判断_2026-08-23.md と Human Gate Evidence、未承認時は承認依頼ログ
- 統合台帳の対象、期限、再開条件、証拠先（承認時はbounded状態、未承認時は未承認）

人の明示承認がない限り、実Provider接続、login、契約、API call、Data download、Secret、費用は行わない。
```

### P5R2-18 — DATA-G1承認時だけ実Provider受入を行う

```text
step_id=P5R2-18。開始条件はP5R2-DATA-G1の対象Provider、host、symbol、期間、通信、Secret、費用、保存先、Run ID、Evidence rootが明示承認済みであること。承認内容外へ一歩でも出る場合は実行せず停止する。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A120_PythonImplementer_v0_1（.codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。実行前にGateの対象とtrusted scopeを再照合し、receiptへaccepted scope、actual scope、network isolation、Secret use、cost、provider response、Data promotionを記録する。

作業:
1. approved providerのsource 1mだけを取得し、上位足の直接取得・混在をしない。
2. Download Jobの開始、進捗、cancel、failure、retry、staging、quality、atomic promotionを検証する。
3. 取得Dataをすぐusableにせず、schema、UTC順、重複、欠損、identity、provenance、品質状態を検査する。
4. 外部通信を伴うRunとlocal fake provider Runを別Run ID・別Evidence rootにする。
5. Secret、費用、host、対象symbol、期間が承認外なら即時停止し、Dataをusableへ昇格しない。

物理削除はこのStepの対象外。P5R2-DELETE-G1が未承認なら、実Data／Run／Evidence／監査の削除を行わない。
```

P5R2-18実績（2026-08-23）:

- 状態は`P5R2-18_LOCAL_GREEN / P5R2-18_EXTERNAL_BLOCKED_HOST_ISOLATION`。専用Runner、request、allowlist、registration、外部Runのhost-isolation記録を作成した。
- `RUN-P5R2-18-LOCAL-001`の固定WSL Gateはformatter／lint／type／testの4 GateすべてPASS。WSLは`networking_mode=none`、default routeなし、外向きNICなしを確認した。
- External dry-runは`BLOCKED`、理由は`HOST_LEVEL_ISOLATION_NOT_VERIFIED`。`RUN-P5R2-18-EXTERNAL-001`のexecute、download、normalization、staging、Catalog promotionは0件である。
- P5R2-DATA-G1の承認範囲は変更しない。host-level isolationが独立に`VERIFIED`になるまで、P5R2-18 externalは再開しない。P5R2-19は外部request 0のlocal UI統合として完了候補を確認し、P5R2-20へ進める。
- 証拠: [`P5R2-18 log`](./phase5R2/ログ/P5R2-18_外部Data受入・専用Runner_2026-08-23.md)、[`runtime receipt`](./phase5R2/quality/runtime-receipt-P5R2-18.json)、[`local verification`](../tests/evidence/phase5R2/RUN-P5R2-18-LOCAL-001/verification.json)、[`external preflight`](../tests/evidence/phase5R2/RUN-P5R2-18-EXTERNAL-001/preflight/registration-preflight.json)。

### P5R2-19 — Web製品UIと3画面の統合・a11y・visual・E2E

```text
step_id=P5R2-19。開始条件はP5R2-16 local統合GREEN、必要ならP5R2-18のDATA受入、H1承認。実Application APIへ接続するUIを対象とし、固定ダミーUIを実機能の証拠として扱わない。DELETE-G1前は実削除を実行しない。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A172_WebProductUiEngineer_v0_1（.codex/agents/AutoTrade_A172_WebProductUiEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A171_UiVisualQaReviewer_v0_1（.codex/agents/AutoTrade_A171_UiVisualQaReviewer_v0_1.json、model=gpt-5.6-terra）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_web_product_ui_implementation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。実Application API、外部request 0、role／name／label、keyboard／focus、axe、desktop 1280x900、mobile 390x844をreceiptへ保存する。

実装・検証:
1. Single Backtestの時間足選択は15m／30m／1h／4h／1dだけ。1mはsource説明に限定。
2. Data Catalogは銘柄、時間足、期間、quality、usable、legacy、Job state、provenanceを表示。
3. 不足Dataのエラー、生成確認dialog、銘柄を引き継いだ生成画面、複数時間足、期間既定値を検証。
4. 実行一覧・進捗・結果サマリーで同じRun state／cancel可否／理由を表示し、in-flight disableと再送を検証。
5. ResultArtifact削除はDELETE-G1未承認時に拒否またはdisabledで理由を表示し、CSV／Data／Audit／Evidenceを保護する。
6. API request、外部host、Secretの監視を行い、許可外requestがあれば失敗扱いにする。

出力:
- ui/mock/src/、ui/mock/tests/、必要な実Application UI adapter
- tests/evidence/phase5R2/<RunId>/P5R2-19_ui/
- a11y／visual／E2E結果、capture registry、runtime receipt
```

### P5R2-20 — DELETE-G1 packetを作成し、人が物理削除範囲を承認する

```text
step_id=P5R2-20。人判断Step。P5R2-19のUIが削除状態と保護対象を正しく表示できていない場合、またはlocal guard／REDが未完了の場合は承認依頼を出さず停止する。

人が確認する対象:
1. 物理削除対象は利用者が明示したterminal result Artifactだけか。
2. 許可root、logical result_artifact_id、Run／Artifact台帳、canonical path、symlink／Windows reparse、traversal、TOCTOU防御。
3. Export済みCSV、Historical Data、Run本体、Audit、Evidence、保持選択結果をcascade削除しない契約。
4. DELETE_PENDING、RESULT_DELETED、DELETE_FAILED、部分失敗、再起動、同時要求、復元なし。
5. 実Data／実Runを使う受入範囲と、一時fixtureだけで行う範囲。既存Evidenceを削除しないこと。
6. 物理削除後のManual表現と、先にCSVをExportする注意書き。

出力:
- doc/phase5R2/08_DELETE-G1/08_P5R2-DELETE-G1承認packet.html
- plan/phase5R2/ログ/P5R2-20_DELETE-G1_承認依頼_2026-08-23.md
- 統合台帳の対象、期限、再開条件、証拠先（未承認のまま）

明示承認がない限り、unlink／Remove-Item／既存Artifact削除を行わない。承認はHistorical Data、Run本体、CSV、Audit、Evidenceの削除許可を含まない。
```

### P5R2-DELETE-G1 — 物理削除範囲を人が承認する

```text
step_id=P5R2-DELETE-G1。人判断を開始する独立Gate Stepである。開始条件はP5R2-20のDELETE-G1 packetが存在し、P5R2-15のlocal delete guard／REDとP5R2-19の保護対象表示が確認できること。packet作成を承認とみなさない。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1（.codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。Coordinatorと全Agentのspawn／waitが成立しない場合は、receiptにruntime_backend、dispatch_mode=RUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。人の承認はAIの完了statusで代替しない。

人が確認する対象:
1. 物理削除は、利用者が明示したterminal result Artifactだけか。
2. logical result_artifact_idから固定許可rootを解決し、任意path、traversal、symlink／reparse、TOCTOU、別Run、active Runを拒否できるか。
3. Export済みCSV、Historical Data、Run本体、監査、Evidence、保持選択結果をcascade削除しないか。
4. DELETE_PENDING、RESULT_DELETED、DELETE_FAILED、部分失敗、再起動、同時要求、復元なしを受け入れるか。
5. 既存実Data／Runを使う範囲と一時fixtureだけの範囲、実施時の証拠先、費用、権限を明示したか。

承認待ちの状態を次の文字列で保存する:
- `P5R2-DELETE-G1_UNAPPROVED`
- `P5R2-DELETE-G1_APPROVED_BOUNDED_P5R2_21_FIXTURE_ONLY`（対象と範囲を明示した場合だけ）

承認文の例は「P5R2-DELETE-G1を承認します。承認packetに記載したterminal result Artifactだけを対象に、CSV・Historical Data・Run本体・監査・Evidenceを保護して物理削除を実行してください。」である。単なる「続けて」は承認とみなさない。

出力:
- plan/phase5R2/ログ/P5R2-DELETE-G1_HumanGate_2026-08-23.md
- plan/phase5R2/quality/runtime-receipt-P5R2-DELETE-G1.json と .md
- 統合台帳のGate行（未承認または明示承認済みのどちらかを正確に反映）

人の明示承認がない限り、P5R2-21へ進まず、unlink／Remove-Item／既存Artifact削除を行わない。
```

### P5R2-21 — DELETE-G1承認時だけ物理削除受入を行う

```text
step_id=P5R2-21。開始条件はP5R2-DELETE-G1の対象、許可root、依存、CSV保護、監査、path安全、復元なし、実受入範囲の明示承認。承認範囲外のpath・ID・Data・Runは絶対に対象にしない。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A110_PythonTestEngineer_v0_1（.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A120_PythonImplementer_v0_1（.codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A140_DebugEngineer_v0_1（.codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、security-review、autotrade_skill_ops_security_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。安全確認に失敗した場合は物理削除を実行せずDELETE_FAILED／BLOCKEDで停止する。

実装・Test:
1. API入力はlogical result_artifact_idだけ。任意pathを受付しない。
2. 台帳からRun、Artifact種別、許可root、CSV状態、依存数を解決する。
3. canonical pathがroot外、..を含む、absolute任意path、symlink／reparse、台帳ID不一致、unlink直前の差し替えならfail-closed。
4. active Run、保持選択、EXPORTING CSV、Historical Data、Run本体、Audit、Evidence、別Run Artifactを拒否する。
5. 許可された一時fixture、またはDELETE-G1で明示された限定Artifactだけを対象に物理削除し、削除後にRESULT_DELETED tombstoneとAuditを残す。
6. 失敗時はDELETE_FAILEDとして対象・保護対象を残し、cascadeを続けない。restore APIは作らない。

出力:
- tests/evidence/phase5R2/<RunId>/P5R2-21_delete/
- Python/UIコード、RED→GREEN、security／code review、runtime receipt
- 既存実Data／Run／Evidence／Auditを削除していない確認
```

### P5R2-22 — 01_バックテスト手順書を改訂し、実画像を取得する

```text
step_id=P5R2-22。開始条件はP5R2-13〜21の対象機能が実装・検証済みで、画像を撮る操作が実Application APIでassertできること。未実装機能をManualへ書かない。H2未承認のため、ManualをP5R2完了宣言として扱わない。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A171_UiVisualQaReviewer_v0_1（.codex/agents/AutoTrade_A171_UiVisualQaReviewer_v0_1.json、model=gpt-5.6-terra）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_html_doc_writer_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。Playwrightは実Application APIへ接続し、可視名／role／labelをassertしてから同じ状態を撮影する。desktop 1280x900、mobile 390x844、axe、外部request 0またはDATA-G1承認範囲だけをreceiptへ保存する。

改訂対象:
1. P5R5の履歴であるSpot／1m説明と、現行のstrategy timeframe／1m sourceを明確に分離する。
2. Single Backtestの5時間足、30m、期間境界、Preflight、生成確認、銘柄／複数時間足／期間入力、全期間既定値を説明する。
3. Data Download／Generation Jobの開始、進捗、取消、失敗、再試行、Catalog、quality、usable、merge／replace、conflictを説明する。
4. 実行一覧・進捗・結果サマリーのcancel、terminal state不変、in-flight disable、結果保持、不要Artifact物理削除、CSV／Data／Audit／Evidence保護を説明する。
5. 失敗・復旧、restart、RECOVERY_REQUIRED、削除不可条件、復元なし、安全境界、Broker／Paper／Live非対象を平易に説明する。
6. 本文assert、Test ID、Evidence、PNG、viewport、alt、caption、capture registry、改訂履歴を双方向追跡する。

対象文書:
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- 必要な場合だけdoc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html

Acceptance:
- 実装済み・Test済みの操作だけが利用可能として書かれている。
- 旧1m固定を現在仕様として残さない。
- 画像はassert後、desktop/mobile、axe、Evidence link、alt/caption付き。
- Manual本体の更新結果、差分、レビューをP5R2-H2 packetへ渡す。
```

### P5R2-23 — 最終統合・Security／Code／UI／Manualレビューと再試験

```text
step_id=P5R2-23。開始条件はP5R2-22のManual候補、全local／provider／delete受入Evidence、8件coverage、各Gateの承認記録が揃っていること。H2はまだ未承認であり、完了宣言・P6開始は行わない。

CoordinatorはAutoTradeProject_ImplementationQuality_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A130_VerificationEngineer_v0_1（.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A150_PythonCodeReviewer_v0_1（.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A160_TradingSecurityReviewer_v0_1（.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A171_UiVisualQaReviewer_v0_1（.codex/agents/AutoTrade_A171_UiVisualQaReviewer_v0_1.json、model=gpt-5.6-terra）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_python_test_quality_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2とquality fixed Run contractを適用する。各reviewはFindings first。Critical／Highが1件でも残る場合はP5R2-23_REVIEW_BLOCKEDで改訂Stepへ戻す。

確認:
1. 8 atomic RequirementのREQ→AC→UI→API→Persistence→Test→Evidence→Manual→Gate coverage。
2. timeframe、Historical Data、Run cancel／delete、CSV、Data、Audit、Evidence、P6境界のcross-document整合。
3. path safety、TOCTOU、symlink／reparse、active Run、CSV、Audit、Evidence protection、network／Secret／cost。
4. P5R旧legacy、v3、v4、P5R2台帳、index、Manualの状態矛盾。
5. 実画面のdesktop/mobile、axe、focus、keyboard、request監視、Manual画像のassert。
6. 管理hash再導入がなく、A95がALLOWできるか。用途不明のprotected hashはNEEDS_HUMAN_GATE。

出力:
- plan/phase5R2/ログ/P5R2-23_最終統合レビュー・再試験_2026-08-22.md
- tests/evidence/phase5R2/<RunId>/P5R2-23_final/
- Finding採否、改訂差分、再試験結果、runtime receipt
```

### P5R2-24 — H2承認packetを作成する

```text
step_id=P5R2-24。開始条件はP5R2-23の最終レビューでCritical／High=0、P5R2-22のManual／画像／Evidenceが揃い、8 atomic Requirement coverageが100%であること。人のH2承認はまだ受領していない。完了候補を作るだけで、P5R2完了宣言・P6開始は行わない。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。A10は8件coverageとUnknownを確認し、A80は文書導線、A90はFindings first、A95は管理hash再導入だけを確認する。

作業:
1. AT-REQ-004の8 atomic Requirementごとに、実装、Test、Evidence、Manual、Gate、残Unknownを1行で追跡する。
2. P5R2-23のreview finding、採否、再試験、P5R2-DATA-G1／DELETE-G1の承認範囲、P5R2-UNK-QG-003をpacketへ反映する。P5R2-UNK-QG-001／002はlocal解消済みとしてEvidenceを参照する。
3. P5R2完了候補、P6再引渡し候補、P6-H0が別Gateであることを分離する。
4. 統合台帳、doc/index、Manual、v4、P5R2成果物の現在状態を確認する。H2はUNAPPROVEDのまま。

出力:
- doc/phase5R2/06_完了/09_P5R2-H2完了・P6再引渡しpacket.html（H2未承認）
- plan/phase5R2/ログ/P5R2-24_H2_packet作成_2026-08-22.md
- runtime-receipt-P5R2-24.json と .md

Acceptance:
- packetに、承認対象、未承認事項、残Unknown、禁止事項、Evidence先、P6-H0分離がある。
- Critical／Highが残る場合はH2 packetを完成扱いせず、P5R2-24_REVIEW_BLOCKEDで停止する。
```

### P5R2-H2 — 完了・P6再引渡しを人が承認する

```text
step_id=P5R2-H2。人判断Step。P5R2-23のCritical／High=0、全Acceptance、Manual、Evidence、Gate、Unknown、P6境界が揃わない場合はH2 packetを承認依頼せずP5R2-H2_UNREADYで停止する。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1（.codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用し、H2 packet作成のruntime receiptを保存する。H2 packet作成は承認ではなく、人の明示判断待ちである。

人が確認する対象:
- 8 atomic Requirementの全Acceptance。
- 5種類のstrategy timeframe、1m source、30m、legacy、UTC、quality、全期間。
- Historical Data Download／Generation、Catalog、merge／replace、conflict、provider境界。
- 3画面のcancel、結果保持、result Artifact物理削除、CSV／Data／Audit／Evidence保護、復元なし。
- Manual本体、実画像、axe、Evidence、改訂履歴、旧1m説明の履歴化。
- Open Unknown、P5R2-UNK-QG-003、DATA-G1／DELETE-G1の残り、P6停止と再引渡し。

出力:
- doc/phase5R2/06_完了/09_P5R2-H2完了・P6再引渡しpacket.html（未承認）
- plan/phase5R2/ログ/P5R2-H2_承認依頼.md
- 統合台帳のH2行（未承認）

明示文「P5R2-H2を承認します。P5R2を完了し、P6-H0へ引き渡してください。」がない限り、P5R2完了・P6開始へ進まない。
```

### P5R2-25 — H2承認後の完了判定とP6再引渡し

```text
step_id=P5R2-25。開始条件はP5R2-H2の人の明示承認、全Evidenceの参照可能性、統合台帳・index・Manual・v4・P5R2完了HTMLの状態一致。P6実装を開始するStepではなく、P6-H0の入力を引き渡すStepである。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1（.codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A10_RequirementsCurator_v0_1（.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A80_DocumentIntegrator_v0_1（.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）、AutoTrade_A90_DesignReviewer_v0_1（.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json、model=gpt-5.6-luna）、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（.codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json、model=gpt-5.6-luna、reasoning_effort=low）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

RDC-P5R2-0.2を適用する。H2承認をP6-H0承認に読み替えない。P6実装、Paper、Live、Broker、Secret、実資金は開始しない。

作業:
1. P5R2-REQ／AC、実装、Test、UI、Manual、Evidence、review、Unknown、Gateを最終coverageへ集約する。
2. `P5R2-COMPLETE_WITH_OPEN_UNKNOWN`または`P5R2-COMPLETE`を、H2の承認内容に応じて正確に記録する。UnknownをPassにしない。
3. v4を現在正本として保持し、v3／P5R／candidate／旧Manualを履歴へリンクする。
4. 統合台帳にP5R2-H2承認、P5R2完了、P6-H0が別Gateであること、残Unknown、再開条件、Evidence先を記録する。
5. doc/index.htmlにP5R2完了判定、v4、Manual、P6引渡し、P6-H0の順序を反映する。

出力:
- doc/phase5R2/06_完了/10_P5R2完了判定・P6-H0引渡し.html
- plan/phase5R2/ログ/P5R2-25_P5R2完了・P6再引渡し_2026-08-22.md
- 最終runtime receipt

Acceptance:
- P5R2完了とP6-H0待ちが明確に分離される。
- P6の実装・実行は開始していない。
- Git status、差分、機械検証、commit／pushの記録が完了する。
```

## 9. `01_バックテスト手順書`改訂の独立Acceptance

P5R2-CREQ-DOC-001は、単なる文言更新ではなく、実装・検証済み機能への追従を要求する。P5R2-22で次を満たす。

| ID | 改訂Acceptance |
|---|---|
| `P5R2-MAN-AC-01` | 5種類のstrategy timeframe、1m source、30m、legacyの意味が初心者にも分かる。旧1m固定を現在仕様として書かない。 |
| `P5R2-MAN-AC-02` | Data Download／Generation、銘柄、複数時間足、期間、既定全期間、quality、usable、失敗、取消、再試行を画面と一致して説明する。 |
| `P5R2-MAN-AC-03` | Data不足時にRunを開始せず、理由表示、確認dialog、銘柄引継ぎ生成画面への遷移を説明する。 |
| `P5R2-MAN-AC-04` | 実行一覧・進捗・結果サマリーのcancel判定、terminal状態不変、二重押下、再送、復旧を説明する。 |
| `P5R2-MAN-AC-05` | 保持結果と不要result Artifactの違い、物理削除、CSV先行Export、CSV／Data／Audit／Evidence保護、復元なしを説明する。 |
| `P5R2-MAN-AC-06` | 失敗、RECOVERY_REQUIRED、CONFLICT、UNUSABLE、DELETE_FAILED、provider停止を平易な日本語で説明する。 |
| `P5R2-MAN-AC-07` | 全画像が可視名／role／labelのassert後に取得され、desktop／mobile、alt、caption、Evidence、capture registryに追跡できる。 |
| `P5R2-MAN-AC-08` | BT-MAN→Requirement／AC→Test→Evidence→PNG→Manualの双方向リンクと改訂履歴がある。 |
| `P5R2-MAN-AC-09` | 未実装、未検証、未承認の機能を「利用可能」「成功」と書かない。 |

## 10. v0.2の計画Acceptance

| ID | Acceptance |
|---|---|
| `P5R2-PLAN2-AC-01` | 要件v4が正式Currentで、v3・P5R履歴・candidateが混同されずに保持される。 |
| `P5R2-PLAN2-AC-02` | 4領域と8件のatomic Requirementを別々に表示し、全8件に後続coverageがある。 |
| `P5R2-PLAN2-AC-03` | P5R旧完了範囲、P5R2の製品要件、P6開始条件が分離されている。 |
| `P5R2-PLAN2-AC-04` | P5R2-08からP5R2-25まで、途中欠番なく、直接実行可能な全文Promptがある。 |
| `P5R2-PLAN2-AC-05` | 各PromptにOrchestrator／Agent／Skill完全名、JSON path、固定model、RDC receipt、fallback、独立性表示がある。 |
| `P5R2-PLAN2-AC-06` | H1／DATA-G1／DELETE-G1／H2の対象、期限、再開条件、証拠先、禁止事項がStep単位で明記される。 |
| `P5R2-PLAN2-AC-07` | `run_test.ps1`のphase namespace制約とtrusted scope／fixture identityの不確実性をUnknownとして保持する。 |
| `P5R2-PLAN2-AC-08` | 管理hash、manifest、stale、fingerprint、hash retry、receipt hashを完了条件にしない。 |
| `P5R2-PLAN2-AC-09` | 実装前の詳細設計、RED、レビュー、改訂、再レビューが分離される。 |
| `P5R2-PLAN2-AC-10` | local fake providerと実Provider受入が別Step、別Run ID、別Evidence rootである。 |
| `P5R2-PLAN2-AC-11` | DELETE-G1前の実削除がなく、許可後も論理ID・固定root・CSV／Audit／Evidence保護がある。 |
| `P5R2-PLAN2-AC-12` | `01_バックテスト手順書`の改訂が独立Stepで、実画面・axe・Evidence・Manual fidelityを必須とする。 |
| `P5R2-PLAN2-AC-13` | H2後のP5R2完了とP6-H0が別状態として再引渡しされる。 |

## 11. 人へ求める次の判断

この計画は作成済みであり、現在の実行入口は本書である。P5R2-H1は承認packet、詳細設計再レビュー、権限移譲記録に基づき承認済みである。H1の承認範囲は、詳細設計、RED、対象path、Quality Gate、fixture、Evidence root、local実装に限定する。DATA-G1、DELETE-G1、H2の承認があるまで、外部Data、実削除、完了宣言、P6は開始しない。

要件v4正式化、計画v0.2再作成、P5R2-08〜10、P5R2-H1、P5R2-18 local quality、P5R2-19 local UI、P5R2-20 DELETE-G1 packet、P5R2-21 local物理削除受入、P5R2-22のバックテスト手順書改訂候補・実画像・a11y／link確認は完了した。P5R2-18 externalはhost-level isolation未確認でBlockedのまま、P5R2-22はP5R2-23最終統合レビューとH2判定待ち、H2は未承認である。P5R2完了宣言とP6はH2まで停止する。

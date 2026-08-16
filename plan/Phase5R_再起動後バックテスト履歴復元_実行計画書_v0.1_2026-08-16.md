# 再起動後バックテスト履歴復元 実行計画書

- 文書ID: `AUTOTRADE-BACKTEST-RECOVERY-PLAN-001`
- 作成日: 2026-08-16（Asia/Tokyo）
- 状態: `STEP1_COMPLETED / RECOVERY-07_COMPLETED_WITH_RUNTIME_FALLBACK / GIT_HANDOFF_COMPLETED`
- 対象: Windows再起動・API再起動後も、バックテストの履歴・結果詳細・LedgerをUIから再び開けるようにする。
- 対象アプリ: `src/autotrade/application/backtest_product.py` と `ui/mock/`
- データ保存境界: `E:\strategy_test_data\autotrade\backtest\`
- 新しい保存ディレクトリ名: `catalog`（`temp`、`tmp`、`phase5r`を使わない）
- 実行証跡: `tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/<RunId>/`
- 計画・ログ: `plan/phase5R_restart_recovery/`

## 1. この計画で完成させること

現在は、バックテストが完了すると `result.json` はEドライブへ保存される。しかし、Application APIが起動したときにそのファイルを読み直して、画面の履歴一覧へ戻す処理がない。そのため、Windows再起動、APIプロセス再起動、アプリの停止・再起動後に、結果ファイルは残っているのにUIの履歴が空になる。

この計画では、次の状態を完成とする。

1. 完了した新しいRunについて、結果本体と、履歴一覧に必要な実行条件・状態・時刻・結果参照をEドライブへ原子的に保存する。
2. API起動時にEドライブの履歴カタログと既存の結果ファイルを読み込み、メモリ上のRun一覧を復元する。
3. 復元後に `GET /api/backtest/runs/history` で過去Runが返る。
4. 復元後に `GET /api/backtest/runs/<run_id>` と `GET /api/backtest/runs/<run_id>/rows` で結果詳細とLedgerを開ける。
5. 復元された完了Runを使って、比較と新しいCSV生成を行える。
6. 旧形式の `result.json` しか存在しないRunも、分かる範囲だけを復元し、推測した値を確定情報として扱わない。
7. 実行中にAPIが落ちたRunは、成功扱いにも自動再開可能扱いにもせず、`RECOVERY_REQUIRED` として安全に表示する。
8. 履歴ファイルが壊れている、結果本体が欠けている、パスが不正な場合は黙って消さず、復元問題として取得できる状態にする。
9. UIはAPI再起動後に履歴タブを開けば自動取得でき、結果を開く操作まで完了する。
10. Windows再起動を模したAPIプロセス停止・再起動のPlaywright検証を行い、再起動前後で同じRun ID、指標、Ledgerが確認できる。

### 中学生向けの完成イメージ

バックテストを「テストの答案」と考える。今までは答案をEドライブへ置いていたが、アプリが「どの答案があるか」を覚えていなかった。今回、答案と一緒に「名前・条件・点数・保存場所」を記録し、アプリを再起動したらその記録を読み直す。だから、Windowsを再起動しても、前の答案を画面から開けるようになる。

## 2. 現状事実と設計方針

### 2.1 現状事実

| 確認対象 | 現状 | 影響 |
|---|---|---|
| `BacktestProductService._runs` | Pythonプロセス内の辞書だけ | API再起動でRun一覧が消える |
| `result.json` | `results/<run_id>/result.json`へ結果・rows・provenanceを保存 | 結果本体は残るが、現APIが自動発見しない |
| Run条件 | 現行result.jsonの旧形式には完全なspecがない | 旧結果復元時は既知値と不明値を分ける必要がある |
| `MetadataStore` | P4の別Application API用SQLite実装。現P5R HTTP APIには接続されていない | そのまま接続すると別契約の大規模変更になる |
| 既定保存先 | `E:\strategy_test_data\autotrade\backtest\` | Cドライブへフォールバックしてはならない |
| 起動経路 | `start_autotrade.bat`からAPIとUIを起動 | Windows再起動後は新しいPythonプロセスが新しいサービスを作る |

### 2.2 今回の採用候補

今回の第一候補は、P5Rの現HTTP APIと直接接続できる、Eドライブ上のアプリケーション専用JSON履歴カタログである。結果本体は従来どおり `results/<run_id>/result.json`、履歴メタデータは `catalog/runs/<run_id>.json` とする。各Runを別ファイルにし、書き込み中の一時ファイルを完成ファイルとして読まないように原子的な置換で保存する。管理目的のhashやmanifestは追加しない。

P4の未接続SQLite `MetadataStore` は今回のP5R修正へ無理に接続しない。SQLite採用は、P4契約との統合設計・移行・Human Gateが別途必要になるため、今回の最小完成範囲から外す。将来必要になった場合は別設計にする。ただし今回の詳細設計レビューで、この判断を確認し、Unknownとして残す必要があれば明記する。

### 2.3 安全境界

- 外部市場Data、Broker、Secret、実注文、実資金には接続しない。
- 新規保存先はEドライブの `autotrade/backtest/catalog` 配下とする。
- Cドライブ、Windowsの一時フォルダ、`temp`、`tmp`、`phase5r`という新規保存先は使わない。
- 復元できないRunを成功扱いにしない。
- 復元したRunのspecで不明な項目を推測値として確定しない。
- 途中Runのチェックポイントを、戦略状態まで復元できないまま自動再開しない。
- 管理・参照効率化だけを目的とするhash、manifest、stale、fingerprint、hash retryを追加しない。

## 3. 対象成果物

| 区分 | パス | 目的 |
|---|---|---|
| 計画書 | `plan/Phase5R_再起動後バックテスト履歴復元_実行計画書_v0.1_2026-08-16.md` | 本書。プロンプト群と実行結果を管理する |
| 実行ログ | `plan/phase5R_restart_recovery/` | 各Stepの受領、レビュー、採否、Unknownを記録する |
| 履歴カタログ実装 | `src/autotrade/application/history_catalog.py` または設計で確定した既存ファイル | Eドライブ上のRun履歴を安全に読み書きする |
| サービス改修 | `src/autotrade/application/backtest_product.py` | 起動時復元、保存、旧形式互換、回復要否を実装する |
| 保存先定義 | `src/autotrade/application/storage_paths.py` | `catalog`の標準パスを定義する |
| API改修 | `src/autotrade/application/http_server.py` | 復元情報・health表示が必要なら追加する |
| Pythonテスト | `tests/phase5R/test_backtest_history_recovery.py` など | RED/GREEN、壊れたファイル、旧形式、API再起動相当を検証する |
| UI改修 | `ui/mock/src/P5RBacktestScreen.tsx`、必要なら`backtestApi.ts` | 履歴タブの再取得と回復状態の表示を改善する |
| UIテスト | `ui/mock/tests/backtest-history-recovery.spec.ts` など | API停止・再起動後の履歴復元をブラウザで検証する |
| 詳細設計 | `doc/phase5R/02_実装詳細設計/03_再起動後バックテスト履歴復元実装詳細設計書.html` | 実装可能な永続化・復元契約を正式化する |
| 手順書 | `doc/phase5R/07_運用手順/01_バックテスト手順書.html` | 再起動後に履歴を確認する操作を追記する |
| 完了判定 | `doc/phase5R/06_完了/05_再起動後バックテスト履歴復元完了判定.html` | この機能の完了条件・証拠を記録する |
| Index | `doc/index.html` | 新しい正式HTMLへ到達できるようにする |
| 統合台帳 | `doc/00_全Phase残課題Blocked統合台帳.html` | Open Unknown、Recovery境界、Human Gate状態を同期する |

## 4. 実行Runtime共通契約

以下は、各Stepのプロンプトへ適用する。完全名を列挙しただけでは実行済みとしない。

1. `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` の利用可否を最初に確認する。
2. 指定OrchestratorのJSONを読み、JSONに定義された固定modelを使ってCoordinatorを実spawnする。
3. Coordinatorは、プロンプトに明記された全Agentを一体ずつspawnし、各Agent JSONの固定modelでwaitする。
4. 受領記録には、`orchestrator_name`、`orchestrator_json_path`、`orchestrator_model`、`orchestrator_agent_id`、`agent_name`、`agent_json_path`、`agent_model`、`agent_id`、`spawn_status`、`wait_status`、`output_ref`、`independent`、`review_mode`を記録する。
5. 起動できない場合は、変更・レビュー・完了判定より先に、`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`LOCAL_FALLBACK_NO_SUBAGENTS`、未起動Agent、理由、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を`plan/phase5R_restart_recovery/`へ記録する。未起動を独立実行済みと表現しない。
6. 固定modelを代替modelへ黙って置き換えない。`default_orchestrator`を変更しない。
7. Human Gate、外部I/O、Secret、UnknownのPass、Critical/High指摘がある場合はFail-closedで止める。起動不能Fallbackだけは事実を記録したうえで、ルート責務チェックリストにより継続できる。
8. 管理用hashを作らない。A95はhashを計算せず、管理用hash経路の再導入だけを静的に判定する。

## 5. Human Gateと停止条件

| Gate | 位置 | 承認対象 | 今回の扱い |
|---|---|---|---|
| `AUTOTRADE-BACKTEST-RECOVERY-DESIGN` | 詳細設計完了後 | 保存形式、旧結果互換、途中Runの扱い、Eドライブ境界 | ユーザーから移譲された承認権限を使えるが、判断内容をEvidenceへ明記する |
| `AUTOTRADE-BACKTEST-RECOVERY-ACCEPTANCE` | 最終検証後 | 再起動後に履歴・詳細・Ledgerが復元されること | 実機Windows再起動が未実施なら、APIプロセス再起動検証と手動確認の差を明記する |

次の状態では完了を宣言しない。

- `result.json`があるだけで履歴APIの復元が未確認。
- 再起動前と再起動後でRun IDまたは指標・Ledgerが一致しない。
- 壊れた保存ファイルを無視して、何も問題がないように見せる。
- `RECOVERY_REQUIRED`を成功または自動再開可能として表示する。
- Cドライブまたは一時フォルダへ新規実行データを書き込む。
- 外部通信、Secret、Broker、実注文、実資金の経路が混入する。
- Critical/Highのレビュー指摘が残る。

## 6. Step間の依存関係

```text
Step 1 事実棚卸し・設計判断・プロンプト固定
  |
  v
Step 2 実装詳細設計の作成・初回レビュー・改訂・再レビュー
  |
  v
Step 3 pytest/Playwright REDテストの追加とRED確認
  |
  v
Step 4 Eドライブ永続化・起動時復元の最小実装
  |
  v
Step 5 Python品質・API再起動・UI/Playwright検証
  |
  v
Step 6 手順書・要件追跡・完了判定・Index・統合台帳の反映
  |
  v
Step 7 独立レビュー・A95・自己評価・Git確認・commit・push
```

Step 2が承認済みになるまで本番コードを変更しない。Step 3でテストが意図した理由でREDになったことを確認してからStep 4へ進む。Step 5はStep 4のGREEN後に行う。文書更新は実装の事実と検証結果を反映するため、主要検証後にStep 6で行う。

## 7. Step 1 — 事実棚卸し・設計判断・プロンプト固定

### このStepの目的

現在のコード、既存結果ファイル、起動経路、P4の未接続永続化、UIの履歴取得を読み、今回何を保存・復元するかを確定する。設計を推測で始めない。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-01
Role: 再起動後バックテスト履歴復元の事実棚卸し・計画確定ルートAgent

目的:
WindowsまたはApplication APIの再起動後も、完了したBacktest Runの履歴・結果・LedgerをUIから開けるようにするため、実装前の事実、既存契約、設計候補、対象外、Unknown、受入条件を固定する。まだ本番コードを変更しない。

使用Orchestrator:
- AutoTradePhasePlanning_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。代替modelへ置換しない。

担当Agent:
- AutoTrade_A05_PhaseExecutionPlanner_v0_1
  JSON: .codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json
- AutoTrade_A10_RequirementsCurator_v0_1
  JSON: .codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json
- AutoTrade_A90_DesignReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_phase_execution_planning_v0_1
- autotrade_skill_source_reader_v0_1
- autotrade_skill_traceability_v0_1
- autotrade_skill_design_review_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

発火制御と実行証跡:
1. 最初にmulti_agent_v1__spawn_agent / multi_agent_v1__wait_agentの利用可否を確認する。
2. Coordinatorを上記Orchestratorの固定modelで実起動し、指定Agentを全件個別spawnしてwaitする。
3. 受付・完了status、agent_id、JSON path、model、Skills、output_refをplan/phase5R_restart_recovery/RECOVERY-01-runtime-dispatch.mdへ保存する。
4. 起動不能なら、先にRUNTIME_DISPATCH_FALLBACK_REQUIRED、LOCAL_FALLBACK_NO_SUBAGENTS、未起動Agent、理由、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。独立実行済みとは書かない。
5. 旧Phase1専用部品、default_orchestrator、A07/A08の通常manifest管理経路は起動しない。
6. 管理用hash、manifest hash、stale、fingerprint、hash retryを作らない。A95は候補分類だけを行う。

読む入力:
- README.md
- AGENTS.md
- settings/language.md
- settings/ai_component_rules.md
- doc/index.html
- doc/00_全Phase残課題Blocked統合台帳.html
- doc/requirements/01_自動トレードシステム要件定義書_v3.html
- doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- src/autotrade/application/backtest_product.py
- src/autotrade/application/http_server.py
- src/autotrade/application/storage_paths.py
- src/autotrade/application/persistence.py
- src/autotrade/application/result_view.py
- ui/mock/src/backtestApi.ts
- ui/mock/src/P5RBacktestScreen.tsx
- ui/mock/tests/p5r-backtest.spec.ts
- start_autotrade.bat、stop_autotrade.bat、scripts/start_autotrade.ps1、scripts/stop_autotrade.ps1
- 既存のtests/phase5Rとtests/evidence

調査項目:
1. _runs、_sweeps、_csv_jobs、holdout状態がどこで作られ、どこで消えるかを行番号付きで記録する。
2. result.jsonの実際の保存形式と、既存Eドライブにある旧形式の代表例を読む。Secretや個人情報は証跡へコピーしない。
3. RunViewに必要な全項目を列挙し、現result.jsonだけで復元できる項目・復元できない項目を分ける。
4. P4 MetadataStoreが現P5R APIへ接続されていない事実と、今回接続しない場合の理由を記録する。
5. Eドライブ以外への保存、temp/tmp/phase5r名、新規hash管理経路が入らない候補だけを残す。
6. APIプロセスを止めて起動し直したときのユーザー操作と、UIが履歴を取得するタイミングを確認する。
7. 完了したRun、旧形式Run、実行中に落ちたRun、壊れたファイルの期待状態を定義する。

出力:
- plan/phase5R_restart_recovery/RECOVERY-01_事実棚卸し.md
- plan/phase5R_restart_recovery/RECOVERY-01_traceability.md
- plan/phase5R_restart_recovery/RECOVERY-01-runtime-dispatch.md

完了条件:
- 実装対象ファイルと除外ファイルが確定している。
- 新規保存先がEドライブのautotrade/backtest/catalogであり、C/temp/phase5rを使わない。
- 新形式と旧形式の復元ルール、途中Runのfail-closedルール、壊れたファイルの表示ルールが文章で確定している。
- 必須テストケースがRunView、rows、比較、CSV、API再起動、UI再起動、旧形式、破損、パス脱出まで追跡できる。
- UnknownをPassにしていない。
```

### Step 1完了時の確認

- [ ] 本計画書とStep 1実行ログが保存されている。
- [ ] 現状の「結果本体はあるがUI履歴が復元できない」事実が再確認されている。
- [ ] Step 2へ進める設計境界が確定している。

## 8. Step 2 — 実装詳細設計の作成・初回レビュー・改訂・再レビュー

### このStepの目的

実装者が追加判断なしに、保存形式、起動時復元、旧result.json互換、破損時処理、API/UI契約、テストを実装できる詳細設計を正式HTMLにする。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-02
Role: 再起動後バックテスト履歴復元の実装詳細設計・レビュー統合Agent

目的:
RECOVERY-01の事実棚卸しを入力に、P5Rの既存実装へ安全に追加できる実装詳細設計書を作成し、A91初回レビュー、A90横断・Red Teamレビュー、レビュー反映、A91再レビューまで完了する。設計が承認されるまで本番コードは変更しない。

使用Orchestrator:
- AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。

担当Agent:
- AutoTrade_A10_RequirementsCurator_v0_1
  JSON: .codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json
- AutoTrade_A20_ArchitectureDomainArchitect_v0_1
  JSON: .codex/agents/AutoTrade_A20_ArchitectureDomainArchitect_v0_1.json
- AutoTrade_A82_ImplementationDetailDesigner_v0_1
  JSON: .codex/agents/AutoTrade_A82_ImplementationDetailDesigner_v0_1.json
- AutoTrade_A91_ImplementationDetailReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A91_ImplementationDetailReviewer_v0_1.json
- AutoTrade_A90_DesignReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_implementation_detail_design_v0_1
- autotrade_skill_implementation_detail_review_v0_1
- autotrade_skill_architecture_writer_v0_1
- autotrade_skill_domain_modeling_v0_1
- autotrade_skill_source_reader_v0_1
- autotrade_skill_traceability_v0_1
- autotrade_skill_design_review_v0_1
- autotrade_skill_red_team_review_v0_1
- autotrade_skill_revision_integration_v0_1
- autotrade_skill_html_doc_writer_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

実行契約:
1. 指定Orchestratorを固定modelでspawnし、指定Agentを全件個別spawnしてwaitする。
2. 受領証跡をplan/phase5R_restart_recovery/RECOVERY-02-runtime-dispatch.mdへ保存する。
3. 起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを先に記録する。
4. 独立レビューを実行できなかった場合、ルートAgentの自己レビューを独立レビュー済みと表現しない。
5. 管理用hash、manifest、stale、fingerprintを作成しない。

読む入力:
- RECOVERY-01の全出力
- doc/ai_foundation/14_実装詳細設計書構成標準.html
- doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html
- doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html
- doc/requirements/01_自動トレードシステム要件定義書_v3.html
- doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html
- 対象リポジトリの実装・テスト・storage_paths

設計書に必ず定義すること:
1. ドメイン概要: 再起動前後で何が変わり、何を戻すのかを中学生でも分かる日本語で説明する。
2. ファイル構成、Mermaidのモジュール構造図、実線矢印のデータ受渡し名、直後の受渡し表。
3. 履歴カタログの保存場所、ファイル名、schema_version、必須項目、型、nullability、相対パス規則、上書き禁止、原子的書込み。
4. RunViewの保存契約とresult.jsonの結果本体の関係。Result bodyはrows/metrics/provenance、catalogはspec/status/timestamps/refsを担当することを明記する。
5. 新形式Runのcreate、running、failed、cancelled、succeeded、API起動時restoreの処理順をMermaidで示す。
6. API停止中のRUNNING/QUEUED/CANCELLEDを、なぜ自動再開せずRECOVERY_REQUIREDにするかを定義する。
7. 旧result.jsonだけのRunから復元できる項目、UNKNOWNにする項目、legacy表示の方法を定義する。旧結果を勝手に補完しない。
8. JSON破損、schema不一致、run_id不一致、results外へのパス、result欠落、catalog欠落の挙動をfail-closedで定義する。
9. `GET /api/backtest/runs/history`、`GET /api/backtest/runs/<id>`、`GET /api/backtest/runs/<id>/rows`、compare、CSVが復元Runで使える条件を定義する。
10. UI履歴タブの取得タイミング、再起動後のメッセージ、RECOVERY_REQUIREDの表示を定義する。
11. 既存P4 MetadataStoreを今回接続しない理由、将来のSQLite移行をUnknownとして整理する。
12. 単体、結合、APIプロセス再起動、Playwrightの全テストケースを文章で列挙する。
13. REQ/DEC/UNK/ARTの追跡表、Run Manifest、data_version、Human Gate、レビュー採否表、改訂履歴を含める。

正式出力:
- doc/phase5R/02_実装詳細設計/03_再起動後バックテスト履歴復元実装詳細設計書.html
- plan/phase5R_restart_recovery/RECOVERY-02_詳細設計レビュー.md
- plan/phase5R_restart_recovery/RECOVERY-02_traceability.md
- plan/phase5R_restart_recovery/RECOVERY-02-runtime-dispatch.md

完了条件:
- A91初回レビューでCritical/High/Unknownを残したままPassにしない。
- A90横断・Red Teamの指摘と採否を記録する。
- 指摘を反映した後にA91再レビューを実施する。
- A91再レビューで実装へ渡せる状態になっている。未解決ならStep 3へ進めず停止する。
- doc/index.htmlから正式設計書へ到達できる導線を更新する。
```

## 9. Step 3 — pytest/Playwright REDテストの追加とRED確認

### このStepの目的

実装前に「APIを作り直したら過去Runが見える」「Ledgerを開ける」「旧形式が復元される」「破損を成功扱いしない」ことをテストとして固定し、意図した未実装状態でREDを確認する。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-03
Role: 再起動後バックテスト履歴復元のTDD REDテスト担当Agent

目的:
承認済みRECOVERY-02詳細設計に従い、実装コードを変更せずにpytestと必要なPlaywrightテストを先に追加し、意図した理由で失敗するREDを確認する。

使用Orchestrator:
- AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。

担当Agent:
- AutoTrade_A110_PythonTestEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json
- AutoTrade_A130_VerificationEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json
- AutoTrade_A90_DesignReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_python_test_quality_v0_1
- autotrade_skill_test_strategy_v0_1
- tdd-workflow
- e2e-testing
- autotrade_skill_traceability_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

実行契約:
1. Orchestratorをspawnし、A110、A130、A90、A95を全件spawn/waitする。
2. 受領証跡をplan/phase5R_restart_recovery/RECOVERY-03-runtime-dispatch.mdへ保存する。
3. 起動不能時はFallbackを先に記録し、独立実行済みとは書かない。
4. 外部ネットワーク、Broker、Secret、実データ追加、実注文は使用しない。
5. テスト追加後、実際にテストを実行し、未実装機能が原因のREDであることを確認する。構文エラーや依存不足だけの失敗はREDとして認めない。

追加するテスト候補:
1. `BacktestProductService`を同じruntime_rootで作り直すと、完了Runのlist_runsに同じrun_idが出る。
2. 作り直したサービスでget_runがmetrics/spec/provenanceを返し、get_rowsが保存済みrowsを返す。
3. 作り直したサービスでcompare_runsが復元Runを比較できる。
4. 作り直したサービスで復元RunからCSV Jobを作成し、CSVダウンロードできる。
5. 新規Runはresult.jsonだけでなくcatalogの履歴レコードも生成する。
6. `result.json`だけの旧形式fixtureはlegacy/recovered表示で復元され、存在しない条件を勝手に確定しない。
7. catalog JSONが壊れている、run_idがファイル名と違う、result.jsonが壊れている、相対パスがresults外を指す場合はRECOVERY_REQUIREDまたはrecovery issueになり、SUCCEEDEDとして扱われない。
8. API再起動相当のThreadingHTTPServer停止・再生成後、history/detail/rowsが同じRunを返す。
9. 途中のRUNNINGレコードを起動時に自動成功・自動再開せずRECOVERY_REQUIREDにする。
10. `reset_for_local_test`はテスト用のメモリ状態だけを初期化し、ユーザーの保存結果を勝手に削除しない。
11. storage_pathsにcatalogがEドライブ配下で、C/temp/tmp/phase5rを含まない契約を追加する。
12. PlaywrightでRun作成完了→APIプロセス停止→API再起動→履歴タブ→結果を開く→Ledger表示を検証する。テストはプロセスを対象識別できる安全な方法で停止し、無関係なPIDをkillしない。

テスト境界:
- pytestのruntime_rootにはtmp_pathを使ってよいが、実アプリの既定保存先はEドライブであることを別テストで確認する。
- 新しいfixtureは匿名の小さな合成OHLCVだけを使う。既存のEドライブ結果をfixtureとしてコピーしない。
- 管理用hash/checksumをテストの受入条件にしない。

出力:
- tests/phase5R/test_backtest_history_recovery.py
- ui/mock/tests/backtest-history-recovery.spec.ts（実装対象がUIまで必要と設計で確定した場合）
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/RECOVERY-03_RED.md
- plan/phase5R_restart_recovery/RECOVERY-03-runtime-dispatch.md

完了条件:
- 実装コードを変更していない。
- 追加テストが実行され、履歴復元の未実装を原因とするREDが確認できる。
- REDのコマンド、終了コード、失敗要約、テストID、設計IDをEvidenceへ記録する。
- REDが環境不足や無関係な回帰の場合は、Step 4へ進まず原因を記録する。
```

## 10. Step 4 — Eドライブ永続化・起動時復元の最小実装

### このStepの目的

承認済み詳細設計とREDテストの範囲だけで、履歴カタログ、起動時復元、旧形式互換、破損時の回復要否、CSV/holdoutの必要な再起動境界、UIの履歴再取得を実装する。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-04
Role: 再起動後バックテスト履歴復元の最小実装Agent

目的:
承認済みRECOVERY-02詳細設計とRECOVERY-03 REDテストを満たす最小差分を実装し、まず対象REDをGREENにする。設計外のSQLite統合、外部接続、別Phase機能は実装しない。

使用Orchestrator:
- AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。

担当Agent:
- AutoTrade_A120_PythonImplementer_v0_1
  JSON: .codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json
- AutoTrade_A110_PythonTestEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json
- AutoTrade_A130_VerificationEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json
- AutoTrade_A140_DebugEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_python_implementation_v0_1
- autotrade_skill_python_test_quality_v0_1
- autotrade_skill_debug_recovery_v0_1
- autotrade_skill_traceability_v0_1
- autotrade_skill_ops_security_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

実行契約:
1. Orchestratorを固定modelでspawnし、指定Agent全件を個別spawn/waitする。
2. 変更前にRECOVERY-03 RED EvidenceとRECOVERY-02承認済みDD-IDを確認する。
3. target_pathsとexcluded_pathsをRun Manifestへ固定し、証跡をtests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/へ置く。
4. 起動不能時はFallback receiptを先に保存し、独立実行済みとは書かない。
5. A120はテスト削除、skip、閾値緩和、対象外変更、外部I/O、Secret、Broker、Liveを行わない。

実装要求:
1. 必要なら`storage_paths.py`へ`BACKTEST_CATALOG_ROOT`を追加する。既定値はEドライブ配下の`autotrade/backtest/catalog`とし、禁止名検査へ追従する。
2. `history_catalog.py`など設計で決めた単一責務モジュールを作り、Runの履歴レコードをJSONで原子的に保存・読込する。保存中の`.writing`などの未完成ファイルを正規レコードとして読まない。
3. 新規Run作成時、完了時、失敗時、取消時など設計で指定した状態境界で履歴レコードを保存する。保存失敗を成功扱いしない。
4. 完了時は結果本体を先に安全に公開し、その後履歴レコードを公開する、または設計で決めた同等の整合性規則にする。resultとcatalogの不一致を起動時に検出する。
5. `BacktestProductService.__init__`で履歴を読み込み、復元Runを`_runs`へ再構成する。復元Runのthread/eventは新規作成し、実行中だった旧threadを再開しない。
6. 新形式ではspec、kind、parent_id、status、progress、total、started_at、ended_at、metrics、provenance、failure、checkpoint、resume_count、result_referenceを保存する。
7. 旧形式result.jsonだけの場合は、rows/metrics/provenanceから安全に分かる範囲だけを再構成し、`recovery_mode=LEGACY_RESULT_ONLY`などを表示する。不明な戦略・時刻・条件を作り話しない。
8. catalogやresultが壊れていたら無視して成功一覧から消すのではなく、RECOVERY_REQUIREDまたはrecovery reportで停止理由を取得できるようにする。
9. API再起動後にlist/get/rows/compareが復元Runで使えるようにする。
10. 復元Runから新しいCSV Jobを作れるようにする。既存CSV Jobまで復元する設計なら、その契約に従う。復元できないJobを成功扱いしない。
11. Holdoutの一度だけという安全状態を再起動後も守る設計なら、その状態をEドライブへ保存する。未実装ならUnknownとして台帳に残し、成功宣言しない。
12. UIの履歴タブでAPIを再取得し、復元Runを「結果を開く」できるようにする。必要なら起動後初回表示でも履歴取得を行う。
13. APIのhealth/recovery情報を追加する場合、外部I/O無効の既存契約を壊さない。

実装後:
1. RECOVERY-03の対象pytestを同じコマンドで実行しGREENを確認する。
2. 失敗した場合はA140の上限付き仮説ループで原因を分類し、同じ仮説を2回以上無制限に試さない。
3. 修正後のtarget diff、テスト結果、未解決UnknownをEvidenceへ記録する。

完了条件:
- 新規Runの保存→サービス再生成→履歴/詳細/rows復元がGREEN。
- 旧形式、破損、途中Run、パス脱出の安全テストが設計どおりGREEN。
- Eドライブ以外へ新規実行データを書いていない。
- 実装は承認済みDD-IDとREDテストの範囲に限定されている。
```

## 11. Step 5 — Python品質・API再起動・UI/Playwright検証

### このStepの目的

単体テストだけでなく、実際のHTTP APIを停止・再起動し、同じEドライブの結果がUI履歴へ戻ることを確認する。プロセス境界を越えた復元を検証する。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-05
Role: 再起動後バックテスト履歴復元の統合検証Agent

目的:
RECOVERY-04実装について、pytest、build、既存Backtest UI回帰、APIプロセス再起動、Playwrightの履歴復元journey、アクセシビリティ、外部通信ゼロを検証する。失敗は隠さず分類する。

使用Orchestrator:
- AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。

担当Agent:
- AutoTrade_A130_VerificationEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json
- AutoTrade_A140_DebugEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json
- AutoTrade_A150_PythonCodeReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json
- AutoTrade_A160_TradingSecurityReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_python_test_quality_v0_1
- autotrade_skill_debug_recovery_v0_1
- autotrade_skill_python_code_review_v0_1
- e2e-testing
- verification-loop
- autotrade_skill_ops_security_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

実行契約:
1. Orchestratorをspawnし、指定Agent全件を個別spawn/waitする。
2. 固定Run ID、target_paths、excluded_paths、fixture、証跡rootを記録する。
3. 起動不能時はFallbackを先に記録する。独立レビュー済みとは書かない。
4. 外部ネットワーク、Broker、Secret、実注文、実資金を使わない。

検証順序:
1. `git diff --check`とPython compile/importの対象確認。
2. RECOVERY-03/04の対象pytestを実行する。
3. 既存`tests/phase5R`と関連Backtest/Applicationテストを実行する。
4. UIのunit/build/lintを実行する。
5. Playwrightで次のjourneyを実行する。
   - APIを起動する。
   - Preflight→Single Run→SUCCEEDEDまで進める。
   - Run ID、5指標、Ledger行を記録する。
   - APIプロセスを、起動スクリプトが記録した対象PIDまたはテストが自分で起動した対象プロセスだけ、安全に停止する。無関係なPIDを終了しない。
   - 同じruntime_root/Eドライブ結果を使ってAPIを新しいプロセスで起動する。
   - UIで履歴タブを開き、再起動前のRun IDを確認する。
   - 「結果を開く」を押し、同じ5指標とLedgerを確認する。
   - 復元Runを選んで比較とCSV生成が成功することを確認する。
   - 外部リクエストが0件であることを確認する。
6. 破損catalog、旧形式result、実行途中の再起動を別の隔離fixtureで検証する。
7. A150はPython差分をFindings firstでレビューする。A160は外部I/O、fail-open、パス、データ混入、実取引到達経路をレビューする。
8. Critical/High/UnknownをPassにせず、必要ならA140で原因別に修正して同じ検証を再実行する。

Evidence:
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/verification.json
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/api-restart-recovery.json
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/playwright/
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/reviews/
- plan/phase5R_restart_recovery/RECOVERY-05_検証ログ.md

完了条件:
- Python対象テスト、UI build/unit/lint、API再起動、Playwright履歴復元、A11y、外部通信ゼロが事実に基づき判定できる。
- 再起動前後のRun ID、metrics、rowsの同一性が確認できる。
- 失敗、破損、RECOVERY_REQUIREDが誤って成功表示されない。
- EvidenceのないPassを記録していない。
```

## 12. Step 6 — 要件・手順書・完了判定・Index・統合台帳の反映

### このStepの目的

実装と検証で確認できた事実だけを正式文書へ反映する。初心者が「Windows再起動後にどう履歴を戻すか」を手順書だけで分かる状態にする。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-06
Role: 再起動後バックテスト履歴復元の文書統合Agent

目的:
RECOVERY-05の実装・検証Evidenceを根拠に、要件追跡、実装詳細設計、初心者向けバックテスト手順書、完了判定、doc/index.html、統合Blocked台帳を矛盾なく更新する。未検証の機能を完成扱いしない。

使用Orchestrator:
- AutoTradeProject_DesignDocSet_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。

担当Agent:
- AutoTrade_A10_RequirementsCurator_v0_1
  JSON: .codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json
- AutoTrade_A80_DocumentIntegrator_v0_1
  JSON: .codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json
- AutoTrade_A81_DesignDocSetWriter_v0_1
  JSON: .codex/agents/AutoTrade_A81_DesignDocSetWriter_v0_1.json
- AutoTrade_A90_DesignReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_design_doc_set_writer_v0_1
- autotrade_skill_html_doc_writer_v0_1
- autotrade_skill_source_reader_v0_1
- autotrade_skill_traceability_v0_1
- autotrade_skill_revision_integration_v0_1
- autotrade_skill_design_review_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

実行契約:
1. Orchestratorをspawnし、指定Agent全件を個別spawn/waitする。
2. 受領証跡をplan/phase5R_restart_recovery/RECOVERY-06-runtime-dispatch.mdへ保存する。
3. 起動不能時はFallbackを先に記録する。
4. A95は管理用hashを計算せず、再導入だけを判定する。

更新対象:
1. `doc/requirements/01_自動トレードシステム要件定義書_v3.html`
   - P5Rの完了条件へ「再起動後の履歴・結果・Ledger復元」を追記する。
   - 旧形式互換、破損時RECOVERY_REQUIRED、途中Run自動再開不可の境界を追跡する。
2. `doc/phase5R/02_実装詳細設計/03_再起動後バックテスト履歴復元実装詳細設計書.html`
   - 実装・レビュー・再レビュー・Evidenceへのリンクを反映する。
3. `doc/phase5R/07_運用手順/01_バックテスト手順書.html`
   - 「Windows再起動後に過去のRunを確認する」章を追加する。
   - start_autotrade.batを実行する。
   - ブラウザでBacktestを開く。
   - 「履歴・比較」タブを開く、必要なら「履歴を更新」を押す。
   - 再起動前のRun IDを探す。
   - 「結果を開く」を押し、5指標とLedgerを確認する。
   - 結果がない場合の確認先を、E:\strategy_test_data\autotrade\backtest\results\とcatalogへ案内する。ただしファイルを直接編集しないよう注意する。
   - `RECOVERY_REQUIRED`の意味を平易に説明する。
   - ブラウザ更新だけではAPI再起動ではないこと、Windows再起動ではAPIが新しく起動することを説明する。
4. `doc/phase5R/06_完了/05_再起動後バックテスト履歴復元完了判定.html`
   - 要件、実装、テスト、API再起動、Playwright、残Unknown、Human Gateを表で記録する。
   - 実機Windows再起動を行っていない場合は、APIプロセス再起動との違いを明記する。
5. `doc/index.html`
   - 新しい詳細設計書と完了判定へリンクする。
6. `doc/00_全Phase残課題Blocked統合台帳.html`
   - この機能の完了状態、未完了の実機再起動確認、将来SQLite移行Unknownなどを現在状態へ同期する。古い事実は履歴として残す。

文書品質:
- 専門用語の直後に中学生でも分かる説明を付ける。
- 事実、設計、検証済み、未検証を混ぜない。
- P5Rの履歴復元完成と、Forward/Shadow/Paper/Liveの完成を混同しない。
- 画像を新たに作る場合は、Playwrightで取得したものだけを使い、手加工しない。

完了条件:
- 文書間の保存先、API、操作名、状態名、完了条件が一致する。
- 手順書だけを読んだ初心者が、Windows再起動後の履歴確認を実行できる。
- doc/index.htmlから正式成果物へ到達できる。
- Open UnknownをPassにしていない。
```

## 13. Step 7 — 独立レビュー・A95・自己評価・Git引渡し

### このStepの目的

実装・テスト・文書の整合性を独立観点で確認し、未解決の重大指摘を閉じてから、対象ファイルだけをcommit/pushする。

### そのまま実行するプロンプト

```text
Phase ID: AUTOTRADE-BACKTEST-RECOVERY
Step ID: RECOVERY-07
Role: 再起動後バックテスト履歴復元の最終受入・Git引渡しAgent

目的:
今回の変更が、Windows/API再起動後のバックテスト履歴復元という依頼だけを満たし、外部I/Oや実取引を増やしていないことを確認する。最終的にgit status、差分、機械検証、commit、pushを事実に基づいて完了する。

使用Orchestrator:
- AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- JSON: .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json
- 固定model: JSON定義から再読して使用する。

担当Agent:
- AutoTrade_A90_DesignReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json
- AutoTrade_A150_PythonCodeReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json
- AutoTrade_A160_TradingSecurityReviewer_v0_1
  JSON: .codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json
- AutoTrade_A130_VerificationEngineer_v0_1
  JSON: .codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json
- AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
  JSON: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json

使用Skill:
- autotrade_skill_design_review_v0_1
- autotrade_skill_python_code_review_v0_1
- autotrade_skill_python_test_quality_v0_1
- autotrade_skill_ops_security_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1
- agent-self-evaluation

実行契約:
1. Orchestratorをspawnし、指定Agent全件を個別spawn/waitする。
2. 起動不能時はFallback receiptを先に保存し、独立実行済みと書かない。
3. A95を対象の新規・大幅変更ファイルへ静的適用する。hash値、manifest、stale、fingerprint、hash retryを生成しない。

最終確認:
1. `git status --short`を確認し、今回のタスクで変更した対象ファイル一覧を作る。既存のユーザー変更を混ぜない。
2. `git diff --check`、対象pytest、関連pytest、UI build/unit/lint、Playwright、PowerShell構文、リンク検査を実行する。
3. 新規コードがEドライブへ書くこと、C/temp/tmp/phase5rへ書かないことを確認する。
4. catalog/resultの原子性、パス脱出拒否、壊れたファイルのfail-closed、途中RunのRECOVERY_REQUIREDを確認する。
5. API再起動前後のRun ID、metrics、rows、compare、CSVのEvidenceを確認する。
6. 手順書・詳細設計・要件v3・完了判定・Index・統合台帳のリンクと状態を照合する。
7. Critical/High/Unknownの未解決があれば完了・commit・pushを止め、原因と再開条件を記録する。
8. `agent-self-evaluation`形式で、Accuracy、Completeness、Clarity、Actionability、Concisenessを1〜5で評価し、5未満には具体的な根拠を書く。修正可能な不足は修正してから再評価する。
9. すべての機械検証とレビューが完了した後、今回の変更だけを意味のある単位でcommitする。reset --hard、checkout、force pushは使わない。
10. 現在ブランチの追跡先へpushし、push後にgit status --short、git log -1 --oneline --decorate、追跡先を確認する。

出力:
- plan/phase5R_restart_recovery/RECOVERY-07_最終レビュー.md
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/reviews/
- tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/agent-self-evaluation.md
- 最終報告へcommit ID、branch、push先、検証結果、Open Unknownを記録する。

完了条件:
- 再起動後の履歴・結果・Ledger復元がAPIとUIで証明される。
- 変更範囲、差分、検証結果、レビュー、A95が確認済み。
- commit/pushの成否を事実として報告できる。
```

## 14. Step 2以降の実行ログ

| Step | 実行日時 | 状態 | 主な成果物 | 未解決事項 |
|---|---|---|---|---|
| RECOVERY-01 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | `plan/phase5R_restart_recovery/RECOVERY-01_事実棚卸し.md`、`RECOVERY-01_traceability.md` | Coordinator/Agentはthread上限で未起動。独立実行扱いにしない |
| RECOVERY-02 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | 詳細設計HTML、`RECOVERY-02_詳細設計レビュー.md`、`RECOVERY-02_traceability.md` | 設計レビューはルート責務チェックリストで代替。大量データ上限・バックアップ・P4 DB統合はUnknownとして残す |
| RECOVERY-03 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | `tests/phase5R/test_backtest_history_recovery.py`、`tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/RECOVERY-03_RED.md` | 6件失敗。未実装の履歴復元機能が原因の意図したRED。Coordinator/Agentはthread上限で未起動 |
| RECOVERY-04 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | Python/UI実装、`RECOVERY-04_GREEN.md` | 対象pytest、既存P5R回帰、UI buildを確認。Coordinator/Agentはthread上限で未起動 |
| RECOVERY-05 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | `verification.json`、`api-restart-recovery.json`、Playwright画像、レビュー記録 | API子プロセス停止・再起動後のRun ID/metrics/provenance/rows/UI復元、既存desktop/mobile、unit/build/lintを確認。Coordinator/Agentはthread上限で未起動 |
| RECOVERY-06 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | v3.1、実装詳細設計v0.2、手順書v0.5、完了判定、Index、統合台帳、`RECOVERY-06-runtime-dispatch.md` | 完了範囲とOpen scopeを文書間で同期。Coordinator/Agentはthread上限で未起動 |
| RECOVERY-07 | 2026-08-16 | `COMPLETED_WITH_RUNTIME_FALLBACK` | `RECOVERY-07_最終レビュー.md`、A95記録、自己評価、Git引渡し | 実機Windows再起動は未実施。commit `a6c42cb`、push `origin/main` 完了 |

## 15. 既知の後続Unknown

この計画で解決しないものは、完了判定で明示的に残す。

- P4の汎用SQLite `MetadataStore`をP5Rの実HTTP APIへ統合するかどうか。
- 実機のWindows再起動を自動テストだけでなく人間操作として確認するかどうか。
- 実行中RunのチェックポイントとStrategyStateを完全に永続化し、再起動後に安全に再開する機能。
- 大量Runを想定した中央インデックス、保持期限、バックアップ、移行の運用設計。
- Forward Test以降の実時間データ、複数Unit、Portfolio、Risk、OMS、Paper、Live機能。

これらを今回のバックテスト履歴復元が完成したことの根拠に使わない。UnknownはUnknownのまま、決定時期と担当Phaseを記録する。

## 16. 計画書完了条件

- [x] 複数Stepのプロンプト群を作成した。
- [x] 各StepにOrchestrator、Agent、Skill、入力、出力、完了条件、停止条件を記載した。
- [x] 再起動後履歴、旧形式、破損、途中Run、Eドライブ境界、UI/Playwright、文書、Gitを含めた。
- [x] Step 2〜7を順番に実行する。
- [x] 最終レビュー、自己評価、A95静的確認、HTMLリンク、機械検証を完了する。
- [x] Git commit `a6c42cb` を作成し、`origin/main`へpushする。

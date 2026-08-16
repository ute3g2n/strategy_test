# AutoTrade ローカルアプリ一括起動 実行計画書

文書ID: `AUTOTRADE-APP-STARTUP-PLAN-001`
版: `v0.1`
作成日: `2026-08-16`
対象: Windowsのbatを入口とするAutoTradeローカルアプリの一括起動、停止、手順書反映
状態: `EXECUTION_COMPLETE_WITH_OPEN_UNKNOWN`

## 1. この計画で実現すること

利用者がWindowsのエクスプローラーで入口batをダブルクリックすると、プロジェクトの現在位置に関係なく、次の状態になることを目標とする。

1. 必要なPythonとNode.js/npmが使えるか確認される。
2. UI依存パッケージがなければ、`ui/mock/package-lock.json`に従って`npm ci`で準備される。
3. UIが最新ソースからbuildされる。
4. loopback限定のAutoTrade Application APIが`127.0.0.1:8765`で起動する。
5. UIのpreviewサーバーが`127.0.0.1:4173`で起動する。
6. APIの`/health`とUIの`/`が応答するまで待つ。
7. ブラウザで`http://127.0.0.1:4173`が開く。
8. APIとUIの標準出力・標準エラーがプロジェクト内のローカルログへ保存される。
9. すでに正しいAPIとUIが動いている場合は二重起動せず、ブラウザを開くだけにする。
10. ポートが別の不明なプロセスに使われている場合は、勝手に終了させず、原因と確認場所を表示して停止する。
11. 別の停止batをダブルクリックすれば、この起動経路で動かしたAPI/UIを安全に止められる。

本計画の範囲は、AutoTrade全体のうち、ローカルのBacktest UIとローカルAPIを起動して利用可能にする部分だけである。外部市場Data、Broker、Secret、実注文、実資金、Paper、Live、WSL、外部送信は扱わない。

## 2. 現在の起動構成

| 部品 | 起動方法 | 待受先 | 役割 |
|---|---|---|---|
| AutoTrade Application API | `py -3 scripts/phase5r/backtest_api_server.py --host 127.0.0.1 --port 8765` | `http://127.0.0.1:8765/health` | Backtestの計算・履歴・CSV・Holdout・Walk-forward API |
| AutoTrade UI | `ui/mock`で`npm run preview -- --host 127.0.0.1 --port 4173` | `http://127.0.0.1:4173/` | ブラウザで操作する画面 |
| UI build | `ui/mock`で`npm run build` | `ui/mock/dist/` | previewが配信するUIファイルを作る |
| 入口 | プロジェクト直下の`start_autotrade.bat` | なし | 上記を一括実行し、ブラウザを開く |
| 停止 | プロジェクト直下の`stop_autotrade.bat` | なし | 8765/4173の起動経路プロセスを止める |

## 3. 起動スクリプトの受入条件

### 3.1 Windows利用者の操作

- エクスプローラーで`start_autotrade.bat`をダブルクリックするだけでよい。
- batをどのカレントディレクトリから呼んでも、`%~dp0`からプロジェクトルートを解決する。
- 成功時はブラウザが開き、Backtest画面へ移動できる。
- `-NoBrowser`を付けた場合だけ、検査用にブラウザを開かない。
- `stop_autotrade.bat`でAPI/UIを止められる。

### 3.2 安全境界

- APIとUIは必ず`127.0.0.1`にbindする。`0.0.0.0`を使わない。
- ポート競合時に、無関係なプロセスを自動終了しない。
- 実注文、外部Data、Broker、Secretへ接続しない。
- `npm ci`は依存パッケージがない場合だけ実行し、入力されたlockfileを使う。
- ログにSecret値を出力する機能を追加しない。
- 停止処理は、対象プロジェクトの起動経路であることを確認してから対象プロセスだけを終了する。

### 3.3 起動失敗時の情報

少なくとも次を利用者へ示す。

- Python/npmが見つからない。
- `npm ci`または`npm run build`が失敗した。
- 8765または4173が他プロセスに使用されている。
- APIのhealth checkが時間内に成功しなかった。
- UIのhealth checkが時間内に成功しなかった。
- APIログ、APIエラーログ、UIログ、UIエラーログの保存先。

## 4. 変更対象とEvidence

| ID | 成果物 | 保存先 |
|---|---|---|
| START-ART-01 | ダブルクリック入口 | `start_autotrade.bat` |
| START-ART-02 | 起動処理本体 | `scripts/start_autotrade.ps1` |
| START-ART-03 | 停止入口 | `stop_autotrade.bat` |
| START-ART-04 | 停止処理本体 | `scripts/stop_autotrade.ps1` |
| START-ART-05 | 起動スクリプト静的検査 | `tests/phase5R/test_autotrade_app_startup.py` |
| START-ART-06 | 起動スモークEvidence | `tests/evidence/AUTOTRADE-APP-STARTUP/RUN-20260816-001/` |
| START-ART-07 | 操作手順書追補 | `doc/phase5R/07_運用手順/01_バックテスト手順書.html` |
| START-ART-08 | 完了判定 | `doc/phase5R/06_完了/04_AutoTradeアプリ一括起動完了判定.html` |
| START-ART-09 | 実行Receipt | `plan/autotrade_app_startup/` |

## 5. Step間の依存関係

```text
Step 1 調査・プロンプト固定
        |
        v
Step 2 起動・停止スクリプト実装
        |
        v
Step 3 静的検査・実起動スモーク・UI回帰
        |
        v
Step 4 手順書・Index・完了HTML反映
        |
        v
Step 5 統合レビュー・A95・自己評価
        |
        v
Step 6 Git確認・commit・push
```

実装と実起動は依存するため直列にする。Step 5のレビューは、Step 3とStep 4のEvidenceがそろってから行う。

## 6. 共通の実行Runtime契約

各Stepのプロンプトは、AI部品名を並べるだけで終了扱いにしない。実行時には次を行う。

- OrchestratorのJSON pathと固定modelを読み、`multi_agent_v1__spawn_agent`を試す。
- Coordinatorが受理された場合は、指定Agentを一体ずつspawnし、`multi_agent_v1__wait_agent`で完了を取得する。
- 起動不能なら、変更前に`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`をReceiptへ書く。
- ルートAgentの自己確認を独立Agent実行済みと偽らない。
- 未解決Critical/High、外部I/O、Secret、実注文、UnknownのPassはFail-closedで停止する。

## 7. そのまま実行できるプロンプト群

### Step 1: 起動経路・依存・安全境界の調査

```text
あなたはAUTOTRADE-APP-STARTUP-PLAN-001のStep 1を実行するルート実行Agentです。

目的:
WindowsのbatダブルクリックでAutoTradeローカルBacktest UIが使える状態になるために必要な起動部品、依存、ポート、ログ、停止条件、既存テストを事実ベースで棚卸しする。

実行Runtime:
- runtime_backend: multi_agent_v1
- orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
- orchestrator_json_path: .codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json
- Agents: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1
- 固定modelは各JSON定義を正本とする。代替modelへ置換しない。

最初にmulti_agent_v1__spawn_agentでCoordinatorを起動し、受理されたら全Agentを個別spawnしてwaitする。起動できなければ、plan/autotrade_app_startup/01-runtime-dispatch.mdへ理由、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを先に記録する。

読むもの:
- README.md、settings/language.md、settings/ai_component_rules.md
- doc/index.html、doc/00_全Phase残課題Blocked統合台帳.html
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- ui/mock/package.json、ui/mock/playwright.config.ts、ui/mock/src/backtestApi.ts
- scripts/phase5r/backtest_api_server.py、src/autotrade/application/http_server.py
- 既存のbat/cmd/PowerShell/Node起動スクリプトとpackage.json

確認すること:
1. API、UI、build、依存、ポート、health endpoint、loopback境界を一覧化する。
2. 現在の手順書が手動起動をどこまで説明しているか確認する。
3. 起動失敗、ポート競合、依存不足、API停止、UI停止の復旧要件を整理する。
4. 入口batに必要な引数、ログ、idempotency、browser起動、stop経路を決める。
5. 外部Data、Broker、Secret、実注文、実資金を扱わない境界を確認する。

作成物:
- plan/autotrade_app_startup/01_起動経路調査.md
- plan/autotrade_app_startup/01-runtime-dispatch.md
- plan/autotrade_app_startup/01-traceability.md

完了条件:
- 実装前に、どのプロセスをどの順番で起動するか説明できる。
- ポート競合時に無関係なプロセスを終了しない方針が決まっている。
- UIの成功条件とAPIの成功条件が別々に定義されている。
- Unknownと対象外がPassになっていない。
```

### Step 2: bat入口・PowerShell起動/停止処理の実装

```text
あなたはAUTOTRADE-APP-STARTUP-PLAN-001のStep 2を実行するルート実装Agentです。

目的:
Step 1の事実と方針に従い、Windows Explorerからダブルクリックできるbat入口と、堅牢なPowerShell起動・停止処理を実装する。

実行Runtime:
- runtime_backend: multi_agent_v1
- orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- orchestrator_json_path: .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json
- Agents: AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1
- Skills: autotrade_skill_ops_security_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_debug_recovery_v0_1
- 固定modelは各JSON定義を正本とする。

起動契約:
- 変更前にCoordinatorと指定Agentのspawn/waitを試し、Receiptを保存する。
- 起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED等を記録し、独立実行済みと書かない。

実装対象:
- start_autotrade.bat
- scripts/start_autotrade.ps1
- stop_autotrade.bat
- scripts/stop_autotrade.ps1

実装仕様:
1. `%~dp0`からプロジェクトルートを求め、カレントディレクトリに依存しない。
2. Python、npm、ui/mock/package-lock.json、node_modulesの有無を確認する。
3. node_modulesがない場合だけnpm ciを実行する。
4. npm run buildを実行し、失敗時はUIを起動しない。
5. APIを127.0.0.1:8765、UIを127.0.0.1:4173で起動する。
6. API /health、UI / を指定秒数まで待つ。
7. 正常ならhttp://127.0.0.1:4173を既定ブラウザで開く。
8. `-NoBrowser`を検査用に受け付ける。
9. すでに同じAPI/UIが正常なら二重起動しない。
10. ポートが別プロセスに占有されている場合は停止し、PIDとログ場所を表示する。
11. API/UIのstdout/stderrをruntime/autotrade_app/へ保存する。
12. API/UIをlocalhost以外へbindしない。
13. stop側は対象プロジェクトの起動経路だけを確認して終了し、無関係なPIDをkillしない。
14. 例外・終了コード・タイムアウトを利用者に分かる日本語で表示する。

完了条件:
- ダブルクリック入口と停止入口が存在する。
- PowerShell構文検査が通る。
- 入口batが実行本体へ正しく引数を渡す。
- 外部接続・実注文・Secret・実資金の経路を追加していない。
```

### Step 3: 静的検査・実起動スモーク・UI回帰

```text
あなたはAUTOTRADE-APP-STARTUP-PLAN-001のStep 3を実行する検証Agentです。

目的:
起動スクリプトが実際にAPIとUIを起動し、ブラウザからBacktestを利用できることを確認する。

実行Runtime:
- runtime_backend: multi_agent_v1
- orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- orchestrator_json_path: .codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json
- Agents: AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、e2e-testing

起動契約:
- spawn/waitを先に試す。失敗時はReceiptへfallbackを記録する。

検証:
1. tests/phase5R/test_autotrade_app_startup.pyを作り、bat/ps1の安全境界、引数、ポート、ログ、health check、停止経路を静的検査する。
2. `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_autotrade.ps1 -NoBrowser`相当で実起動する。
3. http://127.0.0.1:8765/healthが200で、external_io disabledを返すことを確認する。
4. http://127.0.0.1:4173/が200で、UI HTMLが返ることを確認する。
5. UIの既存Playwright Backtestテストを実行する。
6. 起動後に再度startを実行し、二重起動せず成功することを確認する。
7. stopを実行し、8765/4173が停止することを確認する。
8. 起動失敗時のログと終了コードをEvidenceへ保存する。
9. 外部リクエストが発生していないことを確認する。

Evidence:
- tests/evidence/AUTOTRADE-APP-STARTUP/RUN-20260816-001/
- plan/autotrade_app_startup/03-runtime-dispatch.md

完了条件:
- static test、実起動、API health、UI health、既存UI回帰、停止確認がすべてPASS。
- 起動失敗時に無関係なプロセスを終了していない。
```

### Step 4: 操作手順書・Index・完了HTMLへの反映

```text
あなたはAUTOTRADE-APP-STARTUP-PLAN-001のStep 4を実行する文書統合Agentです。

目的:
初心者が「どのbatをダブルクリックし、何が起きれば使える状態なのか」を操作手順書だけで理解できるようにする。

実行Runtime:
- runtime_backend: multi_agent_v1
- orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
- orchestrator_json_path: .codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json
- Agents: AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_traceability_v0_1

起動契約:
- spawn/waitを先に試す。起動不能ならfallback Receiptを保存し、独立レビュー済みと書かない。

更新対象:
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- doc/index.html
- doc/phase5R/06_完了/04_AutoTradeアプリ一括起動完了判定.html
- 必要に応じてdoc/00_全Phase残課題Blocked統合台帳.html

手順書へ必ず追加する内容:
1. 「0. アプリを一括起動する」を既存Backtest手順の前に置く。
2. `start_autotrade.bat`をダブルクリックする操作を最初の手順にする。
3. API、UI、build、ブラウザ、health checkを中学生でも分かる言葉で説明する。
4. 成功時に見えるURLとBacktest画面を明記する。
5. `runtime/autotrade_app/`のログ場所を明記する。
6. Python/npm未導入、依存不足、build失敗、ポート競合、API/UI未起動の直し方を表にする。
7. `stop_autotrade.bat`による停止方法を追加する。
8. localhost限定、外部Data/Broker/Secret/実注文/実資金なしを明記する。
9. 一括起動は「Backtestを使える状態にする準備」であり、Backtest結果の正しさや利益を保証しないと明記する。
10. 既存の機能一覧・BT-MAN-01〜16との導線を壊さない。

完了条件:
- 初心者がbatの場所、クリック対象、成功状態、失敗時のログ、停止方法を迷わない。
- doc/index.htmlから手順書と完了判定へ到達できる。
- 外部接続や本番機能が起動するように誤解させない。
```

### Step 5: 統合レビュー・A95・自己評価・完了判定

```text
あなたはAUTOTRADE-APP-STARTUP-PLAN-001のStep 5を実行する最終レビューAgentです。

目的:
実装、実起動Evidence、手順書、Index、停止経路、安全境界を横断して確認し、必要な修正を入れてから完了判定を作る。

実行Runtime:
- runtime_backend: multi_agent_v1
- orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
- orchestrator_json_path: .codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json
- Agents: AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1
- Skills: autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、autotrade_skill_traceability_v0_1、agent-self-evaluation

確認項目:
1. ダブルクリック入口がカレントディレクトリに依存しない。
2. API/UIのloopback、health、port conflict、idempotency、logs、stopが一致する。
3. 手順書と実装のファイル名・URL・ログ場所・エラー文が一致する。
4. Playwrightとstatic testのEvidenceが存在する。
5. 外部I/O、Secret、実注文、実資金を追加していない。
6. A95を対象ファイルへ静的適用し、管理用hash経路を追加していない。
7. Open UnknownをPassにしない。
8. agent-self-evaluation.mdへAccuracy、Completeness、Clarity、Actionability、Concisenessの5軸と具体的根拠を書く。

作成物:
- plan/autotrade_app_startup/05_統合レビュー.md
- tests/evidence/AUTOTRADE-APP-STARTUP/RUN-20260816-001/startup-quality-report.json
- tests/evidence/AUTOTRADE-APP-STARTUP/RUN-20260816-001/agent-self-evaluation.md
- doc/phase5R/06_完了/04_AutoTradeアプリ一括起動完了判定.html

完了条件:
- Critical/Highが0。
- 起動・停止・手順・Evidence・Indexが相互に一致する。
- 「アプリ起動完了」と「Backtest結果が正しい」「本番運用可能」を混同しない。
```

### Step 6: Git確認・コミット・プッシュ

```text
あなたはAUTOTRADE-APP-STARTUP-PLAN-001のStep 6を実行するルート引渡しAgentです。

1. git status --shortで変更を確認する。
2.今回作成・変更したファイルだけを一覧化する。既存のユーザー変更を混ぜない。
3. git diff --check、静的テスト、実起動スモーク、Playwright、A95、Secret scan、リンク検査を確認する。
4. bat/PowerShellの内容をレビューし、loopback以外のbind、無関係なkill、Secret出力がないことを確認する。
5. 意味のある単位でcommitする。reset --hard、checkout、force pushは使わない。
6. 現在のブランチの追跡先へpushする。
7. push後にgit status --short、git log -1 --oneline --decorate、追跡先を確認する。
8. 最終報告に、入口bat、起動URL、停止方法、検証結果、Open Unknown、commit、push先を記載する。
```

## 8. 最終チェックリスト

- [x] `start_autotrade.bat`をダブルクリックできる。
- [x] `%~dp0`からプロジェクトルートを解決する。
- [x] APIとUIが127.0.0.1限定で起動する。
- [x] build、依存、health check、browser起動が一連で動く。
- [x] 二重起動とポート競合を安全に扱う。
- [x] API/UIのログ場所が分かる。
- [x] `stop_autotrade.bat`で停止できる。
- [x] 起動スクリプトの静的テストがPASSする。
- [x] 実起動スモークと既存Backtest E2EがPASSする。
- [x] 手順書、Index、完了HTMLが更新される。
- [x] A95、Secret、リンク、差分検査がPASSする。
- [ ] Git commit/push結果が確認される（本計画書の変更後に実施）。

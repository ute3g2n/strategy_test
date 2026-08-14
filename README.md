# strategy_test

## 概要

このリポジトリは、タートルズ・トレンドフォロー自動売買システムの要件整理、設計、AI実行基盤整備、研究用成果物管理を行うための作業場所です。

いまのAI実行基盤は、Phase 1専用部品を証跡として残しつつ、Phase 2以降で再利用できる汎用部品へ整理した状態です。

## 最初に見る場所

人間もAIエージェントも、最初は次を確認すると全体像をつかみやすいです。

1. `README.md`
2. `settings/language.md`
3. `settings/ai_component_rules.md`
4. `doc/index.html`
5. `doc/00_全Phase残課題Blocked統合台帳.html`
6. 必要に応じて `plan/` 配下の計画書

## どこに何があるか

- `doc/`
  正式なHTML成果物の保存先。
- `doc/index.html`
  すべての正式HTML成果物の入口。
- `doc/00_全Phase残課題Blocked統合台帳.html`
  Phase 0以降のBlocked、Unknown、残リスク、Human Gate待ちを管理する唯一の正本。旧台帳は履歴として残し、現在の状態はここだけで更新する。
- `doc/ai_foundation/`
  AI実行基盤の棚卸し、移行方針、仕様、作成ルール、検証結果。
- `doc/phase1/`
  Phase 1の正式HTML成果物。
- `plan/`
  計画書、実行プロンプト、ログ、台帳。
- `settings/`
  言語ルール、AI部品ルールなどのプロジェクト共通設定。
- `.codex/skills/`
  実行可能なSkill定義。
- `.codex/agents/`
  実行可能なAgent定義。
- `.codex/orchestrators/`
  実行可能なOrchestrator定義。
- `research/`
  調査や研究系の原稿、派生成果物。
- `scripts/`
  補助スクリプト。

## AI実行基盤

### 標準で使う部品

- Orchestrator:
  `AutoTradeProject_Orchestrator_v0_1`
  `AutoTradePhasePlanning_Orchestrator_v0_1`
  `AutoTradeComponentLifecycle_Orchestrator_v0_1`
  `AutoTradeProject_UiMock_Orchestrator_v0_1`
  `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
  `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`
  `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`
- Agents:
  `AutoTrade_A05_PhaseExecutionPlanner_v0_1`
  `AutoTrade_A06_AiComponentEngineer_v0_1`
  `AutoTrade_A07_ContextManifestMaintainer_v0_1`
  `AutoTrade_A08_ContextRouter_v0_1`
  `AutoTrade_A10_RequirementsCurator_v0_1`
  `AutoTrade_A20_ArchitectureDomainArchitect_v0_1`
  `AutoTrade_A30_StrategyQaArchitect_v0_1`
  `AutoTrade_A40_ExecutionEnginePocArchitect_v0_1`
  `AutoTrade_A50_AdapterArchitect_v0_1`
  `AutoTrade_A60_RiskAccountArchitect_v0_1`
  `AutoTrade_A70_OpsSecurityArchitect_v0_1`
  `AutoTrade_A80_DocumentIntegrator_v0_1`
  `AutoTrade_A81_DesignDocSetWriter_v0_1`
  `AutoTrade_A82_ImplementationDetailDesigner_v0_1`
  `AutoTrade_A90_DesignReviewer_v0_1`
  `AutoTrade_A91_ImplementationDetailReviewer_v0_1`
  `AutoTrade_A110_PythonTestEngineer_v0_1`
  `AutoTrade_A120_PythonImplementer_v0_1`
  `AutoTrade_A130_VerificationEngineer_v0_1`
  `AutoTrade_A140_DebugEngineer_v0_1`
  `AutoTrade_A150_PythonCodeReviewer_v0_1`
  `AutoTrade_A160_TradingSecurityReviewer_v0_1`
  `AutoTrade_A170_UiMockEngineer_v0_1`
  `AutoTrade_A171_UiVisualQaReviewer_v0_1`
- Skills:
  `.codex/skills/autotrade_skill_*_v0_1/`
  Phase実行計画作成では `autotrade_skill_phase_execution_planning_v0_1` を使います。
  AI部品作成・変更では `autotrade_skill_ai_component_lifecycle_v0_1` を使います。
  新規／大幅変更文書のmanifest保守では `autotrade_skill_context_manifest_maintenance_v0_1` と `AutoTrade_A07_ContextManifestMaintainer_v0_1` を使い、資料参照の絞り込みでは `autotrade_skill_context_routing_v0_1` と `AutoTrade_A08_ContextRouter_v0_1` を使います。A07は1ファイルの追加・更新判定、A08はvalidator済みmanifestからの候補選定だけを行い、本文の全量投入・Secret・外部I/O・Git書込みは行いません。
  UIモック作成では `AutoTradeProject_UiMock_Orchestrator_v0_1`、`AutoTrade_A170_UiMockEngineer_v0_1`、`AutoTrade_A171_UiVisualQaReviewer_v0_1` とUI専用Skill 3件を完全名で指定します。正式合否は固定 `@playwright/test`、Storybook、Vitest/axeで判定し、AI向けCLIは匿名ローカル探索に限定します。
  実装詳細設計では `autotrade_skill_implementation_detail_design_v0_1` と `autotrade_skill_implementation_detail_review_v0_1` を使います。
  Python本実装の品質ループでは `autotrade_skill_python_implementation_v0_1`、`autotrade_skill_python_test_quality_v0_1`、`autotrade_skill_debug_recovery_v0_1`、`autotrade_skill_python_code_review_v0_1` を明示指定します。実行証跡は `tests/evidence/{phase_id}/{run_id}/` に保存し、`scripts/quality_gate/` は `trusted_scopes.json` に登録されたRun IDの固定コマンドだけを実行します。`scope_mode=target_only` のRunは登録済みtarget_pathsだけを試験対象とし、対象外のHEAD/worktree差分では止めません。Phaseのtest subprocessはhost outbound isolation確認がない場合にBLOCKEDとします。

### Phase実行計画

各Phaseを開始する前に、まずそのPhaseの実行計画書を作成します。実行計画書は `plan/` 配下に保存し、必ず複数ステップに分割し、各ステップにそのまま実行できるプロンプトを含めます。

標準の依頼プロンプトは [Phase実行計画書作成依頼プロンプト](./doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html) を参照してください。

### AI部品作成・変更

Skill、サブエージェント、オーケストレータの作成または変更では、まず既存再利用を調査し、その後に実体更新、最後に仕様と導線を更新します。標準の依頼プロンプトは [AI部品作成更新依頼プロンプト](./doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html) を参照してください。

### 資料・コード参照効率化

新しいMarkdown／HTML文書はA07へ必ず渡し、既存文書の大幅変更もA07へ更新要否を判定させます。ソースコードの構造変更は決定的なコードmanifest更新へ渡します。どちらもvalidator PASS、または原因と再開条件を含む正直なBLOCKED receiptがない限り完了扱いにしません。日常保守では常時Orchestratorを起動せず、AI部品そのものの作成・変更だけをComponentLifecycleへ渡します。詳細な最終説明資料は、システム完成後に正式HTMLとして追加します。

### 実装詳細設計

実装者がそのまま着手するための設計書は、まず誰にでも分かるドメイン概要、ファイル構成、Mermaidによる構造図、モジュールごとの入出力、Mermaidによる処理フロー、全テストケース表を示し、その後に型付き契約、永続化、異常系、コード例または擬似コードを続けます。コード・固有名詞以外は日本語で説明し、表の前には何を判断する表かを記します。標準は [実装詳細設計書構成標準](./doc/ai_foundation/14_実装詳細設計書構成標準.html)、HTML構成は [実装詳細設計書HTMLテンプレート](./doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html)、依頼文は [実装詳細設計書作成依頼プロンプト](./doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html) です。作成から専門レビュー、改訂、再レビューまでは `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、`AutoTrade_A82_ImplementationDetailDesigner_v0_1`、`AutoTrade_A91_ImplementationDetailReviewer_v0_1` を使います。

### 証跡として残す部品

- `AutoTradePhase1_*`
- `autotrade_phase1_skill_*_v0_1`

これらは `frozen / legacy / phase1証跡` として扱います。新しいPhaseの標準部品としては使わず、既存成果物との対応を保つために残しています。

## 代表的な入口文書

- [HTML成果物インデックス](./doc/index.html)
- [AI実行基盤 現状棚卸し](./doc/ai_foundation/01_AI実行基盤現状棚卸し.html)
- [AI部品整理方針・移行マップ](./doc/ai_foundation/02_AI部品整理方針移行マップ.html)
- [プロジェクト汎用Skill仕様](./doc/ai_foundation/03_プロジェクト汎用Skill仕様.html)
- [プロジェクト汎用サブエージェント仕様](./doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html)
- [プロジェクト汎用オーケストレータ仕様](./doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html)
- [AI部品相関図・発火制御図](./doc/ai_foundation/06_AI部品相関図発火制御図.html)
- [AI部品作成ルール](./doc/ai_foundation/07_AI部品作成ルール.html)
- [AI実行基盤整理検証結果](./doc/ai_foundation/08_AI実行基盤整理検証結果.html)
- [実装詳細設計書構成標準](./doc/ai_foundation/14_実装詳細設計書構成標準.html)
- [実装詳細設計AI基盤仕様](./doc/ai_foundation/15_実装詳細設計AI基盤仕様.html)
- [実装詳細設計書HTMLテンプレート](./doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html)
- [実装詳細設計書作成依頼プロンプト](./doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html)

### WSL隔離品質ゲート

Windows側の本リポジトリとWSLクローンは別の作業ツリーです。通常の編集はWindows側だけで行います。ユーザーが明示的に委譲した実機Run・隔離品質Gateでは、AIがWSL cloneのbranch/origin/HEAD/statusを確認し、dirtyな変更をリポジトリ外のローカルアーカイブへ保存したうえで`git stash push --include-untracked`により可逆退避し、clean確認後に`git pull --ff-only`を自律実行できます。`reset`、`clean`、force、rebase、checkout、stash drop/pop、未コミット変更の上書きは行いません。同期後はHEAD、clean状態、trusted scope、fixture hashを再確認し、stashは自動復元せず保持します。

`RUN-P2-IC-001-WSL` は、P2-D07の固定fixtureをWSL2 `networkingMode=none` で実行する専用scopeです。Linux用venvは `.venv/bin/python` 固定で、証跡は `tests/evidence/phase2/RUN-P2-IC-001-WSL/` に保存します。BLK-RUN-003は、実機での隔離・4 Gate・完全復元証跡がそろい、ユーザーが「承認します」と明示した時点で解決済みとします。

Windowsホストからの唯一の人間向け実行入口は `run_test.ps1`（WSL内から実行しない）です。WSL上のCodexやVS Codeのターミナルから `powershell.exe` を呼び出す場合もWSL内実行に該当するため、Windows側で独立したPowerShellを起動する。実行開始時点では、`wsl -l -v` で全ディストリビューションが `Stopped` であることを確認する。この時点のwrapperはWindows側のWSL version・一覧・対象がWSL2であることだけを確認し、Linux distroを起動する事前確認は行わない。

ただし、`\wsl.localhost` 上のファイルを読むだけで対象WSLが起動するため、Codexや対象Ubuntu内のプロセスが動いている状態で実行してはいけません。Codexを終了し、対象WSL内の処理がないことを確認した後、次の許可付きコマンドを実行します。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\wsl_quality_gate\run_test.ps1 -AllowRunningDistro
```

`run_test.ps1` が内部で `run_isolated_p2.ps1` を起動し、wrapperの標準出力・標準エラー・終了コードと選択した証跡を `tests/evidence/phase2/RUN-P2-IC-001-WSL/automation/` に保存します。通常の実行では、host wrapperが隔離中にWSL cloneから採取した `wsl-verification-capture.json` だけを、今回のwrapper execution IDが一致する場合に限って使います。Windows cloneに残る同名の古い `verification.json` は読みません。設定前にBLOCKEDとなった場合だけ、今回のexecution IDと更新時刻が一致する `preflight.json` を使います。証跡を読むためだけに隔離解除後のWSLを再起動しません。

内部wrapperは `.wslconfig` に `networkingMode=none` と `firewall=true` を一時設定して `wsl --shutdown` を実行した後、対象ディストリビューションを一回だけ起動します。起動後のLinux runnerが、WSL2 kernel、repository、manifest、Linux用venv、wheelhouse、registry、network隔離、固定tool version、fixture checksumを確認し、すべて通過した場合だけ固定4 Gateを実行します。終了後は `try/finally` で `.wslconfig` を元のバイト列へ復元し、再度 `wsl --shutdown` を実行します。

実行後に「実行した」と伝えれば、このautomationディレクトリを確認してデバッグします。

## AGENTS.md と README.md の更新タイミング

`AGENTS.md` と `README.md` は常に更新する必要はありません。次のような変化が入ったときに追記または修正します。

- 標準のAI実行基盤が変わったとき
- ディレクトリ構成や保存ルールが変わったとき
- 最初に読むべき入口資料が変わったとき
- 人間またはAIが初回に迷いやすい構成変更が入ったとき

軽微な成果物追加やログ増加だけでは、毎回更新しなくてよいです。

## 自動コミット監視

このリポジトリの自動コミット経路は、CTXMAP-H1の承認後だけ有効になるローカル監視です。監視の前段で
`scripts.context_index.context_watch` が変更をまとめ、`check_context_gate.py` が文書・ソースのマニフェスト整合性、Secret、
rename／削除、A07のpending状態を検査します。GateがPASSしない限り、`git add`、commit、pushは実行されません。

H1の承認記録は `plan/context_index/CTXMAP-H1_approval.json` に、次の条件を満たす形で人間が保存します。

```json
{
  "gate_id": "CTXMAP-H1",
  "status": "APPROVED",
  "approval_text": "CTXMAP-H1を承認します"
}
```

このファイルがない、内容が違う、または `APPROVED` でない場合は、起動コマンド自身が説明付きで拒否します。承認記録をAIが作成したり、承認前に監視を試験起動したりしてはいけません。

### バックグラウンドで起動

```bash
npm run watch-start
```

### 状態確認

```bash
npm run watch-status
```

### 停止

```bash
npm run watch-stop
```

### 前面で起動

```bash
npm run watch-commit
```

前面起動もH1を確認してから、ローカルの単一workerとして実行します。イベントはdebounceされ、処理中は直列化されます。
マニフェスト、receipt、Gate報告などの自己生成ファイルは次のイベントにしないため、自己更新ループを起こしません。

### Gateだけを手動実行

自動コミットを行わず、変更の検査とマニフェスト更新だけを行う場合は、変更集合を明示します。

```bash
python -m scripts.context_index.check_context_gate `
  --root . `
  --changed scripts/context_index/example.py `
  --report plan/context_index/runtime/context_gate_report.json
```

Gateは `context/artifact_manifest.json`、`context/manifest_state.json`、`context/code_manifest.json`、
`context/relation_graph.json`を必要に応じて更新し、判定を `plan/context_index/runtime/` に保存します。
新規・大幅変更文書でA07が利用できない場合は `A07_RUNTIME_UNAVAILABLE` のpendingとして停止します。

### 失敗時の手動復旧

1. `plan/context_index/runtime/context_watch_pending.json` と `context_gate_report.json` で、Secret、A07、validator、rename／削除のどれで止まったかを確認します。
2. 原因を直した後、同じ明示変更集合で `check_context_gate.py` を一度実行します。本文を外部へ送ったり、pendingを削除して成功扱いにしたりしません。
3. Gateの `allowed_paths` だけを確認し、必要な場合に `auto-commit.sh --allowlist-file <path>` を実行します。既存の未追跡資料や既存stage変更は自動で混ぜません。
4. 監視を止める場合は `npm run watch-stop`、PIDとログを確認する場合は `npm run watch-status` を使います。

イベントログと復旧状態は `plan/context_index/runtime/`、前面／起動経路の標準ログは `watch-commit.log` と `watch-commit.err.log` に保存します。
外部ネットワーク、外部MCP、永続サービス、Secret本文の送信はこの経路では行いません。

## 自動コミットの注意

- `.git`、`node_modules`、`.env`、`.env.*`、`*.log` と、Context Index自身の生成物は監視対象外です。
- 連続変更はdebounce後にまとめますが、A07未起動・timeout・validator不合格は自動再試行せずpendingで閉じます。
- `auto-commit.sh` は変更集合を受け取らない限り動作せず、`git add -- <明示path>`だけを使います。`git add -A`による既存ユーザー変更の混入は許可しません。
- コミットメッセージは `auto: update by Codex [YYYY-MM-DD HH:MM:SS]` 形式です。pushはGate PASS後だけで、テストでは `--no-push` を使います。

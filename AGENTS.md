# Project Codex Configuration

## 入口

このプロジェクトでAIエージェントが最初に把握すべき場所は次のとおり。

- `README.md`
  プロジェクト全体の概要、人間向けの入口、主要ディレクトリ、運用メモ。
- `settings/language.md`
  このプロジェクトで使う言語、文体、出力上の基本ルール。
- `settings/ai_component_rules.md`
  AI部品の命名、発火制御、保存先、Phase専用部品の作成条件。
- `doc/index.html`
  正式なHTML成果物の総合インデックス。
- `doc/00_全Phase残課題Blocked統合台帳.html`
  Phase 0以降のBlocked、Unknown、残リスク、Human Gate待ちを根本原因でまとめる唯一の正本。新規発見、再オープン、解消はこの台帳へ反映し、旧台帳は履歴・証拠として参照する。
  人間の承認・認証・利用許可が必要な事項（H1/H2/Human Gate、外部接続、Secret、費用、権限を含む）は、未承認の段階から必ずこの台帳にID、対象、期限、再開条件、証拠先を登録する。台帳にない承認待ちを作業文書だけで管理してはならない。状態確認はこのHTMLだけで完結できるようにする。
- `doc/ai_foundation/`
  AI実行基盤の棚卸し、移行方針、汎用Skill仕様、汎用Agent仕様、汎用Orchestrator仕様、作成ルール、検証結果。
- `doc/phase1/`
  Phase 1の正式HTML成果物。
- `plan/`
  計画書、実行プロンプト、ログ、台帳。

## Windows・WSLの作業ツリー規則

- 通常の編集・実装・文書更新はWindows側の `C:\\project\\strategy_test` だけに行う。Windows側を正本として先に保存する。
- WSLクローンへの通常の編集、UNC経由のコピー、パッチ適用は行わない。ただし、ユーザーは2026-08-10に、実機Run・隔離品質Gateに必要な場合のWSLクローンについて、未コミット変更を可逆退避して同期する権限をAIへ明示委譲した。
- 同期前に、対象WSLクローンの絶対パス、branch、origin、HEAD、`git status --porcelain=v1`、ignored項目をnative Windowsから読み取り確認する。`.venv`、cache、wheelhouse、既存automationログなど`.gitignore`で許可された生成物は保持し、対象パスが想定外、branch/originが不一致、または未知のignored項目・Secret・鍵・`.env`・認証情報らしい変更がある場合は停止する。
- dirtyな場合は、次の可逆手順だけを自律実行してよい。①リポジトリ外の `C:\\Users\\ute3g\\AppData\\Local\\Codex\\wsl-archives\\strategy_test\\<UTC timestamp>\\` にHEAD、branch、origin、status、binary diff、未追跡一覧を保存する。②アーカイブの一覧と内容を確認する。③WSL側で `git stash push --include-untracked --message codex-wsl-archive-<UTC timestamp>` を実行し、stash refとclean状態を確認する。許可済みignored生成物は保持し、未知のignored変更は自動処理せず停止する。
- 退避確認後の同期はnative Windowsから `wsl.exe -d <distro> -- bash -lc "cd <repo> && git pull --ff-only"` だけを実行する。`reset`、`clean`、`checkout`、`rebase`、force、remote変更、stash drop、stash pop、未コミット変更の上書きは行わない。fast-forward不能やpull失敗時はstashとアーカイブを保持して停止する。
- 同期後はWSL側のHEAD、branch、origin、clean状態、対象Runのtrusted scope、fixture hash、target scopeを再確認する。stashは自動復元せず、復元は別判断として報告する。WSL側の成果物編集は行わず、実行証跡の正本はWindows側へ取得する。
- `.codex/orchestrators/`
  実行可能なOrchestrator定義。
- `.codex/agents/`
  実行可能なAgent定義。
- `.codex/skills/`
  実行可能なSkill定義。

WSL隔離品質ゲートの実行入口は `scripts/wsl_quality_gate/run_test.ps1` だけとする。`run_test.ps1` が内部で `run_isolated_p2.ps1` を呼び出す。native Windowsから実行する場合、対象Runが終了済みであることを確認し、必要なら `-AllowRunningDistro` を付ける。Run ID、固定4 Gate、対象範囲、fixture hashは `scripts/quality_gate/trusted_scopes.json` を正本とし、実行証跡は `tests/evidence/{phase_id}/<RunId>/` に置く。通常WSL NAT、Windows用 `.venv/Scripts/python.exe`、隔離後のpip、markerだけの隔離証明、外部接続を禁止する。ユーザーが対象Runについて「承認します」と明示した場合は、署名なしでHuman Gateを承認済みとして扱う。

## AI実行基盤の現状

- 汎用Orchestrator:
  `AutoTradeProject_Orchestrator_v0_1`
  `AutoTradePhasePlanning_Orchestrator_v0_1`
  `AutoTradeComponentLifecycle_Orchestrator_v0_1`
  `AutoTradeProject_UiMock_Orchestrator_v0_1`
  `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
  `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`
  `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`
- 汎用Agents:
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
  `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`
  `AutoTrade_A91_ImplementationDetailReviewer_v0_1`
  `AutoTrade_A110_PythonTestEngineer_v0_1`
  `AutoTrade_A120_PythonImplementer_v0_1`
  `AutoTrade_A130_VerificationEngineer_v0_1`
  `AutoTrade_A140_DebugEngineer_v0_1`
  `AutoTrade_A150_PythonCodeReviewer_v0_1`
  `AutoTrade_A160_TradingSecurityReviewer_v0_1`
  `AutoTrade_A170_UiMockEngineer_v0_1`
  `AutoTrade_A171_UiVisualQaReviewer_v0_1`
- 汎用Skills:
  `.codex/skills/autotrade_skill_*_v0_1/`
  Phase実行計画作成では `autotrade_skill_phase_execution_planning_v0_1` を標準で使う。
  AI部品作成・変更では `autotrade_skill_ai_component_lifecycle_v0_1` を標準で使う。
  新規／大幅変更文書、計画、ソース、テスト、AI部品の管理hash再導入判定では `autotrade_skill_protected_hash_policy_guard_v0_1` と `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1` を使う。A95はhash値、manifest、stale、fingerprint、hash retryを作らず、管理hashはBLOCKED、用途不明はNEEDS_HUMAN_GATE、直接の保護対象hashだけを目的・停止範囲付きでALLOWとする。A07/A08は文章manifest管理の通常経路から起動しない。
  UIモック作成では `AutoTradeProject_UiMock_Orchestrator_v0_1`、`AutoTrade_A170_UiMockEngineer_v0_1`、`AutoTrade_A171_UiVisualQaReviewer_v0_1` とUI専用Skill 3件を完全名で指定する。正式合否は固定 `@playwright/test`、Storybook、Vitest/axeで判定し、AI向けCLIは匿名ローカル探索に限定する。
  実装詳細設計では `autotrade_skill_implementation_detail_design_v0_1` と `autotrade_skill_implementation_detail_review_v0_1` を標準で使う。
  Python本実装の品質ループでは `autotrade_skill_python_implementation_v0_1`、`autotrade_skill_python_test_quality_v0_1`、`autotrade_skill_debug_recovery_v0_1`、`autotrade_skill_python_code_review_v0_1` を明示指定で使う。
  実行証跡は `tests/evidence/{phase_id}/{run_id}/` に保存し、`scripts/quality_gate/` は `trusted_scopes.json` に登録されたRun IDの固定コマンドだけを実行する。`scope_mode=target_only` のRunは登録済みtarget_pathsだけを試験対象とし、対象外のHEAD/worktree差分では止めない。Phaseのtest subprocessはhost outbound isolation確認がない場合にBLOCKEDとする。
  新規文書、大幅変更文書、構造変更コードは、完了前にpath、schema、link、Secret、状態、要件追跡の非hash確認とA95の静的ポリシー判定へ渡す。管理用hashのvalidator PASS、manifest更新、stale判定、hash retry、hash receiptは完了条件にしない。A95の未起動を実行済みと偽らず、用途不明はHuman Gateへ送る。
- CTXMAPの旧commit／watch／validatorによる管理hash経路は通常経路から廃止した。`scripts/context_index/auto-commit.sh`、watcher、context Gateは管理用hashを計算・照合・retryせず、現行成果物の完了条件にも使わない。必要な保護対象hash、Secret、外部I/O、Human Gate、Unknown、対象範囲、権限境界は別途維持する。
- `npm run watch-start`、`npm run watch-commit` は旧運用の履歴入口として扱い、現行の新規文書・大幅変更・ソース変更では起動しない。A95の静的ポリシー判定とpath、schema、link、Secret、状態確認を使用する。
- Phase 1専用部品:
  `AutoTradePhase1_*`
  `autotrade_phase1_skill_*_v0_1`
  これらは `frozen / legacy / phase1証跡` として扱い、新規Phase実行の標準部品には使わない。

- 実ランタイム起動契約:
  Phase計画とAI部品変更の直接プロンプトは、完全名の列挙だけで完了扱いにせず、`multi_agent_v1__spawn_agent`／`multi_agent_v1__wait_agent` によるOrchestrator実起動、指定Agent全件の個別起動、定義JSON固定model、wait完了、受領証跡を要求する。起動不能時は `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を記録し、ルート責務チェックリストで継続する。未起動を独立実行済みと偽らない。Human Gate、外部I/O、Secret、UnknownのPass、Critical／Highは従来どおり停止する。

## 読み取り順の目安

AI部品の作成、設計、レビュー、Phase実行に入る前は、原則として次の順で確認する。

1. `README.md`
2. `settings/language.md`
3. `settings/ai_component_rules.md`
4. 関連する `doc/index.html` と該当HTML成果物
5. `doc/00_全Phase残課題Blocked統合台帳.html` で現在の停止条件を確認
6. 必要なら `plan/` 配下の計画書とログ

## Phase実行計画

各Phaseを開始する前に、まず実行計画書を作成する。標準の依頼プロンプトは `doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html` を参照する。計画書は `plan/` 配下へ保存し、複数ステップに分割し、各ステップにそのまま実行できるプロンプトを含める。

## AI部品作成・変更

Skill、サブエージェント、オーケストレータの作成または変更では、まず既存再利用を調査し、その後に実体更新、最後に仕様と導線を更新する。標準の依頼プロンプトは `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html` を参照する。
新しいAI部品または既存AI部品の大幅変更では、`AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`を静的に発火させる。A95はhashを計算せず、manifestを作らず、管理hashのretryを要求しない。

## 実装詳細設計

モジュール構成、型付き入出力、永続化、正常・異常系シーケンス、コード例または擬似コード、テストまでを必要とする設計書は、`AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、`AutoTrade_A82_ImplementationDetailDesigner_v0_1`、`AutoTrade_A91_ImplementationDetailReviewer_v0_1` を使用する。構成標準は `doc/ai_foundation/14_実装詳細設計書構成標準.html` を正本、HTML構成は `doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html`、依頼文は `doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html` を使う。最初にドメイン概要、ファイル構成、Mermaidによる構造図、モジュール入出力、Mermaidによる処理フロー、全テストケース表を読める順で置く。コード・固有名詞以外は日本語で説明し、各表の目的を先に示す。専門レビュー、改訂、再レビューを完了してから実装へ引き渡す。

## 更新ルール

`AGENTS.md` と `README.md` は常に更新する必要はない。次のような変化があったタイミングで追記または修正する。

- AI実行基盤の名前空間、標準Orchestrator、標準Agent、標準Skillが変わったとき
- `doc/`、`plan/`、`.codex/`、`settings/` の役割や保存ルールが変わったとき
- 新しい入口文書や、最初に読むべき重要ドキュメントが増えたとき
- 人間やAIが最初に見て迷いやすい構成変更が入ったとき
- 残課題、Unknown、Blocked、Human Gate、承認状態、再開条件のいずれかを更新したときは、更新対象の行だけで終わらせず、統合台帳全体を検索する。関連するHuman Gate行、Blocked行、Unknown行、最新状態欄、履歴リンクの矛盾を同時に点検し、現在状態をすべて整合させる。古い事実は履歴として残すが、履歴であることを明記する。

軽微な文言修正、ログ増加、成果物追加だけでは毎回更新しなくてよい。

## タスク完了時のGit処理

- タスク完了判定の直前に、`git status --short`でGit管理下の変更を確認する。
- Git管理下の変更がある場合は、変更範囲・差分・機械検証結果を確認したうえで、意味のある単位でコミットし、現在のブランチの追跡先へプッシュする。
- ユーザーが明示的にコミットまたはプッシュを禁止した場合、認証・接続・追跡先が利用できない場合、または差分に意図しない変更・Secret・鍵・個人情報が含まれる場合は、コミット／プッシュせず理由を実行ログと最終報告へ残す。
- 既存のユーザー変更を混ぜない。コミット前に対象ファイルを一覧化し、今回のタスクで作成・変更したものだけをステージ対象にする。`reset --hard`、`checkout`、force push、履歴書換えは行わない。
- コミットまたはプッシュが成功した場合は、最終報告に成功したブランチ・コミット・プッシュ先を明記する。失敗した場合は変更を保持したまま停止理由を報告する。

@./settings/language.md
@./settings/ai_component_rules.md

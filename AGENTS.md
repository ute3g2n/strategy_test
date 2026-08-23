# Project Codex Configuration

## 通常開発モード（PRODUCT_ONLY）

この節は、ユーザーが別の運用を明示しない限り、通常の機能追加、不具合修正、調査、仕様書・マニュアルの更新に適用する標準ルールである。通常タスクは、関連箇所の調査、必要な実装、変更リスクに応じた関連テスト、必要な利用者向け文書の更新、チャット報告だけで完了できる。

- Phase実行計画、Agent、Skill、Orchestrator、Human Gate、runtime receipt、実行ログ、完了packet、管理用hash、manifest、stale判定、管理用台帳同期は、ユーザーが明示的に要求した場合または外部接続、実取引、費用、Secret、重要データの物理削除など実害があり得る操作に必要な場合だけ実行する。
- ユーザーが成果物や変更対象を指定した場合は、指定された範囲だけを変更し、追加の計画書、証跡、台帳、Git操作を行わない。
- Agent、Skill、Orchestratorの定義は利用可能な道具として保持するが、通常タスクでは自動起動しない。
- 仕様書・計画書・マニュアル・総合台帳は、ユーザーの依頼、製品仕様の変更、ユーザー操作の変更、または実用上の一元管理が必要な場合だけ更新する。
- 外部接続、Secret、費用、実取引、重要データの物理削除は、通常モードでも実行前にユーザー確認を必要とする。
- 無関係な既存変更を上書きしない、Secretを保存しない、破壊的操作を安全に扱う、変更リスクに応じたテストを行う、という製品・データ安全上の制約は常に維持する。
- この節と後続の既存ルールが通常タスクについて矛盾する場合は、この節を優先し、後続ルールはユーザーが明示した高度な運用または該当する専門作業にだけ適用する。

## 入口

このプロジェクトでAIエージェントが最初に把握すべき場所は次のとおり。

- `README.md`
  プロジェクト全体の概要、人間向けの入口、主要ディレクトリ、運用メモ。
- `settings/language.md`
  このプロジェクトで使う言語、文体、出力上の基本ルール。
- `settings/ai_component_rules.md`
  AI部品の命名、発火制御、保存先、Phase専用部品の作成条件。
- `doc/index.html`
  正式なHTML成果物を一覧化する場合の入口。通常タスクでは、正式文書の追加・削除・移動がある場合だけ更新する。
- `doc/00_全Phase残課題Blocked統合台帳.html`
  Phase全体のBlocked、Unknown、残リスク、Human Gate待ちを一元管理する必要がある場合の正本。通常タスクでは、ユーザーが更新を求めた場合または現在状態の一元管理が実用上必要な場合だけ参照・更新する。
  人間の承認・認証・利用許可が必要な事項は、外部接続、Secret、費用、実取引、重要データの物理削除など、実害があり得る場合に限り、対象と再開条件を確認する。通常タスクで未承認事項を自動的に台帳へ登録しない。
- `doc/ai_foundation/`
  AI実行基盤の過去仕様と任意利用の参考資料。通常タスクでは、該当作業を明示的に依頼された場合だけ読む。
- `doc/phase1/`
  Phase 1の正式HTML成果物。
- `plan/`
  ユーザーが指定した計画書や実行プロンプトを保存する場所。通常タスクのログ、receipt、証跡、台帳を自動生成しない。

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

WSL隔離品質ゲートは、ユーザーが明示的に隔離実行を依頼した場合、または外部接続・実取引・Secret・費用などの高リスク検証に必要な場合だけ使用する。使用する場合の実行入口は `scripts/wsl_quality_gate/run_test.ps1` とし、対象Run、対象範囲、fixture、外部接続境界を確認する。通常のローカル機能修正では、WSL隔離、固定Gate、Run証跡、Human Gateを要求しない。

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
  `AutoTrade_A172_WebProductUiEngineer_v0_1`
- 汎用Skills:
  `.codex/skills/autotrade_skill_*_v0_1/`
  Phase実行計画作成では `autotrade_skill_phase_execution_planning_v0_1` を、ユーザーが計画書を依頼した場合だけ使う。
  AI部品作成・変更では `autotrade_skill_ai_component_lifecycle_v0_1` を、実際にAI部品を作成・変更するときだけ使う。
  A95と `autotrade_skill_protected_hash_policy_guard_v0_1` は、ユーザーがAI部品や管理ルールの変更レビューを明示した場合だけ使う。通常のコード、テスト、仕様書、マニュアル変更では起動しない。
  UI、Web製品UI、実装詳細設計、Python品質ループ用の専用部品は、該当作業でユーザーが利用を求めた場合または独立レビューが実質的に必要な場合だけ使う。
  実行証跡、Run Manifest、固定Gate、A95判定、hash receiptは、明示的にその運用を指定された場合だけ作成する。通常の関連テストでは、結果をチャットで報告し、証跡ファイルを作成しない。
- CTXMAPの旧commit／watch／validatorによる管理hash経路は通常経路から廃止した。`scripts/context_index/auto-commit.sh`、watcher、context Gateは管理用hashを計算・照合・retryせず、現行成果物の完了条件にも使わない。必要な保護対象hash、Secret、外部I/O、Human Gate、Unknown、対象範囲、権限境界は別途維持する。
- `npm run watch-start`、`npm run watch-commit` は旧運用の履歴入口として扱い、現行の新規文書・大幅変更・ソース変更では起動しない。A95の静的ポリシー判定とpath、schema、link、Secret、状態確認を使用する。
- Phase 1専用部品:
  `AutoTradePhase1_*`
  `autotrade_phase1_skill_*_v0_1`
  これらは `frozen / legacy / phase1証跡` として扱い、新規Phase実行の標準部品には使わない。

- 実ランタイム起動契約:
  ユーザーがOrchestratorやAgentの利用を明示した場合だけ、`multi_agent_v1__spawn_agent`／`multi_agent_v1__wait_agent`による実起動、指定Agentのwait、定義JSONのmodel確認を行う。起動不能時のfallback記録も、その明示依頼に含まれる場合だけ作成する。通常タスクでは、Agent一覧、runtime receipt、独立実行証跡を要求しない。外部I/O、Secret、費用、実取引、重要データ削除に関する安全停止は常に維持する。

## 読み取り順の目安

AI部品の作成、設計、レビュー、Phase実行をユーザーから明示的に依頼された場合は、次の順で確認する。通常の機能修正では、依頼に関係するソースコード、テスト、仕様だけを読む。

1. `README.md`
2. `settings/language.md`
3. `settings/ai_component_rules.md`
4. 関連する `doc/index.html` と該当HTML成果物
5. `doc/00_全Phase残課題Blocked統合台帳.html` で現在の停止条件を確認
6. 必要なら `plan/` 配下の計画書とログ

## Phase実行計画

ユーザーがPhase実行計画書の作成を明示的に依頼した場合だけ、`doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html`を参照して計画書を作成する。通常の機能追加や不具合修正では、Phase計画書、Step分割、後続プロンプトを作成しない。

## AI部品作成・変更

ユーザーがAI部品の作成または変更を明示的に依頼した場合だけ、既存再利用の調査、実体更新、仕様更新を行う。必要に応じて `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html` を参照する。AI部品の変更に対するA95確認も、ユーザーがそのレビューを求めた場合だけ行う。通常の製品コード、テスト、仕様書、マニュアル変更では、AI部品のライフサイクル処理を起動しない。

## 実装詳細設計

ユーザーが実装詳細設計書を明示的に依頼した場合だけ、`AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、`AutoTrade_A82_ImplementationDetailDesigner_v0_1`、`AutoTrade_A91_ImplementationDetailReviewer_v0_1`と関連テンプレートを使用する。通常の機能修正では、必要な設計判断をチャットまたは該当仕様へ最小限記載し、設計書セット、専門レビュー、改訂、再レビューを必須にしない。

## 品質確認ルール（PRODUCT_ONLY）

通常タスクの品質確認は、変更内容とリスクに応じて必要な範囲だけ実行する。管理文書、Agent、Gate、receiptの存在を品質確認の代わりにしない。

- 通常のコード変更では、変更したコードと直接関係する自動テストを実行する。
- 不具合修正では、可能な限り再現条件を固定したテストを追加または実行する。
- 共通基盤、永続化、注文、ポジション、金額計算、ヒストリカルデータ、削除処理を変更した場合は、主要正常系、重大な異常系、境界値、再実行、データ整合性を変更範囲に応じて確認する。
- UI変更では、主要操作、処理中状態、成功・失敗表示、二重送信防止、必要なキーボード操作とアクセシビリティを確認する。
- 外部API境界は、通常はmockまたはlocal fixtureで検証する。実接続、実データ取得、実注文はユーザーの明示許可なしに実行しない。
- 全テスト、全HTMLリンク検査、全設計レビュー、WSL隔離品質Gateは、共通基盤への変更、広い影響範囲、リリース前確認、またはユーザー指定がある場合だけ実行する。
- テスト結果は最終チャットへ簡潔に報告する。テスト結果を転載した証跡ファイル、品質Gate票、receiptは通常作成しない。
- 品質確認の縮小によって、Secret保護、fail-closed、実取引防止、データ削除安全、入力検証を弱めてはならない。

## 更新ルール

`AGENTS.md` と `README.md` は常に更新する必要はない。次のような変化があったタイミングで追記または修正する。

- AI実行基盤の名前空間、標準Orchestrator、標準Agent、標準Skillが変わったとき
- `doc/`、`plan/`、`.codex/`、`settings/` の役割や保存ルールが変わったとき
- 新しい入口文書や、最初に読むべき重要ドキュメントが増えたとき
- 人間やAIが最初に見て迷いやすい構成変更が入ったとき
- 残課題、Unknown、Blocked、Human Gate、承認状態、再開条件を総合台帳で管理する必要がある場合は、ユーザーが更新を依頼したときだけ、関連行と現在状態を一度に確認する。通常タスクでは、管理専用の台帳更新や履歴リンク同期を行わない。

軽微な文言修正、ログ増加、成果物追加だけでは毎回更新しなくてよい。

## タスク完了時のGit処理

- commitとpushは、ユーザーが明示的に依頼した場合、または依頼範囲に機能完了時のGit処理が明確に含まれる場合だけ行う。通常のタスク完了時に自動実行しない。
- ユーザーがcommitまたはpushを依頼した場合は、実行前に対象ファイル、差分、必要な機械検証結果を確認する。
- ユーザーが「指定ファイルの生成・変更のみ」と指定した場合は、Git操作を行わない。
- commitする場合も、既存のユーザー変更を混ぜない。`reset --hard`、`checkout`、force push、履歴書換えは行わない。
- commitまたはpushを行わなかったことを理由に、実行ログ、receipt、管理用台帳を作成しない。必要な説明は最終チャットで簡潔に行う。

@./settings/language.md
@./settings/ai_component_rules.md

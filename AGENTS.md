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
- `doc/ai_foundation/`
  AI実行基盤の棚卸し、移行方針、汎用Skill仕様、汎用Agent仕様、汎用Orchestrator仕様、作成ルール、検証結果。
- `doc/phase1/`
  Phase 1の正式HTML成果物。
- `plan/`
  計画書、実行プロンプト、ログ、台帳。
- `.codex/orchestrators/`
  実行可能なOrchestrator定義。
- `.codex/agents/`
  実行可能なAgent定義。
- `.codex/skills/`
  実行可能なSkill定義。

## AI実行基盤の現状

- 汎用Orchestrator:
  `AutoTradeProject_Orchestrator_v0_1`
  `AutoTradePhasePlanning_Orchestrator_v0_1`
  `AutoTradeComponentLifecycle_Orchestrator_v0_1`
  `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
  `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`
- 汎用Agents:
  `AutoTrade_A05_PhaseExecutionPlanner_v0_1`
  `AutoTrade_A06_AiComponentEngineer_v0_1`
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
- 汎用Skills:
  `.codex/skills/autotrade_skill_*_v0_1/`
  Phase実行計画作成では `autotrade_skill_phase_execution_planning_v0_1` を標準で使う。
  AI部品作成・変更では `autotrade_skill_ai_component_lifecycle_v0_1` を標準で使う。
  実装詳細設計では `autotrade_skill_implementation_detail_design_v0_1` と `autotrade_skill_implementation_detail_review_v0_1` を標準で使う。
- Phase 1専用部品:
  `AutoTradePhase1_*`
  `autotrade_phase1_skill_*_v0_1`
  これらは `frozen / legacy / phase1証跡` として扱い、新規Phase実行の標準部品には使わない。

## 読み取り順の目安

AI部品の作成、設計、レビュー、Phase実行に入る前は、原則として次の順で確認する。

1. `README.md`
2. `settings/language.md`
3. `settings/ai_component_rules.md`
4. 関連する `doc/index.html` と該当HTML成果物
5. 必要なら `plan/` 配下の計画書とログ

## Phase実行計画

各Phaseを開始する前に、まず実行計画書を作成する。標準の依頼プロンプトは `doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html` を参照する。計画書は `plan/` 配下へ保存し、複数ステップに分割し、各ステップにそのまま実行できるプロンプトを含める。

## AI部品作成・変更

Skill、サブエージェント、オーケストレータの作成または変更では、まず既存再利用を調査し、その後に実体更新、最後に仕様と導線を更新する。標準の依頼プロンプトは `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html` を参照する。

## 実装詳細設計

モジュール構成、型付き入出力、永続化、正常・異常系シーケンス、コード例または擬似コード、テストまでを必要とする設計書は、`AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、`AutoTrade_A82_ImplementationDetailDesigner_v0_1`、`AutoTrade_A91_ImplementationDetailReviewer_v0_1` を使用する。構成標準は `doc/ai_foundation/14_実装詳細設計書構成標準.html` を正本、HTML構成は `doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html`、依頼文は `doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html` を使う。最初にドメイン概要、ファイル構成、Mermaidによる構造図、モジュール入出力、Mermaidによる処理フロー、全テストケース表を読める順で置く。コード・固有名詞以外は日本語で説明し、各表の目的を先に示す。専門レビュー、改訂、再レビューを完了してから実装へ引き渡す。

## 更新ルール

`AGENTS.md` と `README.md` は常に更新する必要はない。次のような変化があったタイミングで追記または修正する。

- AI実行基盤の名前空間、標準Orchestrator、標準Agent、標準Skillが変わったとき
- `doc/`、`plan/`、`.codex/`、`settings/` の役割や保存ルールが変わったとき
- 新しい入口文書や、最初に読むべき重要ドキュメントが増えたとき
- 人間やAIが最初に見て迷いやすい構成変更が入ったとき

軽微な文言修正、ログ増加、成果物追加だけでは毎回更新しなくてよい。

@./settings/language.md
@./settings/ai_component_rules.md

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
5. 必要に応じて `plan/` 配下の計画書

## どこに何があるか

- `doc/`
  正式なHTML成果物の保存先。
- `doc/index.html`
  すべての正式HTML成果物の入口。
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
  `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
  `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`
- Agents:
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
- Skills:
  `.codex/skills/autotrade_skill_*_v0_1/`
  Phase実行計画作成では `autotrade_skill_phase_execution_planning_v0_1` を使います。
  AI部品作成・変更では `autotrade_skill_ai_component_lifecycle_v0_1` を使います。
  実装詳細設計では `autotrade_skill_implementation_detail_design_v0_1` と `autotrade_skill_implementation_detail_review_v0_1` を使います。

### Phase実行計画

各Phaseを開始する前に、まずそのPhaseの実行計画書を作成します。実行計画書は `plan/` 配下に保存し、必ず複数ステップに分割し、各ステップにそのまま実行できるプロンプトを含めます。

標準の依頼プロンプトは [Phase実行計画書作成依頼プロンプト](./doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html) を参照してください。

### AI部品作成・変更

Skill、サブエージェント、オーケストレータの作成または変更では、まず既存再利用を調査し、その後に実体更新、最後に仕様と導線を更新します。標準の依頼プロンプトは [AI部品作成更新依頼プロンプト](./doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html) を参照してください。

### 実装詳細設計

実装者がそのまま着手するための設計書は、まず誰にでも分かるドメイン概要、ファイル構成、Mermaidによる構造図、モジュールごとの入出力、Mermaidによる処理フロー、全テストケース表を示し、その後に型付き契約、永続化、異常系、コード例または擬似コードを続けます。コード・固有名詞以外は日本語で説明し、表の前には何を判断する表かを記します。標準は [実装詳細設計書構成標準](./doc/ai_foundation/14_実装詳細設計書構成標準.html) です。作成から専門レビュー、改訂、再レビューまでは `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、`AutoTrade_A82_ImplementationDetailDesigner_v0_1`、`AutoTrade_A91_ImplementationDetailReviewer_v0_1` を使います。

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

## AGENTS.md と README.md の更新タイミング

`AGENTS.md` と `README.md` は常に更新する必要はありません。次のような変化が入ったときに追記または修正します。

- 標準のAI実行基盤が変わったとき
- ディレクトリ構成や保存ルールが変わったとき
- 最初に読むべき入口資料が変わったとき
- 人間またはAIが初回に迷いやすい構成変更が入ったとき

軽微な成果物追加やログ増加だけでは、毎回更新しなくてよいです。

## 自動コミット監視

このリポジトリには、ファイル変更を監視して自動的に `git commit` と `git push` を行う補助コマンドがあります。

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

停止するときは `Ctrl+C` を使います。

## 自動コミットの注意

- `.git`、`node_modules`、`.env`、`.env.*`、`*.log` は監視対象外です。
- 連続変更による過剰なコミットを避けるため、一定時間まとめてから実行します。
- コミットメッセージは `auto: update by Codex [YYYY-MM-DD HH:MM:SS]` 形式です。

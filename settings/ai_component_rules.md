# AI部品ルール

## 目的

このプロジェクトでは、AI部品の命名、発火制御、保存先、Phase専用部品の扱いを明示的に管理する。

## 命名

- 汎用Orchestrator:
  `AutoTradeProject_*`
- 汎用Agent:
  `AutoTrade_Axx_*`
- 汎用Skill:
  `autotrade_skill_*`
- Phase専用Orchestrator:
  `AutoTradePhaseX_*`
- Phase専用Agent:
  `AutoTradePhaseX_Axx_*`
- Phase専用Skill:
  `autotrade_phaseX_skill_*`

## 作成ルール

- まず汎用Skill、汎用Agent、汎用Orchestratorで対応できるか確認する。
- 汎用部品で不足する場合だけ、Phase専用部品を作る。
- Phase専用部品を作るときは、理由、利用期限または凍結条件、HTML仕様書を必須にする。
- 既存名と衝突する場合は上書きせず、衝突として報告して停止する。
- Phase 1専用部品は `frozen / legacy / phase1証跡` として扱い、削除、移動、改名、上書きをしない。

## 発火ルール

- プロンプトには、使用するOrchestrator、Agent、Skillの完全名を明記する。
- AI部品タスクでは、既存部品を推測起動しない。
- 指定部品が存在しない場合は、現在のステップが作成ステップかどうかを確認する。
- 作成ステップでない場合は、既存部品で代替せず、不足部品名を報告して停止する。
- `default_orchestrator` は明示承認なしに変更しない。

## 保存ルール

- 正式な仕様書、設計書、検証結果はHTMLで `doc/` 配下に保存する。
- 計画書、実行プロンプト、ログ、台帳は `plan/` 配下に保存する。
- `doc/` 配下のHTML成果物は、すべて `doc/index.html` から到達できるようにする。
- Phase別HTMLは `doc/phaseX/` に保存する。
- AI実行基盤関連HTMLは `doc/ai_foundation/` に保存する。

## Phase実行計画ルール

- 各Phaseを開始する前に、必ずそのPhaseの実行計画書を作成する。
- 実行計画書は `plan/PhaseX_実行計画書_v0.1_YYYY-MM-DD.md` の形式で `plan/` 配下に保存する。
- 実行計画書は必ず複数ステップに分割し、各ステップにそのまま実行できるプロンプトを含める。
- Phase実行計画書を作成するときは、標準として `AutoTradePhasePlanning_Orchestrator_v0_1`、`AutoTrade_A05_PhaseExecutionPlanner_v0_1`、`autotrade_skill_phase_execution_planning_v0_1` を使用する。
- 依頼プロンプトの標準雛形は `doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html` を参照する。
- 実行計画の補助HTMLを作る場合は `doc/phaseX/00_実行計画/` 配下に保存し、`doc/index.html` から到達できるようにする。

## AI部品作成変更ルール

- Skill、サブエージェント、オーケストレータの作成または変更では、まず既存の汎用部品の再利用可否を調査する。
- その後に、必要な実体ファイルを作成または変更し、最後に対象ドキュメントを更新する。
- AI部品の作成または変更では、標準として `AutoTradeComponentLifecycle_Orchestrator_v0_1`、`AutoTrade_A06_AiComponentEngineer_v0_1`、`autotrade_skill_ai_component_lifecycle_v0_1` を使用する。
- 依頼プロンプトの標準雛形は `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html` を参照する。
- 実体更新だけで終わらせず、`doc/ai_foundation/03` から `08`、`doc/index.html`、必要に応じて `AGENTS.md` と `README.md` を同じ変更セットで更新する。

## 安全ルール

- 投資助言、売買推奨、特定商品の推奨をしない。
- UnknownをPassにしない。UnknownにはIDと決定タイミングを持たせる。
- Secret、APIキー、認証情報を出力しない。
- Fail-closed、監査証跡、手動介入後復旧条件を弱めない。
- 外部仕様を扱う場合は、公式一次情報を優先し、URLと確認日を記録する。

## AGENTS.md と README.md の更新ルール

`AGENTS.md` と `README.md` は常時更新ではなく、次のような変化が入ったときに追記または修正する。

- 標準のAI実行基盤が変わったとき
- ディレクトリ構成や保存ルールが変わったとき
- 最初に読むべき入口資料が変わったとき
- 人間またはAIが初回に迷いやすい構成変更が入ったとき

軽微な成果物追加やログ増加だけでは、毎回更新しなくてよい。

## AI基盤仕様書の追従更新ルール

汎用Skill、汎用サブエージェント、汎用オーケストレータに追加・変更・廃止が発生した場合は、実体ファイルだけで終わらせず、対応するAI基盤仕様書も同じ作業内で更新する。

- Skillに変更があった場合:
  `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
- サブエージェントに変更があった場合:
  `doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html`
- オーケストレータに変更があった場合:
  `doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html`
- 相関、発火制御、利用判断に影響する場合:
  `doc/ai_foundation/06_AI部品相関図発火制御図.html`

複数種別にまたがる変更では、該当する仕様書をすべて更新する。少なくとも、正式名称、責務、使用Skill、停止条件、相関図、更新対象表が実体と一致していることを確認する。

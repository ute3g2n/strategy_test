# AI実行基盤整理計画書

作成日: 2026-08-04  
対象: タートルズ・トレンドフォロー自動売買システム  
状態: v0.1 たたき台  

参照:

- `plan/Phase1_実行計画書_v0.1_2026-08-02.md`
- `doc/phase1/00_実行基盤/00_Skill定義.html`
- `doc/phase1/00_実行基盤/00_サブエージェント定義.html`
- `doc/phase1/00_実行基盤/00_Phase1オーケストレータ仕様.html`
- `.codex/skills/autotrade_phase1_skill_*_v0_1/SKILL.md`
- `.codex/agents/AutoTradePhase1_*.json`
- `.codex/orchestrators/AutoTradePhase1_Orchestrator_v0_1.json`

> 本計画書は、Phase 1専用として作成したSkill、サブエージェント、オーケストレータを、プロジェクト全体で再利用できるAI実行基盤へ整理するための実行計画である。既存のPhase 1専用部品は監査証跡として残し、新しい汎用部品を別名前空間で作成する。

---

## 1. 背景と課題

Phase 1では、誤発火を避けるために `AutoTradePhase1_` と `autotrade_phase1_skill_` の専用名前空間を使った。この判断はPhase 1の安全な完走には有効だった。

一方で、現在の部品名、入力、境界条件には `Phase 1`、`P1-xx`、`H1-x`、`doc/phase1/` などの前提が強く埋め込まれている。そのため、Phase 2以降で同種の設計、調査、レビュー、HTML成果物作成に使い回すには、プロンプトが重くなり、誤解も起きやすい。

本整理では、Phase 1専用部品を削除せず、プロジェクト汎用部品を新設する。

---

## 2. 整理方針

### 2.1 基本方針

- Phase 1専用部品は `legacy / frozen / phase1証跡` として残す。
- 今後の実行では、プロジェクト汎用の `AutoTrade_` / `autotrade_skill_` / `AutoTradeProject_` 名前空間を使う。
- Skillは小さめの作業規約として残す。
- サブエージェントは15体から9体前後へ統合する。
- オーケストレータはプロジェクト汎用1本を作り、Phase別Runbookを入力として切り替える。
- Phase依存の制約はSkillやAgentへ直書きせず、実行時入力として渡す。

### 2.2 統合判断

| 種別 | 判断 | 理由 |
|---|---|---|
| Skill | 原則として小さく維持 | 複数Agentから横断利用する作業規約であり、統合しすぎると不要な文脈が混ざるため。 |
| サブエージェント | 類似責務のみ統合 | プロンプト指定を軽くしつつ、判断軸の違う責務は混ぜないため。 |
| オーケストレータ | 汎用1本へ集約 | DAG、依存関係、Gate、成果物状態の管理はPhase横断で共通化できるため。 |
| Phase専用部品 | 残置 | 過去成果物の再現性、監査証跡、実行ログとの対応を保つため。 |

---

## 3. 目標構成

### 3.1 名前空間

| 区分 | 用途 | 名前空間 | 例 |
|---|---|---|---|
| プロジェクト汎用オーケストレータ | Phase横断のDAG、Gate、成果物統合 | `AutoTradeProject_` | `AutoTradeProject_Orchestrator_v0_1` |
| プロジェクト汎用サブエージェント | Phase横断の役割 | `AutoTrade_Axx_` | `AutoTrade_A20_ArchitectureDomainArchitect_v0_1` |
| プロジェクト汎用Skill | Phase横断の作業規約 | `autotrade_skill_` | `autotrade_skill_traceability_v0_1` |
| Phase専用オーケストレータ | 特定Phaseの凍結済み証跡 | `AutoTradePhaseX_` | `AutoTradePhase1_Orchestrator_v0_1` |
| Phase専用Skill | 特定Phaseだけで使う作業規約 | `autotrade_phaseX_skill_` | `autotrade_phase1_skill_poc_design_v0_1` |

### 3.2 プロジェクト汎用サブエージェント案

| ID | 完全名 | 統合元 | 主な責務 | 推奨モデル |
|---|---|---|---|---|
| A10 | `AutoTrade_A10_RequirementsCurator_v0_1` | Phase1 A01 | 要件抽出、Phaseスコープ分離、追跡ID、Unknown台帳 | `gpt-5.6-luna` |
| A20 | `AutoTrade_A20_ArchitectureDomainArchitect_v0_1` | Phase1 A02, A03 | 全体構成、ドメイン分割、共通モデル、依存方向 | `gpt-5.6-luna` |
| A30 | `AutoTrade_A30_StrategyQaArchitect_v0_1` | Phase1 A04, A10の一部 | Strategy Interface、Golden test、Look-ahead防止、戦略QA | `gpt-5.6-luna` |
| A40 | `AutoTrade_A40_ExecutionEnginePocArchitect_v0_1` | Phase1 A05, A06 | 共通実行モデル、取引エンジンPoC評価、Replay/Realtime整合 | `gpt-5.6-luna` |
| A50 | `AutoTrade_A50_AdapterArchitect_v0_1` | Phase1 A07 | Broker Adapter、Market Data Adapter、外部ID境界 | `gpt-5.6-luna` |
| A60 | `AutoTrade_A60_RiskAccountArchitect_v0_1` | Phase1 A08 | Portfolio、Risk、Account、OMS責務境界 | `gpt-5.6-luna` |
| A70 | `AutoTrade_A70_OpsSecurityArchitect_v0_1` | Phase1 A09 | 監視、Secrets、環境分離、安全停止、運用設計 | `gpt-5.6-luna` |
| A80 | `AutoTrade_A80_DocumentIntegrator_v0_1` | Phase1 A11, A14 | HTML設計書、index更新、レビュー反映、変更履歴 | `gpt-5.1` |
| A90 | `AutoTrade_A90_DesignReviewer_v0_1` | Phase1 A12, A13 | 整合性レビュー、Red Teamレビュー、未確定事項監査 | `gpt-5.6-luna` |

### 3.3 プロジェクト汎用Skill案

| 完全名 | 元Skill | 方針 |
|---|---|---|
| `autotrade_skill_orchestration_v0_1` | `autotrade_phase1_skill_orchestration_v0_1` | Phase ID、Gate、成果物Rootを入力化する。 |
| `autotrade_skill_source_reader_v0_1` | `autotrade_phase1_skill_source_reader_v0_1` | 要件、Phase方針、既存成果物の読み取りを汎用化する。 |
| `autotrade_skill_traceability_v0_1` | `autotrade_phase1_skill_traceability_v0_1` | ID体系を `REQ-*`, `DEC-*`, `UNK-*`, `ART-*` としてPhase横断化する。 |
| `autotrade_skill_official_research_v0_1` | `autotrade_phase1_skill_official_research_v0_1` | 公式一次情報、URL、確認日、根拠管理を継続する。 |
| `autotrade_skill_html_doc_writer_v0_1` | `autotrade_phase1_skill_html_doc_writer_v0_1` | `doc/index.html` 更新必須、`doc/phaseX/` 保存規約を明示する。 |
| `autotrade_skill_architecture_writer_v0_1` | `autotrade_phase1_skill_architecture_writer_v0_1` | アーキテクチャ判断、依存方向、境界設計を汎用化する。 |
| `autotrade_skill_domain_modeling_v0_1` | `autotrade_phase1_skill_domain_modeling_v0_1` | Entity、Event、Command、State、ID、Timeを汎用化する。 |
| `autotrade_skill_strategy_interface_v0_1` | `autotrade_phase1_skill_strategy_design_v0_1` | Strategy Plugin Interfaceを汎用化する。 |
| `autotrade_skill_turtle_strategy_rules_v0_1` | `autotrade_phase1_skill_strategy_design_v0_1` | Turtle固有ルールは専用Skillとして分離する。 |
| `autotrade_skill_golden_test_v0_1` | `autotrade_phase1_skill_golden_test_v0_1` | Golden test設計を汎用化する。 |
| `autotrade_skill_adapter_boundary_v0_1` | `autotrade_phase1_skill_adapter_boundary_v0_1` | Broker/Data Vendor依存の隔離を汎用化する。 |
| `autotrade_skill_execution_model_v0_1` | `autotrade_phase1_skill_execution_model_v0_1` | Backtest/Shadow/Paper/Live共通実行を汎用化する。 |
| `autotrade_skill_poc_evaluation_v0_1` | `autotrade_phase1_skill_poc_design_v0_1` | PoC評価軸、採点、Human Gateを汎用化する。 |
| `autotrade_skill_trading_engine_poc_v0_1` | `autotrade_phase1_skill_poc_design_v0_1` | 取引エンジン候補評価は専用Skillとして分離する。 |
| `autotrade_skill_risk_account_design_v0_1` | `autotrade_phase1_skill_risk_account_design_v0_1` | Risk/Account/OMS境界を汎用化する。 |
| `autotrade_skill_ops_security_v0_1` | `autotrade_phase1_skill_ops_security_v0_1` | Secrets、監視、安全停止、環境分離を汎用化する。 |
| `autotrade_skill_test_strategy_v0_1` | `autotrade_phase1_skill_test_strategy_v0_1` | テスト戦略、品質Gate、Failure injectionを汎用化する。 |
| `autotrade_skill_design_review_v0_1` | `autotrade_phase1_skill_design_reviewer_v0_1` | 整合性レビューを汎用化する。 |
| `autotrade_skill_red_team_review_v0_1` | `autotrade_phase1_skill_red_team_review_v0_1` | 安全性、運用事故、危険な先送り監査を汎用化する。 |
| `autotrade_skill_revision_integration_v0_1` | `autotrade_phase1_skill_revision_integrator_v0_1` | レビュー反映、差分記録、最終化を汎用化する。 |

### 3.4 相関図

各HTML仕様書には、次のような相関図を含める。実装時はHTML内にMermaid等の外部CDNへ依存せず、`<pre>` またはCSS付きの簡易図として埋め込む。

```text
AutoTradeProject_Orchestrator_v0_1
  |
  +-- Phase Runbook
  |     +-- phase_id
  |     +-- step_id
  |     +-- output_root: doc/phaseX/
  |     +-- gate_policy
  |     +-- detail_boundary
  |
  +-- AutoTrade_A10_RequirementsCurator_v0_1
  |     +-- autotrade_skill_source_reader_v0_1
  |     +-- autotrade_skill_traceability_v0_1
  |
  +-- AutoTrade_A20_ArchitectureDomainArchitect_v0_1
  |     +-- autotrade_skill_architecture_writer_v0_1
  |     +-- autotrade_skill_domain_modeling_v0_1
  |
  +-- AutoTrade_A80_DocumentIntegrator_v0_1
  |     +-- autotrade_skill_html_doc_writer_v0_1
  |     +-- autotrade_skill_revision_integration_v0_1
  |
  +-- AutoTrade_A90_DesignReviewer_v0_1
        +-- autotrade_skill_design_review_v0_1
        +-- autotrade_skill_red_team_review_v0_1

Frozen / legacy:
  AutoTradePhase1_Orchestrator_v0_1
  AutoTradePhase1_A00...A14
  autotrade_phase1_skill_*_v0_1
```

---

## 4. 成果物

正式な仕様書はHTML形式で作成し、`doc/` 配下に保存する。`doc/index.html` から必ず到達できるようにする。

| ID | 成果物 | 出力先 |
|---|---|---|
| AF-D01 | AI実行基盤 現状棚卸し | `doc/ai_foundation/01_AI実行基盤現状棚卸し.html` |
| AF-D02 | AI部品整理方針・移行マップ | `doc/ai_foundation/02_AI部品整理方針移行マップ.html` |
| AF-D03 | プロジェクト汎用Skill仕様 | `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html` |
| AF-D04 | プロジェクト汎用サブエージェント仕様 | `doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html` |
| AF-D05 | プロジェクト汎用オーケストレータ仕様 | `doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html` |
| AF-D06 | AI部品相関図・発火制御図 | `doc/ai_foundation/06_AI部品相関図発火制御図.html` |
| AF-D07 | AI部品作成ルール | `doc/ai_foundation/07_AI部品作成ルール.html` |
| AF-D08 | AI実行基盤整理 検証結果 | `doc/ai_foundation/08_AI実行基盤整理検証結果.html` |

補助成果物:

- `.codex/skills/autotrade_skill_*_v0_1/SKILL.md`
- `.codex/agents/AutoTrade_A*.json`
- `.codex/orchestrators/AutoTradeProject_Orchestrator_v0_1.json`
- `settings/ai_component_rules.md`
- `AGENTS.md`
- `.codex/config.json`

---

## 5. プロジェクト全体ルール化方針

### 5.1 作成ルール

AI部品を新規作成または更新するときは、次をプロジェクト共通ルールとする。

- 汎用部品は `AutoTradeProject_`、`AutoTrade_Axx_`、`autotrade_skill_` の名前空間を使う。
- Phase専用部品は、特定Phaseだけで使う明確な理由がある場合に限り `AutoTradePhaseX_`、`autotrade_phaseX_skill_` を使う。
- Phase専用部品を作る場合は、汎用部品では不十分な理由、利用期限、凍結条件を仕様書に記録する。
- 既存部品を推測で起動しない。プロンプトには使用するオーケストレータ、サブエージェント、Skillの完全名を明記する。
- 既存名と衝突する場合は上書きせず、衝突として報告する。
- `default_orchestrator` は明示承認なしに変更しない。
- 正式な仕様書はHTMLで作成し、`doc/index.html` からリンクできるようにする。
- `plan/` は計画書、プロンプト、ログ、台帳を置く場所とし、正式HTML仕様書は `doc/` に置く。
- UnknownをPassにしない。未確定事項IDと決定タイミングを記録する。
- 投資助言、売買推奨、特定商品の推奨にならない表現にする。

### 5.2 ルールの保存先

プロジェクト全体へ効かせるため、次を作成または更新する。

- `settings/ai_component_rules.md`: AI部品作成、命名、発火制御、HTML仕様書保存のプロジェクト共通ルール。
- `AGENTS.md`: `@./settings/ai_component_rules.md` を追加し、Codexが常に参照できるようにする。
- `doc/ai_foundation/07_AI部品作成ルール.html`: 人間レビュー用のHTML版ルール。

---

## 6. 実行フェーズ

本整理は4フェーズで実行する。細かいサブステップに分けすぎず、各フェーズ内で調査、作成、レビュー、修正を完結させる。

### AF-01 現状棚卸しと整理方針確定

目的: 既存のPhase 1専用部品と仕様書を棚卸しし、汎用化、分割、統合、残置の判断をHTMLで固定する。

出力:

- `doc/ai_foundation/01_AI実行基盤現状棚卸し.html`
- `doc/ai_foundation/02_AI部品整理方針移行マップ.html`
- `doc/index.html` 更新

実行プロンプト:

```text
ステップID: AF-01
ロール: AI実行基盤アーキテクト
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A10_RequirementsCurator_v0_1, AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_source_reader_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_architecture_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_html_doc_writer_v0_1

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- ただし本ステップでは、上記AI部品がまだ存在しない場合がある。その場合は既存部品を代替起動せず、本計画書に従った人間実行またはCodex通常実行として、仕様書作成のみを行う。
- 既存の AutoTradePhase1_* または autotrade_phase1_skill_* は、調査対象として読むだけにする。実行部品として起動しない。
- 既存名と衝突する場合は上書きせず、衝突として報告する。

タスク:
既存の .codex/skills、.codex/agents、.codex/orchestrators、.codex/config.json、doc/phase1/00_実行基盤 配下の仕様書を読み、AI実行基盤の現状棚卸しと整理方針を作成してください。

入力:
- .codex/skills/autotrade_phase1_skill_*_v0_1/SKILL.md
- .codex/agents/AutoTradePhase1_*.json
- .codex/orchestrators/AutoTradePhase1_Orchestrator_v0_1.json
- .codex/config.json
- doc/phase1/00_実行基盤/*.html
- plan/AI実行基盤整理計画書_v0.1_2026-08-04.md

作業:
1. 現在存在するSkill、サブエージェント、オーケストレータを一覧化する。
2. 各部品を、プロジェクト汎用へ昇格、分割して昇格、統合して昇格、Phase 1専用として残置、廃止候補に分類する。
3. Phase 1専用部品を削除せず、frozen / legacy として扱う理由を明記する。
4. 汎用部品とPhase専用部品の関係が分かる相関図をHTML内に含める。
5. 公式設計書として、AF-D01とAF-D02をHTMLで作成する。
6. doc/index.html からAF-D01とAF-D02へリンクできるように更新する。

レビュー:
- AutoTrade_A90_DesignReviewer_v0_1相当の観点で、統合しすぎ、分割しすぎ、既存証跡破壊、発火制御漏れを確認する。
- 指摘を反映してHTMLを更新する。

完了条件:
- 既存部品の残置理由と、新設する汎用部品の一覧が明確であること。
- Phase 2以降で使うAI部品名の候補が確定していること。
```

### AF-02 汎用Skill、サブエージェント、オーケストレータ仕様書作成

目的: 実体作成前に、プロジェクト汎用AI部品の仕様をHTMLで固定する。

出力:

- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
- `doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html`
- `doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html`
- `doc/ai_foundation/06_AI部品相関図発火制御図.html`
- `doc/ai_foundation/07_AI部品作成ルール.html`
- `doc/index.html` 更新

実行プロンプト:

```text
ステップID: AF-02
ロール: AI部品仕様設計者
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A20_ArchitectureDomainArchitect_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_architecture_writer_v0_1, autotrade_skill_html_doc_writer_v0_1, autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- ただし本ステップでは、上記AI部品がまだ存在しない場合がある。その場合は既存部品を代替起動せず、本計画書とAF-01成果物に従った人間実行またはCodex通常実行として、仕様書作成のみを行う。
- AutoTradePhase1_* と autotrade_phase1_skill_* は参照元として読むだけにする。
- 既存名と衝突する場合は上書きせず、衝突として報告する。

タスク:
AF-01の整理方針に基づき、プロジェクト汎用のSkill、サブエージェント、オーケストレータの仕様書をHTML形式で作成してください。

入力:
- doc/ai_foundation/01_AI実行基盤現状棚卸し.html
- doc/ai_foundation/02_AI部品整理方針移行マップ.html
- plan/AI実行基盤整理計画書_v0.1_2026-08-04.md
- doc/phase1/00_実行基盤/*.html
- .codex/skills/autotrade_phase1_skill_*_v0_1/SKILL.md
- .codex/agents/AutoTradePhase1_*.json
- .codex/orchestrators/AutoTradePhase1_Orchestrator_v0_1.json

作業:
1. autotrade_skill_*_v0_1 の各Skillについて、目的、入力、出力、禁止事項、品質チェック、Phase依存パラメータを定義する。
2. AutoTrade_A10 から AutoTrade_A90 までの各サブエージェントについて、責務、入力、出力、使用Skill、推奨モデル、境界条件を定義する。
3. AutoTradeProject_Orchestrator_v0_1 について、DAG管理、Phase Runbook、Human Gate、成果物統合、発火制御、Unknown管理、doc/index.html更新方針を定義する。
4. プロジェクト汎用部品とPhase専用部品の相関図、発火制御図、利用判断フローをHTML内に含める。
5. AI部品作成ルールをHTML仕様書として作成する。
6. doc/index.html からAF-D03からAF-D07へリンクできるように更新する。

レビュー:
- 統合されたサブエージェントが責務過多になっていないか確認する。
- Skillが大きくなりすぎて再利用性を失っていないか確認する。
- Phase専用部品の新規作成条件が厳密か確認する。
- 既存Phase 1証跡を壊さないことを確認する。

完了条件:
- 実体作成者がHTML仕様書だけを見て、汎用Skill、サブエージェント、オーケストレータを作成できること。
```

### AF-03 汎用AI部品の実体作成とプロジェクトルール反映

目的: AF-02仕様に従い、汎用AI部品の実体を作成し、プロジェクト全体ルールとして参照されるようにする。

出力:

- `.codex/skills/autotrade_skill_*_v0_1/SKILL.md`
- `.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json` など9体
- `.codex/orchestrators/AutoTradeProject_Orchestrator_v0_1.json`
- `settings/ai_component_rules.md`
- `AGENTS.md` 更新
- `.codex/config.json` 更新。ただし `default_orchestrator` は変更しない。

実行プロンプト:

```text
ステップID: AF-03
ロール: AI実行基盤実装者
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A80_DocumentIntegrator_v0_1, AutoTrade_A90_DesignReviewer_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_html_doc_writer_v0_1, autotrade_skill_revision_integration_v0_1, autotrade_skill_design_review_v0_1

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- ただし本ステップは、上記AI部品自体を作成対象に含む。未存在の場合は既存部品を代替起動せず、AF-02仕様に従って実体ファイルを作成する。
- AutoTradePhase1_* と autotrade_phase1_skill_* は参照元として読むだけにする。移動、削除、上書きをしない。
- 既存名と衝突する場合は、既存部品を上書きせず、衝突として報告して停止する。
- default_orchestrator は変更しない。

タスク:
AF-02で作成したHTML仕様書に従い、プロジェクト汎用のSkill、サブエージェント、オーケストレータの実体を作成し、AI部品作成ルールをプロジェクト全体へ反映してください。

入力:
- doc/ai_foundation/03_プロジェクト汎用Skill仕様.html
- doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html
- doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html
- doc/ai_foundation/06_AI部品相関図発火制御図.html
- doc/ai_foundation/07_AI部品作成ルール.html
- .codex/config.json
- AGENTS.md

作業:
1. .codex/skills/ 配下に autotrade_skill_*_v0_1 の各SKILL.mdを作成する。
2. .codex/agents/ 配下に AutoTrade_A10 から AutoTrade_A90 までのサブエージェントJSONを作成する。
3. .codex/orchestrators/ 配下に AutoTradeProject_Orchestrator_v0_1.json を作成する。
4. .codex/config.json の orchestrators に AutoTradeProject_Orchestrator_v0_1 を追加する。ただし default_orchestrator は変更しない。
5. settings/ai_component_rules.md を作成し、AI部品作成、命名、発火制御、HTML仕様書保存、Phase専用部品作成条件を記載する。
6. AGENTS.md に @./settings/ai_component_rules.md を追加する。
7. Phase 1専用部品は frozen / legacy として残し、削除しない。

レビュー:
- JSONとして読み込めることを確認する。
- 各Skillに目的、入力、出力、禁止事項、品質チェックがあることを確認する。
- 各Agentにname、model、skill、role、inputs、outputs、boundariesがあることを確認する。
- オーケストレータにagents、workflow/runbook方針、global_constraints、human_gate方針があることを確認する。
- default_orchestrator が変更されていないことを確認する。

完了条件:
- Phase 2以降の計画書が AutoTradeProject_Orchestrator_v0_1 と AutoTrade_Axx / autotrade_skill_* を指定して実行できること。
```

### AF-04 検証、採用判定、Phase 2以降への引き継ぎ

目的: 汎用AI実行基盤が仕様どおり作成され、Phase 2以降で使用できることを確認する。

出力:

- `doc/ai_foundation/08_AI実行基盤整理検証結果.html`
- `doc/index.html` 更新
- 必要に応じて `plan/phase2/` 以降のプロンプト雛形

実行プロンプト:

```text
ステップID: AF-04
ロール: AI実行基盤レビュアー
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: AutoTrade_A90_DesignReviewer_v0_1, AutoTrade_A80_DocumentIntegrator_v0_1
使用モデル: gpt-5.6-terra
使用Skill完全名: autotrade_skill_design_review_v0_1, autotrade_skill_red_team_review_v0_1, autotrade_skill_traceability_v0_1, autotrade_skill_html_doc_writer_v0_1

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- AutoTradePhase1_* と autotrade_phase1_skill_* は比較対象として読むだけにする。実行部品として起動しない。
- 既存名と衝突する場合は、既存部品を上書きせず、衝突として報告する。

タスク:
AF-03で作成した汎用AI部品とプロジェクトルールを検証し、Phase 2以降で採用可能か判定してください。

入力:
- .codex/skills/autotrade_skill_*_v0_1/SKILL.md
- .codex/agents/AutoTrade_A*.json
- .codex/orchestrators/AutoTradeProject_Orchestrator_v0_1.json
- .codex/config.json
- settings/ai_component_rules.md
- AGENTS.md
- doc/ai_foundation/*.html

作業:
1. 作成済みファイルの存在確認を行う。
2. JSON妥当性を検証する。
3. Skill、Agent、Orchestratorの相互参照が正しいことを確認する。
4. 汎用部品とPhase専用部品の使い分けルールが明確であることを確認する。
5. AGENTS.mdからsettings/ai_component_rules.mdが参照されていることを確認する。
6. doc/index.htmlからAF-D01からAF-D08まで到達できることを確認する。
7. 検証結果をHTMLで作成する。

レビュー:
- 発火制御が緩すぎないか確認する。
- Phase専用部品を誤って汎用利用しない設計になっているか確認する。
- 汎用Agentが統合されすぎて実行不能になっていないか確認する。
- 今後のPhase計画書に書くべき共通プロンプトヘッダーを確認する。

完了条件:
- AutoTradeProject_Orchestrator_v0_1 をPhase 2以降の標準オーケストレータ候補として採用できること。
- Phase 1専用部品が監査証跡として残っていること。
- プロジェクト全体ルールとしてAI部品作成ルールが参照可能であること。
```

---

## 7. Phase 2以降の共通プロンプトヘッダー案

AF-04完了後、Phase 2以降の各実行プロンプトは次の形式を使う。

```text
ステップID: <Phase別ステップID>
ロール: <ロール名>
使用オーケストレータ完全名: AutoTradeProject_Orchestrator_v0_1
担当サブエージェント完全名: <AutoTrade_Axx_..._v0_1>
使用モデル: <モデル名>
使用Skill完全名: <autotrade_skill_*_v0_1一覧>

Phase Runbook:
- phase_id: <例: Phase 2>
- output_root: <例: doc/phase2/>
- log_root: <例: plan/phase2/ログ/>
- detail_boundary: <このPhaseで固定する範囲>
- human_gate_policy: <Gate名と停止条件>

発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- Phase専用部品を使う場合は、その完全名、理由、利用期限、凍結条件を明記する。
- 指定AI部品が存在しない場合は、既存部品で代替せず、不足部品名を報告して停止する。
- default_orchestrator は変更しない。

成果物ルール:
- 正式設計書はHTML形式で doc/ 配下へ保存する。
- Phase別HTMLは doc/phaseX/ 配下へ保存する。
- すべてのHTML成果物は doc/index.html からリンクで到達できるようにする。
- UnknownをPassにせず、未確定事項台帳または該当HTMLの未確定事項へ記録する。
```

---

## 8. リスクと対策

| リスク | 内容 | 対策 |
|---|---|---|
| 既存Phase 1証跡の破壊 | 既存部品をリネーム、移動、削除するとPhase 1成果物との対応が崩れる。 | Phase 1専用部品はfrozenとして残し、新しい汎用部品を別名で作る。 |
| 汎用化しすぎ | どのPhaseにも使えるが、実際の作業指示が曖昧になる。 | Phase Runbookでphase_id、output_root、detail_boundary、Gateを毎回渡す。 |
| 統合しすぎ | Agentの責務が広くなり、レビューや出力が浅くなる。 | Agentは9体前後に抑え、Skillは小さく保つ。 |
| 分割しすぎ | プロンプトの指定が重くなり、実行管理が煩雑になる。 | 類似責務のAgentだけ統合する。 |
| 誤発火 | 既存SkillやPhase専用部品が意図せず使われる。 | プロンプトに完全名を明記し、未指定部品の利用を禁止する。 |
| default変更事故 | 既存default orchestratorを変えて別タスクへ影響する。 | `default_orchestrator` は明示承認なしに変更しない。 |

---

## 9. 完了判定

本整理計画は、次を満たした時点で完了とする。

- AF-D01からAF-D08までのHTML仕様書が存在する。
- `doc/index.html` からAF-D01からAF-D08へ到達できる。
- `.codex/skills/autotrade_skill_*_v0_1/SKILL.md` が作成されている。
- `.codex/agents/AutoTrade_A*.json` が作成されている。
- `.codex/orchestrators/AutoTradeProject_Orchestrator_v0_1.json` が作成されている。
- `.codex/config.json` に `AutoTradeProject_Orchestrator_v0_1` が追加されている。
- `default_orchestrator` が意図せず変更されていない。
- `settings/ai_component_rules.md` が存在し、`AGENTS.md` から参照されている。
- Phase 1専用部品が削除されず、frozen / legacy として扱われている。
- Phase 2以降のプロンプトが、汎用AI実行基盤を指定して書ける状態になっている。

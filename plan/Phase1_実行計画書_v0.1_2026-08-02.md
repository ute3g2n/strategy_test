# Phase 1 実行計画書

作成日: 2026-08-02  
対象: タートルズ・トレンドフォロー自動売買システム  
状態: v0.1 たたき台  
参照:

- `plan/自動トレードシステム_要件定義書.md`
- `plan/Phase分割と設計書整備方針_v0.1_2026-08-02.md`

> 本計画書は、自動売買システムの設計作業をAIエージェント群で進めるための実行計画である。投資助言、売買推奨、特定商品の推奨を目的としない。

---

## 1. Phase 1の目的

Phase 1では、後続Phaseの土台になる全体設計を作成する。全詳細設計をこの段階で固定するのではなく、次を「後続Phaseの憲法」として凍結する。

- 本番システムと研究用コードの境界
- 全体アーキテクチャ
- ドメイン分割と境界づけられたコンテキスト
- 主要モジュールの責務
- Backtest / Shadow / Paper / Live で共通化するドメインモデル
- Strategy Plugin Interface
- Broker Adapter / Market Data Adapter の境界
- 口座管理、リスク管理、注文管理の責務分離
- ログ、監査証跡、メトリクス、アラート方針
- Secrets、環境分離、セキュリティ、安全停止方針
- テスト戦略、Golden test、品質Gate
- Phase 2以降で詳細化する設計バックログ

Phase 1では、IBKR APIの全エンドポイント仕様、Databento取得ジョブの全詳細、Backtest Engineの全クラス設計、Live運用Runbookの全手順、画面・Dashboardの細部は固定しない。

---

## 2. 成果物方針

Phase 1で作成する設計書は、人間の可読性を優先してすべてHTML形式とする。補助ログ、台帳、差分表はCSVまたはMarkdownでもよいが、正式な設計書は `.html` とする。HTML成果物は `doc/` 配下へ保存し、`doc/index.html` から必ず到達できるようにする。

### 2.1 出力ルート

```text
doc/
  index.html
  phase1/
  00_実行基盤/
  01_要件追跡/
  02_全体設計/
  03_ドメイン設計/
  04_共通モデル/
  05_戦略設計/
  06_アダプター境界/
  07_実行モデル/
  08_リスク口座管理/
  09_非機能要件/
  10_テスト品質/
  11_ロードマップ/
  12_統合レビュー/

plan/phase1/
  ログ/
```

### 2.2 主要HTML設計書

| ID | 設計書 | 出力先 |
|---|---|---|
| D01 | 全HTML成果物インデックス | `doc/index.html` |
| D02 | 要件追跡マトリクス | `doc/phase1/01_要件追跡/01_要件追跡マトリクス.html` |
| D03 | システム全体構成設計書 | `doc/phase1/02_全体設計/02_システム全体構成設計書.html` |
| D04 | ドメイン分割・境界づけられたコンテキスト設計書 | `doc/phase1/03_ドメイン設計/03_ドメイン分割設計書.html` |
| D05 | モジュール責務・データフロー設計書 | `doc/phase1/03_ドメイン設計/03_モジュール責務データフロー設計書.html` |
| D06 | 共通ドメインモデル設計書 | `doc/phase1/04_共通モデル/04_共通ドメインモデル設計書.html` |
| D07 | イベント・注文・口座・ID・時系列設計書 | `doc/phase1/04_共通モデル/04_イベント注文口座ID時系列設計書.html` |
| D08 | Strategy Plugin Interface設計書 | `doc/phase1/05_戦略設計/05_Strategy_Plugin_Interface設計書.html` |
| D09 | Turtle Golden test設計書 | `doc/phase1/05_戦略設計/05_Turtle_Golden_test設計書.html` |
| D10 | Broker / Market Data Adapter境界設計書 | `doc/phase1/06_アダプター境界/06_Adapter境界設計書.html` |
| D11 | Backtest / Shadow / Paper / Live 共通実行モデル設計書 | `doc/phase1/07_実行モデル/07_共通実行モデル設計書.html` |
| D12 | 取引エンジンPoC評価設計書 | `doc/phase1/07_実行モデル/07_取引エンジンPoC評価設計書.html` |
| D13 | Portfolio / Risk / Account責務境界設計書 | `doc/phase1/08_リスク口座管理/08_Risk_Account責務境界設計書.html` |
| D14 | 非機能要件設計書 | `doc/phase1/09_非機能要件/09_非機能要件設計書.html` |
| D15 | 設定・Secrets・環境分離設計書 | `doc/phase1/09_非機能要件/09_設定Secrets環境分離設計書.html` |
| D16 | ログ・監査証跡・メトリクス・アラート設計書 | `doc/phase1/09_非機能要件/09_監視監査設計書.html` |
| D17 | セキュリティ・安全停止方針設計書 | `doc/phase1/09_非機能要件/09_セキュリティ安全停止設計書.html` |
| D18 | テスト戦略・品質Gate設計書 | `doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html` |
| D19 | Phase 2以降の詳細設計バックログ | `doc/phase1/11_ロードマップ/11_詳細設計バックログ.html` |
| D20 | Phase 1完了判定・Phase 2移行承認書 | `doc/phase1/12_統合レビュー/12_Phase1完了判定とPhase2移行承認書.html` |

---

## 3. 基本フロー

各設計書は、原則として次の流れで作成する。

1. 調査  
   参照ドキュメント、既存成果物、公式一次情報、未確定事項を整理する。
2. ドキュメント作成  
   HTML形式で設計書ドラフトを作成する。各設計判断には根拠、制約、後続Phaseへの影響を明記する。
3. レビュー  
   一貫性、実装可能性、安全性、未確定事項の扱い、Phase 1で詳細化しすぎていないかを確認する。
4. 修正  
   レビュー指摘を反映し、残課題とHuman Gate項目を明確にする。
5. 統合  
   すべての設計書の用語、ID、責務境界、依存関係、Gate条件を揃える。

重要な例外として、P1-00ではまずAI実行基盤を作成する。P1-00の成果物には、サブエージェント定義、Skill定義、オーケストレータ仕様、HTMLテンプレート、レビュー観点、実行ログ形式を含める。

---

## 4. Phase 1専用名前空間

既存のSkill、サブエージェント、オーケストレータが誤って発火しないように、Phase 1で作成・使用するAI部品はすべて専用名前空間を持つ完全名で指定する。

### 4.1 命名ルール

| 種別 | 命名形式 | 例 |
|---|---|---|
| オーケストレータ | `AutoTradePhase1_Orchestrator_v0_1` | `AutoTradePhase1_Orchestrator_v0_1` |
| サブエージェント | `AutoTradePhase1_Axx_<role>_v0_1` | `AutoTradePhase1_A04_StrategyArchitect_v0_1` |
| Skill | `autotrade_phase1_skill_<purpose>_v0_1` | `autotrade_phase1_skill_strategy_design_v0_1` |

### 4.2 発火防止ルール

- 各プロンプトで明示されたオーケストレータ、サブエージェント、Skillの完全名だけを使用する。
- 既存のSkill、既存のサブエージェント、既存のオーケストレータを推測で使用しない。
- 短縮名の `A00` から `A14` は計画書内の参照用IDであり、実行時の名前ではない。
- P1-00では、下表の完全名を持つAI部品を新規作成する。
- P1-01以降で指定された完全名のAI部品が存在しない場合は、代替の既存Skillを使わず、P1-00の再実行が必要であると報告して停止する。

---

## 5. サブエージェント構成

モデル名は実行環境で利用可能な名称に置換する。下表では、最高推論モデルを `gpt-5.4`、高速な文書整形モデルを `gpt-5.1` と仮置きする。

| ID | サブエージェント完全名 | 主な責務 | 推奨モデル | 使用Skill完全名 |
|---|---|---|---|---|
| A00 | `AutoTradePhase1_A00_Orchestrator_v0_1` | 全体DAG管理、依存関係、Gate、成果物統合 | `gpt-5.4` | `autotrade_phase1_skill_orchestration_v0_1`, `autotrade_phase1_skill_traceability_v0_1` |
| A01 | `AutoTradePhase1_A01_RequirementsCurator_v0_1` | 要件定義とPhase方針の抽出、追跡ID付与 | `gpt-5.4` | `autotrade_phase1_skill_source_reader_v0_1`, `autotrade_phase1_skill_traceability_v0_1` |
| A02 | `AutoTradePhase1_A02_SystemArchitect_v0_1` | 全体構成、モジュール分割、データフロー | `gpt-5.4` | `autotrade_phase1_skill_architecture_writer_v0_1` |
| A03 | `AutoTradePhase1_A03_DomainArchitect_v0_1` | 境界づけられたコンテキスト、共通モデル | `gpt-5.4` | `autotrade_phase1_skill_domain_modeling_v0_1` |
| A04 | `AutoTradePhase1_A04_StrategyArchitect_v0_1` | Strategy Plugin、Turtleルール、Golden test | `gpt-5.4` | `autotrade_phase1_skill_strategy_design_v0_1`, `autotrade_phase1_skill_golden_test_v0_1` |
| A05 | `AutoTradePhase1_A05_ExecutionModelArchitect_v0_1` | Backtest / Shadow / Paper / Live 共通実行モデル | `gpt-5.4` | `autotrade_phase1_skill_execution_model_v0_1` |
| A06 | `AutoTradePhase1_A06_EnginePocAnalyst_v0_1` | NautilusTrader / LEAN 評価軸、PoCシナリオ | `gpt-5.4` | `autotrade_phase1_skill_official_research_v0_1`, `autotrade_phase1_skill_poc_design_v0_1` |
| A07 | `AutoTradePhase1_A07_AdapterArchitect_v0_1` | Broker Adapter、Market Data Adapterの境界設計 | `gpt-5.4` | `autotrade_phase1_skill_adapter_boundary_v0_1` |
| A08 | `AutoTradePhase1_A08_RiskAccountArchitect_v0_1` | Portfolio、Risk、Account責務境界 | `gpt-5.4` | `autotrade_phase1_skill_risk_account_design_v0_1` |
| A09 | `AutoTradePhase1_A09_OpsSecurityArchitect_v0_1` | 監視、Secrets、環境分離、安全停止 | `gpt-5.4` | `autotrade_phase1_skill_ops_security_v0_1` |
| A10 | `AutoTradePhase1_A10_QaArchitect_v0_1` | テスト戦略、品質Gate、レビュー基準 | `gpt-5.4` | `autotrade_phase1_skill_test_strategy_v0_1` |
| A11 | `AutoTradePhase1_A11_HtmlDocumentEngineer_v0_1` | HTMLテンプレート、CSS、可読性、リンク整備 | `gpt-5.1` | `autotrade_phase1_skill_html_doc_writer_v0_1` |
| A12 | `AutoTradePhase1_A12_ConsistencyReviewer_v0_1` | 用語、ID、設計書間矛盾、追跡性レビュー | `gpt-5.4` | `autotrade_phase1_skill_design_reviewer_v0_1` |
| A13 | `AutoTradePhase1_A13_RedTeamReviewer_v0_1` | 安全性、運用リスク、過剰固定、未知情報の監査 | `gpt-5.4` | `autotrade_phase1_skill_red_team_review_v0_1` |
| A14 | `AutoTradePhase1_A14_RevisionIntegrator_v0_1` | レビュー反映、最終版作成、変更履歴整備 | `gpt-5.4` | `autotrade_phase1_skill_revision_integrator_v0_1` |

---

## 6. 作成するSkill群

P1-00で、次のSkill群をローカルに作成する。Skillは、AIエージェントへ渡す作業規約として扱う。

| Skill完全名 | 目的 |
|---|---|
| `autotrade_phase1_skill_orchestration_v0_1` | ステップDAG、並列化、成果物依存、Gate管理 |
| `autotrade_phase1_skill_source_reader_v0_1` | 要件定義、Phase方針、既存第0段階成果物の読み取り規約 |
| `autotrade_phase1_skill_traceability_v0_1` | 要件ID、設計判断ID、未確定事項ID、成果物IDの追跡規約 |
| `autotrade_phase1_skill_official_research_v0_1` | 外部仕様調査時の一次情報優先、URL、取得日、根拠管理 |
| `autotrade_phase1_skill_html_doc_writer_v0_1` | HTML設計書テンプレート、CSS、目次、表、相互リンク規約 |
| `autotrade_phase1_skill_architecture_writer_v0_1` | 全体構成、モジュール責務、依存方向の設計規約 |
| `autotrade_phase1_skill_domain_modeling_v0_1` | Entity、Value Object、Event、Command、State、ID、Timeの整理規約 |
| `autotrade_phase1_skill_strategy_design_v0_1` | Strategy Plugin、Turtle原典再現、現代版比較軸の設計規約 |
| `autotrade_phase1_skill_golden_test_v0_1` | N、Donchian、Unit、Stop、Pyramiding等のGolden test設計規約 |
| `autotrade_phase1_skill_adapter_boundary_v0_1` | Broker / Market Data依存を閉じ込める境界設計規約 |
| `autotrade_phase1_skill_execution_model_v0_1` | Backtest / Shadow / Paper / Live 共通実行モデル設計規約 |
| `autotrade_phase1_skill_poc_design_v0_1` | 取引エンジンPoCの評価軸、検証シナリオ、採点規約 |
| `autotrade_phase1_skill_risk_account_design_v0_1` | Portfolio / Risk / Account / OMSの責務分離規約 |
| `autotrade_phase1_skill_ops_security_v0_1` | 監視、通知、Secrets、安全停止、障害対応の設計規約 |
| `autotrade_phase1_skill_test_strategy_v0_1` | テスト分類、品質Gate、レビュー観点、完了条件の規約 |
| `autotrade_phase1_skill_design_reviewer_v0_1` | 設計書レビューのチェックリストと指摘フォーマット |
| `autotrade_phase1_skill_red_team_review_v0_1` | Fail-closed、安全性、運用事故、未確定事項の批判的監査 |
| `autotrade_phase1_skill_revision_integrator_v0_1` | レビュー指摘の反映、差分記録、最終版統合規約 |

---

## 7. オーケストレータ方針

`AutoTradePhase1_Orchestrator_v0_1` は、次を実施する。

- P1-00で実行基盤を作る。
- 各ステップの入力、出力、担当エージェント、使用Skill、モデルを固定する。
- 調査、ドラフト、レビュー、修正を同一ステップ内で完結させる。
- 設計書間で用語、ID、責務境界が矛盾した場合は統合レビューで差し戻す。
- UnknownをPassにしない。
- Phase 1で詳細化しすぎる項目は、詳細設計バックログへ移す。
- 外部サービスやライブラリを扱う場合は公式一次情報と確認日を残す。
- HTML成果物には、概要、前提、非目的、設計判断、未確定事項、後続Phaseへの引き継ぎを含める。

---

## 8. 共通プロンプトヘッダー

各ステップのプロンプトは、次のヘッダーを先頭に付ける。

```text
ステップID: <ステップID>
ロール: <ロール名>
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: <AutoTradePhase1_Axx_<role>_v0_1>
使用モデル: <モデル名>
使用Skill完全名: <autotrade_phase1_skill_*_v0_1一覧>

共通ルール:
- このプロンプトで使用してよいAI部品は、上記の完全名で指定されたオーケストレータ、サブエージェント、Skillだけである。
- 既存のSkill、既存のサブエージェント、既存のオーケストレータを推測で使用しない。
- 指定された完全名のAI部品が存在しない場合、代替実行せず、不足部品名を報告して停止する。ただしP1-00は不足部品を作成する。
- 出力は日本語で作成する。
- 正式な設計書はHTML形式で作成する。
- HTMLは単体で読める構成にし、見出し、目次、表、設計判断ID、未確定事項IDを含める。
- 参照元ファイルの内容を優先する。
- 外部仕様を確認する場合は公式一次情報を優先し、URL、取得日、要約を残す。
- UnknownをPassにしない。
- 投資助言、売買推奨、特定商品の推奨にならない表現にする。
- Phase 1で詳細化しすぎる内容は、詳細設計バックログへ移す。
- すべての成果物に作成日、文書状態、入力、出力、残課題を記載する。
```

---

## 9. 実行ステップ

### P1-00 実行基盤、サブエージェント、Skill、オーケストレータ作成

目的: Phase 1の設計書作成を機械的に進めるための実行基盤を作る。

入力:

- `plan/自動トレードシステム_要件定義書.md`
- `plan/Phase分割と設計書整備方針_v0.1_2026-08-02.md`
- 本計画書

出力:

- `doc/phase1/00_実行基盤/00_Phase1オーケストレータ仕様.html`
- `doc/phase1/00_実行基盤/00_サブエージェント定義.html`
- `doc/phase1/00_実行基盤/00_Skill定義.html`
- `doc/phase1/00_実行基盤/00_HTML設計書テンプレート.html`
- `doc/phase1/00_実行基盤/00_レビュー観点チェックリスト.html`
- `plan/phase1/ログ/00_プロンプト実行ログ.csv`

プロンプト:

```text
ステップID: P1-00
ロール: Phase 1 実行基盤オーケストレーター
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A00_Orchestrator_v0_1, AutoTradePhase1_A11_HtmlDocumentEngineer_v0_1, AutoTradePhase1_A12_ConsistencyReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_orchestration_v0_1, autotrade_phase1_skill_html_doc_writer_v0_1, autotrade_phase1_skill_design_reviewer_v0_1
発火制御:
- このステップで作成予定の完全名を持つAI部品だけを作成・使用する。
- 既存のSkill、サブエージェント、オーケストレータを推測で起動しない。
- 既存名と衝突する場合は、既存部品を流用せず、衝突として報告する。

タスク:
Phase 1で各設計書を作成するための実行基盤を作成してください。

作成するもの:
1. サブエージェント定義
2. Skill定義
3. オーケストレータ仕様
4. HTML設計書テンプレート
5. レビュー観点チェックリスト
6. プロンプト実行ログ形式

必須要件:
- 各サブエージェントに、責務、入力、出力、使用Skill、推奨LLMモデルを割り当てる。
- 基本フローは、調査、ドキュメント作成、レビュー、レビュー反映修正、統合とする。
- 並列実行できる設計書と、依存関係上シーケンシャルにする設計書を分ける。
- HTMLテンプレートには、文書状態、目次、設計判断、未確定事項、要件追跡、レビュー履歴、後続Phase引き継ぎを含める。
- 新規作成または移動したHTML成果物は、同じステップ内で `doc/index.html` にリンクを追加する。
- Phase 1で詳細化しすぎる項目を検知した場合、詳細設計バックログへ送るルールを定義する。

完了条件:
- P1-01以降のエージェントが、作成された基盤だけを見て実行を開始できること。
```

### P1-00B 実体作成と検証

目的: P1-00で作成済みの仕様定義に従い、Phase 1専用のSkill本体、サブエージェント本体、オーケストレータ本体を作成し、P1-01以降が参照できることを検証する。

入力:

- `doc/phase1/00_実行基盤/00_Phase1オーケストレータ仕様.html`
- `doc/phase1/00_実行基盤/00_サブエージェント定義.html`
- `doc/phase1/00_実行基盤/00_Skill定義.html`
- `doc/phase1/00_実行基盤/00_HTML設計書テンプレート.html`
- `doc/phase1/00_実行基盤/00_レビュー観点チェックリスト.html`

出力:

- `.codex/orchestrators/AutoTradePhase1_Orchestrator_v0_1.json`
- `.codex/agents/AutoTradePhase1_A00_Orchestrator_v0_1.json`
- `.codex/agents/AutoTradePhase1_A01_RequirementsCurator_v0_1.json`
- `.codex/agents/AutoTradePhase1_A02_SystemArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A03_DomainArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A04_StrategyArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A05_ExecutionModelArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A06_EnginePocAnalyst_v0_1.json`
- `.codex/agents/AutoTradePhase1_A07_AdapterArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A08_RiskAccountArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A09_OpsSecurityArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A10_QaArchitect_v0_1.json`
- `.codex/agents/AutoTradePhase1_A11_HtmlDocumentEngineer_v0_1.json`
- `.codex/agents/AutoTradePhase1_A12_ConsistencyReviewer_v0_1.json`
- `.codex/agents/AutoTradePhase1_A13_RedTeamReviewer_v0_1.json`
- `.codex/agents/AutoTradePhase1_A14_RevisionIntegrator_v0_1.json`
- `.codex/skills/autotrade_phase1_skill_orchestration_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_source_reader_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_traceability_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_official_research_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_html_doc_writer_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_architecture_writer_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_domain_modeling_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_strategy_design_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_golden_test_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_adapter_boundary_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_execution_model_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_poc_design_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_risk_account_design_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_ops_security_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_test_strategy_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_design_reviewer_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_red_team_review_v0_1/SKILL.md`
- `.codex/skills/autotrade_phase1_skill_revision_integrator_v0_1/SKILL.md`
- `doc/phase1/00_実行基盤/00_実行基盤検証結果.html`

プロンプト:

```text
ステップID: P1-00B
ロール: Phase 1 実体作成・検証オーケストレーター
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A00_Orchestrator_v0_1, AutoTradePhase1_A11_HtmlDocumentEngineer_v0_1, AutoTradePhase1_A12_ConsistencyReviewer_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_phase1_skill_orchestration_v0_1, autotrade_phase1_skill_html_doc_writer_v0_1, autotrade_phase1_skill_design_reviewer_v0_1
発火制御:
- このステップで使用してよいAI部品は、上記の完全名で指定した作成対象だけである。
- 既存のSkill、サブエージェント、オーケストレータを推測で起動しない。
- 既存名と衝突する場合は、既存部品を流用せず、衝突として報告する。
- 実行環境に正式登録APIがある場合は登録する。登録APIがない場合は、既存プロジェクト形式に合わせた機械実行用定義ファイルとして作成する。

タスク:
P1-00で作成済みの仕様定義に従い、Phase 1専用のSkill本体、サブエージェント本体、オーケストレータ本体を一気に作成し、検証してください。

作成するもの:
1. `.codex/skills/` 配下に、`autotrade_phase1_skill_*_v0_1` の各Skill本体を作成する。
2. `.codex/agents/` 配下に、`AutoTradePhase1_A00_..._v0_1` から `AutoTradePhase1_A14_..._v0_1` までの各サブエージェント本体を作成する。
3. `.codex/orchestrators/` 配下に、`AutoTradePhase1_Orchestrator_v0_1` のオーケストレータ本体を作成する。
4. 必要に応じて `.codex/config.json` にPhase 1オーケストレータを追加する。ただし既存default_orchestratorは変更しない。
5. `doc/phase1/00_実行基盤/00_実行基盤検証結果.html` を作成する。

検証:
- 全Skill本体が存在し、Skill完全名、目的、入力、出力、禁止事項、品質チェックを含むこと。
- 全サブエージェント本体が存在し、完全名、モデル、Skill、責務、入力、出力、境界を含むこと。
- オーケストレータ本体が存在し、P1-01以降のDAG、使用エージェント、Human Gate、発火制御を含むこと。
- 既存Skill、既存サブエージェント、既存オーケストレータの名前を流用していないこと。
- P1-01以降のプロンプトが、作成済みの完全名を参照できること。

完了条件:
- 実体作成と検証が完了し、H1-0承認へ進めること。
```

### P1-01 要件抽出と追跡マトリクス作成

目的: 要件定義書とPhase方針から、Phase 1で扱う要件、扱わない詳細、後続Phaseへの引き継ぎを切り分ける。

出力:

- `doc/phase1/01_要件追跡/01_Phase1スコープ定義.html`
- `doc/phase1/01_要件追跡/01_要件追跡マトリクス.html`
- `doc/phase1/01_要件追跡/01_未確定事項台帳.html`

プロンプト:

```text
ステップID: P1-01
ロール: 要件追跡キュレーター
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A01_RequirementsCurator_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_source_reader_v0_1, autotrade_phase1_skill_traceability_v0_1, autotrade_phase1_skill_html_doc_writer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
参照ドキュメントを読み、Phase 1で設計対象にする要件、Phase 1では詳細化しない要件、Phase 2以降へ送る詳細設計項目を分類してください。

入力:
- plan/自動トレードシステム_要件定義書.md
- plan/Phase分割と設計書整備方針_v0.1_2026-08-02.md

作業:
1. Q1からQ30、OD-01からOD-08、Phase方針の項目を抽出する。
2. 各項目に追跡IDを付与する。
3. Phase 1成果物D01からD20のどの設計書で扱うかを対応付ける。
4. Phase 1で固定する判断と、後続Phaseで詳細化する判断を分ける。
5. UnknownをPassにせず、未確定事項として台帳化する。

レビュー:
- A12が設計書の漏れ、ID重複、Phase 1スコープ逸脱をレビューする。
- 指摘を反映して最終HTMLを更新する。

完了条件:
- 以降の全設計書が参照できる要件追跡マトリクスが完成していること。
```

### P1-02 HTMLテンプレート適用と成果物インデックス作成

目的: すべてのHTML設計書の共通構造、見た目、相互リンクを固定し、`doc/index.html` から全HTMLへ到達できる導線を作る。

出力:

- `doc/index.html`
- `doc/phase1/00_実行基盤/00_HTMLスタイルガイド.html`

プロンプト:

```text
ステップID: P1-02
ロール: HTML設計書エンジニア
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A11_HtmlDocumentEngineer_v0_1
使用モデル: gpt-5.1
使用Skill完全名: autotrade_phase1_skill_html_doc_writer_v0_1, autotrade_phase1_skill_traceability_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Phase 1のすべてのHTML設計書に適用するスタイルガイドと成果物インデックスを作成してください。

必須要件:
- 各HTMLは単体で読めるようにする。
- CSSは原則としてHTML内に埋め込む。
- 外部CDNに依存しない。
- 目次、要約、入力、設計判断、未確定事項、レビュー履歴、関連文書リンクを含める。
- `doc/index.html` から、Phase 1で作成した全HTML成果物へリンクで直接到達できるようにする。
- 長文でも読みやすいよう、表、折りたたみ、アンカーリンクを使う。
- スマートフォン表示よりも、PCでの設計レビュー可読性を優先する。

レビュー:
- A12が全設計書で使える構造か確認する。

完了条件:
- 後続ステップが同じHTMLテンプレートを使えること。
```

### P1-03 全体アーキテクチャとドメイン分割設計

目的: システムの大枠、責務分離、依存方向を固定する。

出力:

- `doc/phase1/02_全体設計/02_システム全体構成設計書.html`
- `doc/phase1/03_ドメイン設計/03_ドメイン分割設計書.html`
- `doc/phase1/03_ドメイン設計/03_モジュール責務データフロー設計書.html`

プロンプト:

```text
ステップID: P1-03
ロール: 全体アーキテクト
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A02_SystemArchitect_v0_1, AutoTradePhase1_A03_DomainArchitect_v0_1
使用モデル: gpt-5.5
使用Skill完全名: autotrade_phase1_skill_architecture_writer_v0_1, autotrade_phase1_skill_domain_modeling_v0_1, autotrade_phase1_skill_html_doc_writer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
タートルズ・トレンドフォロー自動売買システムの全体アーキテクチャ、ドメイン分割、モジュール責務、データフローを設計してください。

必須論点:
- 研究用コードと本番運用コードの境界
- モジュラーモノリス、イベント駆動、アダプター方式の採用理由
- Data Ingestion、Raw Store、Normalization、Catalog、Event Engine、Strategy Plugin、Risk、OMS、Broker Adapter、Reconciliation、Monitoringの責務
- Strategyが担当する責務と、担当しない責務
- Backtest / Shadow / Paper / Live で共通化する部分
- Broker依存、Market Data依存を閉じ込める境界
- 後続Phaseで詳細化する項目

レビュー:
- A12が設計書間の整合性をレビューする。
- A13が密結合、安全停止漏れ、Broker依存漏れ、Phase 1での過剰詳細化をレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- 後続設計書が参照するドメイン境界と依存方向が明確であること。
```

### P1-04 共通ドメインモデル、イベント、注文、口座、ID、時系列設計

目的: BacktestからLiveまで共通に扱う最小ドメインモデルを固定する。

出力:

- `doc/phase1/04_共通モデル/04_共通ドメインモデル設計書.html`
- `doc/phase1/04_共通モデル/04_イベント注文口座ID時系列設計書.html`

プロンプト:

```text
ステップID: P1-04
ロール: 共通ドメインモデル設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A03_DomainArchitect_v0_1, AutoTradePhase1_A05_ExecutionModelArchitect_v0_1, AutoTradePhase1_A08_RiskAccountArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_domain_modeling_v0_1, autotrade_phase1_skill_execution_model_v0_1, autotrade_phase1_skill_risk_account_design_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Backtest / Shadow / Paper / Live で共通に使うドメインモデルを設計してください。実装クラスの詳細ではなく、概念モデル、状態、イベント、識別子、時系列の意味を固定してください。

必須論点:
- MarketEvent、SignalEvent、OrderIntent、Order、Fill、Position、AccountSnapshot、RiskSnapshot、TimerEvent、HealthEvent
- 注文ライフサイクルの標準状態
- client order id、event id、run id、strategy id、instrument idの命名方針
- UTC、取引所現地時刻、営業日、バー確定時刻の扱い
- 順不同イベント、重複イベント、再起動後復旧に必要な最低情報
- 約定、口座、ポジションの正本管理方針
- Phase 4以降で詳細化する注文例外パターン

レビュー:
- A12が用語とIDの一貫性をレビューする。
- A13が再現性、監査証跡、障害復旧の観点でレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- Strategy、OMS、Risk、Adapterの各設計が同じモデルを参照できること。
```

### P1-05 Strategy Plugin InterfaceとTurtle Golden test設計

目的: 戦略ロジックを差し替え可能にし、原典再現と現代版比較のテスト基準を固定する。

出力:

- `doc/phase1/05_戦略設計/05_Strategy_Plugin_Interface設計書.html`
- `doc/phase1/05_戦略設計/05_Turtle_Golden_test設計書.html`

プロンプト:

```text
ステップID: P1-05
ロール: Strategy設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A04_StrategyArchitect_v0_1, AutoTradePhase1_A10_QaArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_strategy_design_v0_1, autotrade_phase1_skill_golden_test_v0_1, autotrade_phase1_skill_test_strategy_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Strategy Plugin Interfaceと、タートルズ戦略のGolden test設計を作成してください。

必須論点:
- initialize、restore、on_market_event、on_order_event、on_account_event、on_timer、emit_intents、snapshot、health
- Strategyが出力するOrderIntentまたはTargetPositionの最低項目
- Strategy Configの主要項目
- 原典 System 1、System 2、現代版候補を比較可能にする設計
- N、True Range、Donchian Channel、0.5N追加、2N Stop、勝ちブレイクフィルター、4/6/10/12 Unit上限
- intraday breakoutと終値確認Entryの比較軸
- Strategyが担当しない責務
- Golden testに必要な固定入力、期待出力、許容誤差、禁止事項

レビュー:
- A12が要件追跡と用語整合をレビューする。
- A13が過剰最適化、Look-ahead、Backtest専用設計化をレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- Phase 3でStrategyとBacktestを実装する前提仕様として使えること。
```

### P1-06 Adapter境界設計

目的: BrokerとMarket Dataの依存を閉じ込め、実API変更に強い境界を固定する。

出力:

- `doc/phase1/06_アダプター境界/06_Adapter境界設計書.html`

プロンプト:

```text
ステップID: P1-06
ロール: Adapter境界設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A07_AdapterArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_adapter_boundary_v0_1, autotrade_phase1_skill_official_research_v0_1, autotrade_phase1_skill_html_doc_writer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Broker AdapterとMarket Data Adapterの境界設計を作成してください。IBKRやDatabentoの詳細API全仕様は固定せず、依存を閉じ込めるインターフェース境界を固定してください。

必須論点:
- Broker Adapterの責務と非責務
- Market Data Adapterの責務と非責務
- Backtest、Paper、Liveで共通化する入力イベント
- Broker側注文IDと内部client order idの対応
- Market DataのRaw、Normalized、Tradable、Signal、Derived、Experimentレイヤーとの関係
- 公式一次情報で確認が必要な外部制約のリスト
- Phase 2、Phase 4で詳細化するAPI仕様バックログ

レビュー:
- A12が全体構成、共通モデルとの整合性をレビューする。
- A13がBroker依存漏れ、Data Vendor依存漏れ、安全停止漏れをレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- Phase 2のMarket Data詳細設計、Phase 4のBroker詳細設計へ引き継げる境界が明確であること。
```

### P1-07 共通実行モデルと取引エンジンPoC評価設計

目的: Backtest / Shadow / Paper / Live の共通実行モデルと、NautilusTrader / LEAN等のPoC評価軸を固定する。

出力:

- `doc/phase1/07_実行モデル/07_共通実行モデル設計書.html`
- `doc/phase1/07_実行モデル/07_取引エンジンPoC評価設計書.html`

プロンプト:

```text
ステップID: P1-07
ロール: 実行モデル・取引エンジンPoC設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A05_ExecutionModelArchitect_v0_1, AutoTradePhase1_A06_EnginePocAnalyst_v0_1, AutoTradePhase1_A10_QaArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_execution_model_v0_1, autotrade_phase1_skill_poc_design_v0_1, autotrade_phase1_skill_official_research_v0_1, autotrade_phase1_skill_test_strategy_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Backtest / Shadow / Paper / Live の共通実行モデルと、取引エンジンPoCの評価設計を作成してください。

必須論点:
- 履歴イベントリプレイとリアルタイムイベント処理の共通化
- Backtestを証券会社内蔵バックテストに依存させない方針
- Shadow、Paper、Liveの差分をAdapterと環境で吸収する方針
- 実験manifest、run id、データバージョン、設定バージョン
- NautilusTrader、LEAN / QuantConnect系の評価観点
- PoCシナリオ: 1市場20日breakout、1分足リプレイ、Entry/Add/Stop/Exit、部分約定、再起動復旧、IBKR Paper接続、Open order/Fill/Position再同期、Heartbeat通知
- 採点表とHuman Gate
- 取引エンジン最終決定をPhase 1で行うための証拠条件

レビュー:
- A12が要件定義との対応をレビューする。
- A13がPoCで実資金機能へ踏み込みすぎていないか、安全面をレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- OD-02 取引エンジン最終決定に必要なPoC基準が明確であること。
```

### P1-08 Portfolio / Risk / Account責務境界設計

目的: 戦略、口座管理、リスク管理、OMSの責務境界を固定する。

出力:

- `doc/phase1/08_リスク口座管理/08_Risk_Account責務境界設計書.html`

プロンプト:

```text
ステップID: P1-08
ロール: Portfolio / Risk / Account設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A08_RiskAccountArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_risk_account_design_v0_1, autotrade_phase1_skill_domain_modeling_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Portfolio、Risk、Account、OMS、Strategyの責務境界を設計してください。

必須論点:
- StrategyがUnit、シグナル、OrderIntentを出す範囲
- Portfolioが資産配分、相関集中、ポジション上限を扱う範囲
- AccountがCash、Margin、NAV、入出金を扱う範囲
- Riskが日次損失、最大DD、注文数量、Kill Switch中の新規注文禁止を扱う範囲
- OMSが注文状態遷移、重複防止、Cancel / Replace、再同期を扱う範囲
- 1Nリスク、年率ボラ目標10%、最大DD15%の扱い
- Paper前、Live前に最終決定すべきリスク項目

レビュー:
- A12が共通モデル、Strategy設計、Adapter設計との整合性をレビューする。
- A13がFail-closedと誤発注リスクの観点でレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- Phase 5で詳細設計する前提となる責務境界が明確であること。
```

### P1-09 非機能要件、監視、Secrets、セキュリティ、安全停止設計

目的: 運用品質と安全性の最小基準をPhase 1で固定する。

出力:

- `doc/phase1/09_非機能要件/09_非機能要件設計書.html`
- `doc/phase1/09_非機能要件/09_設定Secrets環境分離設計書.html`
- `doc/phase1/09_非機能要件/09_監視監査設計書.html`
- `doc/phase1/09_非機能要件/09_セキュリティ安全停止設計書.html`

プロンプト:

```text
ステップID: P1-09
ロール: 運用・セキュリティ設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A09_OpsSecurityArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_ops_security_v0_1, autotrade_phase1_skill_html_doc_writer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
非機能要件、設定、Secrets、環境分離、監視、監査証跡、メトリクス、アラート、安全停止方針を設計してください。

必須論点:
- Windows研究環境と東京クラウドVM環境の分離
- Backtest / Shadow / Paper / Live の設定分離
- Secret Manager利用、Paper secretとLive secretの分離、Gitやログへの秘匿情報混入禁止
- Market data、Broker接続、Strategy heartbeat、Event queue、Position/Order不整合、NAV/PnL/DD、バックアップ成否の監視
- INFO、WARNING、CRITICAL、EMERGENCYの通知レベル
- 新規注文停止、一括Cancel、戦略停止、Bot停止、Broker GUIによる最終介入
- Fail-closed方針
- RPO / RTOの目標
- Phase 6、Phase 7で詳細化するRunbook項目

レビュー:
- A12が要件追跡と他設計書との整合性をレビューする。
- A13が安全停止、手動介入、監査ログ、秘密情報漏洩リスクを重点レビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- 安全停止と監査証跡が後付けにならない最低基準が明文化されていること。
```

### P1-10 テスト戦略・品質Gate設計

目的: 後続Phaseの実装品質を判定するテスト戦略とGateを固定する。

出力:

- `doc/phase1/10_テスト品質/10_テスト戦略品質Gate設計書.html`

プロンプト:

```text
ステップID: P1-10
ロール: QA設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A10_QaArchitect_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_test_strategy_v0_1, autotrade_phase1_skill_golden_test_v0_1, autotrade_phase1_skill_design_reviewer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Phase 2以降の実装を安全に進めるため、テスト戦略と品質Gateを設計してください。

必須論点:
- Unit test、Golden test、Integration test、Replay test、Reconciliation test、Failure injection test、Operational rehearsal
- N、True Range、Donchian、System 1勝ちブレイクフィルター、0.5N追加、2N Stop、4/6/10/12 Unit上限、Gap時の保守的約定、ロール損益、データ異常時fail-closed
- Look-ahead、Survivorship bias、Data snooping、候補別パラメータ最適化の防止
- BacktestからShadow、ShadowからPaper、Paperから少額Live、少額Liveから本番Liveの品質Gate
- Human Gateと機械Gateの分離
- テスト証跡と再現性

レビュー:
- A12が全設計書に品質Gateが対応しているか確認する。
- A13がLive前に見逃すと危険なGate漏れをレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- 後続Phaseの完了判定が曖昧にならないこと。
```

### P1-11 Phase 2以降の詳細設計バックログとロードマップ作成

目的: Phase 1で固定しない詳細設計を、後続Phaseへ明確に引き継ぐ。

出力:

- `doc/phase1/11_ロードマップ/11_詳細設計バックログ.html`
- `doc/phase1/11_ロードマップ/11_Phase2以降ロードマップ.html`

プロンプト:

```text
ステップID: P1-11
ロール: ロードマップ設計者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A00_Orchestrator_v0_1, AutoTradePhase1_A01_RequirementsCurator_v0_1, AutoTradePhase1_A12_ConsistencyReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_orchestration_v0_1, autotrade_phase1_skill_traceability_v0_1, autotrade_phase1_skill_design_reviewer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
Phase 1で詳細化しない項目を、Phase 2以降の詳細設計バックログとして整理してください。

必須論点:
- Phase 2 Market Data基盤で詳細化する設計書
- Phase 3 Strategy / Backtest基盤で詳細化する設計書
- Phase 4 Broker / Paper Trading基盤で詳細化する設計書
- Phase 5 Portfolio / Risk / Account管理で詳細化する設計書
- Phase 6 Forward Test運用で詳細化する設計書
- Phase 7 Live移行準備で詳細化する設計書
- Phase 8 Live運用で継続更新する設計書
- 各Phase開始前の入力条件、作成成果物、完了Gate
- 未確定事項OD-01からOD-08の決定タイミング

レビュー:
- A12が設計書間の引き継ぎ漏れをレビューする。
- A13が危険な先送り、過剰な先行固定をレビューする。
- 指摘を反映してHTMLを更新する。

完了条件:
- Phase 2以降で何をいつ詳細化するかが追跡可能であること。
```

### P1-12 統合レビューとレッドチーム監査

目的: Phase 1成果物全体を横断し、矛盾、漏れ、安全性リスク、実装不能な設計を検出する。

出力:

- `doc/phase1/12_統合レビュー/12_統合レビュー結果.html`
- `doc/phase1/12_統合レビュー/12_レッドチーム監査結果.html`
- `doc/phase1/12_統合レビュー/12_修正指示一覧.html`

プロンプト:

```text
ステップID: P1-12
ロール: 統合レビュー・レッドチーム監査者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A12_ConsistencyReviewer_v0_1, AutoTradePhase1_A13_RedTeamReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_design_reviewer_v0_1, autotrade_phase1_skill_red_team_review_v0_1, autotrade_phase1_skill_traceability_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
P1-01からP1-11までの全HTML設計書を横断レビューしてください。

レビュー観点:
1. 要件追跡漏れ
2. 設計書間の用語不一致
3. 責務境界の矛盾
4. Broker依存、Market Data依存の漏れ
5. Backtest専用設計がLiveへ流用できないリスク
6. Strategyと基盤の密結合
7. Risk、OMS、Account、Portfolioの責務混線
8. 監査ログ、再現性、run id、event idの不足
9. Secrets漏洩リスク
10. Fail-closed、安全停止、手動介入の不足
11. Phase 1で詳細化しすぎている項目
12. Phase 2以降へ先送りしすぎている危険項目

出力形式:
- 指摘ID
- 重要度
- 対象設計書
- 該当箇所
- 問題内容
- 修正方針
- Human Gate要否

完了条件:
- P1-13が修正反映を開始できる粒度で指摘が整理されていること。
```

### P1-13 レビュー反映、最終版統合、Phase 1完了判定

目的: レビュー指摘を反映し、Phase 1成果物をHuman Gateへ提出できる状態にする。

出力:

- 修正済みのD01からD19
- `doc/phase1/12_統合レビュー/12_Phase1完了判定とPhase2移行承認書.html`
- `doc/phase1/12_統合レビュー/12_レビュー反映履歴.html`

プロンプト:

```text
ステップID: P1-13
ロール: 修正統合者
使用オーケストレータ完全名: AutoTradePhase1_Orchestrator_v0_1
担当サブエージェント完全名: AutoTradePhase1_A14_RevisionIntegrator_v0_1, AutoTradePhase1_A00_Orchestrator_v0_1, AutoTradePhase1_A12_ConsistencyReviewer_v0_1
使用モデル: gpt-5.4
使用Skill完全名: autotrade_phase1_skill_revision_integrator_v0_1, autotrade_phase1_skill_orchestration_v0_1, autotrade_phase1_skill_design_reviewer_v0_1
発火制御:
- 上記の完全名で指定したAI部品だけを使用する。
- 指定AI部品が存在しない場合は、既存Skill等で代替せず、P1-00の再実行が必要であると報告して停止する。

タスク:
P1-12の統合レビューとレッドチーム監査の指摘を反映し、Phase 1の最終版成果物を作成してください。

作業:
1. 指摘ごとに、採用、部分採用、保留、却下を判断する。
2. 採用・部分採用の指摘を対象HTML設計書へ反映する。
3. 保留・却下の指摘には理由を記録する。
4. すべての設計書の設計判断ID、未確定事項ID、関連リンクを更新する。
5. Phase 1完了判定とPhase 2移行承認書を作成する。

Phase 1完了Gate:
- D01からD20が存在する。
- 要件追跡マトリクスで未対応のPhase 1必須項目がない。
- Strategy Interface、Adapter境界、共通実行モデル、Risk/Account責務境界が互いに矛盾していない。
- Phase 1で固定しない詳細は、詳細設計バックログへ移されている。
- 取引エンジンPoCの評価基準が明確である。
- 安全停止、Secrets、監査ログ、再現性の最低基準が明記されている。
- Phase 2へ進むためのHuman Gate項目が明確である。

完了条件:
- 人間レビュー担当者が、Phase 1完了可否とPhase 2移行可否を判断できること。
```

---

## 10. 並列化方針

P1-00、P1-01、P1-02は順番に実施する。その後、次の並列実行を許可する。

| 並列グループ | 対象ステップ | 依存 |
|---|---|---|
| G1 | P1-03、P1-04 | P1-01、P1-02 |
| G2 | P1-05、P1-06、P1-07 | P1-03、P1-04のドラフト |
| G3 | P1-08、P1-09、P1-10 | P1-03からP1-07のドラフト |
| G4 | P1-11 | P1-03からP1-10のレビュー済みドラフト |
| G5 | P1-12 | P1-01からP1-11の全成果物 |
| G6 | P1-13 | P1-12 |

P1-05、P1-06、P1-07は相互依存が強いため、各ドラフト完了時点でA00が中間整合レビューを行う。

---

## 11. Human Gate

| Gate | タイミング | 承認内容 |
|---|---|---|
| H1-0 | P1-00完了後 | サブエージェント、Skill、オーケストレータ、HTMLテンプレートの承認 |
| H1-1 | P1-01完了後 | Phase 1スコープと要件追跡マトリクスの承認 |
| H1-2 | P1-07完了後 | 取引エンジンPoC評価基準の承認 |
| H1-3 | P1-12完了後 | 統合レビュー指摘の修正方針承認 |
| H1-4 | P1-13完了後 | Phase 1完了、Phase 2移行承認 |

Human Gateで承認が必要な項目は、承認前に次のGateへ進めない。

---

## 12. Phase 1で作らない詳細設計

次はPhase 1で設計方針と境界だけを決め、詳細は後続Phaseへ分割する。

- Databento取得ジョブの全スケジュール、全APIパラメータ
- IBKR APIの全エンドポイント、全例外ハンドリング
- Backtest Engineの全クラス、全関数
- ロール規則の資産別最終仕様
- 注文状態遷移の全例外パターン
- Live運用Runbook全文
- Dashboard UIの細部
- 実資金運用パラメータの最終値

---

## 13. 完了条件

Phase 1は、次を満たしたときに完了とする。

- D01からD20のHTML成果物が揃っている。
- 要件定義書のPhase 1必須項目が追跡可能である。
- Phase 1で固定する判断と、Phase 2以降で詳細化する判断が分離されている。
- Strategy、Adapter、Execution Model、Risk、Account、OMSの責務境界が矛盾していない。
- Golden test設計が、Phase 3の実装へ引き継げる粒度になっている。
- 取引エンジンPoC評価基準が、OD-02の決定に使える粒度になっている。
- 安全停止、監査ログ、Secrets、環境分離、再現性の最低基準が明文化されている。
- Phase 2へ進むためのHuman Gateが承認されている。

---

## 14. 次アクション

1. P1-00を実行し、Phase 1実行基盤を作る。
2. H1-0で、サブエージェント、Skill、オーケストレータ、HTMLテンプレートを承認する。
3. P1-01で、要件追跡マトリクスを作成する。
4. P1-03以降を並列実行し、設計書群を作成する。
5. P1-12、P1-13で統合レビューと修正を行う。


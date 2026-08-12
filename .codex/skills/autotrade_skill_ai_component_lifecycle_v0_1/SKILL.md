---
name: autotrade_skill_ai_component_lifecycle_v0_1
description: Skill、サブエージェント、オーケストレータの作成・変更を進めるための汎用Skill。既存部品の再利用調査、必要最小限の新設または明示変更、関連HTML仕様書と共通ルールの追従更新を一連で行うときに使う。
---

# autotrade_skill_ai_component_lifecycle_v0_1

## 目的
AI実行基盤の部品追加や変更を、実体ファイルだけで終わらせず、再利用調査、実装、仕様更新、検証まで一貫して進める。

## 入力
- 変更対象または新設対象の要件
- `.codex/skills/`, `.codex/agents/`, `.codex/orchestrators/`, `.codex/config.json`
- `settings/ai_component_rules.md`
- `doc/ai_foundation/03` から `08`
- `AGENTS.md`, `README.md`, `doc/index.html`

## 出力
- 新規または更新された Skill / Agent / Orchestrator
- 追従更新された HTML仕様書、共通ルール、導線
- 再利用判断、変更理由、停止条件、残課題

## 標準フロー
1. 既存の汎用Skill、汎用Agent、汎用Orchestratorを調査し、再利用候補と不足責務を分ける。
2. 新設か変更かを明示し、対象の完全名、責務、境界条件、使用Skillを確定する。
3. Skill、Agent、Orchestratorの実体を作成または更新する。
4. `doc/ai_foundation/03` から `08`、`doc/index.html`、必要に応じて `AGENTS.md` と `README.md` を追従更新する。
5. JSON整合、リンク整合、参照整合を確認し、残課題があれば明記する。

## 実ランタイム起動契約（RDC-AI-COMPONENT-0.2）

AI部品の作成・変更依頼も、完全名を列挙するだけでは実行証拠にならない。ルート実行Agentは変更前に `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` を確認し、`AutoTradeComponentLifecycle_Orchestrator_v0_1` のJSON path、`model=gpt-5.6-terra`、変更範囲、入力、出力、明示されたAgents／Skillsを渡してCoordinatorを実spawnする。CoordinatorはPromptの全Agentを一体ずつspawnし、Agent JSONの固定modelをmodel引数へ渡してwaitする。

Orchestratorの `agents` map外でもPromptで完全名指定されたAgentを省略しない。各起動について、runtime backend、dispatch mode、親／子ID、JSON path、model、Skills、受付／完了status、出力参照、`independent`、`review_mode`をログへ保存する。spawn／waitや固定model受理ができない場合は、`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、理由、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を先に記録し、ルートが責務チェックリストを適用して継続する。起動不能を独立実行済みと表現しない。UnknownのPass、仕様追従欠落、Secret、default変更、Critical／High未解決は別のFail-closed停止条件である。

## 禁止事項
- 既存部品を推測で流用しない。
- 明示されていない部品名へ勝手にリネームしない。
- 新規作成時に既存名と衝突したまま上書きしない。
- 仕様書更新を省略しない。
- `default_orchestrator` を変更しない。
- UnknownをPassにしない。

## 品質チェック
- 再利用した既存部品と新設した部品の境界が説明されている。
- Skill、Agent、Orchestratorの完全名が全成果物で一致している。
- `doc/ai_foundation/03` から `06` が実体と整合している。
- `07` と `settings/ai_component_rules.md` が運用ルールを反映している。
- `08` に今回の追補検証結果が残っている。
- `doc/index.html` から新規HTMLへ到達できる。

## Phase依存パラメータ
- `step_id`
- `output_root`
- `artifact_index`
- `change_scope`

## 参照成果物
- `doc/ai_foundation/07_AI部品作成ルール.html`
- `doc/ai_foundation/11_AI部品作成更新AI部品仕様.html`
- `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html`

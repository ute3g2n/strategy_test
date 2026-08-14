# CTX-02 AI部品再利用・同期記録

- 計画: `CTXMAP-PLAN-001 v0.1`
- ステップ: `CTX-02`
- 基準HEAD: `5a96f1832ab15814d9262ee32489b672ab9df0e6`
- H0: 2026-08-14、ユーザーの「承認する。続けて」により承認済み
- 実行方針: `autotrade_skill_ai_component_lifecycle_v0_1` と `skill-creator`

## 1. 再利用判断

| 対象 | 判断 | 根拠 |
|---|---|---|
| `AutoTradeComponentLifecycle_Orchestrator_v0_1` | 再利用 | AI部品の作成・変更、既存部品調査、仕様同期、receiptを既に統制している。常時監視用Orchestratorは追加しない。 |
| `AutoTrade_A06_AiComponentEngineer_v0_1` | 再利用・責務追加 | A07/A08の新設、既存部品の最小変更、AI基盤HTML同期のCoordinatorとして維持する。manifest解析そのものは集約しない。 |
| `AutoTrade_A10_RequirementsCurator_v0_1` | 再利用 | CTXMAPの要件、境界、Unknown、追跡IDを整理する。 |
| `AutoTrade_A80_DocumentIntegrator_v0_1` | 再利用・完了条件追加 | HTML、index、レビュー履歴の統合に加え、文書差分をA07へ渡す責務を追加する。固定modelは変更しない。 |
| `AutoTrade_A90_DesignReviewer_v0_1` | 再利用・レビュー | A07/A08の責務、fail-closed、AI基盤同期をFindings firstで確認する。 |
| `autotrade_skill_html_doc_writer_v0_1` | 再利用・完了条件追加 | 新規／大幅変更文書をA07へ渡し、validator PASSまたはBLOCKEDを受領する。 |
| `autotrade_skill_design_doc_set_writer_v0_1` | 再利用・完了条件追加 | 文書セット内の各HTMLをA07へ1ファイル単位で渡す。 |
| `autotrade_skill_python_implementation_v0_1` / A120 | 再利用・完了条件追加 | 構造変更コードを決定的コードmanifest/index更新へ渡す。A07へ任意のソース全文を渡さない。 |
| Phase 1 `A07/A08` | 再利用しない | `frozen / legacy / phase1証跡`であり、汎用CTXMAP部品へ流用・上書きしない。 |

## 2. 新設した部品

1. `autotrade_skill_context_manifest_maintenance_v0_1`
2. `AutoTrade_A07_ContextManifestMaintainer_v0_1`
3. `autotrade_skill_context_routing_v0_1`
4. `AutoTrade_A08_ContextRouter_v0_1`

A07は文書1ファイルの`record_add`／`record_update`／`metadata_unchanged`／`blocked`をstrict JSONで返す。A08はvalidator済みmanifestと依頼文だけからprimary 1〜3件、supporting 0〜6件、JIT範囲、不足情報を返す。両者にネットワーク、Secret、任意path、Git書込み、本文全量保存を与えない。

## 3. 同期した既存導線

- `.codex/orchestrators/AutoTradeComponentLifecycle_Orchestrator_v0_1.json`
- `AutoTrade_A06_AiComponentEngineer_v0_1.json`
- `AutoTrade_A120_PythonImplementer_v0_1.json`
- `autotrade_skill_html_doc_writer_v0_1/SKILL.md`
- `autotrade_skill_design_doc_set_writer_v0_1/SKILL.md`
- `autotrade_skill_python_implementation_v0_1/SKILL.md`
- `settings/ai_component_rules.md`
- `AGENTS.md`
- `README.md`
- `doc/ai_foundation/03`〜`08`
- `doc/index.html`
- `doc/00_全Phase残課題Blocked統合台帳.html`

## 4. 検証結果と残留事項

- JSON parse: PASS（`.codex/config.json`、Orchestrator、Agents計50ファイル）。
- Skill frontmatter・500行上限: PASS（A07 Skill 73行、A08 Skill 58行）。
- Skill Creator `quick_validate.py`: BLOCKED。実行環境に`yaml`モジュールがなく、依存取得は行わなかった。PowerShellによるfrontmatter・行数検証へ縮退した。
- 名前衝突: PASS（Orchestrator／Agent 57件）。
- static map参照: PASS。A07/A08のJSONとprimary Skillのpathが存在する。
- `default_orchestrator`: `middle-school-explanation-orchestrator`のまま不変。
- A07/A08/A80固定model `gpt-5.1`: 現runtimeの利用可能modelにないため未起動。代替modelでの成功扱いはしていない。
- A90再レビュー試行: spawn後wait timeout、shutdown。独立レビュー完了とは扱わず、receiptへFallbackを記録する。

CTX-02は新規部品・同期と静的検証を完了条件へ進めるが、runtimeの独立closed-loopはFallback状態である。Critical／High、Unknown、H1未承認を解消したことを意味しない。

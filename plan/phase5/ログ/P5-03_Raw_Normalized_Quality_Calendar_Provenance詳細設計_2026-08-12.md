# P5-03 Raw / Normalized / Quality / Calendar / Provenance 詳細設計ログ

- Date: 2026-08-12 (Asia/Tokyo)
- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan / scope: `P5-PLAN-001` / design, read, HTML, log only
- State: `P5-03_COMPLETE_WITH_LOCAL_FALLBACK_SELF_REVIEW`

## 発火制御

`P5-H0=APPROVED` とP5-02完了を確認。P5-H1/P5-DATA-G1/P5-H2は未承認。DB、migration、repository、fixture、Application、UI、dependency、real Run、external I/O、Provider、Secret、external Data、cost、Coreは変更・実行していない。P4 metadata DBにData bodyを保存しない。

## Runtime dispatch receipt

rootでは `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` の実起動を確認した。Orchestratorは実spawn・wait完了した。一方、Coordinator内のchild runtimeは利用不能で、各childの個別spawn/waitはfallbackとなった。名前やJSON読込を起動証跡として扱っていない。

| orchestrator | JSON path | model | spawn | wait | agent_id | output_ref | fallback_reason | independent | review_mode |
|---|---|---|---|---|---|---|---|---|---|
| AutoTradeProject_ImplementationDesign_Orchestrator_v0_1 | `C:/project/strategy_test/.codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json` | gpt-5.6-terra | SPAWNED | COMPLETED | `019ff5a5-e463-7101-ae54-5441b098f192` | `agent://019ff5a5-e463-7101-ae54-5441b098f192/final` | Coordinator child runtime unavailable; child fallback recorded below | false | COORDINATOR_RECEIPT_WITH_CHILD_FALLBACK |

### Complete child receipt (exact required order)

| order | child | JSON path | model | spawn | wait | agent_id | output_ref | fallback_reason | independent | review_mode |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | A10 | `C:/project/strategy_test/.codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 2 | A20 | `C:/project/strategy_test/.codex/agents/AutoTrade_A20_ArchitectureDomainArchitect_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 3 | A30 | `C:/project/strategy_test/.codex/agents/AutoTrade_A30_StrategyQaArchitect_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS; map外Agentも未省略 | false | SELF_REVIEW_FALLBACK |
| 4 | A40 | `C:/project/strategy_test/.codex/agents/AutoTrade_A40_ExecutionEnginePocArchitect_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 5 | A50 | `C:/project/strategy_test/.codex/agents/AutoTrade_A50_AdapterArchitect_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 6 | A70 | `C:/project/strategy_test/.codex/agents/AutoTrade_A70_OpsSecurityArchitect_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS; map外Agentも未省略 | false | SELF_REVIEW_FALLBACK |
| 7 | A80 | `C:/project/strategy_test/.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json` | gpt-5.1 | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 8 | A82 | `C:/project/strategy_test/.codex/agents/AutoTrade_A82_ImplementationDetailDesigner_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 9 | A90 | `C:/project/strategy_test/.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |
| 10 | A91 | `C:/project/strategy_test/.codex/agents/AutoTrade_A91_ImplementationDetailReviewer_v0_1.json` | gpt-5.6-luna | UNAVAILABLE | UNAVAILABLE | N/A | N/A | RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS | false | SELF_REVIEW_FALLBACK |

## Local fallback responsibility checklist

| 観点 | 結果 |
|---|---|
| 要件・追跡 | P5-TR-002〜004とREQ-V2-0027〜0032を接続。 |
| Domain/Architecture | immutable Raw、versioned Normalized、Calendar/Roll分類、Quality stop、Manifest/Provenanceを分離。 |
| Strategy/QA | future、look-ahead、survivorshipをPASSにしない全テストを定義。 |
| Adapter/Ops | Provider/Secret/external I/Oを型境界外に置き、relative pathとhashだけを観測。 |
| 実装詳細 | モジュール、型、保存、正常/失敗フロー、擬似コード、P5-08/09入力を記述。 |
| レビュー | LOCAL SELF-REVIEWのみ。Critical=0、High=0、独立レビューなし。 |

## 成果物と検証

- `doc/phase5/02_データ詳細設計/03_Raw_Normalized_Quality_Calendar_Provenance詳細設計書.html`
- `doc/index.html`、Phase5計画HTML、統合台帳のP5-03状態・導線
- `git diff --check`、HTML相対リンク、Mermaid asset参照、境界語の静的確認を行う。

P5-04は本書を入力にする。P5-08/09はP5-DATA-G1、固定Runner、全Version/hash、Evidence root、host isolationが揃うまで開始しない。

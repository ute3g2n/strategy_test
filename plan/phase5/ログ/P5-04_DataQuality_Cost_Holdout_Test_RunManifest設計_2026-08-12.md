# P5-04 Data Quality / Cost / Holdout / Test / Run Manifest 設計ログ

- Date: 2026-08-12 (Asia/Tokyo)
- Phase / Step: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12` / `P5-04`
- Plan: `P5-PLAN-001`
- State: `P5-04_COMPLETE_WITH_LOCAL_FALLBACK_SELF_REVIEW`
- Timestamp: `2026-08-12T00:00:00+09:00`

## 発火制御

`P5-H0=APPROVED`、P5-02、P5-03完了を統合台帳と正式HTMLで確認した。P5-H1/P5-DATA-G1/P5-H2は未承認。設計・read・HTML・logだけを更新し、外部Data、Provider、Secret、費用、外部I/O、実測取得、実Run、依存、DB/migration/repository/fixture/Application/UI/Coreの変更は0件である。

## Runtime dispatch receipt

root receipt は実行コンテキストで受領済みであり、child runtime は公開されなかった。`multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` がツール一覧に存在しないため、作業前に `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`LOCAL_FALLBACK_NO_SUBAGENTS` を記録する。JSON読込・Skill読込・自己レビューをspawn証跡として扱わない。

| orchestrator | JSON path | model | spawn | wait | agent_id | output_ref | fallback_reason | independent | review_mode |
|---|---|---|---|---|---|---|---|---|---|
| AutoTradeProject_ImplementationDesign_Orchestrator_v0_1 | `C:/project/strategy_test/.codex/orchestrators/AutoTradeProject_ImplementationDesign_Orchestrator_v0_1.json` | gpt-5.6-terra | SPAWNED_BY_ROOT | COMPLETED_BY_ROOT | `019ff5a5-e463-7101-ae54-5441b098f192` | `agent://019ff5a5-e463-7101-ae54-5441b098f192/final` | child runtime unavailable; child fallback follows | false | COORDINATOR_RECEIPT_WITH_CHILD_FALLBACK |

### Child fallback receipt（指定順・8/8）

|order|agent|JSON path|model|spawn|wait|agent_id|output_ref|fallback_reason|independent|review_mode|
|---:|---|---|---|---|---|---|---|---|---|---|
|1|AutoTrade_A30_StrategyQaArchitect_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A30_StrategyQaArchitect_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS; agents map外でも未省略|false|SELF_REVIEW_FALLBACK|
|2|AutoTrade_A40_ExecutionEnginePocArchitect_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A40_ExecutionEnginePocArchitect_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS|false|SELF_REVIEW_FALLBACK|
|3|AutoTrade_A50_AdapterArchitect_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A50_AdapterArchitect_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS|false|SELF_REVIEW_FALLBACK|
|4|AutoTrade_A70_OpsSecurityArchitect_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A70_OpsSecurityArchitect_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS; agents map外でも未省略|false|SELF_REVIEW_FALLBACK|
|5|AutoTrade_A80_DocumentIntegrator_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json`|gpt-5.1|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS|false|SELF_REVIEW_FALLBACK|
|6|AutoTrade_A82_ImplementationDetailDesigner_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A82_ImplementationDetailDesigner_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS|false|SELF_REVIEW_FALLBACK|
|7|AutoTrade_A90_DesignReviewer_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS|false|SELF_REVIEW_FALLBACK|
|8|AutoTrade_A91_ImplementationDetailReviewer_v0_1|`C:/project/strategy_test/.codex/agents/AutoTrade_A91_ImplementationDetailReviewer_v0_1.json`|gpt-5.6-luna|UNAVAILABLE|UNAVAILABLE|N/A|N/A|RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS|false|SELF_REVIEW_FALLBACK|

## Fallback責務チェック

|観点|結果|
|---|---|
|Strategy/QA・Execution|as-of、look-ahead、survivorship、holdout再利用拒否、fixed replayをTEST-P5-DATA-IDに定義。|
|Adapter/Ops|Provider/Secret/外部I/Oを境界外に固定し、host outbound isolation UNKNOWNは停止。|
|実装詳細|型、保存境界、処理順、エラー、冪等性、Manifest、疑似コード、P5-06/08/09/H2接続を記載。|
|文書統合・レビュー|AF-D16のDD-01〜12、Mermaid、受渡し表、全テスト、index/台帳/計画同期をself-review。独立性=false。|

## 検証

- P5-02/P5-03のData contract、Raw/Normalized/Quality/Calendar/Provenanceを参照。
- 実測と固定仮定、P4 synthetic/fixed evidenceと実市場Evidenceを分離。
- Critical=0、High=0、外部I/O=0、未承認GateのPass=0、child receipt=8/8。
- 静的検証: `git diff --check`、HTMLのlocal Mermaid asset、相対リンク、TEST-P5-DATA-ID、Gate/Unknown文言を確認する。

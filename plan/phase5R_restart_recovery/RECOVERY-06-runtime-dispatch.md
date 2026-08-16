# RECOVERY-06 文書統合ランタイム起動証跡

- 実行日: 2026-08-16
- 要求されたOrchestrator: `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
- 要求されたAgent: A10、A80、A81、A90、A95
- 実行バックエンド: `multi_agent_v1`

`multi_agent_v1__spawn_agent` を実際に実行したが、`collab spawn failed: agent thread limit reached` で起動できなかった。`wait_agent` は起動対象がないため未実行である。独立Agentの文書レビュー済みとは扱わない。

| 対象 | 起動 | agent_id | independent | review_mode |
|---|---|---|---|---|
| AutoTradeProject_DesignDocSet_Orchestrator_v0_1 | FAILED: thread limit | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A10_RequirementsCurator_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A80_DocumentIntegrator_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A81_DesignDocSetWriter_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A90_DesignReviewer_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |

ルート担当が、要件・設計・手順書・完了判定・Index・統合台帳の保存先、状態名、対象外、Evidenceリンクを照合した。A95の管理用hashは計算していない。

安全・データ・再現性に関わる保護情報を除き、今回の計画は管理用hashを作らない。

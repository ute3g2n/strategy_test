# RECOVERY-05 UI・API再起動受入ランタイム起動証跡

- 実行日: 2026-08-16
- 要求されたOrchestrator: `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`
- 要求されたAgent: A130、A140、A171、A95
- 実行バックエンド: `multi_agent_v1`

`multi_agent_v1__spawn_agent` を実際に実行したが、`collab spawn failed: agent thread limit reached` で起動できなかった。`wait_agent` は起動対象がないため未実行である。独立Agentによる受入とは扱わず、ルート担当がAPIプロセス再起動、UI再読み込み、PlaywrightのRun ID・指標・provenance・行・Ledger、外部リクエスト0件を確認した。

| 対象 | 起動 | agent_id | independent | review_mode |
|---|---|---|---|---|
| AutoTradeProject_ImplementationQuality_Orchestrator_v0_1 | FAILED: thread limit | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A130_VerificationEngineer_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A140_DebugEngineer_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A171_UiVisualQaReviewer_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |
| AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 | NOT_STARTED | N/A | false | SELF_REVIEW_FALLBACK |

実際に完了した確認の証拠は `tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/api-restart-recovery.json`、`verification.json`、`backtest-history-after-api-restart.png`、および `ui/mock/tests/backtest-history-recovery.spec.ts` である。

安全・データ・再現性に関わる保護情報を除き、今回の計画は管理用hashを作らない。

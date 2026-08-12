# P5-06 dispatch receipts

- Recorded at: 2026-08-12 Asia/Tokyo
- Runtime status: `RUNTIME_DISPATCH_FALLBACK_REQUIRED`
- Fallback: `LOCAL_FALLBACK_NO_SUBAGENTS`
- Reason: Root `multi_agent_v1__spawn_agent` / `multi_agent_v1__wait_agent` completed successfully. The Coordinator child runtime was unavailable, so the six child rows below use the required fallback record.
- Review mode: `SELF_REVIEW_FALLBACK`
- Independence: `false` for every unstarted runtime participant.

| Order | Participant | JSON path | Fixed model | Agent ID | Spawn / wait | Output ref | Fallback reason | Independent | Review mode |
|---:|---|---|---|---|---|---|---|---|---|
| root | AutoTradeProject_ImplementationQuality_Orchestrator_v0_1 | `C:/project/strategy_test/.codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json` | `gpt-5.6-terra` | `019ff5c0-5620-7881-b7b3-5b6473319164` | `SPAWNED / COMPLETED` | `agent://019ff5c0-5620-7881-b7b3-5b6473319164/final` | child runtime unavailable; child fallback below | false | COORDINATOR_RECEIPT_WITH_CHILD_FALLBACK |
| 1 | AutoTrade_A110_PythonTestEngineer_v0_1 | `C:/project/strategy_test/.codex/agents/AutoTrade_A110_PythonTestEngineer_v0_1.json` | `gpt-5.6-luna` | `N/A` | `UNAVAILABLE / UNAVAILABLE` | local responsibility checklist | `RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS` | false | SELF_REVIEW_FALLBACK |
| 2 | AutoTrade_A120_PythonImplementer_v0_1 | `C:/project/strategy_test/.codex/agents/AutoTrade_A120_PythonImplementer_v0_1.json` | `gpt-5.6-luna` | `N/A` | `UNAVAILABLE / UNAVAILABLE` | local responsibility checklist | `RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS` | false | SELF_REVIEW_FALLBACK |
| 3 | AutoTrade_A130_VerificationEngineer_v0_1 | `C:/project/strategy_test/.codex/agents/AutoTrade_A130_VerificationEngineer_v0_1.json` | `gpt-5.6-luna` | `N/A` | `UNAVAILABLE / UNAVAILABLE` | local responsibility checklist | `RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS` | false | SELF_REVIEW_FALLBACK |
| 4 | AutoTrade_A140_DebugEngineer_v0_1 | `C:/project/strategy_test/.codex/agents/AutoTrade_A140_DebugEngineer_v0_1.json` | `gpt-5.6-luna` | `N/A` | `UNAVAILABLE / UNAVAILABLE` | local responsibility checklist | `RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS` | false | SELF_REVIEW_FALLBACK |
| 5 | AutoTrade_A150_PythonCodeReviewer_v0_1 | `C:/project/strategy_test/.codex/agents/AutoTrade_A150_PythonCodeReviewer_v0_1.json` | `gpt-5.6-luna` | `N/A` | `UNAVAILABLE / UNAVAILABLE` | `reviews/python-code-review.md` | `RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS` | false | SELF_REVIEW_FALLBACK |
| 6 | AutoTrade_A160_TradingSecurityReviewer_v0_1 | `C:/project/strategy_test/.codex/agents/AutoTrade_A160_TradingSecurityReviewer_v0_1.json` | `gpt-5.6-luna` | `N/A` | `UNAVAILABLE / UNAVAILABLE` | `reviews/trading-security-review.md` | `RUNTIME_DISPATCH_FALLBACK_REQUIRED; LOCAL_FALLBACK_NO_SUBAGENTS` | false | SELF_REVIEW_FALLBACK |

The listed children are recorded in the required order. They were not independently executed or reviewed; only the root Coordinator receipt is actual.

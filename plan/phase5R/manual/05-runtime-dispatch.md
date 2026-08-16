# P5R-MANUAL-05 Runtime Dispatch Receipt

```json
{
  "runtime_backend": "multi_agent_v1",
  "dispatch_mode": "COORDINATOR_SPAWN_ATTEMPTED_THREAD_LIMIT_FALLBACK",
  "orchestrator_name": "AutoTradeProject_DesignDocSet_Orchestrator_v0_1",
  "orchestrator_json_path": ".codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json",
  "orchestrator_model": "gpt-5.6-terra",
  "orchestrator_agent_id": "N/A",
  "phase_id": "P5R",
  "step_id": "P5R-MANUAL-05",
  "accepted_status": "NOT_ACCEPTED",
  "completion_status": "RUNTIME_DISPATCH_FALLBACK_REQUIRED",
  "fallback_reason": "multi_agent_v1__spawn_agent returned agent thread limit reached before a coordinator agent was accepted",
  "unstarted_agents": [
    {"agent_name":"AutoTrade_A80_DocumentIntegrator_v0_1","agent_json_path":".codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json","agent_model":"gpt-5.6-luna","agent_id":"N/A"},
    {"agent_name":"AutoTrade_A90_DesignReviewer_v0_1","agent_json_path":".codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json","agent_model":"gpt-5.6-luna","agent_id":"N/A"},
    {"agent_name":"AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1","agent_json_path":".codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json","agent_model":"gpt-5.6-luna","agent_id":"N/A"}
  ],
  "independent": false,
  "review_mode": "SELF_REVIEW_FALLBACK",
  "output_reference": "doc/phase5R/06_完了/03_バックテスト手順書改善完了判定.html"
}
```

ルートで機能一覧、全手順、画像、Registry、静的テスト、リンク、Web出典、安全境界を横断確認する。起動不能を独立レビュー済みとは扱わない。

なお、未起動Agent名に含まれる`AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`は、保護対象のData同一性、再現性、安全境界を壊す変更を静的に止めるための部品名である。このReceiptでは、文書管理用の識別子、差分管理、古い状態の自動判定、再生成経路を追加・計算・比較・再試行していない。A95の実行結果は別途、対象成果物の構造・経路・安全境界を確認した静的判定として記録する。

A95が起動できなかった場合でも、管理用のhashを計算しない。管理用のhashの比較や再試行もしない。

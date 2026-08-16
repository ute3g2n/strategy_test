# P5R-MANUAL-02 Runtime Dispatch Receipt

```json
{
  "runtime_backend": "multi_agent_v1",
  "dispatch_mode": "COORDINATOR_SPAWN_ATTEMPTED_THREAD_LIMIT_FALLBACK",
  "orchestrator_name": "AutoTradeProject_DesignDocSet_Orchestrator_v0_1",
  "orchestrator_json_path": ".codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json",
  "orchestrator_model": "gpt-5.6-terra",
  "orchestrator_agent_id": "N/A",
  "phase_id": "P5R",
  "step_id": "P5R-MANUAL-02",
  "accepted_status": "NOT_ACCEPTED",
  "completion_status": "RUNTIME_DISPATCH_FALLBACK_REQUIRED",
  "fallback_reason": "multi_agent_v1__spawn_agent returned agent thread limit reached before a coordinator agent was accepted",
  "unstarted_agents": [
    {"agent_name":"AutoTrade_A81_DesignDocSetWriter_v0_1","agent_json_path":".codex/agents/AutoTrade_A81_DesignDocSetWriter_v0_1.json","agent_model":"gpt-5.6-luna","agent_id":"N/A"},
    {"agent_name":"AutoTrade_A90_DesignReviewer_v0_1","agent_json_path":".codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json","agent_model":"gpt-5.6-luna","agent_id":"N/A"},
    {"agent_name":"AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1","agent_json_path":".codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json","agent_model":"gpt-5.6-luna","agent_id":"N/A"}
  ],
  "independent": false,
  "review_mode": "SELF_REVIEW_FALLBACK",
  "output_reference": "doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html"
}
```

`AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1` は、管理用の識別子を生成する部品ではなく、廃止された管理経路が再導入されていないかを静的に確認する部品として記録した。安全・Data・再現性を直接守る保護対象以外の識別子、manifest、digest、再試行経路は生成・保存・比較していない。

ルールドキュメントの内容は、Step 1の要件表、公式URL、プロジェクトのHTML・Unknown・廃止された文書管理経路をルートで照合した。起動不能を独立レビュー済みとは扱っていない。

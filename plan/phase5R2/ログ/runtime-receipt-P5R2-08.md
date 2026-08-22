# P5R2-08 runtime receipt

状態: `RUNTIME_DISPATCH_FALLBACK_REQUIRED`。`multi_agent_v1`によるルートのplanner probeは起動・wait完了したが、指定Coordinator／各指定Agentへの実行バインドと、planner probeからのnested dispatchは確立しなかった。未起動の指定Agentを独立実行済みとは扱わない。

|対象|固定model|agent_id|状態|独立性 / review mode|
|---|---|---|---|---|
|runtime planner probe（指定Coordinatorへのバインドなし）|gpt-5.6-terra|`01a0294e-5f8d-75f3-9ec0-a2d2801ce91d`|ACCEPTED / COMPLETED / wait COMPLETED|false / ROOT_FALLBACK_REVIEW|
|AutoTradePhasePlanning_Orchestrator_v0_1|gpt-5.6-terra|N/A|NOT_BOUND / NOT_DISPATCHED|false / SELF_REVIEW_FALLBACK|
|AutoTrade_A05_PhaseExecutionPlanner_v0_1|gpt-5.6-luna|N/A|NOT_DISPATCHED|false / SELF_REVIEW_FALLBACK|
|AutoTrade_A10_RequirementsCurator_v0_1|gpt-5.6-luna|N/A|NOT_DISPATCHED|false / SELF_REVIEW_FALLBACK|
|AutoTrade_A80_DocumentIntegrator_v0_1|gpt-5.6-luna (low)|N/A|NOT_DISPATCHED|false / SELF_REVIEW_FALLBACK|
|AutoTrade_A90_DesignReviewer_v0_1|gpt-5.6-luna|N/A|NOT_DISPATCHED|false / SELF_REVIEW_FALLBACK|
|AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1|gpt-5.6-luna (low)|N/A|NOT_DISPATCHED|false / SELF_REVIEW_FALLBACK|

ルートfallbackによる順次チェックは、A05相当のStep境界、A10相当の要件抽出、A80相当の成果物統合、A90相当のUnknown/Gate確認、A95相当の静的管理hash禁止判定として実施した。これは指定Agentの実行・wait・独立レビューの証拠ではない。管理用hashは計算・保存・比較・retryしない。安全・データ・再現性に直結する既存の保護対象は、目的と失敗時の停止範囲が明記される場合だけ別Human Gateで扱う。詳細はJSON receiptおよびP5R2-08ログを参照する。

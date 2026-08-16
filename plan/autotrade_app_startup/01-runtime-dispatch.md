# AUTOTRADE-APP-STARTUP-PLAN-001 Step 1 Runtime Receipt

対象Step: `AUTOTRADE-APP-STARTUP-01`
実行日: `2026-08-16`
状態: `RUNTIME_DISPATCH_FALLBACK_REQUIRED`

## Runtime結果

`multi_agent_v1__spawn_agent`で、次のCoordinator起動を試みた。

- Orchestrator: `AutoTradePhasePlanning_Orchestrator_v0_1`
- Orchestrator JSON: `.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json`
- 指定Agent: `AutoTrade_A05_PhaseExecutionPlanner_v0_1`、`AutoTrade_A10_RequirementsCurator_v0_1`、`AutoTrade_A90_DesignReviewer_v0_1`
- 起動結果: `NOT_ACCEPTED`
- 失敗理由: `collab spawn failed: agent thread limit reached`
- Coordinator `agent_id`: `N/A`
- 指定Agent `agent_id`: 全件 `N/A`
- `independent`: `false`
- `review_mode`: `SELF_REVIEW_FALLBACK`
- `wait_agent`: 受理されたAgent IDがないため、待機対象なし

指定部品の定義を列挙しただけで、独立Agentが実行済みとは扱わない。以下の調査は、ルートAgentがStep 1の責務チェックリストを適用した結果である。

## ルート確認結果

- `README.md`、`settings/language.md`、`settings/ai_component_rules.md`を確認した。
- 現在の入口候補は`auto-commit.cmd`だけで、アプリ起動用batは存在しない。
- UIは`ui/mock/package.json`の`npm run build`と`npm run preview`を使う。
- APIは`scripts/phase5r/backtest_api_server.py`から`src/autotrade/application/http_server.py`を呼ぶ。
- APIの既定入口は`127.0.0.1:8765/health`、UIの既定入口は`127.0.0.1:4173/`である。
- APIは`ALLOWED_UI_ORIGIN = http://127.0.0.1:4173`を使い、loopback外へbindしない契約になっている。
- UIの`VITE_P5R_API_BASE`既定値は`http://127.0.0.1:8765`である。
- `ui/mock/node_modules`、`.venv/Scripts/python.exe`、`ui/mock/dist/index.html`、`ui/mock/package-lock.json`は存在する。
- PlaywrightはAPIとpreviewを別プロセスで起動する構成である。
- 現行手順書には手動起動コマンドがあるが、ダブルクリック入口、依存確認、health待機、二重起動、停止入口、ポート競合時の扱いは一体化されていない。

## Step 1判定

Step 2では、入口batをプロジェクト直下に置き、PowerShell本体で次を実装する。

1. `%~dp0`からルートを解決する。
2. Python/npmと依存を確認する。
3. `npm ci`は`node_modules`がない場合だけ実行する。
4. `npm run build`後にAPI/UIをloopback限定で起動する。
5. `/health`と`/`を確認してからブラウザを開く。
6. 既存の正しいプロセスは二重起動しない。
7. 不明なポート占有プロセスは終了せず、停止する。
8. ログと停止入口を提供する。

外部Data、Broker、Secret、実注文、実資金、Paper、Liveは対象外のまま維持する。

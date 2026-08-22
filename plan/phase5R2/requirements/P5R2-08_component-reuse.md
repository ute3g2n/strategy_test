# P5R2-08 既存部品再利用判定

判定日は2026-08-22。read-onlyで確認した現行入口であり、H1前のtarget path確定・変更許可ではない。

## 現行ソース入口と再利用判定

|区分|根拠path / 入口|判定|P5R2での役割・不足|
|---|---|---|---|
|Product API|`src/autotrade/application/api.py`、`http_server.py`|変更候補|既存HTTP/DTO境界は再利用。DataSet/Generation/Artifact削除のAPIは未提供。|
|Backtest product|`src/autotrade/application/backtest_product.py` の `BacktestProductService`|変更候補|既存Run、cancel、CSV、history復元を維持。ただし`SPOT/1m`固定であり、P5R2時間足要求を満たさない。|
|Run/Job|`run_service.py`、`job_service.py`、`persistence.py`|再利用可能（契約拡張候補）|Job状態、expected revision、既存監査の土台はある。Download/Generation分離、OperationGuard、terminal取消監査は責務不足。|
|Persistence/履歴|`persistence.py`、`history_catalog.py`、`storage_paths.py`、`result_view.py`|変更候補|既存Run/CSV/結果保存は再利用。DataSet identity/coverage/provenance、Artifact tombstone、安全な削除操作は未設計。|
|時間足/品質|`backtest/timeframe_aggregator.py`、`market_data/quality.py`、`application/preflight.py`|変更候補|集約・品質の既存部品を調査入力に再利用。UTC anchor、partial排除、1本補間、source/derived分離の受入契約は不足。|
|Market Data|`market_data/acquisition_protocol.py`、`catalog_resolver.py`、`normalized_store.py`|再利用可能（local限定）|local fake/provider境界の候補。Provider login/API/download/Secret/費用はDATA-G1まで対象外。|
|UI|`ui/mock/src/P5RBacktestScreen.tsx`、`backtestApi.ts`|変更候補|実Application APIの既存画面・Run取消表示は再利用。1m default、Data管理/生成遷移、3画面共通取消、Artifact削除UIは未対応。|
|UI Test|`ui/mock/tests/p5r-backtest.spec.ts`、`p5r-backtest-manual-improvement.spec.ts`|対象外（H1前）|P5R履歴のTestとして読むだけ。Playwright起動・変更はH1後。|
|Python Test|`tests/application/`、`tests/backtest/`、`tests/phase5R/`|対象外（H1前）|既存回帰根拠として読むだけ。RED/Green/test subprocessはH1後。|
|Manual|`doc/phase5R/07_運用手順/01_バックテスト手順書.html`|再利用可能（履歴・改訂先）|P5R v0.5を保持し、P5R2-22で実証済み操作だけを追記する。|
|Quality入口|`scripts/wsl_quality_gate/run_test.ps1`、`trusted_scopes.json`|責務不足 / Unknown|`phase[0-9]+`制約にP5R2 namespaceの互換がない。P5R既存Runを無断流用しない。|

## AI部品の再利用判定

|部品|判定|理由|
|---|---|---|
|`AutoTradePhasePlanning_Orchestrator_v0_1`|再利用可能|P5R2-08の入力整理・Agent選定・Gate管理に合致。default変更不要。|
|A05/A10/A80/A90/A95|再利用候補|計画、要件抽出、統合、レビュー、管理hash静的防止の責務は既存定義で足りる。今回のruntimeではルートplanner probeだけが実行され、指定子Agentへのバインド・nested dispatchは確立しなかったため、独立実行済みではない。|
|`autotrade_skill_source_reader_v0_1`、`traceability`、`orchestration`、`protected_hash_policy_guard`|再利用可能|入力整理、追跡、Unknown停止、管理hash排除に直接対応。|
|ComponentLifecycle|不要|新規Skill/Agent/Orchestratorを作成・変更しない。既存JSONの責務で足り、部品変更は別Stepでのみ再判定する。|

## H1で人が判断する対象候補

|分類|H1に出す候補|未確定理由|
|---|---|---|
|設計対象|timeframe/preflight、Data Job/Catalog、Run cancel/ResultArtifact、Persistence/recovery、UI/Manual接続|P5R2-09/10の詳細設計とCritical/High=0確認が前提。|
|target paths|`src/autotrade/application/`、`src/autotrade/backtest/`、`src/autotrade/market_data/`、`ui/mock/src/`、`tests/application/`、`tests/backtest/`、`tests/phase5R/`、`ui/mock/tests/`、品質scripts|具体的ファイル集合、excluded paths、実削除境界はH1で固定する。|
|fixture|既存 `tests/evidence/phase5/RUN-P5-09-BINANCE-001/.../BTCUSDT-1m-2025-02.csv.gz` と既存market-data fixture群の適合性|P5R2要求のcoverage/qualityを満たすか未確定。新しい保護対象hashは導入しない。|
|固定入口候補|`scripts/wsl_quality_gate/run_test.ps1` の登録済みRun方式|Evidence phaseの正規表現が`phase[0-9]+`。P5R2用Run ID、phase_id、target_only、fixture、host isolationは未承認。|

管理用hash、manifest、receipt hash、fingerprint、stale、retryは再利用・新設・比較対象にしない。保護対象hashが本当に必要になった場合だけ、目的・対象・比較時点・失敗時停止範囲を別Human Gateへ出す。

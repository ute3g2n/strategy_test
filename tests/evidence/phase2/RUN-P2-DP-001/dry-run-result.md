# P2-08 fixture-only dry-run結果

実行日: 2026-08-08  
Run ID: `RUN-P2-DP-001`  
対象: `P2-08` Databento取得プロトコル

## 判定

- H2-2（Databento外部取得の明示承認）は承認記録なし。外部API、実データ、Secret、Brokerは使用していない。
- CLIは `source_mode=fixture` の request planだけを生成し、`external_io_allowed=false` を固定した。
- P2-07固定fixtureのSHA256は `sha256:a30055c3dfc71834801d298f57c4f758e602cf6fcec057762c15a0c8c27f1b79`。
- HTTP 401/403/206/404/429および `degraded/pending/missing` は成功にせず、HealthEventへ分類して停止または縮退する。
- `generated_at`、現在時刻、API key、Authorization、token、secretはrequest plan・metadataへ出力しない。

## 実装境界

`FixtureGateway`は固定fixtureの読込み、checksum、schemaを検査するだけで、Databento SDK・socket・HTTP clientをimportしない。`scripts/market_data/dry_run_request.py`はsource checkoutから同CLIを起動する薄い入口である。外部取得GatewayはH2-2承認後の別作業として未実装のまま残す。

## 未解決

- `H2-2`: 外部取得を許可するか、対象dataset・symbol・期間・費用上限・Secret投入方法を人間が承認する必要がある。
- `UNK-P2-07`: P2-07で固定したStore境界を実Databento応答へ接続する検証は未実施。

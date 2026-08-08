# P2-09 Data Quality / Replay検証ログ

- Run: `RUN-P2-RPL-001`
- 入力: P2-07固定fixture、P2-08 request plan / DBN checksum
- fixture SHA256: `sha256:a30055c3dfc71834801d298f57c4f758e602cf6fcec057762c15a0c8c27f1b79`
- fixture data_version: `dv_ed27a1e51b4a39bef629`
- Data Quality matrix: PASS（異常はfail-closed）
- Replay: PASS（fixture限定でManifest・MarketEvent系列を再現）
- 条件付き銘柄分離: PASS
- 実DBN→NormalizedBar / MarketEvent: UNKNOWN（decoder・変換境界未実装）
- Data Gate: UNKNOWN、Signal生成・Phase 3 handoff停止、H2-3へ送付

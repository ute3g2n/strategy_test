# RUN-P5R2-18-EXTERNAL-001

P5R2-DATA-G1で承認された、Binance Data Vision Spotのbounded pilot用External Run rootです。

- source: `1m` only
- symbols: `BTCUSDT`, `ETHUSDT`
- period: UTC `2025-02-24T00:00:00Z` inclusive through `2025-03-01T00:00:00Z` exclusive
- objects: monthly archive and sibling `.CHECKSUM`, maximum four objects
- derived intervals: local `15m`, `30m`, `1h`, `4h`, `1d`
- provider fee cap: `0 USD`
- raw provider-data redistribution: prohibited
- host-level isolation: currently `NOT_VERIFIED`, therefore execute and promotion are blocked

The runner defaults to a local dry-run. The existing P5 Runner is not reused. No login, API key, Secret, REST, WebSocket, `Authorization`, redirect, proxy, physical deletion, or P6 start is allowed. Existing Historical Data, Run, Result, CSV, Audit, and Evidence are never overwritten or deleted.

# P5R2-DATA-G1 delegated approval

- Gate: `P5R2-DATA-G1`
- Decision: `APPROVED_BOUNDED_P5R2_18`
- Decision date: `2026-08-23`
- Decision owner: root Codex, under the user-delegated P5R2 Human Gate authority recorded in `plan/phase5R2/ログ/P5R2-HumanGate権限移譲_2026-08-22.md`
- Decision packet: `doc/phase5R2/07_DATA-G1/07_P5R2-DATA-G1承認packet.html`

## Approved scope

The approval is limited to the following bounded pilot for `P5R2-18` and does not authorize a general provider connection.

- Provider: Binance Data Vision public archive.
- Host: `data.binance.vision:443`, HTTPS only.
- Market segment: Spot.
- Symbols: `BTCUSDT` and `ETHUSDT` only.
- Provider source interval: `1m` only.
- Period: UTC `2025-02-24T00:00:00Z` inclusive through `2025-03-01T00:00:00Z` exclusive.
- Source objects: matching monthly kline archives and their sibling `.CHECKSUM` objects only; maximum four archive objects in total.
- Derived intervals: create locally from the approved `1m` source only: `15m`, `30m`, `1h`, `4h`, `1d`.
- External Run: `RUN-P5R2-18-EXTERNAL-001`, in a separate external Run and Evidence root from local quality Runs.
- Local promotion root: `E:\\strategy_test_data\\autotrade\\historical\\spot\\klines\\1m`, using the approved staging and atomic-promotion flow.
- Provider fee cap: `0 USD`. A paywall, contract requirement, payment prompt, or any possible charge is an immediate stop.
- Communication boundary: redirects rejected, proxy disabled, and no API key, Secret, login, REST, WebSocket, or `Authorization` header.

## Mandatory stop conditions

Stop before or during the external Run if any provider, host, symbol, period, interval, path, schema, timestamp, UTC, duplicate, gap, checksum, cost, or Secret condition differs from this approval. Process-level egress controls and host-level isolation are separate evidence requirements; process-level controls must not be reported as host-level isolation. If host-level isolation is unavailable, record `NOT_VERIFIED` and stop promotion.

## Explicitly not approved

This decision does not approve any other provider, host, symbol, period, interval, direct upper-timeframe download, API call, login, contract, Secret, charge, redistribution of raw provider data, physical deletion, or P6 start. `P5R2-DELETE-G1` and `P5R2-H2` remain unapproved. The retention and redistribution terms, archive completeness, and host-level isolation Unknowns remain open.

# A40 engine-boundary review — RUN-P3-BT-REPAIR-002

- External engine is fixed to `ENGINE_NOT_USED` in the typed P3-07 Core Manifest and request.
- Public result rows contain no engine, Broker order, API key, or Secret field.
- `EngineAdapter` is a typed Protocol; no vendor SDK type is imported into Backtest Core or Strategy.
- Incomplete or unpinned mapping adapters stop with a structured reason instead of certifying parity.

Decision: no Critical/High finding; engine parity and real-engine execution remain outside this run.

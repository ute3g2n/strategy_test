# P5R-02A 品質Gate scope proposal

- proposed Run ID: `RUN-P5R-03-20260816-001`
- scope mode: `target_only`
- target: `src/autotrade/application`, `src/autotrade/backtest`, `scripts/phase5r`, `scripts/quality_gate`, `tests/application`, `tests/backtest`, `tests/phase5R`, `ui/mock`
- excluded: `.env`, `doc`, `plan`, `research`, `third_party`, existing `tests/evidence/phase5`, Broker/Secret/Cloud/external Data
- fixture: existing P5-09 local normalized BTCUSDT/ETHUSDT only; no new download
- output root: `tests/evidence/phase5R/RUN-P5R-03-20260816-001/`
- fixed four gates: ruff format, ruff check, mypy, pytest as specified in `doc/phase5R/02_実装詳細設計/02_P5R品質Gate_RunManifest設計書.html`
- UI gates: `npm --prefix ui/mock run build`, `npm --prefix ui/mock run test`, fixed `@playwright/test` P5R spec on desktop 1280x900 and mobile 390x844
- network: host outbound isolation confirmation required; any external request or secret detection is BLOCKED
- protected policy: no management hash, manifest fingerprint, stale, or hash retry
- registration status before H1: PROPOSAL_ONLY / NOT_REGISTERED

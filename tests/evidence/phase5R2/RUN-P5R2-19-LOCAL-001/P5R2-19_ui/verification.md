# P5R2-19 UI verification

- Run: `RUN-P5R2-19-LOCAL-001`
- Scope: loopback-only Web Product UI connected to the P5R2 Application API.
- Runtime fallback: the requested named Agent dispatch did not complete. The root agent performed the listed checks and records this as `SELF_REVIEW_FALLBACK`; no independent Agent completion is claimed.

## Acceptance results

| Area | Result | Evidence / note |
|---|---|---|
| Strategy timeframe | PASS | The selectable values are exactly `15m`, `30m`, `1h`, `4h`, `1d`; `1m` is explanatory source text only. |
| Data Catalog | PASS | Catalog columns include symbol, timeframe, period, quality, usable, legacy, Job state, and provenance. |
| Missing-data journey | PASS | `DATA_INSUFFICIENT` is shown, the confirmation dialog preserves symbol/timeframe/range, and the generation form supports multiple strategy timeframes. |
| Generation entry point | PASS | The generation form can be opened directly from the Catalog at any time. |
| Run list / result summary | PASS | SCREEN-09 and SCREEN-10 consume the same Application API Run state and cancellation reason model. |
| Cancel double-submit boundary | PASS | In-flight UI controls are disabled while the request is pending; server cancellation remains the existing OperationGuard path. |
| Delete boundary | PASS | The original P5R2-19 acceptance was fail-closed before DELETE-G1. The current re-capture after bounded DELETE-G1 shows the approved panel; no physical delete was executed in this P5R2-19 journey. The actual confirmation-to-delete acceptance is recorded separately in P5R2-21. |
| External boundary | PASS | Provider download remains disabled with `HOST_LEVEL_ISOLATION_NOT_VERIFIED`; no external host, Secret, login, cost, or data download was used. |
| Accessibility / visual | PASS | Fixed Chromium desktop `1280x900` and mobile `390x844`; dedicated Playwright journey had no critical/serious axe violations and captured screenshots after assertions. |

## Machine checks

- Backend targeted regression: `63 passed`.
- UI build: PASS.
- UI lint: PASS with the repository's existing Fast Refresh warnings only.
- UI Vitest: `13 passed`.
- Dedicated P5R2 Playwright: `2 passed` (`chromium-desktop`, `chromium-mobile`).
- Dedicated browser external request monitor: `0` outside `127.0.0.1:4173` and `127.0.0.1:8765`.

## Explicit non-actions

No external provider request, authentication, Secret, cost, physical deletion, existing Data/Run/Audit/Evidence deletion, or P6 activity was performed.

The result-screen screenshot and capture registry were refreshed after P5R2-DELETE-G1 approval so the current UI wording is not mistaken for the historical pre-gate state. P5R2-19 remains the UI integration record; P5R2-21 is the authoritative physical-delete acceptance.

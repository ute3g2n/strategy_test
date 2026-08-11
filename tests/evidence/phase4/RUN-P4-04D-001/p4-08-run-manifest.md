# P4-08 Run Manifest

- Step: `P4-08`
- Phase: `PHASE4_PRODUCT_APPLICATION_BACKTEST_2026_08_11`
- Run ID: `RUN-P4-04D-001`
- Execution date: `2026-08-12` (Asia/Tokyo)
- Baseline: `d8784df` (P4-07 completed)
- Approval: `P4-H1=APPROVED` in [human-gate-p4-h1.md](human-gate-p4-h1.md)
- Trusted scope: `scripts/quality_gate/trusted_scopes.json` / `RUN-P4-04D-001`
- Scope mode: `target_only`
- Final Step status: `COMPLETED_P4-08_P4-09_PENDING`

## Target and exclusion

P4-08 uses the explicitly recorded fixed local UI target `ui/mock`, together with the P4-06／P4-07 local Application test scope. Evidence is stored under the registered Evidence exception path.

| Target | Purpose |
|---|---|
| `ui/mock` | P4-04C SCREEN-01〜21 fixed dummy UI, contract metadata, Playwright／Storybook／Vitest／axe |
| `src/autotrade/application` | Read-only P4-07 local API contract input; no Python source changed in P4-08 |
| `tests/application`, `tests/phase4`, `tests/fixtures/phase4` | Read-only P4-07 contract and fixture input |

The following remained excluded or unchanged: `src/autotrade/backtest`, `src/autotrade/market_data`, `src/autotrade/strategy`, Core ResultStore／Evidence／CSV source, `doc` except documentation links, `plan` except execution log and status, `.env`, `research`, `third_party`, external database, HTTP server, Broker／Paper／Live, Secret, real Risk／Account／OMS, WSL, Cloud and external I/O.

## Fixed UI execution contract

- Seed: `20260811`
- Base datetime: `2026-08-11 12:00`
- Locale／timezone: `ja-JP`／`Asia/Tokyo`
- Desktop: Chromium, viewport `1280x900`
- Mobile: Chromium Pixel 5 profile, viewport `390x844`
- Playwright: `1.62.1`
- Storybook: `10.5.7`
- Vitest: `4.1.10`
- axe-core: `4.13.0`
- Data: fixed anonymous dummy only
- Browser external requests: 0

## Expected Evidence

- 21 desktop screenshots under `p4-08-playwright/screenshots/chromium-desktop/`
- 21 mobile screenshots under `p4-08-playwright/screenshots/chromium-mobile/`
- Playwright JSON result: `p4-08-playwright/results.json`
- Playwright report: `p4-08-playwright/playwright-report/index.html`
- Dispatch: `p4-08-dispatch.md`
- Verification: `p4-08-verification.md`
- Quality: `p4-08-quality-gate.md`
- Fallback self-review: `p4-08-self-review.md`

## Stop conditions checked

- P4-H1 approval and Run linkage: PASS
- Core source diff: 0
- External request／Secret／Broker／Paper／Live／Cloud: 0／not used
- Contract／scope／reason mismatch: 0 after the initial test assertion was corrected
- axe Critical／Serious: 0
- `UNK-P4-04D-004` host outbound isolation: UNKNOWN; WSL gate not started
- `UNK-P4-UI-002` font／OS rendering baseline: UNKNOWN; not converted to PASS
- Critical／High: 0 unresolved

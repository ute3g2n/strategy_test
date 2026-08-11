# P4-08 Verification Evidence

## Findings first

| Finding | Severity | Result | Evidence |
|---|---|---|---|
| Initial API assertion required the wrong common IDs | High during test authoring | Closed; P4-04C contract map is now the assertion source | `ui/mock/src/p4Contract.ts`, `p4-08.spec.ts` |
| Coordinator child dispatch did not return verifiable receipts | Medium / process | Recorded; no independent result claimed | [p4-08-dispatch.md](p4-08-dispatch.md) |
| font／OS and pixel baseline acceptance | Medium / Unknown | Open; not converted to PASS | [P4-04C UI design](../../../doc/phase4/02_実装詳細設計/06_ProductApplication_UI全21画面詳細設計書.html) |

## Screen and contract coverage

The implementation contains exactly one contract entry for `SCREEN-01` through `SCREEN-21`. The P4-04C classification is preserved:

| Scope | Screens | Verification |
|---|---|---|
| `P4_TARGET` | `SCREEN-02/03/04/08/09/10/11/12/19` | Contract scope, exact API-P4-ID list, reason ID, ten common states |
| `P4_BOUNDARY_TARGET` | `SCREEN-01/17/18/21` | Contract scope, exact API-P4-ID list, boundary reason, ten common states |
| `BOUNDARY_ONLY` | `SCREEN-05/06/07/13/14/15/16/20` | Fixed `UNAPPROVED`, `P4_OUT_OF_SCOPE`, no functional operation |

The P4-08 test checks all 21 routes in both viewports against the same `p4ScreenContracts` map. It exercises 13 P4 target／boundary screens × 10 common states = 130 state operations per viewport, and confirms the eight Boundary-only screens remain fail-closed.

## API／UI boundary

The contract strip exposes the exact API IDs from P4-04C and P4-07 without adding an HTTP transport. The UI remains a fixed anonymous dummy and does not copy result bodies, file bytes, absolute paths, Secret values, Core internals or external data into the screen. The boundary test observed no request outside the local preview origin, `data:`, `blob:` or `about:` schemes.

## Visual and accessibility verification

- Desktop Chromium `1280x900`: 21 screenshots, route／contract／state test PASS.
- Mobile Chromium Pixel 5 profile `390x844`: 21 screenshots, route／contract／state test PASS.
- `axe-core` WCAG2A／WCAG2AA scan: all 21 screens × 2 viewports, Critical／Serious violations 0.
- Keyboard／focus／name／role contracts: Vitest／Playwright existing UI tests plus P4-08 route and state checks PASS; Dialog and mobile navigation remain local and no external request is made.
- Formal font／OS rendering and pixel-diff baseline: Unknown `UNK-P4-UI-002`; screenshots are evidence, not a claim that an unresolved font/OS baseline is accepted.

## Safety and scope

- Core source diff: 0.
- External I/O／HTTP／Broker／Paper／Live／Cloud／Secret: 0.
- Existing UI changes are traceable to `SCREEN-ID`, P4-04C scope, API-P4-ID and reason ID in `p4Contract.ts`.
- P4-H2 is not approved; the Human Gate screen remains a boundary and does not perform mode promotion.
- Host outbound isolation remains Unknown `UNK-P4-04D-004`; WSL quality gate was not started.

## Evidence references

- [P4-08 JSON results](p4-08-playwright/results.json)
- [P4-08 Playwright report](p4-08-playwright/playwright-report/index.html)
- [P4-08 screenshots](p4-08-playwright/screenshots/)
- [P4-08 run manifest](p4-08-run-manifest.md)
- [P4-08 quality gate](p4-08-quality-gate.md)
- [P4-08 fallback self-review](p4-08-self-review.md)

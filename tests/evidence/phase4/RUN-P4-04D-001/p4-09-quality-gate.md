# P4-09 Integrated Quality Gate

Run: `RUN-P4-04D-001`<br>
Step: `P4-09`<br>
Scope: read-only integrated review of the approved local P4 target

## Machine checks

| Gate | Command or source | Result | Evidence |
|---|---|---|---|
| Formatter | `.venv/Scripts/python.exe -m ruff format --check src/autotrade/application tests/application tests/phase4 tests/fixtures/phase4` | PASS — 24 files already formatted | P4-09 execution log |
| Lint | `.venv/Scripts/python.exe -m ruff check src/autotrade/application tests/application tests/phase4 tests/fixtures/phase4` | PASS — all checks passed | P4-09 execution log |
| Type | `.venv/Scripts/python.exe -m mypy src/autotrade/application` | PASS — 20 source files | P4-09 execution log |
| Python tests | `.venv/Scripts/python.exe -m pytest tests/application tests/phase4 -q` | PASS — 17 passed | P4-09 execution log |
| Python evidence hashes | P4-06 and P4-07 hash manifests | PASS | `p4-09-verification.md` |
| UI evidence hashes | P4-08 hash manifest | PASS | `p4-09-verification.md` |
| Fixture hash | registered Phase 3 backtest fixture | PASS — `aeb03df1...c536fa4` | `p4-09-run-manifest.md` |
| Core source diff | diff from approved P4 baseline | PASS — 0 files | `p4-09-verification.md` |
| Dependency diff | P4-08 vs P4-07 baseline `d8784df` | PASS — 0 dependency files | `p4-09-verification.md` |
| Documentation links | index／ledger／P4 design set local links | PASS | `p4-09-verification.md` |
| Git whitespace | `git diff --check` | PASS | P4-09 execution log |

## Reused P4-08 UI gates

The P4-08 stored result is rechecked without regenerating or changing UI evidence:

| Check | Result |
|---|---|
| Playwright result | 6 expected, 0 unexpected, 0 skipped |
| Screenshots | 42 total: 21 desktop + 21 mobile |
| Viewports | Chromium `1280x900`; Pixel 5 profile `390x844` |
| axe | WCAG2A／WCAG2AA; Critical／Serious = 0 |
| Browser external request | 0 outside local preview／data／blob／about boundary |
| Storybook／Vitest／build／lint | PASS in P4-08 quality evidence |

## Not-PASS conditions

| Condition | Status | Effect |
|---|---|---|
| Host outbound isolation | `UNKNOWN` (`UNK-P4-04D-004`) | P4-H2 candidate blocked; WSL gate not started |
| Font／OS／formal pixel baseline | `UNKNOWN` (`UNK-P4-UI-002`) | screenshots remain runtime evidence only |
| Child-Agent independent review | `NOT_STARTED` | fallback self-review only; no independent completion claim |
| P4-H2 approval | `WAITING_FOR_USER_APPROVAL` | P4-10 prohibited |

The unknowns above are intentionally not converted to PASS. The local code and design checks have no unresolved Critical／High finding, but P4-09 cannot certify P4-H2 readiness while a required stop condition remains unknown.

# P4-06 Verification

## Commands and results

| Check | Command / source | Result |
|---|---|---|
| Approval | `human-gate-p4-h1.md` | `P4-H1=APPROVED` |
| Registry | `scripts/quality_gate/trusted_scopes.json` parsed as JSON; lookup `scopes.RUN-P4-04D-001` | registered; approval, target-only scope, fixture and four checks aligned |
| Fixture | `Get-FileHash -Algorithm SHA256 tests/fixtures/phase3/run_p3_backtest_fixture_manifest_v1.json` | expected hash matched |
| Core diff | `git diff --name-only HEAD -- src/autotrade/backtest src/autotrade/market_data src/autotrade/strategy` | no output |
| Baseline Core diff | same command against `2ce571e` | no output |
| RED | `.venv\\Scripts\\python.exe -m pytest tests\\phase4\\test_p4_red_contract.py -q` | initial `6 failed`, exit `1`; old module name mismatch recorded |
| GREEN contract | `.venv\\Scripts\\python.exe -m pytest tests\\application tests\\phase4 -q` | `8 passed`, exit `0` |
| Formatter | `.venv\\Scripts\\python.exe -m ruff format --check src\\autotrade\\application tests\\application tests\\phase4 tests\\fixtures\\phase4` | pass |
| Lint | `.venv\\Scripts\\python.exe -m ruff check src\\autotrade\\application tests\\application tests\\phase4 tests\\fixtures\\phase4` | pass |
| Type | `.venv\\Scripts\\python.exe -m mypy src\\autotrade\\application` | pass; 20 source files |
| Core boundary | target-only diff inspection for `src/autotrade/backtest`, `market_data`, `strategy` | 0 changed |

## RED details

All six failures are `ModuleNotFoundError: No module named 'autotrade.product_application'`. The P4-03 formal file tree names `src/autotrade/application`; therefore this is a pre-existing contract-name mismatch, not permission to create a second `product_application` package.

## Verification judgment

The first lookup used an invalid `runs` key and incorrectly reported the Run as missing. The corrected `scopes.RUN-P4-04D-001` lookup passed. The RED result was valid for the old sentinel and the sentinel was then replaced with the approved `autotrade.application` contract. GREEN and the target quality checks passed. The host outbound isolation and browser/axe runtime Unknowns remain unresolved and are not promoted to PASS.

# TDD evidence: application storage relocation

## RED

- Commit: `afa9c2c test: add autotrade storage relocation contracts`
- The new storage contract tests failed during collection because `autotrade.application.storage_paths` did not yet exist.
- The new artifact naming test also established that runtime IDs must use application-wide names instead of phase identifiers.

## GREEN

- `tests/phase5R/test_autotrade_storage_layout.py`: E-drive-only paths, forbidden path rejection, and application-root containment.
- `tests/phase5R/test_backtest_product_red.py`: default service path, result path, CSV export path, and application-wide IDs.
- `tests/phase5R/test_autotrade_app_startup.py`: startup/stop scripts and manual point to E-drive logs.
- `tests/phase5R/test_http_server_routes.py`: CSV download route returns the generated CSV.
- Final Python verification: 102 tests passed; Ruff passed.

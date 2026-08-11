# P4-07 Local Quality Gate

Run: `RUN-P4-04D-001`
Step: `P4-07`
Scope: target-only Application and Phase 4 contract tests

| Gate | Command | Result |
|---|---|---|
| Formatter | `.venv\Scripts\python.exe -m ruff format --check src\autotrade\application tests\application tests\phase4` | PASS — 23 files already formatted |
| Lint | `.venv\Scripts\python.exe -m ruff check src\autotrade\application tests\application tests\phase4` | PASS |
| Type | `.venv\Scripts\python.exe -m mypy src\autotrade\application` | PASS — 20 source files |
| Test | `.venv\Scripts\python.exe -m pytest tests\application tests\phase4 -q` | PASS — 17 passed |
| Diff hygiene | `git diff --check` | PASS |
| Core boundary | `git diff -- src/autotrade/backtest src/autotrade/market_data src/autotrade/strategy` | PASS — 0 files |
| Fixture | SHA-256 of registered Phase 3 manifest | PASS — registered hash unchanged |

`UNK-P4-04D-004` (host outbound isolation) is not converted to PASS by this
local gate. The WSL gate was not started because its host isolation evidence
is still unknown. `UNK-P4-04D-005` (P4-08 browser/viewport/axe runtime) remains
for P4-08.

No database file, migration execution, external result root, WSL clone, or
network process was started. Tests use `:memory:` SQLite and pytest temporary
directories only.

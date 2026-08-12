# P5-06 direct local checks (non-final)

These checks are non-final evidence only. Formal Gate acceptance is BLOCKED by the registered unresolved host-isolation Unknown.

| Order | Command | Exit code | Result |
|---:|---|---:|---|
| 1 | `.venv/Scripts/python.exe -m ruff format --check src/autotrade/market_data scripts/quality_gate tests/market_data tests/fixtures/market_data` | 0 | PASS |
| 2 | `.venv/Scripts/python.exe -m ruff check src/autotrade/market_data scripts/quality_gate tests/market_data tests/fixtures/market_data` | 0 | PASS |
| 3 | `.venv/Scripts/python.exe -m mypy src/autotrade/market_data` | 0 | `Success: no issues found in 12 source files` |
| 4 | `.venv/Scripts/python.exe -m pytest tests/market_data -q` | 0 | `102 passed` |
| extra | `.venv/Scripts/python.exe -m pytest tests/quality_gate -q` | 0 | `58 passed` |

- P5-specific GREEN: `tests/market_data/test_p5_data_contract_quality.py` — `7 passed`.
- Fixture SHA-256: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99`.
- External communication: `0` attempted; no external command was invoked.
- Host outbound isolation: `UNKNOWN`; this document does not certify it.

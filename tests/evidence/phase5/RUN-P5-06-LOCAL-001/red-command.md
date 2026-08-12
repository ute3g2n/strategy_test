# P5-06 RED evidence

- Command: `.venv/Scripts/python.exe -m pytest tests/market_data/test_p5_data_contract_quality.py -q`
- Exit code: `1`
- Result: `5 passed, 2 failed`
- Failures: `QualityChecker.check()` did not accept the required `calendar_hash`, `expected_calendar_hash`, or `as_of_utc` fixed-local contract inputs.
- Fixture SHA-256: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99`
- Changed paths at RED: `tests/market_data/test_p5_data_contract_quality.py`.
- External communication: `0` attempted.

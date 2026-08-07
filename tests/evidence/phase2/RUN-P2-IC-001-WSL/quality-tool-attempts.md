# ローカル品質コマンド試行記録

実行環境に `.venv/bin/python` と `pytest` が存在しないため、次の実行は開始前にBLOCKEDとなった。隔離後にpip installは行っていない。

- formatter: `.venv/bin/python -m ruff format --check src/autotrade/market_data tests/market_data` — `.venv/bin/python` 不在
- lint: `.venv/bin/python -m ruff check src/autotrade/market_data tests/market_data` — `.venv/bin/python` 不在
- type: `.venv/bin/python -m mypy src/autotrade/market_data` — `.venv/bin/python` 不在
- test: `.venv/bin/python -m scripts.quality_gate.local_p2_pytest` — `.venv/bin/python` 不在

`bash -n`、Python構文確認、JSON検証、trusted scopeのDRY_RUNと改変拒否のスモーク確認は成功した。これは4 GateのPASSやHuman Gate承認を意味しない。

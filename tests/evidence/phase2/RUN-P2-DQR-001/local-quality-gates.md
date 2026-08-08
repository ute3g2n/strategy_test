# P2-07 Windows側ローカル品質Gate

実行環境: `C:\project\strategy_test\.venv\Scripts\python.exe`

| Gate | コマンド | 結果 |
|---|---|---|
| formatter | `ruff format --check src/autotrade/market_data tests/market_data` | PASS（10 files already formatted） |
| lint | `ruff check src/autotrade/market_data tests/market_data` | PASS |
| type | `mypy src/autotrade/market_data` | PASS（7 source files） |
| test | `python -m scripts.quality_gate.local_p2_pytest` | PASS（25 passed） |
| coverage | `pytest tests/market_data --cov=autotrade.market_data --cov-fail-under=80` | PASS（81.80%） |
| manifest | `run_quality_gate.py --manifest ... --dry-run --no-write-evidence` | DRY_RUN（4 Gate schema valid） |

この表はWindows側の実装検証であり、WSL隔離4 Gateの最終Passを代替しない。

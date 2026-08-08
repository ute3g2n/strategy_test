# P2-08 Windows側ローカル品質Gate

実行環境: `C:\project\strategy_test\.venv\Scripts\python.exe`

| Gate | コマンド | 結果 |
|---|---|---|
| formatter | `ruff format --check src/autotrade/market_data tests/market_data scripts/market_data` | PASS |
| lint | `ruff check src/autotrade/market_data tests/market_data scripts/market_data` | PASS |
| type | `mypy src/autotrade/market_data` | PASS（8 source files） |
| test | `pytest tests/market_data` | PASS（39 passed） |
| coverage | `pytest tests/market_data --cov=autotrade.market_data` | PASS（81.76%、fail_under 80%） |

外部I/Oは実行していない。WSL隔離4 Gateは `scripts/wsl_quality_gate/run_test.ps1` の証跡を別途保存し、Windows側結果だけで代替しない。

WSL実行では `networking_mode=none` / host-isolation `CONFIRMED`、formatter・lint・type・testの4 GateがPASSした。汎用RunnerのHuman Gate状態は `HUMAN_GATE_REQUIRED` だが、P2-08はH2-2未承認のfixture-only dry-runであり、外部取得の承認を意味しない。

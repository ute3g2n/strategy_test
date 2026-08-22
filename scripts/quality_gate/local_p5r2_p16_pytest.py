"""P5R2-16 fixed local pytest entrypoint for restart and recovery integration."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run only the P5R2-16 integration contracts and affected local regressions."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase5R/test_p5r2_local_integration_red.py",
            "tests/phase5R/test_backtest_history_recovery.py",
            "tests/market_data/test_p5r2_historical_data_red_contract.py",
            "tests/application/test_p5r2_run_operation_guard.py",
            "tests/phase5R/test_p5r2_backtest_service_cancel_guard.py",
            "tests/phase5R/test_backtest_product_red.py",
            "tests/phase5R/test_autotrade_storage_layout.py",
            "tests/application/test_nonhash_management_boundaries.py",
            "tests/phase5R/test_http_server_routes.py",
            "tests/phase5R/test_http_server_security.py",
            "-q",
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

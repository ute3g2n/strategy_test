"""P5R2-16 fixed local pytest entrypoint for restart and recovery integration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run only the P5R2-16 integration contracts and affected local regressions."""

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase5R/test_p5r2_local_integration_red.py",
            "tests/backtest/test_p5r2_timeframe_red_contract.py",
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
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        diagnostic = Path("tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/p5r2-16-test-output.txt")
        diagnostic.parent.mkdir(parents=True, exist_ok=True)
        diagnostic.write_text(
            f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}\n",
            encoding="utf-8",
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

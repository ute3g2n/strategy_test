"""P5R2-15 fixed local pytest entrypoint for Run operation guards."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run only the P5R2-15 contracts and affected local result regressions."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/application/test_p5r2_run_operation_red_contract.py",
            "tests/application/test_p5r2_run_operation_guard.py",
            "tests/phase5R/test_p5r2_result_artifact_red_contract.py",
            "tests/phase5R/test_p5r2_result_artifact_guard.py",
            "tests/phase5R/test_p5r2_backtest_service_cancel_guard.py",
            "tests/application/test_p4_07_execution.py",
            "tests/application/test_nonhash_management_boundaries.py",
            "-q",
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

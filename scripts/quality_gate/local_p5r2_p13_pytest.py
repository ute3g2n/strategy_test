"""P5R2-13 fixed local pytest entrypoint for timeframe/preflight only."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run the P5R2-13 contracts and the affected P4 regression boundary."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/backtest/test_p5r2_timeframe_red_contract.py",
            "tests/application/test_nonhash_management_boundaries.py",
            "tests/application/test_p4_07_execution.py",
            "-q",
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

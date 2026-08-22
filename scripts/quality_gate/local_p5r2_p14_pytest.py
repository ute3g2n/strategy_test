"""P5R2-14 fixed local pytest entrypoint for Historical Data contracts."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run the P5R2-14 contracts and the affected local regression boundary."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/market_data/test_p5r2_historical_data_red_contract.py",
            "tests/market_data/test_acquisition_protocol.py",
            "tests/market_data/test_catalog_resolver.py",
            "tests/application/test_p4_07_execution.py",
            "-q",
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

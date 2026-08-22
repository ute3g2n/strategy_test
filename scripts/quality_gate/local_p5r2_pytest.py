"""P5R2 fixed local pytest entrypoint for the registered target scope."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run only the P5R2 Python test paths without a shell."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/application",
            "tests/backtest",
            "tests/market_data",
            "tests/phase5R",
            "-q",
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

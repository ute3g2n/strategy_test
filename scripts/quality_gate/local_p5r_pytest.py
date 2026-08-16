"""P5R fixed local pytest entrypoint for the trusted scope only."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run only the registered P5R Python test paths without a shell."""

    return subprocess.run(
        [sys.executable, "-m", "pytest", "tests/application", "tests/backtest", "tests/phase5R", "-q"],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

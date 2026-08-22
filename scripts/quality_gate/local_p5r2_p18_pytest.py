"""P5R2-18 fixed local pytest entrypoint for the bounded external runner."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    """Run only the P5R2-18 runner contracts; no external I/O is requested."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase5R/test_p5r2_external_runner.py",
            "-q",
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())

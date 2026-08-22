"""P5R2-15 fixed local pytest entrypoint for Run operation guards."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run only the P5R2-15 contracts and affected local result regressions."""

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/application/test_p5r2_run_operation_red_contract.py",
            "tests/application/test_p5r2_run_operation_guard.py",
            "tests/phase5R/test_p5r2_result_artifact_red_contract.py",
            "tests/phase5R/test_p5r2_result_artifact_guard.py",
            "tests/phase5R/test_p5r2_backtest_service_cancel_guard.py",
            "tests/phase5R/test_backtest_product_red.py",
            "tests/phase5R/test_http_server_routes.py",
            "tests/phase5R/test_http_server_security.py",
            "tests/application/test_p4_07_execution.py",
            "tests/application/test_nonhash_management_boundaries.py",
            "-q",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        diagnostic_path = Path("tests/evidence/phase5R2/RUN-P5R2-15-LOCAL-001/automation/p5r2-15-pytest-output.txt")
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text(
            f"returncode={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}\n",
            encoding="utf-8",
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

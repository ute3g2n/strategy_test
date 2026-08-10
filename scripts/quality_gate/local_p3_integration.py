"""Run the fixed P3-10 Strategy/Backtest suite without network access."""

from __future__ import annotations

import os
import socket
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _deny_network(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise RuntimeError("P3-10 quality gate forbids outbound network access")


socket.create_connection = _deny_network  # type: ignore[assignment]
socket.getaddrinfo = _deny_network  # type: ignore[assignment]
socket.socket.connect = _deny_network  # type: ignore[method-assign]
socket.socket.connect_ex = _deny_network  # type: ignore[assignment]
socket.socket.sendto = _deny_network  # type: ignore[assignment]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"


class _NoSkipPlugin:
    """Turn every collected or executed skip into a failed P3-10 run."""

    skipped = False

    def pytest_collectreport(self, report: object) -> None:
        if getattr(report, "outcome", None) == "skipped":
            self.skipped = True

    def pytest_runtest_logreport(self, report: object) -> None:
        if getattr(report, "outcome", None) == "skipped":
            self.skipped = True


def main() -> int:
    """Run the immutable Strategy/Backtest targets and write their summary."""
    import pytest

    from scripts.quality_gate.p3_integration_runner import run_p3_10

    plugin = _NoSkipPlugin()
    result = pytest.main(
        ["tests/strategy", "tests/backtest", "--runxfail", "-q"],
        plugins=[plugin],
    )
    quality_gate_status = "PASS" if result == 0 and not plugin.skipped else "FAIL"
    summary = run_p3_10(REPO_ROOT, quality_gate_status=quality_gate_status)
    print(f"P3-10 summary: final_status={summary['final_status']} quality_gate_status={summary['quality_gate_status']}")
    if plugin.skipped:
        return 97
    if result != 0 or summary["final_status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

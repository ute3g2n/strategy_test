"""Run only the fixed P3-05 Golden and bias contract tests offline."""

from __future__ import annotations

import os
import socket


def _deny_network(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise RuntimeError("quality gate forbids outbound network access")


socket.create_connection = _deny_network  # type: ignore[assignment]
socket.socket.connect = _deny_network  # type: ignore[method-assign]
socket.socket.connect_ex = _deny_network  # type: ignore[assignment]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"


class _NoSkipPlugin:
    """Turn every collected or executed skip into a failed P3 contract run."""

    skipped = False

    def pytest_collectreport(self, report: object) -> None:
        if getattr(report, "outcome", None) == "skipped":
            self.skipped = True

    def pytest_runtest_logreport(self, report: object) -> None:
        if getattr(report, "outcome", None) == "skipped":
            self.skipped = True


def main() -> int:
    """Run the immutable P3-05 test paths; callers cannot add targets."""
    import pytest

    plugin = _NoSkipPlugin()
    result = pytest.main(["tests/strategy", "tests/backtest", "--runxfail", "-q"], plugins=[plugin])
    return 97 if plugin.skipped else result


if __name__ == "__main__":
    raise SystemExit(main())

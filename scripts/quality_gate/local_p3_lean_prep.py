"""Run the fixed P3-08A preparation and engine-boundary tests offline."""

from __future__ import annotations

import os
import socket


def _deny_network(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise RuntimeError("P3-08A quality gate forbids outbound network access")


socket.create_connection = _deny_network  # type: ignore[assignment]
socket.getaddrinfo = _deny_network  # type: ignore[assignment]
socket.socket.connect = _deny_network  # type: ignore[method-assign]
socket.socket.connect_ex = _deny_network  # type: ignore[assignment]
socket.socket.sendto = _deny_network  # type: ignore[assignment]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"


class _NoSkipPlugin:
    skipped = False

    def pytest_collectreport(self, report: object) -> None:
        if getattr(report, "outcome", None) == "skipped":
            self.skipped = True

    def pytest_runtest_logreport(self, report: object) -> None:
        if getattr(report, "outcome", None) == "skipped":
            self.skipped = True


def main() -> int:
    import pytest

    plugin = _NoSkipPlugin()
    result = pytest.main(
        ["tests/engine_prep", "tests/strategy", "tests/backtest", "--runxfail", "-q"],
        plugins=[plugin],
    )
    return 97 if plugin.skipped else result


if __name__ == "__main__":
    raise SystemExit(main())

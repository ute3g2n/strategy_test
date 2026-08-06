"""Run only the fixed P2-D07 market-data tests behind a local network boundary."""

from __future__ import annotations

import os
import socket


def _deny_network(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise RuntimeError("quality gate forbids outbound network access")


socket.create_connection = _deny_network  # type: ignore[assignment]
socket.socket.connect = _deny_network  # type: ignore[assignment]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"


def main() -> int:
    """Run the immutable P2-D07 test path; caller cannot supply another target."""
    import pytest

    return pytest.main(["tests/market_data", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())

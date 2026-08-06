"""Run only the quality-gate tests with outbound socket access denied."""

from __future__ import annotations

import socket


def _deny_network(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise RuntimeError("quality gate forbids outbound network access")


socket.create_connection = _deny_network  # type: ignore[assignment]
socket.socket.connect = _deny_network  # type: ignore[assignment]


def main() -> int:
    """Load pytest only after the network boundary is active."""
    import pytest

    return pytest.main(["tests/quality_gate", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())

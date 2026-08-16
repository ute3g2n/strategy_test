"""Security boundary checks for the local-only P5R HTTP adapter."""

from __future__ import annotations

import pytest

from autotrade.application.http_server import ALLOWED_UI_ORIGIN, MAX_JSON_BODY_BYTES, serve


def test_server_rejects_non_loopback_binding() -> None:
    with pytest.raises(ValueError, match="LOOPBACK_ONLY"):
        serve("0.0.0.0", 8765)


def test_local_api_security_limits_are_explicit() -> None:
    assert ALLOWED_UI_ORIGIN == "http://127.0.0.1:4173"
    assert MAX_JSON_BODY_BYTES == 1_000_000

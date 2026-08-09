"""P3-07 compatibility guards after migration to the typed Core entrypoint."""

from __future__ import annotations

import importlib

import pytest


def _operation(name: str):
    try:
        module = importlib.import_module("autotrade.backtest.simulator")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-07 must provide autotrade.backtest.simulator: {error}")
    operation = getattr(module, name, None)
    assert callable(operation), f"autotrade.backtest.simulator.{name} is required"
    return operation


def test_legacy_full_replay_mapping_cannot_certify_a_typed_run() -> None:
    """The typed permutation proof lives in test_backtest_repair_core.py."""
    assert _operation("run_full_replay")({"same_manifest_twice": True}) == {
        "status": "STOPPED",
        "reason": "TYPED_RUN_REQUIRED",
    }


def test_offline_replay_requires_observed_typed_evidence() -> None:
    assert _operation("verify_offline_replay")({"network_attempts": 0, "same_manifest_twice": True}) == {
        "status": "STOPPED",
        "reason": "OFFLINE_PREFLIGHT_UNPROVEN",
    }

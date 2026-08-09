"""P3-07 small integration contracts for deterministic full replay."""

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


def test_full_replay_is_ordered_and_idempotent() -> None:
    assert _operation("run_full_replay")({"same_manifest_twice": True}) == {"ordered_result_hash_equal": True}


def test_offline_replay_has_zero_network_attempts_and_equal_results() -> None:
    assert _operation("verify_offline_replay")({"network_attempts": 0, "same_manifest_twice": True}) == {
        "status": "PASS",
        "result_hash_equal": True,
    }

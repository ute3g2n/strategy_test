"""P3-07 replay-order contracts backed by the immutable replay fixture.

These tests deliberately keep the expected result in the test process.  The
fixture supplies the scenario, while the expected status/reason is a frozen
contract from P3-D05; returning the fixture unchanged must not be sufficient.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "phase3" / "backtest_replay_v1.json"


def _fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _operation(name: str):
    try:
        module = importlib.import_module("autotrade.backtest.replay_order")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-07 must provide autotrade.backtest.replay_order: {error}")
    operation = getattr(module, name, None)
    assert callable(operation), f"autotrade.backtest.replay_order.{name} is required"
    return operation


def test_replay_fixture_schema_and_fill_profile_are_frozen() -> None:
    fixture = _fixture()
    assert fixture["schema_version"] == "p3-backtest-replay-v1"
    assert fixture["replay_order_rule_version"] == "replay-order-v1"
    assert fixture["fill_profile"] == {
        "profile_id": "ConservativeOHLCv1",
        "decimal_quantum": "0.01",
        "rounding_mode": "ROUND_DOWN_FOR_SELL_ROUND_UP_FOR_BUY",
    }
    assert {case["id"] for case in fixture["cases"]} == {
        "next_bar_entry",
        "long_stop_gap",
        "short_stop_gap",
        "intrabar_ambiguous",
        "future_roll",
        "replay_twice",
    }


@pytest.mark.parametrize(
    ("operation_name", "input_value", "expected"),
    [
        (
            "normalize_replay",
            {"source": "order_permuted", "permutations": 2},
            {"status": "STOPPED", "reason": "TYPED_RUN_REQUIRED"},
        ),
        (
            "reject_replay_duplicate",
            {"same_event_id": True, "payload_changed": True},
            {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"},
        ),
        (
            "reject_bad_m1",
            {"bar_kind": "BAR_1M", "utc": False},
            {"status": "STOPPED"},
        ),
        (
            "replay_is_idempotent",
            {"same_manifest": True},
            {"result_hash_equal": True},
        ),
    ],
)
def test_replay_operations_have_deterministic_contract(
    operation_name: str, input_value: dict[str, Any], expected: dict[str, Any]
) -> None:
    first = _operation(operation_name)(input_value)
    second = _operation(operation_name)(dict(input_value))
    assert first == expected
    assert second == first


def test_replay_fixture_captures_next_bar_and_future_information_guards() -> None:
    cases = {case["id"]: case for case in _fixture()["cases"]}
    assert cases["next_bar_entry"]["decision_time_utc"] < cases["next_bar_entry"]["min_eligible_bar_open_utc"]
    assert cases["next_bar_entry"]["expected_same_bar_fill"] is False
    assert cases["future_roll"]["published_at_utc"] > cases["future_roll"]["decision_time_utc"]
    assert cases["future_roll"]["expected_reason"] == "FUTURE_CALENDAR_OR_ROLL"

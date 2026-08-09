"""P3-05 RED boundaries for incomplete, future, and reordered Strategy input."""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "strategy" / "multi_timeframe_v1.json"


def _fixture() -> Mapping[str, Any]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    return fixture


@pytest.mark.parametrize("case_name", ["unclosed", "future", "calendar_mismatch", "duplicate", "out_of_order"])
def test_strategy_rejects_invalid_multitimeframe_input(case_name: str) -> None:
    fixture = _fixture()
    rejection_cases = fixture["rejection_cases"]
    assert isinstance(rejection_cases, dict)
    rejected_case = rejection_cases[case_name]
    assert isinstance(rejected_case, dict)
    input_value = rejected_case["input"]
    expected_value = rejected_case["expected"]

    try:
        service = importlib.import_module("autotrade.strategy.service")
    except ModuleNotFoundError as error:
        pytest.fail(f"{case_name}: P3-06 must provide Strategy service input validation: {error}")

    validate_closed_batch = getattr(service, "validate_closed_batch", None)
    assert callable(validate_closed_batch), "P3-06 must provide validate_closed_batch"
    result = validate_closed_batch(case=input_value, calendar=fixture["calendar"])
    assert result == expected_value


def test_strategy_processes_one_normalized_simultaneous_close_batch_once() -> None:
    fixture = _fixture()
    simultaneous_close = fixture["simultaneous_close"]
    assert isinstance(simultaneous_close, dict)

    try:
        service = importlib.import_module("autotrade.strategy.service")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-06 must provide Strategy service simultaneous-close handling: {error}")

    process_simultaneous_close = getattr(service, "process_simultaneous_close", None)
    assert callable(process_simultaneous_close), "P3-06 must provide process_simultaneous_close"
    actual = process_simultaneous_close(case=simultaneous_close["input"], calendar=fixture["calendar"])
    assert actual == simultaneous_close["expected"]

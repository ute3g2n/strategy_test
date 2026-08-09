"""P3-05R ordinary RED contracts for the named M30 Strategy operations."""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "strategy" / "m30_strategy_v2.json"
_CASE_APIS = {
    "GT-TUR-036": ("autotrade.strategy.service", "validate_m30_configuration"),
    "GT-TUR-037": ("autotrade.strategy.service", "process_m30_cohort"),
    "GT-TUR-038": ("autotrade.strategy.service", "validate_m30_bar_provenance"),
    "GT-TUR-039": ("autotrade.strategy.service", "validate_m30_batch"),
    "GT-TUR-040": ("autotrade.strategy.snapshot", "restore_m30_context"),
}


def _cases() -> Mapping[str, Mapping[str, Any]]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    cases = fixture["cases"]
    assert isinstance(cases, dict)
    return cases


@pytest.mark.parametrize("case_id", sorted(case_id for case_id in _CASE_APIS if case_id != "GT-TUR-038"))
def test_named_m30_strategy_operation_matches_fixed_contract(case_id: str) -> None:
    """Each P3-D04 M30 operation receives input only, never its answer key."""
    module_name, operation_name = _CASE_APIS[case_id]
    case = _cases()[case_id]
    input_value = case["input"]
    expected_value = case["expected"]

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        pytest.fail(f"{case_id}: P3-06 must provide {module_name}.{operation_name}: {error}")
    operation = getattr(module, operation_name, None)
    assert callable(operation), f"{case_id}: {module_name}.{operation_name} is required"

    assert operation(input_value) == expected_value


def test_v2_gt038_keeps_its_approved_historical_acceptance_expectation() -> None:
    """Do not rewrite an approved v2 artifact after the v3 safety revision."""
    expected = _cases()["GT-TUR-038"]["expected"]
    assert expected["accepted"] is True
    assert expected["source_event_count"] == 30
    assert expected["m15_used"] is False

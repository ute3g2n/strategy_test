"""P3-05R ordinary RED contracts for direct M1-to-M30 Backtest aggregation."""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "phase3"
CONTRACT_PATH = FIXTURE_ROOT / "m30_backtest_contract_cases_v2.json"
DATA_PATH = FIXTURE_ROOT / "m30_backtest_v2.json"
MODULE_NAME = "autotrade.backtest.timeframe_aggregator"


def _read_object(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _cases() -> Mapping[str, Mapping[str, Any]]:
    cases = _read_object(CONTRACT_PATH)["cases"]
    assert isinstance(cases, dict)
    return cases


def _input_for_case(case_id: str) -> Mapping[str, Any]:
    case = _cases()[case_id]
    input_value = case["input"]
    assert isinstance(input_value, dict)
    if case_id != "BT-038":
        return input_value

    data = _read_object(DATA_PATH)
    bars = data["direct_m1_bars"]
    anchor = data["session_anchor"]
    assert isinstance(bars, list)
    assert isinstance(anchor, dict)
    return {**input_value, "bars": bars, "session_anchor": anchor}


@pytest.mark.parametrize("case_id", [f"BT-{number:03d}" for number in range(38, 43)])
def test_named_m30_backtest_operation_matches_fixed_contract(case_id: str) -> None:
    """M30 aggregation receives only direct M1 inputs; expected values stay in this test."""
    case = _cases()[case_id]
    operation_name = case["operation"]
    expected_value = case["expected"]
    assert isinstance(operation_name, str)

    try:
        module = importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as error:
        pytest.fail(f"{case_id}: P3-07 must provide {MODULE_NAME}.{operation_name}: {error}")
    operation = getattr(module, operation_name, None)
    assert callable(operation), f"{case_id}: {MODULE_NAME}.{operation_name} is required"

    assert operation(_input_for_case(case_id)) == expected_value

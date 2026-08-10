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
    source_event_ids = data["source_event_ids"]
    assert isinstance(bars, list)
    assert isinstance(anchor, dict)
    assert isinstance(source_event_ids, list)
    return {
        **input_value,
        "bars": bars,
        "session_anchor": anchor,
        "source_event_ids": source_event_ids,
        "parent_manifest_sha256": "sha256:" + "a" * 64,
    }


def _operation(module_name: str, operation_name: str):
    module = importlib.import_module(module_name)
    operation = getattr(module, operation_name, None)
    assert callable(operation), f"{module_name}.{operation_name} is required"
    return operation


@pytest.mark.parametrize("case_id", [f"BT-{number:03d}" for number in range(38, 43)])
def test_named_m30_backtest_operation_matches_fixed_contract(case_id: str) -> None:
    """M30 aggregation receives only direct M1 inputs; migrated boundary cases stay explicit."""
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

    if case_id == "BT-039":
        assert operation(_input_for_case(case_id)) == {
            "status": "STOPPED",
            "reason": "CALENDAR_BOUNDARY_INVALID",
        }
    else:
        actual = operation(_input_for_case(case_id))
        if case_id == "BT-038":
            assert {key: actual[key] for key in expected_value} == expected_value
            assert actual["parent_manifest_sha256"] == "sha256:" + "a" * 64
            assert actual["source_content_sha256"].startswith("sha256:")
            assert actual["source_provenance_sha256"].startswith("sha256:")
        else:
            assert actual == expected_value


def test_m30_source_provenance_changes_when_a_source_bar_changes() -> None:
    aggregate = _operation(MODULE_NAME, "aggregate_m30")
    original = dict(_input_for_case("BT-038"))
    original["bars"] = [dict(bar) for bar in original["bars"]]
    changed = dict(original)
    changed["bars"] = [dict(bar) for bar in original["bars"]]
    changed["bars"][0]["high"] = "110.30"

    first = aggregate(original)
    second = aggregate(changed)

    assert first["timeframe"] == "M30"
    assert second["timeframe"] == "M30"
    assert first["source_event_ids_sha256"] == second["source_event_ids_sha256"]
    assert first["source_content_sha256"] != second["source_content_sha256"]
    assert first["source_provenance_sha256"] != second["source_provenance_sha256"]


def test_m30_rejects_missing_explicit_source_provenance() -> None:
    aggregate = _operation(MODULE_NAME, "aggregate_m30")
    value = dict(_input_for_case("BT-038"))
    value.pop("source_event_ids")
    assert aggregate(value) == {"status": "STOPPED", "reason": "M30_SOURCE_ID_INVALID"}

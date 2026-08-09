"""P3-05 ordinary RED tests for named P3-D05 Backtest operations.

The test gives each operation only its input.  Its expected answer remains in
the test process, so an implementation cannot pass by returning fixture data.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "phase3" / "backtest_contract_cases_v1.json"
_MODULE_BY_CASE = {
    "BT-001": "autotrade.backtest.replay_order",
    "BT-002": "autotrade.backtest.replay_order",
    "BT-003": "autotrade.backtest.replay_order",
    "BT-004": "autotrade.backtest.replay_order",
    "BT-005": "autotrade.backtest.timeframe_aggregator",
    "BT-006": "autotrade.backtest.simulator",
    "BT-007": "autotrade.backtest.calendar_port",
    "BT-008": "autotrade.backtest.timeframe_aggregator",
    "BT-009": "autotrade.backtest.calendar_port",
    "BT-010": "autotrade.backtest.snapshot",
    "BT-011": "autotrade.backtest.snapshot",
    "BT-012": "autotrade.backtest.fill_model",
    "BT-013": "autotrade.backtest.fill_model",
    "BT-014": "autotrade.backtest.fill_model",
    "BT-015": "autotrade.backtest.cost_model",
    "BT-016": "autotrade.backtest.cost_model",
    "BT-017": "autotrade.backtest.roll_model",
    "BT-018": "autotrade.backtest.roll_model",
    "BT-019": "autotrade.backtest.experiment_manifest",
    "BT-020": "autotrade.backtest.simulator",
    "BT-021": "autotrade.backtest.experiment_plan",
    "BT-022": "autotrade.backtest.experiment_plan",
    "BT-023": "autotrade.backtest.experiment_plan",
    "BT-024": "autotrade.backtest.snapshot",
    "BT-025": "autotrade.backtest.result_store",
    "BT-026": "autotrade.backtest.snapshot",
    "BT-027": "autotrade.backtest.simulator",
    "BT-028": "autotrade.backtest.simulator",
    "BT-029": "autotrade.backtest.engine_adapter",
    "BT-030": "autotrade.backtest.engine_adapter",
    "BT-031": "autotrade.backtest.engine_adapter",
    "BT-032": "autotrade.backtest.engine_adapter",
    "BT-033": "autotrade.backtest.timeframe_aggregator",
    "BT-034": "autotrade.backtest.calendar_port",
    "BT-035": "autotrade.backtest.simulator",
    "BT-036": "autotrade.backtest.engine_adapter",
    "BT-037": "autotrade.backtest.simulator",
}

_MIGRATED_EXPECTED = {
    "BT-001": {"status": "STOPPED", "reason": "TYPED_RUN_REQUIRED"},
    "BT-010": {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"},
    "BT-025": {"status": "STOPPED", "reason": "RESULT_NOT_PUBLISHED"},
    "BT-028": {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"},
    "BT-031": {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"},
    "BT-035": {"status": "STOPPED", "reason": "TYPED_RUN_REQUIRED"},
    "BT-036": {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"},
    "BT-037": {"status": "STOPPED", "reason": "OFFLINE_PREFLIGHT_UNPROVEN"},
}


def _cases() -> Mapping[str, Mapping[str, Any]]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    cases = fixture["cases"]
    assert isinstance(cases, dict)
    return cases


@pytest.mark.parametrize("case_id", sorted(_MODULE_BY_CASE))
def test_named_backtest_operation_matches_fixed_contract(case_id: str) -> None:
    """Exercise one operation; migrated legacy mappings use the new fail-closed oracle."""
    case = _cases()[case_id]
    module_name = _MODULE_BY_CASE[case_id]
    operation_name = case["operation"]
    input_value = case["input"]
    expected_value = case["expected"]
    assert isinstance(operation_name, str)

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        pytest.fail(f"{case_id}: P3-07 must provide {module_name}.{operation_name}: {error}")
    operation = getattr(module, operation_name, None)
    assert callable(operation), f"{case_id}: {module_name}.{operation_name} is required"

    assert operation(input_value) == _MIGRATED_EXPECTED.get(case_id, expected_value)

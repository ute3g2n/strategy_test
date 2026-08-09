"""P3-05 ordinary RED tests for the named P3-D04 Strategy operations.

Expected values deliberately stay on the test side.  No production operation
receives a fixture object containing ``expected``.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "strategy" / "turtle_golden_v1.json"
_CASE_APIS = {
    "GT-TUR-001": ("autotrade.strategy.indicators", "true_range_series"),
    "GT-TUR-002": ("autotrade.strategy.indicators", "n_series"),
    "GT-TUR-003": ("autotrade.strategy.indicators", "donchian_channel"),
    "GT-TUR-004": ("autotrade.strategy.turtle_rules", "evaluate_system_1_campaign"),
    "GT-TUR-005": ("autotrade.strategy.turtle_rules", "evaluate_system_2_entry"),
    "GT-TUR-006": ("autotrade.strategy.turtle_rules", "evaluate_intraday_trigger"),
    "GT-TUR-007": ("autotrade.strategy.turtle_rules", "evaluate_close_confirmed_entry"),
    "GT-TUR-008": ("autotrade.strategy.turtle_rules", "evaluate_add"),
    "GT-TUR-009": ("autotrade.strategy.turtle_rules", "evaluate_stop"),
    "GT-TUR-010": ("autotrade.strategy.turtle_rules", "evaluate_strategy_limits"),
    "GT-TUR-011": ("autotrade.strategy.snapshot", "round_trip_snapshot"),
    "GT-TUR-012": ("autotrade.strategy.service", "reject_future_input"),
    "GT-TUR-013": ("autotrade.strategy.service", "process_simultaneous_close"),
    "GT-TUR-014": ("autotrade.strategy.service", "reject_unclosed_batch"),
    "GT-TUR-015": ("autotrade.strategy.service", "canonicalize_batch"),
    "GT-TUR-016": ("autotrade.strategy.service", "validate_calendar_binding"),
    "GT-TUR-017": ("autotrade.strategy.service", "initialize"),
    "GT-TUR-018": ("autotrade.strategy.service", "scan_public_type_boundary"),
    "GT-TUR-019": ("autotrade.strategy.contracts", "parse_decimal_input"),
    "GT-TUR-020": ("autotrade.strategy.turtle_rules", "select_precedence"),
    "GT-TUR-021": ("autotrade.strategy.turtle_rules", "check_long_short_symmetry"),
    "GT-TUR-022": ("autotrade.strategy.snapshot", "reject_context_mismatch"),
    "GT-TUR-023": ("autotrade.strategy.service", "apply_data_gate"),
    "GT-TUR-024": ("autotrade.strategy.service", "scan_forbidden_runtime_calls"),
    "GT-TUR-025": ("autotrade.strategy.service", "build_deterministic_ids"),
    "GT-TUR-026": ("autotrade.strategy.turtle_rules", "evaluate_system_1_failsafe"),
    "GT-TUR-027": ("autotrade.strategy.service", "update_views_then_evaluate"),
    "GT-TUR-028": ("autotrade.strategy.service", "reject_atomically"),
    "GT-TUR-029": ("autotrade.strategy.snapshot", "redelivery_after_restore"),
    "GT-TUR-030": ("autotrade.strategy.turtle_rules", "schedule_single_add"),
    "GT-TUR-031": ("autotrade.strategy.turtle_rules", "evaluate_system_1_exit"),
    "GT-TUR-032": ("autotrade.strategy.turtle_rules", "evaluate_system_2_exit"),
    "GT-TUR-033": ("autotrade.strategy.turtle_rules", "separate_failsafe_identity"),
    "GT-TUR-034": ("autotrade.strategy.turtle_rules", "resolve_virtual_campaign_outcome"),
    "GT-TUR-035": ("autotrade.strategy.service", "enforce_sticky_stop"),
}


def _fixture_cases() -> Mapping[str, Mapping[str, Any]]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    cases = fixture["cases"]
    assert isinstance(cases, dict)
    return cases


@pytest.mark.parametrize("case_id", sorted(_CASE_APIS))
def test_named_strategy_operation_matches_the_golden_expectation(case_id: str) -> None:
    """Each P3-D04 operation receives input only, never the answer key."""
    module_name, operation_name = _CASE_APIS[case_id]
    case = _fixture_cases()[case_id]
    input_value = case["input"]
    expected_value = case["expected"]

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        pytest.fail(f"{case_id}: P3-06 must provide {module_name}.{operation_name}: {error}")
    operation = getattr(module, operation_name, None)
    assert callable(operation), f"{case_id}: {module_name}.{operation_name} is required"

    assert operation(input_value) == expected_value

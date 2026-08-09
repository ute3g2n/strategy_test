"""P3-07 deterministic synthetic performance-input contracts."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "phase3" / "performance_synthetic_v1.json"


def _fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _operation(name: str):
    try:
        module = importlib.import_module("autotrade.backtest.simulator")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-07 must provide autotrade.backtest.simulator: {error}")
    operation = getattr(module, name, None)
    assert callable(operation), f"autotrade.backtest.simulator.{name} is required"
    return operation


def test_performance_fixture_is_synthetic_and_not_an_execution_result() -> None:
    fixture = _fixture()
    assert fixture["schema_version"] == "p3-performance-v1"
    assert fixture["generator_version"] == "synthetic-1m-v1"
    assert fixture["seed"] == 20260809
    assert fixture["markets"] == ["MKT-A", "MKT-B", "MKT-C", "MKT-D", "MKT-E"]
    assert fixture["calendar_years"] == [2024, 2025]
    assert fixture["status_before_h3_1"] == "NOT_EXECUTED"


def test_performance_input_generation_is_repeatable_for_fixed_fixture() -> None:
    fixture = _fixture()
    input_value = {"markets": len(fixture["markets"]), "years": fixture["calendar_years"]}
    first = _operation("generate_performance_input")(input_value)
    second = _operation("generate_performance_input")(dict(input_value))
    assert first == {"deterministic": True}
    assert second == first


def test_performance_measurement_requires_evidence_and_keeps_limits_as_data() -> None:
    fixture = _fixture()
    result = _operation("measure_performance")(
        {
            "elapsed_limit_minutes": fixture["limits"]["elapsed_minutes"],
            "rss_limit_gib": fixture["limits"]["peak_rss_gib"],
        }
    )
    assert result == {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    assert fixture["evidence_schema"] == [
        "cpu",
        "ram_bytes",
        "os",
        "python",
        "elapsed_ms",
        "peak_rss_bytes",
        "input_sha256",
        "result_sha256",
    ]


def test_performance_limits_are_positive_and_explicit() -> None:
    limits = _fixture()["limits"]
    assert limits == {"elapsed_minutes": 30, "peak_rss_gib": 8}
    assert all(isinstance(value, int) and value > 0 for value in limits.values())

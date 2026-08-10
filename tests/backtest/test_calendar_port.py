"""P3-07 CalendarPort contracts for DST and future-publication guards."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "phase3" / "calendar_us_futures_v1.json"


def _fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _operation(name: str):
    try:
        module = importlib.import_module("autotrade.backtest.calendar_port")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-07 must provide autotrade.backtest.calendar_port: {error}")
    operation = getattr(module, name, None)
    assert callable(operation), f"autotrade.backtest.calendar_port.{name} is required"
    return operation


def test_calendar_fixture_schema_and_timezone_are_pinned() -> None:
    fixture = _fixture()
    assert fixture["schema_version"] == "p3-calendar-v1"
    assert fixture["calendar_version"] == "us-futures-fixture-v1"
    assert fixture["timezone"] == "America/Chicago"
    assert fixture["change_rule"].startswith("H3-1 approval")


@pytest.mark.parametrize("case_id", ["normal", "dst_start", "dst_end"])
def test_calendar_aggregation_accepts_normal_and_dst_anchors(case_id: str) -> None:
    cases = {case["id"]: case for case in _fixture()["cases"]}
    case = cases[case_id]
    assert case["session_open_utc"] == case["expected_h4_anchor_utc"]
    assert _operation("aggregate_calendar")({"case": case_id}) == {"status": "PASS"}


def test_all_six_calendar_cases_have_behavioral_decisions() -> None:
    cases = {case["id"]: case for case in _fixture()["cases"]}
    aggregate = _operation("aggregate_calendar")

    assert aggregate(cases["normal"])["calendar_action"] == "OPEN"
    assert aggregate(cases["dst_start"])["calendar_action"] == "OPEN"
    assert aggregate(cases["dst_end"])["calendar_action"] == "OPEN"
    assert aggregate(cases["holiday"]) == {
        "status": "STOPPED",
        "reason": "CALENDAR_BOUNDARY_INVALID",
        "case": "holiday",
        "calendar_action": "CLOSED",
    }
    assert aggregate(cases["short_day"])["calendar_action"] == "OPEN_RESTRICTED"
    assert aggregate(cases["daily_halt"])["calendar_action"] == "HALT_WINDOW"


def test_calendar_window_rejects_short_day_remainder_and_daily_halt() -> None:
    cases = {case["id"]: case for case in _fixture()["cases"]}
    validate = _operation("validate_calendar_window")

    assert (
        validate(
            cases["short_day"],
            "2026-11-27T18:44:00Z",
            "2026-11-27T18:45:00Z",
        )["status"]
        == "PASS"
    )
    assert validate(
        cases["short_day"],
        "2026-11-27T18:45:00Z",
        "2026-11-27T18:46:00Z",
    ) == {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": "short_day"}
    assert validate(
        cases["daily_halt"],
        "2026-01-06T22:15:00Z",
        "2026-01-06T22:16:00Z",
    ) == {"status": "STOPPED", "reason": "CALENDAR_HALT_ACTIVE", "case": "daily_halt"}


def test_calendar_future_publication_is_fail_closed() -> None:
    result = _operation("reject_future_calendar")({"published_after_decision": True})
    assert result == {"status": "STOPPED", "reason": "FUTURE_CALENDAR_OR_ROLL"}


def test_calendar_availability_uses_the_same_future_guard() -> None:
    result = _operation("enforce_calendar_availability")({"published_after_decision": True})
    assert result == {"status": "STOPPED", "reason": "FUTURE_CALENDAR_OR_ROLL"}


def test_calendar_fixture_keeps_holiday_short_day_and_daily_halt_cases() -> None:
    cases = {case["id"]: case for case in _fixture()["cases"]}
    assert cases["holiday"] == {"id": "holiday", "closed": True, "business_date": "2026-12-25"}
    assert cases["short_day"]["session_close_utc"] == "2026-11-27T18:45:00Z"
    assert cases["daily_halt"]["halt_start_utc"] < cases["daily_halt"]["halt_end_utc"]

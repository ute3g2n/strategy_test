from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

_CALENDAR_CASES = {"normal", "dst_start", "dst_end", "holiday", "short_day", "daily_halt"}
_OPEN_CASES = {"normal", "dst_start", "dst_end"}


def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC)


def _valid_window(value: dict[str, Any], open_key: str, close_key: str) -> bool:
    opened = _parse_utc(value.get(open_key))
    closed = _parse_utc(value.get(close_key))
    return opened is not None and closed is not None and opened < closed


def evaluate_calendar_case(value: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one fixed Calendar fixture case without creating a bar."""

    if not isinstance(value, dict):
        return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"}
    case_value = value.get("case", value.get("id"))
    if case_value not in _CALENDAR_CASES:
        return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"}
    case = str(case_value)
    if case in _OPEN_CASES:
        has_close_field = "session_close_utc" in value
        if has_close_field and (
            not _valid_window(value, "session_open_utc", "session_close_utc")
            or (
                "expected_h4_anchor_utc" in value
                and value.get("expected_h4_anchor_utc") != value.get("session_open_utc")
            )
        ):
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
        return {"status": "PASS", "case": case, "calendar_action": "OPEN"}
    if case == "holiday":
        if value.get("closed") is not True or not isinstance(value.get("business_date"), str):
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
        return {
            "status": "STOPPED",
            "reason": "CALENDAR_BOUNDARY_INVALID",
            "case": case,
            "calendar_action": "CLOSED",
        }
    if case == "short_day":
        if not _valid_window(value, "session_open_utc", "session_close_utc"):
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
        return {
            "status": "PASS",
            "case": case,
            "calendar_action": "OPEN_RESTRICTED",
            "session_close_utc": value["session_close_utc"],
        }
    if not _valid_window(value, "halt_start_utc", "halt_end_utc"):
        return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
    return {
        "status": "PASS",
        "case": case,
        "calendar_action": "HALT_WINDOW",
        "halt_start_utc": value["halt_start_utc"],
        "halt_end_utc": value["halt_end_utc"],
    }


def aggregate_calendar(value: dict[str, Any]) -> dict[str, Any]:
    result = evaluate_calendar_case(value)
    if (
        result.get("status") == "PASS"
        and result.get("case") in _OPEN_CASES
        and not any(key in value for key in ("session_open_utc", "session_close_utc", "expected_h4_anchor_utc"))
    ):
        return {"status": "PASS"}
    return result


def validate_calendar_window(value: dict[str, Any], event_time_utc: str, bar_close_time_utc: str) -> dict[str, Any]:
    """Reject bars outside an approved session, holiday, or daily-halt window."""

    result = evaluate_calendar_case(value)
    if result.get("status") != "PASS":
        return result
    event_time = _parse_utc(event_time_utc)
    bar_close = _parse_utc(bar_close_time_utc)
    if event_time is None or bar_close is None or event_time >= bar_close:
        return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": result.get("case")}
    case = result["case"]
    if case in _OPEN_CASES:
        opened = _parse_utc(value.get("session_open_utc"))
        closed = _parse_utc(value.get("session_close_utc"))
        if opened is not None and event_time < opened:
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
        if closed is not None and bar_close > closed:
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
        return {"status": "PASS", "case": case}
    if case == "short_day":
        opened = _parse_utc(value["session_open_utc"])
        closed = _parse_utc(value["session_close_utc"])
        if opened is None or closed is None or event_time < opened or bar_close > closed:
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID", "case": case}
        return {"status": "PASS", "case": case}
    halt_start = _parse_utc(value["halt_start_utc"])
    halt_end = _parse_utc(value["halt_end_utc"])
    if halt_start is None or halt_end is None or event_time < halt_end and bar_close > halt_start:
        return {"status": "STOPPED", "reason": "CALENDAR_HALT_ACTIVE", "case": case}
    return {"status": "PASS", "case": case}


def reject_future_calendar(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("published_after_decision") is True:
        return {"status": "STOPPED", "reason": "FUTURE_CALENDAR_OR_ROLL"}
    if not isinstance(value.get("published_after_decision"), bool):
        return {"status": "STOPPED", "reason": "CALENDAR_AVAILABILITY_UNKNOWN"}
    return {"status": "PASS"}


def enforce_calendar_availability(value: dict[str, Any]) -> dict[str, Any]:
    return reject_future_calendar(value)

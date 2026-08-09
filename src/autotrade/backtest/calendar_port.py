from __future__ import annotations

from typing import Any


def aggregate_calendar(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("case") not in {"dst_start", "dst_end", "normal"}:
        return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"}
    return {"status": "PASS"}


def reject_future_calendar(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("published_after_decision") is True:
        return {"status": "STOPPED", "reason": "FUTURE_CALENDAR_OR_ROLL"}
    if not isinstance(value.get("published_after_decision"), bool):
        return {"status": "STOPPED", "reason": "CALENDAR_AVAILABILITY_UNKNOWN"}
    return {"status": "PASS"}


def enforce_calendar_availability(value: dict[str, Any]) -> dict[str, Any]:
    return reject_future_calendar(value)

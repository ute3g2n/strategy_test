from __future__ import annotations

from typing import Any


def apply_roll(value: dict[str, Any]) -> dict[str, Any]:
    return (
        {"status": "PASS"}
        if value.get("catalog_resolved") and value.get("published_before_decision")
        else {"status": "STOPPED"}
    )


def reject_roll_conflict(value: dict[str, Any]) -> dict[str, Any]:
    conflict = value.get("roll_and_stop_same_bar")
    if not isinstance(conflict, bool):
        return {"status": "STOPPED", "reason": "ROLL_CONFLICT_UNKNOWN"}
    return {"status": "STOPPED"} if conflict else {"status": "PASS"}

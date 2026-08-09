from __future__ import annotations

from typing import Any


def lock_holdout(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("holdout_read_before_final"), bool):
        return {"status": "STOPPED", "reason": "HOLDOUT_EARLY_ACCESS"}
    return (
        {"status": "STOPPED", "reason": "HOLDOUT_EARLY_ACCESS"}
        if value.get("holdout_read_before_final")
        else {"status": "PASS"}
    )


def reject_wall_clock(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("wall_clock_read"), bool):
        return {"status": "STOPPED", "reason": "WALL_CLOCK_DEPENDENCY"}
    return (
        {"status": "STOPPED", "reason": "WALL_CLOCK_DEPENDENCY"} if value.get("wall_clock_read") else {"status": "PASS"}
    )


def reject_plan_mutation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("plan_changed_after_result"), bool):
        return {"status": "STOPPED", "reason": "EXPERIMENT_PLAN_MUTATED"}
    return (
        {"status": "STOPPED", "reason": "EXPERIMENT_PLAN_MUTATED"}
        if value.get("plan_changed_after_result")
        else {"status": "PASS"}
    )

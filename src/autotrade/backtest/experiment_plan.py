from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .contracts import canonical_hash


def _require_utc(value: datetime, *, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{name} must be UTC")


@dataclass(frozen=True)
class TimeWindow:
    start_utc: datetime
    end_utc: datetime

    def __post_init__(self) -> None:
        _require_utc(self.start_utc, name="start_utc")
        _require_utc(self.end_utc, name="end_utc")
        if self.start_utc >= self.end_utc:
            raise ValueError("window start before end is required")

    def as_dict(self) -> dict[str, datetime]:
        return {"start_utc": self.start_utc, "end_utc": self.end_utc}


@dataclass(frozen=True)
class WalkForwardWindow:
    train: TimeWindow
    validation: TimeWindow
    holdout: TimeWindow | None = None


class HoldoutAccessError(RuntimeError):
    """A holdout access attempt that cannot influence candidate selection."""


@dataclass
class ExperimentPlan:
    plan_id: str
    train: TimeWindow
    validation: TimeWindow
    holdout: TimeWindow
    walk_forward_windows: tuple[WalkForwardWindow, ...]
    candidate_config_ids: tuple[str, ...]
    plan_sha256: str
    _holdout_read_count: int = field(default=0, init=False, repr=False)

    @property
    def holdout_read_count(self) -> int:
        return self._holdout_read_count

    def strategy_view(self) -> dict[str, Any]:
        """Expose selection inputs without exposing holdout boundaries/results."""

        return {
            "plan_id": self.plan_id,
            "train": self.train.as_dict(),
            "validation": self.validation.as_dict(),
            "candidate_config_ids": self.candidate_config_ids,
        }

    def read_holdout(self, *, finalized: bool) -> TimeWindow:
        if not finalized:
            raise HoldoutAccessError("HOLDOUT_EARLY_ACCESS")
        if self._holdout_read_count:
            raise HoldoutAccessError("HOLDOUT_ALREADY_READ")
        self._holdout_read_count += 1
        return self.holdout

    def validate_after_result(self, observed_plan_sha256: str) -> dict[str, str]:
        if observed_plan_sha256 != self.plan_sha256:
            return {"status": "STOPPED", "reason": "EXPERIMENT_PLAN_MUTATED"}
        return {"status": "PASS"}


def _plan_payload(
    *,
    plan_id: str,
    train: TimeWindow,
    validation: TimeWindow,
    holdout: TimeWindow,
    walk_forward_windows: tuple[WalkForwardWindow, ...],
    candidate_config_ids: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "plan_id": plan_id,
        "train": train.as_dict(),
        "validation": validation.as_dict(),
        "holdout": holdout.as_dict(),
        "walk_forward_windows": [
            {
                "train": window.train.as_dict(),
                "validation": window.validation.as_dict(),
                "holdout": window.holdout.as_dict() if window.holdout else None,
            }
            for window in walk_forward_windows
        ],
        "candidate_config_ids": candidate_config_ids,
    }


def create_experiment_plan(
    *,
    plan_id: str,
    train: TimeWindow,
    validation: TimeWindow,
    holdout: TimeWindow,
    candidate_config_ids: tuple[str, ...],
    walk_forward_windows: tuple[WalkForwardWindow, ...] = (),
) -> ExperimentPlan:
    if not plan_id or any(part in {".", ".."} for part in plan_id.replace("\\", "/").split("/")):
        raise ValueError("plan_id is invalid")
    if not candidate_config_ids or any(not isinstance(item, str) or not item for item in candidate_config_ids):
        raise ValueError("candidate_config_ids are required")
    if len(set(candidate_config_ids)) != len(candidate_config_ids):
        raise ValueError("candidate_config_ids must be unique")
    windows = (train, validation, holdout)
    if any(left.end_utc > right.start_utc for left, right in zip(windows, windows[1:], strict=False)):
        raise ValueError("windows must not overlap")
    payload = _plan_payload(
        plan_id=plan_id,
        train=train,
        validation=validation,
        holdout=holdout,
        walk_forward_windows=walk_forward_windows,
        candidate_config_ids=candidate_config_ids,
    )
    return ExperimentPlan(
        plan_id,
        train,
        validation,
        holdout,
        walk_forward_windows,
        candidate_config_ids,
        canonical_hash(payload),
    )


def partition_time(plan: ExperimentPlan, value: datetime) -> str:
    _require_utc(value, name="value")
    if plan.train.start_utc <= value < plan.train.end_utc:
        return "TRAIN"
    if plan.validation.start_utc <= value < plan.validation.end_utc:
        return "VALIDATION"
    if plan.holdout.start_utc <= value < plan.holdout.end_utc:
        return "HOLDOUT"
    return "OUT_OF_PLAN"


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

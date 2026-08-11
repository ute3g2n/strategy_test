"""Explicit fail-closed state transition guards."""

from __future__ import annotations

from collections.abc import Mapping

from .contracts import JobStatus, QueueStatus, RunStatus


class InvalidTransition(ValueError):
    """Raised when a persisted state cannot be advanced by the operation."""


RUN_TRANSITIONS: Mapping[RunStatus, frozenset[RunStatus]] = {
    # SUCCEEDED/FAILED/STOPPED/PARTIAL_FAILED are available from DRAFT only
    # for the read-only aggregate projection of an unqueued Sweep parent.
    RunStatus.DRAFT: frozenset(
        {
            RunStatus.REJECTED,
            RunStatus.QUEUED,
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.STOPPED,
            RunStatus.PARTIAL_FAILED,
            RunStatus.RECOVERY_REQUIRED,
        }
    ),
    RunStatus.QUEUED: frozenset({RunStatus.RUNNING, RunStatus.CANCELLED, RunStatus.STOP_REQUESTED}),
    RunStatus.RUNNING: frozenset(
        {
            RunStatus.STOP_REQUESTED,
            RunStatus.STOPPED,
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.RECOVERY_REQUIRED,
        }
    ),
    RunStatus.STOP_REQUESTED: frozenset({RunStatus.STOPPED, RunStatus.CANCELLED, RunStatus.RECOVERY_REQUIRED}),
    RunStatus.STOPPED: frozenset({RunStatus.RECOVERY_REQUIRED}),
    RunStatus.RECOVERY_REQUIRED: frozenset({RunStatus.QUEUED, RunStatus.FAILED}),
    RunStatus.PARTIAL_FAILED: frozenset(),
    RunStatus.REJECTED: frozenset(),
    RunStatus.SUCCEEDED: frozenset(),
    RunStatus.FAILED: frozenset(),
    RunStatus.CANCELLED: frozenset(),
}

JOB_TRANSITIONS: Mapping[JobStatus, frozenset[JobStatus]] = {
    JobStatus.CREATED: frozenset({JobStatus.QUEUED, JobStatus.CANCELLED}),
    JobStatus.QUEUED: frozenset({JobStatus.RUNNING, JobStatus.CANCEL_REQUESTED, JobStatus.CANCELLED}),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.CANCEL_REQUESTED,
            JobStatus.STOPPED,
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.RECOVERY_REQUIRED,
        }
    ),
    JobStatus.CANCEL_REQUESTED: frozenset({JobStatus.CANCELLED, JobStatus.STOPPED, JobStatus.RECOVERY_REQUIRED}),
    JobStatus.STOPPED: frozenset({JobStatus.RECOVERY_REQUIRED}),
    JobStatus.RECOVERY_REQUIRED: frozenset({JobStatus.QUEUED, JobStatus.FAILED}),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
}

QUEUE_TRANSITIONS: Mapping[QueueStatus, frozenset[QueueStatus]] = {
    QueueStatus.WAITING: frozenset({QueueStatus.LEASED, QueueStatus.CANCELLED}),
    QueueStatus.LEASED: frozenset({QueueStatus.RUNNING, QueueStatus.RELEASED}),
    QueueStatus.RUNNING: frozenset({QueueStatus.DONE, QueueStatus.RELEASED}),
    QueueStatus.DONE: frozenset(),
    QueueStatus.RELEASED: frozenset(),
    QueueStatus.CANCELLED: frozenset(),
}


def ensure_transition(current: str, target: str, *, domain: str) -> None:
    allowed_values: set[str]
    try:
        if domain == "run":
            allowed_values = {item.value for item in RUN_TRANSITIONS[RunStatus(current)]}
        elif domain == "job":
            allowed_values = {item.value for item in JOB_TRANSITIONS[JobStatus(current)]}
        elif domain == "queue":
            allowed_values = {item.value for item in QUEUE_TRANSITIONS[QueueStatus(current)]}
        else:
            raise InvalidTransition(f"unknown state domain: {domain}")
    except (KeyError, ValueError) as error:
        raise InvalidTransition(f"{domain}: {current} -> {target} is not allowed") from error
    if target not in allowed_values:
        raise InvalidTransition(f"{domain}: invalid target")

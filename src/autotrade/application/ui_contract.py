"""Fixed local UI view boundary used by P4-06 and P4-08."""

from __future__ import annotations

from typing import Final

UI_CONTRACT_VERSION: Final[str] = "P4-UI-CONTRACT-V1"
SUPPORTED_STATES: Final[tuple[str, ...]] = (
    "INITIAL",
    "INPUT_INVALID",
    "PREFLIGHT_FAILED",
    "QUEUE_WAITING",
    "RUNNING",
    "STOP_CANCEL",
    "SUCCESS",
    "PARTIAL_FAILURE",
    "RECOVERY",
    "EVIDENCE_REFERENCE",
)

_UNVERIFIED_OPERATION_FAILURES: Final[frozenset[str]] = frozenset(
    {"RESTART", "PARTIAL_FAILURE", "MIGRATION_FAILURE"}
)


def validate_ui_payload(payload: dict[str, object]) -> None:
    if payload.get("contract_version") != UI_CONTRACT_VERSION:
        raise ValueError("UI_CONTRACT_VERSION_MISMATCH")
    if payload.get("state") not in SUPPORTED_STATES:
        raise ValueError("UI_STATE_UNSUPPORTED")
    for key in ("absolute_path", "secret", "broker_url", "order_id"):
        if key in payload:
            raise ValueError("UI_FORBIDDEN_FIELD")


def render_preflight_and_operation_view(
    payload: dict[str, object]
) -> dict[str, object]:
    """Return a fail-closed view result for an unverified operation.

    Restart, partial-failure, and migration-failure states must not enter the
    Manual registry as if the operation had been verified.  The UI may show
    the failure and its audit context, but this pure boundary performs no
    persistence, filesystem, network, or registry mutation.
    """

    failure_reason = payload.get("failure_reason")
    operation_failure = payload.get("restart_or_partial_or_migration_failure")
    failure_kind = (
        operation_failure if isinstance(operation_failure, str) else failure_reason
    )
    manual_registry_status = payload.get("manual_registry_status")
    audit = {
        field: payload.get(field)
        for field in (
            "operator",
            "reason",
            "target",
            "status_before",
            "status_after",
            "dependency_count",
            "request_id",
            "correlation_id",
            "failure_reason",
        )
    }

    if (
        failure_kind in _UNVERIFIED_OPERATION_FAILURES
        or manual_registry_status != "REGISTERED"
    ):
        return {
            "error_code": "MANUAL_EVIDENCE_REQUIRED",
            "manual_registry_updated": False,
            "audit": audit,
        }

    return {
        "error_code": None,
        "manual_registry_updated": True,
        "audit": audit,
    }

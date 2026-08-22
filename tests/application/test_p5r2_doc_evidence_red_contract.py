"""P5R2 RED contract for auditable UI/Manual/Evidence operation outcomes."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest

from autotrade.application import ui_contract


def _require_contract(module: ModuleType, name: str, requirement: str) -> Callable[..., object]:
    operation = getattr(module, name, None)
    assert callable(operation), f"{requirement} RED: 未実装契約 {module.__name__}.{name}"
    return operation


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


@pytest.mark.parametrize("failure_kind", ("RESTART", "PARTIAL_FAILURE", "MIGRATION_FAILURE"))
def test_unverified_operation_cannot_enter_manual_registry_and_keeps_audit_context(failure_kind: str) -> None:
    operation = _require_contract(
        ui_contract,
        "render_preflight_and_operation_view",
        "P5R2-CREQ-DOC-001",
    )

    result = operation(
        {
            "operator": "local-operator",
            "reason": "local RED contract",
            "target": "RUN-LOCAL-P5R2-001",
            "status_before": "RUNNING",
            "status_after": "RECOVERY_REQUIRED",
            "dependency_count": 2,
            "request_id": "request-doc-001",
            "correlation_id": "correlation-doc-001",
            "failure_reason": failure_kind,
            "manual_registry_status": "UNREGISTERED",
            "restart_or_partial_or_migration_failure": failure_kind,
        }
    )

    assert _field(result, "error_code") == "MANUAL_EVIDENCE_REQUIRED"
    assert _field(result, "manual_registry_updated") is False
    assert _field(result, "audit")

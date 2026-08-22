"""P5R2 RED contracts for shared Run cancel state and OperationGuard."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest

from autotrade.application import run_service


def _require_contract(module: ModuleType, name: str, requirement: str) -> Callable[..., object]:
    operation = getattr(module, name, None)
    assert callable(operation), f"{requirement} RED: 未実装契約 {module.__name__}.{name}"
    return operation


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _cancel_request(*, state: str, token: str, origin_screen: str, tab_id: str = "tab-1") -> dict[str, object]:
    return {
        "run_id": "RUN-LOCAL-P5R2-001",
        "operation_token": token,
        "request_id": f"request-{token}",
        "actor": "local-operator",
        "origin_screen": origin_screen,
        "tab_id": tab_id,
        "reason": "operator requested cancel",
        "current_state": state,
    }


def test_three_screens_use_one_cancel_result_and_guard_duplicate_requests() -> None:
    operation = _require_contract(
        run_service,
        "request_run_cancel",
        "P5R2-CREQ-RUN-001",
    )

    results = [
        operation(_cancel_request(state="QUEUED", token="token-1", origin_screen=screen))
        for screen in ("EXECUTION_LIST", "PROGRESS", "RESULT_SUMMARY")
    ]

    assert {_field(result, "status_after") for result in results} == {"CANCELLED"}
    assert len({_field(result, "audit_id") for result in results}) == 1

    duplicate = operation(_cancel_request(state="RUNNING", token="token-1", origin_screen="PROGRESS"))
    replay_from_other_tab = operation(
        _cancel_request(state="RUNNING", token="token-2", origin_screen="RESULT_SUMMARY", tab_id="tab-2")
    )
    assert _field(duplicate, "accepted") is False
    assert _field(replay_from_other_tab, "accepted") is False
    assert _field(duplicate, "error_code") in {"OPERATION_IN_FLIGHT", "ALREADY_CANCELLED"}


@pytest.mark.parametrize("terminal_state", ("SUCCEEDED", "FAILED", "CANCELLED", "RECOVERY_REQUIRED"))
def test_terminal_cancel_does_not_change_state_and_is_audited(terminal_state: str) -> None:
    operation = _require_contract(
        run_service,
        "request_run_cancel",
        "P5R2-CREQ-RUN-001",
    )

    result = operation(
        _cancel_request(state=terminal_state, token=f"terminal-{terminal_state}", origin_screen="PROGRESS")
    )

    assert _field(result, "accepted") is False
    assert _field(result, "status_before") == terminal_state
    assert _field(result, "status_after") == terminal_state
    assert _field(result, "error_code") == "TERMINAL_STATE"
    assert _field(result, "audit_id")

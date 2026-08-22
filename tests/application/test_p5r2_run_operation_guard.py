"""Focused P5R2-15 tests for the shared local Run OperationGuard."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from autotrade.application.run_service import OperationGuard


def _request(token: str, *, state: str = "RUNNING", screen: str = "PROGRESS") -> dict[str, object]:
    return {
        "run_id": "RUN-P5R2-GUARD-001",
        "operation_token": token,
        "request_id": f"request-{token}",
        "actor": "local-operator",
        "origin_screen": screen,
        "tab_id": f"tab-{screen}",
        "reason": "operator requested cancel",
        "current_state": state,
        "current_revision": 4,
        "expected_revision": 4,
    }


def test_concurrent_cancel_requests_have_one_state_change_and_one_audit() -> None:
    guard = OperationGuard()

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(
            executor.map(
                lambda index: guard.request_run_cancel(
                    _request(f"token-{index}", screen=("EXECUTION_LIST", "PROGRESS", "RESULT_SUMMARY")[index % 3])
                ),
                range(6),
            )
        )

    assert sum(result["accepted"] is True for result in results) == 1
    assert {result["status_after"] for result in results} == {"STOP_REQUESTED"}
    assert len({result["audit_id"] for result in results}) == 1
    assert len(guard.audit_log("RUN-P5R2-GUARD-001")) == 1


def test_same_token_replay_is_rejected_without_a_second_revision() -> None:
    guard = OperationGuard()
    first = guard.request_run_cancel(_request("token-replay"))
    replay = guard.request_run_cancel(_request("token-replay", state="QUEUED", screen="RESULT_SUMMARY"))

    assert first["accepted"] is True
    assert replay["accepted"] is False
    assert replay["error_code"] == "OPERATION_IN_FLIGHT"
    assert replay["replayed"] is True
    assert replay["audit_id"] == first["audit_id"]
    assert replay["revision_after"] == first["revision_after"]
    assert replay["prior_result"]["audit_id"] == first["audit_id"]


def test_revision_conflict_keeps_run_state_unchanged_and_is_audited() -> None:
    guard = OperationGuard()
    request = _request("token-revision-conflict")
    request["expected_revision"] = 3

    result = guard.request_run_cancel(request)

    assert result["accepted"] is False
    assert result["error_code"] == "REVISION_CONFLICT"
    assert result["status_before"] == "RUNNING"
    assert result["status_after"] == "RUNNING"
    assert result["revision_before"] == 4
    assert result["revision_after"] == 4
    assert len(guard.audit_log("RUN-P5R2-GUARD-001")) == 1


def test_terminal_cancel_is_state_invariant_and_keeps_reason_in_audit() -> None:
    guard = OperationGuard()
    result = guard.request_run_cancel(
        {
            **_request("token-terminal", state="PARTIAL_FAILED"),
            "reason": "terminal result must remain unchanged",
        }
    )

    assert result["accepted"] is False
    assert result["error_code"] == "TERMINAL_STATE"
    assert result["status_before"] == "PARTIAL_FAILED"
    assert result["status_after"] == "PARTIAL_FAILED"
    assert result["audit"]["reason"] == "terminal result must remain unchanged"

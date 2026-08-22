"""Focused P5R2-15 tests for fail-closed ResultArtifact deletion."""

from __future__ import annotations

from pathlib import Path

from autotrade.application.result_view import LocalResultArtifacts


def _request(root: Path, token: str = "delete-token-1") -> dict[str, object]:
    return {
        "logical_artifact_id": "RESULT-P5R2-GUARD-001",
        "artifact_kind": "RESULT",
        "run_state": "SUCCEEDED",
        "operation_token": token,
        "request_id": f"request-{token}",
        "confirmation": True,
        "allowed_root": str(root),
        "physical_io_allowed": True,
    }


def test_delete_gate_rejects_terminal_result_and_leaves_fixture_untouched(tmp_path: Path) -> None:
    artifacts = LocalResultArtifacts(tmp_path)
    sentinel = tmp_path / "results" / "RUN-P5R2-GUARD-001" / "result.json"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep", encoding="utf-8")

    result = artifacts.delete_result_artifact(_request(tmp_path))

    assert result["accepted"] is False
    assert result["deleted"] is False
    assert result["error_code"] == "DELETE_GATE_REQUIRED"
    assert result["physical_io_performed"] is False
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_delete_replay_returns_same_rejection_without_new_audit(tmp_path: Path) -> None:
    artifacts = LocalResultArtifacts(tmp_path)
    first = artifacts.delete_result_artifact(_request(tmp_path))
    replay = artifacts.delete_result_artifact({**_request(tmp_path), "request_id": "second-request"})

    assert first["error_code"] == "DELETE_GATE_REQUIRED"
    assert replay["error_code"] == "DELETE_GATE_REQUIRED"
    assert replay["replayed"] is True
    assert replay["audit_id"] == first["audit_id"]
    assert len(artifacts.delete_audit_log()) == 1


def test_path_argument_is_rejected_even_when_delete_gate_is_not_bypassed(tmp_path: Path) -> None:
    artifacts = LocalResultArtifacts(tmp_path)
    result = artifacts.delete_result_artifact(
        {
            **_request(tmp_path),
            "path": str(tmp_path / "results" / "other"),
        }
    )

    assert result["accepted"] is False
    assert result["error_code"] == "PATH_SAFETY_REJECTED"
    assert result["physical_io_performed"] is False

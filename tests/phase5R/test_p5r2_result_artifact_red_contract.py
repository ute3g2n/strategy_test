"""P5R2 RED guards for temporary ResultArtifact deletion only."""

from __future__ import annotations

from autotrade.application.result_view import LocalResultArtifacts


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def test_result_artifact_delete_guard_rejects_protected_active_and_unsafe_targets(tmp_path) -> None:
    artifacts = LocalResultArtifacts(tmp_path)
    delete = getattr(artifacts, "delete_result_artifact", None)
    assert callable(delete), "P5R2-CREQ-RUN-002 RED: LocalResultArtifacts.delete_result_artifact が未実装"

    for candidate in (
        {"logical_artifact_id": "CSV-LOCAL-001", "artifact_kind": "CSV", "run_state": "SUCCEEDED"},
        {"logical_artifact_id": "DATA-LOCAL-001", "artifact_kind": "HISTORICAL_DATA", "run_state": "SUCCEEDED"},
        {"logical_artifact_id": "RESULT-LOCAL-001", "artifact_kind": "RESULT", "run_state": "RUNNING"},
        {"logical_artifact_id": "../outside", "artifact_kind": "RESULT", "run_state": "SUCCEEDED"},
        {"logical_artifact_id": "RESULT-SYMLINK", "artifact_kind": "RESULT", "path_kind": "SYMLINK_OR_REPARSE"},
        {"logical_artifact_id": "RESULT-OTHER-ID", "artifact_kind": "RESULT", "path_kind": "ID_MISMATCH"},
    ):
        result = delete(
            {
                **candidate,
                "operation_token": "delete-token-1",
                "confirmation": True,
                "allowed_root": str(tmp_path),
                "physical_io_allowed": False,
            }
        )
        assert _field(result, "accepted") is False
        assert _field(result, "error_code") in {
            "PROTECTED_ARTIFACT",
            "ACTIVE_RUN",
            "PATH_SAFETY_REJECTED",
            "ARTIFACT_ID_MISMATCH",
        }

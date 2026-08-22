"""P5R2-21 bounded physical ResultArtifact deletion contract."""

from __future__ import annotations

import json
from pathlib import Path

from autotrade.application.backtest_product import BacktestProductService, _Run
from autotrade.application.result_view import LocalResultArtifacts


def _request(root: Path, run_id: str = "RUN-P5R2-DELETE-TEMP-001", token: str = "delete-token-1") -> dict[str, object]:
    return {
        "logical_artifact_id": f"RESULT-OWNER-{run_id}",
        "artifact_kind": "RESULT",
        "run_state": "SUCCEEDED",
        "operation_token": token,
        "request_id": f"request-{token}",
        "confirmation": True,
        "allowed_root": str(root),
        "physical_io_allowed": True,
    }


def _create_result_fixture(root: Path, run_id: str) -> Path:
    target = root / "results" / run_id
    target.mkdir(parents=True)
    (target / "result.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    (target / "result.commit.json").write_text(json.dumps({"run_id": run_id, "status": "COMMITTED"}), encoding="utf-8")
    return target


def test_approved_delete_removes_only_result_artifact_and_keeps_protected_files(tmp_path: Path) -> None:
    artifacts = LocalResultArtifacts(tmp_path, physical_delete_enabled=True)
    run_id = "RUN-P5R2-DELETE-TEMP-001"
    target = _create_result_fixture(tmp_path, run_id)
    csv_file = tmp_path / "exports" / "CSV-PROTECTED-001" / "result.csv"
    data_file = tmp_path / "historical" / "BTCUSDT-1m.csv"
    audit_file = tmp_path / "audit" / "run-audit.json"
    evidence_file = tmp_path / "evidence" / "verification.json"
    for path in (csv_file, data_file, audit_file, evidence_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("keep", encoding="utf-8")

    result = artifacts.delete_result_artifact(_request(tmp_path, run_id))

    assert result["accepted"] is True
    assert result["deleted"] is True
    assert result["status"] == "RESULT_DELETED"
    assert result["artifact_state"] == "DELETED"
    assert result["physical_io_performed"] is True
    assert not target.exists()
    assert all(path.read_text(encoding="utf-8") == "keep" for path in (csv_file, data_file, audit_file, evidence_file))
    assert result["audit"]["event_type"] == "RESULT_DELETED"
    assert artifacts.delete_audit_log()[-1]["event_type"] == "RESULT_DELETED"


def test_delete_is_idempotent_for_replay_and_new_token_after_tombstone(tmp_path: Path) -> None:
    artifacts = LocalResultArtifacts(tmp_path, physical_delete_enabled=True)
    run_id = "RUN-P5R2-DELETE-TEMP-002"
    _create_result_fixture(tmp_path, run_id)

    first = artifacts.delete_result_artifact(_request(tmp_path, run_id, "delete-token-1"))
    replay = artifacts.delete_result_artifact(_request(tmp_path, run_id, "delete-token-1"))
    second_token = artifacts.delete_result_artifact(_request(tmp_path, run_id, "delete-token-2"))

    assert first["status"] == "RESULT_DELETED"
    assert replay["replayed"] is True
    assert replay["audit_id"] == first["audit_id"]
    assert second_token["status"] == "RESULT_DELETED"
    assert second_token["deleted"] is False
    assert second_token["physical_io_performed"] is False
    assert len(artifacts.delete_audit_log()) == 1


def test_delete_rejects_active_run_unsafe_resolution_and_gate_disabled(tmp_path: Path) -> None:
    run_id = "RUN-P5R2-DELETE-TEMP-003"
    _create_result_fixture(tmp_path, run_id)

    gate_disabled = LocalResultArtifacts(tmp_path)
    rejected = gate_disabled.delete_result_artifact(_request(tmp_path, run_id))
    assert rejected["accepted"] is False
    assert rejected["error_code"] == "DELETE_GATE_REQUIRED"
    assert (tmp_path / "results" / run_id).exists()

    approved = LocalResultArtifacts(tmp_path, physical_delete_enabled=True)
    active = approved.delete_result_artifact(
        {**_request(tmp_path, run_id, "delete-token-active"), "run_state": "RUNNING"}
    )
    unsafe = approved.delete_result_artifact(
        {**_request(tmp_path, run_id, "delete-token-unsafe"), "path_kind": "TOCTOU"}
    )
    assert active["error_code"] == "ACTIVE_RUN"
    assert unsafe["error_code"] == "PATH_SAFETY_REJECTED"
    assert (tmp_path / "results" / run_id).exists()


def test_service_persists_result_deleted_and_restart_does_not_request_recovery(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    runtime_root = tmp_path / "runtime"
    service = BacktestProductService(
        data_root=data_root,
        runtime_root=runtime_root,
        delete_gate_approved=True,
    )
    run_id = "RUN-P5R2-DELETE-TEMP-004"
    run = _Run(
        run_id=run_id,
        spec={
            "symbol": "BTCUSDT",
            "market": "SPOT",
            "timeframe": "30m",
            "timezone": "UTC",
            "calendar": "CRYPTO_24_7_UTC",
            "start": "2025-02-24T00:00:00Z",
            "end": "2025-02-24T01:00:00Z",
            "strategy": "TURTLE_SYS1",
            "parameters": {
                "entry_lookback": "8",
                "exit_lookback": "4",
                "initial_balance": "100000",
                "fee_bps": "1.0",
                "slippage_bps": "2.0",
            },
        },
        status="SUCCEEDED",
        progress=1,
        total=1,
        metrics={"ending_balance": "100000.00"},
    )
    service._runs[run_id] = run
    service._persist_run(run)
    service._history_catalog.write_result(
        run_id,
        {
            "run_id": run_id,
            "metrics": run.metrics or {},
            "rows": [],
            "provenance": {"source_mode": "LOCAL_FAKE"},
            "result_publish_id": f"RESULT-OWNER-{run_id}",
        },
    )

    result = service.delete_result_artifact(
        {
            "logical_artifact_id": f"RESULT-OWNER-{run_id}",
            "artifact_kind": "RESULT",
            "confirmation": True,
            "operation_token": "delete-service-token-1",
            "request_id": "delete-service-request-1",
        }
    )

    assert result["accepted"] is True
    assert result["status"] == "RESULT_DELETED"
    current = service.get_run(run_id)
    assert current["result_deleted"] is True
    assert current["result_reference"] is None
    assert current["result_publish_id"] is None

    restarted = BacktestProductService(data_root=data_root, runtime_root=runtime_root, delete_gate_approved=True)
    restored = restarted.get_run(run_id)
    assert restored["status"] == "SUCCEEDED"
    assert restored["result_deleted"] is True
    assert restored["recovery_mode"] == "RESULT_DELETED"
    assert restarted.recovery_report()["status"] == "CLEAN"


def test_service_rejects_unknown_run_without_physical_io(tmp_path: Path) -> None:
    run_id = "RUN-P5R2-DELETE-UNKNOWN-001"
    _create_result_fixture(tmp_path, run_id)
    service = BacktestProductService(
        data_root=tmp_path / "data",
        runtime_root=tmp_path,
        delete_gate_approved=True,
    )

    result = service.delete_result_artifact(_request(tmp_path, run_id, "delete-token-unknown"))

    assert result["accepted"] is False
    assert result["error_code"] == "RUN_NOT_FOUND"
    assert (tmp_path / "results" / run_id / "result.json").exists()

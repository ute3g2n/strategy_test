"""P5R2-16 RED contracts for durable local restart/recovery integration."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from autotrade.application import history_catalog, job_service
from autotrade.application.backtest_product import BacktestProductService
from autotrade.application.run_service import OperationGuard


def _bar(timestamp: str, close: str) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "1",
    }


def _job_request(request_id: str) -> dict[str, object]:
    start = datetime(2026, 8, 20, tzinfo=UTC)
    bars = [
        _bar((start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"), str(100 + index))
        for index in range(61)
    ]
    source = {
        "dataset_id": "fixture-source-1m",
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "coverage": {"start": "2026-08-19T00:00:00Z", "end": "2026-08-21T00:00:00Z"},
        "quality": "USABLE",
        "usable": True,
        "legacy": False,
        "state": "CURRENT",
        "promotion_state": "PROMOTED",
        "bar_count": len(bars),
        "bars": bars,
        "provenance": {"source_job_id": "fixture-job-001", "source_mode": "LOCAL_FAKE"},
    }
    return {
        "source_dataset_id": "fixture-source-1m",
        "symbol": "BTCUSDT",
        "timeframes": ["15m"],
        "requested_range": {"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:00:00Z"},
        "request_id": request_id,
        "reason": "P5R2-16 local restart fixture",
        "retry_of": None,
        "external_io_allowed": False,
        "source_dataset": source,
    }


def _catalog_request(request_id: str) -> dict[str, object]:
    source_job = job_service.create_timeframe_generation_job(_job_request(request_id))
    assert source_job["state"] == "STAGED"
    request: dict[str, object] = {
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "existing_bars": [],
        "incoming_bars": [_bar("2026-08-20T00:00:00Z", "100")],
        "dataset_id": f"dataset-{request_id}",
        "expected_revision": 0,
        "impact_confirmed": True,
        "provenance": {"source_job_id": source_job["job_id"], "source_mode": "LOCAL_FAKE"},
        "request_id": request_id,
        "staging_id": f"staging-{request_id}",
        "staging_state": "STAGED",
        "promotion_state": "VALIDATING",
        "quality": "PENDING_CATALOG_VALIDATION",
        "usable": False,
        "source_job": source_job,
    }
    return request


def test_operation_guard_replay_survives_process_restart() -> None:
    request = {
        "run_id": "RUN-P5R2-16-OPERATION-001",
        "operation_token": "p5r2-16-operation-token",
        "request_id": "p5r2-16-operation-request",
        "actor": "local-operator",
        "origin_screen": "PROGRESS",
        "reason": "restart persistence",
        "current_state": "RUNNING",
        "current_revision": 4,
        "expected_revision": 4,
    }
    first_guard = OperationGuard()
    first = first_guard.request_run_cancel(request)
    record = first_guard.export_run_operation(str(request["run_id"]))

    second_guard = OperationGuard()
    second_guard.restore_run_operation(str(request["run_id"]), record)
    replay = second_guard.request_run_cancel(
        {**request, "current_state": "STOP_REQUESTED", "current_revision": 5, "expected_revision": 5}
    )

    assert first["accepted"] is True
    assert replay["accepted"] is False
    assert replay["replayed"] is True
    assert replay["error_code"] == "OPERATION_IN_FLIGHT"
    assert replay["audit_id"] == first["audit_id"]
    assert second_guard.audit_log(str(request["run_id"])) == (first["audit"],)


def test_resumed_run_rejects_a_cancel_token_from_the_previous_generation() -> None:
    run_id = "RUN-P5R2-16-GENERATION-001"
    request = {
        "run_id": run_id,
        "operation_token": "p5r2-16-old-generation-token",
        "request_id": "p5r2-16-old-generation-request",
        "actor": "local-operator",
        "origin_screen": "PROGRESS",
        "reason": "old generation",
        "current_state": "QUEUED",
        "current_revision": 0,
        "expected_revision": 0,
    }
    guard = OperationGuard()
    first = guard.request_run_cancel(request)
    guard.reset_run(run_id)
    replay = guard.request_run_cancel({**request, "current_revision": 1, "expected_revision": 1})

    assert first["accepted"] is True
    assert replay["accepted"] is False
    assert replay["error_code"] == "STALE_OPERATION"
    assert replay["status_after"] == "QUEUED"


def test_local_generation_job_running_state_becomes_recovery_after_restart(tmp_path: Path) -> None:
    first_registry = job_service.LocalJobRegistry(tmp_path / "runtime")
    created = first_registry.create_timeframe_generation_job(_job_request("job-restart-001"))
    running = first_registry.advance_timeframe_generation_job(created)

    second_registry = job_service.LocalJobRegistry(tmp_path / "runtime")
    restored = second_registry.get_job(str(running["job_id"]))

    assert restored is not None
    assert restored["state"] == "RECOVERY_REQUIRED"
    assert restored["orphan"] is True
    assert second_registry.recovery_report()["status"] == "RECOVERY_REQUIRED"


def test_catalog_preview_and_staging_survive_restart_before_promotion(tmp_path: Path) -> None:
    request = _catalog_request("catalog-restart-001")
    first_catalog = history_catalog.HistoryCatalog(tmp_path / "runtime")
    request.update(first_catalog.stage_local_dataset(request))
    preview = first_catalog.preview_merge(request)
    request["preview_token"] = preview["operation_token"]

    second_catalog = history_catalog.HistoryCatalog(tmp_path / "runtime")
    promoted = second_catalog.promote_merge(request)

    assert promoted["state"] == "PROMOTED"
    assert promoted["promoted"] is True
    assert second_catalog.list_available_datasets()[0]["dataset_id"] == request["dataset_id"]


def test_cancelled_run_with_operation_record_survives_service_restart(tmp_path: Path) -> None:
    run_id = "RUN-P5R2-16-CANCELLED-001"
    cancel_request = {
        "run_id": run_id,
        "operation_token": "p5r2-16-cancel-token",
        "request_id": "p5r2-16-cancel-request",
        "actor": "local-operator",
        "origin_screen": "PROGRESS",
        "reason": "restart persistence",
        "current_state": "RUNNING",
        "current_revision": 4,
        "expected_revision": 4,
    }
    guard = OperationGuard()
    operation_record = guard.request_run_cancel(cancel_request)
    run_path = tmp_path / "runtime" / "catalog" / "runs" / f"{run_id}.json"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text(
        json.dumps(
            {
                "schema": "autotrade-backtest-history/v1",
                "run_id": run_id,
                "kind": "SINGLE_BACKTEST",
                "status": "CANCELLED",
                "progress": 4,
                "total": 100,
                "spec": {"symbol": "BTCUSDT", "timeframe": "15m"},
                "failure": {"code": "CANCELLED_BY_USER", "retryable": True},
                "checkpoint": {"cursor": 3, "row_count": 4, "state": {"cursor": 3}},
                "operation_revision": 5,
                "operation_record": operation_record,
                "recovery_mode": "NORMAL",
                "result_reference": None,
            }
        ),
        encoding="utf-8",
    )

    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")
    restored = service.get_run(run_id)
    replay = service.request_run_cancel(cancel_request)

    assert restored["status"] == "CANCELLED"
    assert restored["operation_record"] == operation_record
    assert replay["operation"]["accepted"] is False
    assert replay["operation"]["replayed"] is True
    assert replay["operation"]["error_code"] == "OPERATION_IN_FLIGHT"
    assert not any(issue["code"] == "OPERATION_GUARD_STATE_MISSING" for issue in service.recovery_report()["issues"])


def test_corrupt_restart_records_are_reported_and_not_promoted(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    for directory, filename, contents in (
        ("catalog/jobs", "JOB-BAD.json", "{not-json"),
        ("catalog/staging", "STAGING-BAD.json", "{not-json"),
        ("catalog/previews", "PREVIEW-BAD.json", "{not-json"),
        (
            "catalog/promotions",
            "PROMOTION-BAD.json",
            json.dumps({"operation_token": "different", "state": "PREPARED"}),
        ),
    ):
        path = runtime_root / directory / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    catalog = history_catalog.HistoryCatalog(runtime_root)
    report = catalog.recovery_report()
    issue_codes = {issue["code"] for issue in report["issues"]}

    assert report["status"] == "RECOVERY_REQUIRED"
    assert {"STAGING_RECORD_INVALID", "PREVIEW_RECORD_INVALID", "PROMOTION_RECORD_INVALID"} <= issue_codes


def test_promotion_interruption_is_recovery_required_after_restart(tmp_path: Path, monkeypatch) -> None:
    request = _catalog_request("catalog-promotion-recovery-001")
    first_catalog = history_catalog.HistoryCatalog(tmp_path / "runtime")
    request.update(first_catalog.stage_local_dataset(request))
    preview = first_catalog.preview_merge(request)
    request["preview_token"] = preview["operation_token"]
    dataset_path = first_catalog._dataset_path(str(request["dataset_id"]))
    original_write = first_catalog._write_json_atomic

    def fail_dataset_write(path: Path, payload: dict[str, object]) -> None:
        if path == dataset_path:
            raise OSError("injected dataset promotion interruption")
        original_write(path, payload)

    monkeypatch.setattr(first_catalog, "_write_json_atomic", fail_dataset_write)
    rejected = first_catalog.promote_merge(request)

    assert rejected["state"] == "REJECTED"
    assert rejected["reason"] == "PROMOTION_RECOVERY_REQUIRED"

    second_catalog = history_catalog.HistoryCatalog(tmp_path / "runtime")
    report = second_catalog.recovery_report()
    blocked = second_catalog.promote_merge(request)

    assert report["status"] == "RECOVERY_REQUIRED"
    assert any(issue["code"] == "PROMOTION_INCOMPLETE" for issue in report["issues"])
    assert blocked["state"] == "REJECTED"
    assert blocked["reason"] == "PROMOTION_RECOVERY_REQUIRED"

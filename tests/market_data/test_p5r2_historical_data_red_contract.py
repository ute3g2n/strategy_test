"""P5R2 RED contracts for local Historical Data jobs and Catalog merge safety."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from types import ModuleType

import pytest

from autotrade.application import history_catalog, job_service


def _require_module_contract(module: ModuleType, name: str, requirement: str) -> Callable[..., object]:
    operation = getattr(module, name, None)
    assert callable(operation), f"{requirement} RED: 未実装契約 {module.__name__}.{name}"
    return operation


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _bar(timestamp: str, close: str) -> dict[str, str]:
    return {
        "timestamp": timestamp,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "1.00",
    }


def _source_bars() -> list[dict[str, str]]:
    start = datetime(2026, 8, 20, tzinfo=UTC)
    return [
        _bar((start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"), f"{100 + index / 100:.2f}")
        for index in range(61)
    ]


def _job_request() -> dict[str, object]:
    return {
        "source_dataset_id": "fixture-source-1m",
        "symbol": "BTCUSDT",
        "timeframes": ["15m", "30m"],
        "requested_range": {"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:00:00Z"},
        "request_id": "p5r2-local-request-001",
        "reason": "fixed local RED fixture",
        "retry_of": None,
        "external_io_allowed": False,
        "source_dataset": {
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
            "bar_count": 61,
            "bars": _source_bars(),
            "provenance": {"source_job_id": "fixture-job-001", "source_mode": "LOCAL_FAKE"},
        },
    }


def test_download_and_generation_jobs_are_separate_and_promote_only_after_recovery_safe_validation() -> None:
    generation = _require_module_contract(
        job_service,
        "create_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )

    rejected_download = generation({**_job_request(), "job_type": "HISTORICAL_DOWNLOAD"})
    generation_result = generation({**_job_request(), "job_type": "TIMEFRAME_GENERATION"})

    assert _field(rejected_download, "state") == "REJECTED"
    assert _field(rejected_download, "reason") == "EXTERNAL_DOWNLOAD_GATE_REQUIRED"
    assert _field(generation_result, "job_type") == "TIMEFRAME_GENERATION"
    assert _field(generation_result, "job_id")
    assert _field(generation_result, "input") is not None
    assert _field(generation_result, "output") is not None
    assert _field(generation_result, "retry_of") is None

    partial_result = generation(
        {
            **_job_request(),
            "job_type": "TIMEFRAME_GENERATION",
            "failure_injection": "PARTIAL_AFTER_VALIDATION",
        }
    )
    assert _field(partial_result, "state") == "RECOVERY_REQUIRED"
    assert _field(partial_result, "orphan") is True


def test_historical_download_is_gate_blocked_and_default_range_is_fail_closed() -> None:
    download = _require_module_contract(
        job_service,
        "create_historical_download_job",
        "P5R2-CREQ-HD-001",
    )
    generation = _require_module_contract(
        job_service,
        "create_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )

    download_result = download(_job_request())
    assert _field(download_result, "state") == "REJECTED"
    assert _field(download_result, "reason") == "EXTERNAL_DOWNLOAD_GATE_REQUIRED"
    assert _field(download_result, "job_id") is None

    default_result = generation({**_job_request(), "requested_range": None, "use_default_range": True})
    assert _field(default_result, "state") == "REJECTED"
    assert _field(default_result, "reason") == "DEFAULT_RANGE_UNRESOLVED"

    external_result = generation({**_job_request(), "external_io_allowed": True})
    assert _field(external_result, "state") == "REJECTED"
    assert _field(external_result, "reason") == "EXTERNAL_IO_FORBIDDEN"


def test_local_generation_job_cancel_restart_and_retry_are_recovery_safe() -> None:
    cancel = _require_module_contract(
        job_service,
        "cancel_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )
    restart = _require_module_contract(
        job_service,
        "restart_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )
    retry = _require_module_contract(
        job_service,
        "retry_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )

    running = job_service.create_timeframe_generation_job(_job_request())
    assert isinstance(running, dict)
    running["state"] = "RUNNING"
    running["output"] = None
    running["retry_of"] = None
    cancelled = cancel(running)
    assert _field(cancelled, "state") == "CANCELLED"
    assert _field(cancelled, "promoted") is False
    assert _field(cancelled, "reason") == "JOB_CANCELLED"

    recovery_source = job_service.create_timeframe_generation_job(
        {**_job_request(), "request_id": "p5r2-restart-request-001"}
    )
    assert isinstance(recovery_source, dict)
    recovery_source["state"] = "RUNNING"
    recovery_source["output"] = None
    recovery_source["retry_of"] = None
    recovery = restart(recovery_source)
    assert _field(recovery, "state") == "RECOVERY_REQUIRED"
    assert _field(recovery, "orphan") is True
    assert _field(recovery, "promoted") is False

    retried = retry(recovery)
    assert _field(retried, "state") == "STAGED"
    assert _field(retried, "retry_of") == recovery_source["job_id"]
    assert _field(retried, "job_id") != recovery_source["job_id"]
    assert _field(retried, "orphan") is False

    download_retry = retry(
        {
            **running,
            "job_type": "HISTORICAL_DOWNLOAD",
            "state": "RECOVERY_REQUIRED",
        }
    )
    assert _field(download_retry, "state") == "REJECTED"
    assert _field(download_retry, "reason") == "JOB_TYPE_MISMATCH"


def test_job_lifecycle_rejects_unregistered_caller_snapshot() -> None:
    retry = _require_module_contract(
        job_service,
        "retry_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )
    result = retry(
        {
            "job_id": "JOB-TIMEFRAME_GENERATION-unregistered-001",
            "job_type": "TIMEFRAME_GENERATION",
            "state": "RECOVERY_REQUIRED",
            "operation_token": "not-server-owned",
            "input": _job_request(),
        }
    )
    assert _field(result, "state") == "REJECTED"
    assert _field(result, "reason") == "JOB_NOT_FOUND"


def test_catalog_merge_preview_requires_identity_dedupe_conflict_replace_and_impact_review(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    preview = getattr(catalog, "preview_merge", None)
    assert callable(preview), "P5R2-CREQ-HD-002 RED: HistoryCatalog.preview_merge が未実装"

    request = {
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "existing_bars": [_bar("2026-08-20T00:00:00Z", "100.00"), _bar("2026-08-20T00:30:00Z", "998.00")],
        "incoming_bars": [
            _bar("2026-08-20T00:00:00Z", "100.00"),
            _bar("2026-08-20T00:15:00Z", "101.00"),
            _bar("2026-08-20T00:30:00Z", "999.00"),
        ],
        "affected_runs": ["RUN-LOCAL-001"],
        "affected_results": ["RESULT-LOCAL-001"],
        "explicit_replace": False,
        "provenance": {"source_job_id": "merge-job-001", "source_mode": "LOCAL_FAKE"},
        "request_id": "p5r2-merge-preview-001",
    }

    preview_result = preview(request)

    assert _field(preview_result, "identity") == request["identity"]
    assert _field(preview_result, "dedupe_count") == 1
    assert _field(preview_result, "conflict_count") == 1
    assert _field(preview_result, "affected_runs") == request["affected_runs"]
    assert _field(preview_result, "affected_results") == request["affected_results"]
    assert _field(preview_result, "requires_explicit_replace") is True
    assert _field(preview_result, "state") == "CONFLICT"
    assert _field(preview_result, "promotable") is False
    assert _field(preview_result, "operation_token")


def test_catalog_rejects_identity_mismatch_without_auto_merge(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    preview_result = catalog.preview_merge(
        {
            "identity": {
                "provider": "LOCAL_FAKE",
                "market": "SPOT",
                "symbol": "BTCUSDT",
                "source_timeframe": "1m",
                "schema": "ohlcv-v1",
            },
            "existing_identity": {
                "provider": "LOCAL_FAKE",
                "market": "SPOT",
                "symbol": "BTCUSDT",
                "source_timeframe": "1m",
                "schema": "ohlcv-v1",
            },
            "incoming_identity": {
                "provider": "OTHER_PROVIDER",
                "market": "SPOT",
                "symbol": "BTCUSDT",
                "source_timeframe": "1m",
                "schema": "ohlcv-v1",
            },
            "existing_bars": [],
            "incoming_bars": [_bar("2026-08-20T00:00:00Z", "100.00")],
            "explicit_replace": False,
            "provenance": {"source_job_id": "identity-job-001", "source_mode": "LOCAL_FAKE"},
            "request_id": "p5r2-identity-mismatch-001",
        }
    )

    assert _field(preview_result, "state") == "REJECTED"
    assert _field(preview_result, "reason") == "DATA_IDENTITY_MISMATCH"
    assert _field(preview_result, "promotable") is False


def test_catalog_explicit_replace_promotes_atomically_and_lists_usable_dataset(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    promote = getattr(catalog, "promote_merge", None)
    list_available = getattr(catalog, "list_available_datasets", None)
    assert callable(promote), "P5R2-CREQ-HD-002 RED: HistoryCatalog.promote_merge が未実装"
    assert callable(list_available), "P5R2-CREQ-HD-002 RED: HistoryCatalog.list_available_datasets が未実装"

    identity = {
        "provider": "LOCAL_FAKE",
        "market": "SPOT",
        "symbol": "BTCUSDT",
        "source_timeframe": "1m",
        "schema": "ohlcv-v1",
    }
    request = {
        "identity": identity,
        "existing_bars": [_bar("2026-08-20T00:00:00Z", "100.00")],
        "incoming_bars": [_bar("2026-08-20T00:00:00Z", "101.00"), _bar("2026-08-20T00:15:00Z", "102.00")],
        "affected_runs": ["RUN-LOCAL-001"],
        "affected_results": ["RESULT-LOCAL-001"],
        "explicit_replace": True,
        "dataset_id": "dataset-local-001",
        "expected_revision": 0,
        "impact_confirmed": True,
        "provenance": {"source_job_id": "p5r2-merge-apply-001", "source_mode": "LOCAL_FAKE"},
        "request_id": "p5r2-merge-apply-001",
    }
    preview_result = catalog.preview_merge(request)
    request["preview_token"] = _field(preview_result, "operation_token")
    result = promote(request)

    assert _field(result, "state") == "PROMOTED"
    assert _field(result, "promoted") is True
    assert _field(result, "dataset_id") == "dataset-local-001"
    assert _field(result, "affected_runs") == ["RUN-LOCAL-001"]
    assert _field(result, "affected_results") == ["RESULT-LOCAL-001"]
    output = _field(result, "output")
    assert isinstance(output, dict)
    assert output["usable"] is True
    assert output["quality"] == "USABLE"
    assert output["bars"][0]["close"] == "101.00"

    available = list_available()
    assert len(available) == 1
    assert available[0]["dataset_id"] == "dataset-local-001"
    assert available[0]["symbol"] == "BTCUSDT"
    assert available[0]["source_timeframe"] == "1m"
    assert available[0]["quality"] == "USABLE"
    assert available[0]["usable"] is True
    assert available[0]["legacy"] is False
    assert available[0]["provenance"]["request_id"] == "p5r2-merge-apply-001"


def test_generation_requires_verified_local_source_and_does_not_mark_job_output_usable() -> None:
    generation = _require_module_contract(
        job_service,
        "create_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )
    missing_source = generation({**_job_request(), "source_dataset": None})
    assert _field(missing_source, "state") == "REJECTED"
    assert _field(missing_source, "reason") == "SOURCE_DATASET_UNAVAILABLE"

    valid = generation(_job_request())
    assert _field(valid, "state") == "STAGED"
    output = _field(valid, "output")
    assert isinstance(output, dict)
    assert output["usable"] is False
    assert all(dataset["usable"] is False for dataset in output["data_sets"])


def test_generation_rejects_source_whose_bars_do_not_cover_requested_range() -> None:
    generation = _require_module_contract(
        job_service,
        "create_timeframe_generation_job",
        "P5R2-CREQ-HD-001",
    )
    source_dataset = dict(_job_request()["source_dataset"])
    source_dataset["bars"] = _source_bars()[:2]
    source_dataset["bar_count"] = 2
    result = generation({**_job_request(), "source_dataset": source_dataset})
    assert _field(result, "state") == "REJECTED"
    assert _field(result, "reason") == "SOURCE_DATASET_COVERAGE_INSUFFICIENT"


def test_catalog_rejects_external_provider_legacy_and_invalid_dataset_inputs(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    base = {
        "identity": {
            "provider": "OTHER_PROVIDER",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "incoming_bars": [_bar("2026-08-20T00:00:00Z", "100.00")],
        "existing_bars": [],
        "request_id": "p5r2-invalid-001",
        "provenance": {"source_job_id": "invalid-job-001", "source_mode": "OTHER_PROVIDER"},
        "explicit_replace": False,
    }
    provider_result = catalog.preview_merge(base)
    assert provider_result["state"] == "REJECTED"
    assert provider_result["reason"] == "EXTERNAL_PROVIDER_GATE_REQUIRED"

    invalid_bar = catalog.preview_merge(
        {
            **base,
            "identity": {**base["identity"], "provider": "LOCAL_FAKE"},
            "provenance": {"source_job_id": "invalid-job-002", "source_mode": "LOCAL_FAKE"},
            "incoming_bars": [{"timestamp": "not-a-time", "close": "100.00"}],
        }
    )
    assert invalid_bar["state"] == "REJECTED"
    assert invalid_bar["reason"] in {"BAR_TIMESTAMP_INVALID", "BAR_SCHEMA_INVALID"}


def test_catalog_requires_current_revision_and_confirmation_and_preserves_previous_version(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    identity = {
        "provider": "LOCAL_FAKE",
        "market": "SPOT",
        "symbol": "BTCUSDT",
        "source_timeframe": "1m",
        "schema": "ohlcv-v1",
    }
    initial = {
        "identity": identity,
        "existing_bars": [],
        "incoming_bars": [_bar("2026-08-20T00:00:00Z", "100.00")],
        "dataset_id": "dataset-revision-001",
        "expected_revision": 0,
        "impact_confirmed": True,
        "provenance": {"source_job_id": "revision-job-001", "source_mode": "LOCAL_FAKE"},
        "request_id": "revision-request-001",
    }
    initial["preview_token"] = catalog.preview_merge(initial)["operation_token"]
    first = catalog.promote_merge(initial)
    assert first["state"] == "PROMOTED"

    confirmation_missing = catalog.promote_merge(
        {
            **initial,
            "incoming_bars": [_bar("2026-08-20T00:15:00Z", "101.00")],
            "expected_revision": 1,
            "request_id": "revision-request-002",
            "preview_token": None,
        }
    )
    assert confirmation_missing["state"] == "REJECTED"
    assert confirmation_missing["reason"] == "MERGE_CONFIRMATION_REQUIRED"

    current = {
        **initial,
        "existing_bars": [],
        "incoming_bars": [_bar("2026-08-20T00:15:00Z", "101.00")],
        "expected_revision": 1,
        "request_id": "revision-request-002",
        "impact_confirmed": True,
    }
    current["preview_token"] = catalog.preview_merge(current)["operation_token"]
    second = catalog.promote_merge(current)
    assert second["state"] == "PROMOTED"
    assert second["output"]["bar_count"] == 2
    assert (tmp_path / "catalog" / "datasets" / "versions" / "dataset-revision-001.r1.json").exists()

    stale = {**current, "expected_revision": 1, "request_id": "revision-request-stale", "preview_token": None}
    stale_preview = catalog.preview_merge(stale)
    assert stale_preview["current_revision"] == 2
    assert stale_preview["state"] == "PREVIEW_READY"


def test_catalog_preview_token_is_bound_to_reviewed_content_and_consumed_once(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    request = {
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "existing_bars": [],
        "incoming_bars": [_bar("2026-08-20T00:00:00Z", "100.00")],
        "dataset_id": "dataset-token-001",
        "expected_revision": 0,
        "impact_confirmed": True,
        "provenance": {"source_job_id": "token-job-001", "source_mode": "LOCAL_FAKE"},
        "request_id": "token-request-001",
    }
    request["preview_token"] = catalog.preview_merge(request)["operation_token"]
    tampered = {**request, "incoming_bars": [_bar("2026-08-20T00:00:00Z", "999.00")]}
    rejected = catalog.promote_merge(tampered)
    assert rejected["state"] == "REJECTED"
    assert rejected["reason"] == "PREVIEW_TOKEN_MISMATCH"

    promoted = catalog.promote_merge(request)
    assert promoted["state"] == "PROMOTED"
    replay = catalog.promote_merge(request)
    assert replay["state"] == "REJECTED"


def test_catalog_result_publication_is_write_once_for_different_payload(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    payload = {"run_id": "RUN-P5R2-WRITE-001", "metrics": {}, "rows": [], "provenance": {}}
    catalog.write_result(payload["run_id"], payload)
    catalog.write_result(payload["run_id"], dict(payload))
    with pytest.raises(ValueError, match="RESULT_ALREADY_PUBLISHED"):
        catalog.write_result(
            payload["run_id"],
            {"run_id": payload["run_id"], "metrics": {"changed": True}, "rows": [], "provenance": {}},
        )


def test_catalog_available_list_excludes_legacy_and_invalid_state(tmp_path) -> None:
    catalog = history_catalog.HistoryCatalog(tmp_path)
    datasets_root = tmp_path / "catalog" / "datasets"
    datasets_root.mkdir(parents=True, exist_ok=True)
    (datasets_root / "legacy.json").write_text(
        '{"schema":"autotrade-historical-dataset/v1","dataset_id":"legacy","identity":{"provider":"LOCAL_FAKE","market":"SPOT","symbol":"BTCUSDT","source_timeframe":"1m","schema":"ohlcv-v1"},"quality":"USABLE","usable":true,"legacy":true,"state":"CURRENT","promotion_state":"PROMOTED","provenance":{"source_job_id":"legacy-job"},"bars":[]}',
        encoding="utf-8",
    )
    (datasets_root / "staging.json").write_text(
        '{"schema":"autotrade-historical-dataset/v1","dataset_id":"staging","identity":{"provider":"LOCAL_FAKE","market":"SPOT","symbol":"BTCUSDT","source_timeframe":"1m","schema":"ohlcv-v1"},"quality":"USABLE","usable":true,"legacy":false,"state":"STAGING","promotion_state":"VALIDATING","provenance":{"source_job_id":"staging-job"},"bars":[]}',
        encoding="utf-8",
    )
    assert catalog.list_available_datasets() == []

"""P5R2 RED contracts for local Historical Data jobs and Catalog merge safety."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

from autotrade.application import history_catalog, job_service


def _require_module_contract(module: ModuleType, name: str, requirement: str) -> Callable[..., object]:
    operation = getattr(module, name, None)
    assert callable(operation), f"{requirement} RED: 未実装契約 {module.__name__}.{name}"
    return operation


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


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

    running = {
        "job_id": "JOB-TIMEFRAME_GENERATION-lifecycle-001",
        "job_type": "TIMEFRAME_GENERATION",
        "state": "RUNNING",
        "input": _job_request(),
        "output": None,
        "retry_of": None,
    }
    cancelled = cancel(running)
    assert _field(cancelled, "state") == "CANCELLED"
    assert _field(cancelled, "promoted") is False
    assert _field(cancelled, "reason") == "JOB_CANCELLED"

    recovery = restart(running)
    assert _field(recovery, "state") == "RECOVERY_REQUIRED"
    assert _field(recovery, "orphan") is True
    assert _field(recovery, "promoted") is False

    retried = retry(recovery)
    assert _field(retried, "state") == "PROMOTED"
    assert _field(retried, "retry_of") == running["job_id"]
    assert _field(retried, "orphan") is False


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
        "existing_bars": [
            {"timestamp": "2026-08-20T00:00:00Z", "close": "100.00"},
            {"timestamp": "2026-08-20T00:30:00Z", "close": "998.00"},
        ],
        "incoming_bars": [
            {"timestamp": "2026-08-20T00:00:00Z", "close": "100.00"},
            {"timestamp": "2026-08-20T00:15:00Z", "close": "101.00"},
            {"timestamp": "2026-08-20T00:30:00Z", "close": "999.00"},
        ],
        "affected_runs": ["RUN-LOCAL-001"],
        "affected_results": ["RESULT-LOCAL-001"],
        "explicit_replace": False,
        "request_id": "p5r2-merge-preview-001",
    }

    preview_result = preview(request)

    assert _field(preview_result, "identity") == request["identity"]
    assert _field(preview_result, "dedupe_count") == 1
    assert _field(preview_result, "conflict_count") == 1
    assert _field(preview_result, "affected_runs") == request["affected_runs"]
    assert _field(preview_result, "affected_results") == request["affected_results"]
    assert _field(preview_result, "requires_explicit_replace") is True


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
            "incoming_bars": [{"timestamp": "2026-08-20T00:00:00Z", "close": "100.00"}],
            "explicit_replace": False,
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
    result = promote(
        {
            "identity": identity,
            "existing_bars": [{"timestamp": "2026-08-20T00:00:00Z", "close": "100.00"}],
            "incoming_bars": [
                {"timestamp": "2026-08-20T00:00:00Z", "close": "101.00"},
                {"timestamp": "2026-08-20T00:15:00Z", "close": "102.00"},
            ],
            "affected_runs": ["RUN-LOCAL-001"],
            "affected_results": ["RESULT-LOCAL-001"],
            "explicit_replace": True,
            "dataset_id": "dataset-local-001",
            "request_id": "p5r2-merge-apply-001",
        }
    )

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

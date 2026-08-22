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
        "existing_bars": [{"timestamp": "2026-08-20T00:00:00Z", "close": "100.00"}],
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

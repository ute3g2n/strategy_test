"""Job/queue application operations with explicit expected-revision checks."""

from __future__ import annotations

import copy
import re
import threading
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .contracts import (
    ApplicationResponse,
    CancelJobCommand,
    JobView,
    StartJobCommand,
    failure_response,
)
from .persistence import MetadataStore, PersistenceConflict

JsonObject = dict[str, object]
_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_TIMEFRAME_GENERATION = "TIMEFRAME_GENERATION"
_HISTORICAL_DOWNLOAD = "HISTORICAL_DOWNLOAD"
_SUPPORTED_TIMEFRAMES = frozenset({"15m", "30m", "1h", "4h", "1d"})
_LOCAL_JOB_REGISTRY: dict[str, JsonObject] = {}
_LOCAL_JOB_REQUEST_INDEX: dict[str, str] = {}
_JOB_REGISTRY_LOCK = threading.RLock()


class JobService:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store

    def start_job(self, command: StartJobCommand, *, correlation_id: str) -> ApplicationResponse[JobView]:
        try:
            job, _ = self.store.start_job(command, correlation_id)
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(
                code,
                f"P4-MSG-{code}",
                status_code=409,
                recovery_required=code in {"STALE_REVISION", "QUEUE_RUN_STATE_MISMATCH"},
            )
        return ApplicationResponse(202, job, correlation_id=correlation_id)

    def cancel_job(self, command: CancelJobCommand, *, correlation_id: str) -> ApplicationResponse[JobView]:
        try:
            job = self.store.cancel_job(command, correlation_id)
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(code, f"P4-MSG-{code}", status_code=409, recovery_required=code == "STALE_REVISION")
        return ApplicationResponse(200, job, correlation_id=correlation_id)


def create_historical_download_job(value: object) -> JsonObject:
    """Return a gate rejection without creating a job or touching a provider.

    P5R2-14 is deliberately limited to local generation.  Keeping this
    boundary as a public operation makes a future DATA-G1 implementation
    explicit instead of silently converting a download request into a local
    generation request.
    """

    request = _safe_job_input(value if isinstance(value, Mapping) else {})
    return {
        "job_id": None,
        "job_type": _HISTORICAL_DOWNLOAD,
        "state": "REJECTED",
        "reason": "EXTERNAL_DOWNLOAD_GATE_REQUIRED",
        "input": request,
        "output": None,
        "retry_of": request.get("retry_of"),
        "orphan": False,
        "external_io_performed": False,
    }


def create_timeframe_generation_job(value: object) -> JsonObject:
    """Create a local-only generation result with recovery-safe promotion state."""

    if not isinstance(value, Mapping):
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_REQUEST_INVALID", {})

    requested_job_type = value.get("job_type", _TIMEFRAME_GENERATION)
    if requested_job_type == _HISTORICAL_DOWNLOAD:
        return create_historical_download_job(value)
    if requested_job_type != _TIMEFRAME_GENERATION:
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_TYPE_INVALID", value)
    if value.get("external_io_allowed") is not False:
        return _rejected_job(_TIMEFRAME_GENERATION, "EXTERNAL_IO_FORBIDDEN", value)

    request, reason = _normalise_generation_request(value)
    if reason is not None:
        return _rejected_job(_TIMEFRAME_GENERATION, reason, value)
    assert request is not None

    job_id = f"JOB-{_TIMEFRAME_GENERATION}-{request['request_id']}"
    if request.get("retry_of") is not None:
        job_id = f"{job_id}-RETRY-{request['attempt']}"
    retry_of = request["retry_of"]
    if value.get("failure_injection") == "PARTIAL_AFTER_VALIDATION":
        result = {
            "job_id": job_id,
            "job_type": _TIMEFRAME_GENERATION,
            "state": "RECOVERY_REQUIRED",
            "reason": "PROMOTION_RECOVERY_REQUIRED",
            "input": request,
            "output": {
                "staging_state": "ORPHAN_STAGING",
                "promoted": False,
                "usable": False,
                "data_sets": [],
            },
            "retry_of": retry_of,
            "orphan": True,
            "external_io_performed": False,
        }
        return _register_job(result)

    raw_timeframes = request["timeframes"]
    assert isinstance(raw_timeframes, list)
    data_sets = [
        _derived_dataset(request, job_id, timeframe) for timeframe in raw_timeframes if isinstance(timeframe, str)
    ]
    output: JsonObject = {
        "staging_state": "STAGED",
        "promoted": False,
        "usable": False,
        "data_sets": data_sets,
        "source_dataset_id": request["source_dataset_id"],
    }
    result = {
        "job_id": job_id,
        "job_type": _TIMEFRAME_GENERATION,
        "state": "STAGED",
        "reason": "TIMEFRAME_GENERATION_VALIDATION_REQUIRED",
        "input": request,
        "output": output,
        "retry_of": retry_of,
        "orphan": False,
        "external_io_performed": False,
    }
    return _register_job(result)


def cancel_timeframe_generation_job(value: Mapping[str, object]) -> JsonObject:
    """Cancel only an active local generation job without promoting data."""

    if not isinstance(value, Mapping):
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_REQUEST_INVALID", {})
    if value.get("job_type") != _TIMEFRAME_GENERATION:
        return {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_TYPE_MISMATCH",
            "accepted": False,
            "promoted": False,
        }
    trusted, rejection = _trusted_job(value)
    if rejection is not None:
        return rejection
    assert trusted is not None
    state = trusted.get("state")
    if state not in {"QUEUED", "RUNNING", "CANCEL_REQUESTED"}:
        return {
            **_job_projection(value),
            "state": state if isinstance(state, str) else "REJECTED",
            "reason": "JOB_NOT_CANCELLABLE",
            "accepted": False,
            "promoted": value.get("promoted") is True,
        }
    return _transition_job(
        trusted,
        state="CANCELLED",
        reason="JOB_CANCELLED",
        output={"staging_state": "CANCELLED", "promoted": False, "usable": False},
        orphan=False,
    )


def restart_timeframe_generation_job(value: Mapping[str, object]) -> JsonObject:
    """Convert an interrupted active job into an explicit recovery state."""

    if not isinstance(value, Mapping):
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_REQUEST_INVALID", {})
    if value.get("job_type") != _TIMEFRAME_GENERATION:
        return {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_TYPE_MISMATCH",
            "accepted": False,
            "promoted": False,
        }
    trusted, rejection = _trusted_job(value)
    if rejection is not None:
        return rejection
    assert trusted is not None
    state = trusted.get("state")
    if state not in {"QUEUED", "RUNNING", "CANCEL_REQUESTED"}:
        return {
            **_job_projection(value),
            "state": state if isinstance(state, str) else "REJECTED",
            "reason": "RESTART_NOT_REQUIRED",
            "accepted": False,
            "promoted": value.get("promoted") is True,
        }
    return _transition_job(
        trusted,
        state="RECOVERY_REQUIRED",
        reason="RESTART_RECOVERY_REQUIRED",
        output={"staging_state": "ORPHAN_STAGING", "promoted": False, "usable": False},
        orphan=True,
    )


def advance_timeframe_generation_job(value: Mapping[str, object], target_state: str = "RUNNING") -> JsonObject:
    """Advance a server-owned local job without accepting a caller mutation.

    This is intentionally small: it is the local execution seam used by the
    RED/GREEN contract tests.  Callers submit the last server snapshot and a
    capability token; the registry owns the resulting state.
    """

    if not isinstance(value, Mapping):
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_REQUEST_INVALID", {})
    if value.get("job_type") != _TIMEFRAME_GENERATION or target_state not in {"QUEUED", "RUNNING"}:
        return {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_STATE_TRANSITION_INVALID",
            "accepted": False,
            "promoted": False,
        }
    trusted, rejection = _trusted_job(value)
    if rejection is not None:
        return rejection
    assert trusted is not None
    if trusted.get("state") not in {"STAGED", "QUEUED"}:
        return {
            **_job_projection(trusted),
            "state": trusted.get("state"),
            "reason": "JOB_STATE_TRANSITION_INVALID",
            "accepted": False,
            "promoted": False,
        }
    return _transition_job(
        trusted,
        state=target_state,
        reason="JOB_STATE_ADVANCED",
        output=trusted.get("output") if isinstance(trusted.get("output"), Mapping) else None,
        orphan=trusted.get("orphan") is True,
    )


def get_owned_job_snapshot(value: Mapping[str, object]) -> JsonObject:
    """Return a verified server-owned capability snapshot for local consumers."""

    if not isinstance(value, Mapping):
        raise ValueError("JOB_REQUEST_INVALID")
    trusted, rejection = _trusted_job(value)
    if rejection is not None:
        raise ValueError(str(rejection.get("reason", "JOB_NOT_FOUND")))
    assert trusted is not None
    if trusted.get("job_type") != _TIMEFRAME_GENERATION:
        raise ValueError("JOB_TYPE_MISMATCH")
    return copy.deepcopy(trusted)


def retry_timeframe_generation_job(value: Mapping[str, object]) -> JsonObject:
    """Retry only failed/cancelled/recovery jobs and retain the parent job ID."""

    if not isinstance(value, Mapping):
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_REQUEST_INVALID", {})
    if value.get("job_type") != _TIMEFRAME_GENERATION:
        return {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_TYPE_MISMATCH",
            "accepted": False,
            "promoted": False,
        }
    trusted, rejection = _trusted_job(value)
    if rejection is not None:
        return rejection
    assert trusted is not None
    if trusted.get("state") not in {"FAILED", "CANCELLED", "RECOVERY_REQUIRED"}:
        return {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_RETRY_NOT_ALLOWED",
            "accepted": False,
            "promoted": False,
        }
    raw_input = trusted.get("input")
    job_id = trusted.get("job_id")
    if not isinstance(raw_input, Mapping) or not isinstance(job_id, str) or not _valid_identifier(job_id):
        return {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "RETRY_REFERENCE_INVALID",
            "accepted": False,
            "promoted": False,
        }
    request = dict(raw_input)
    request["job_type"] = _TIMEFRAME_GENERATION
    request["retry_of"] = job_id
    request["failure_injection"] = None
    raw_attempt = request.get("attempt", 0)
    request["attempt"] = raw_attempt + 1 if isinstance(raw_attempt, int) and raw_attempt >= 0 else 1
    retried = create_timeframe_generation_job(request)
    retried["accepted"] = retried.get("state") == "STAGED"
    return retried


def _job_projection(value: Mapping[str, object]) -> JsonObject:
    return {
        "job_id": value.get("job_id"),
        "job_type": value.get("job_type", _TIMEFRAME_GENERATION),
        "input": value.get("input"),
        "output": value.get("output"),
        "retry_of": value.get("retry_of"),
        "orphan": value.get("orphan") is True,
        "external_io_performed": False,
        "operation_token": value.get("operation_token"),
        "owner_id": value.get("owner_id"),
        "revision": value.get("revision"),
    }


def _trusted_job(value: Mapping[str, object]) -> tuple[JsonObject | None, JsonObject | None]:
    raw_job_id = value.get("job_id")
    if not isinstance(raw_job_id, str) or not _valid_identifier(raw_job_id):
        return None, {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_REFERENCE_INVALID",
            "accepted": False,
            "promoted": False,
        }
    with _JOB_REGISTRY_LOCK:
        trusted = _LOCAL_JOB_REGISTRY.get(raw_job_id)
        trusted = copy.deepcopy(trusted) if trusted is not None else None
    if trusted is None:
        return None, {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_NOT_FOUND",
            "accepted": False,
            "promoted": False,
        }
    if value.get("operation_token") != trusted.get("operation_token"):
        return None, {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_OPERATION_TOKEN_INVALID",
            "accepted": False,
            "promoted": False,
        }
    if value.get("job_type") != trusted.get("job_type"):
        return None, {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_TYPE_MISMATCH",
            "accepted": False,
            "promoted": False,
        }
    if value.get("state") != trusted.get("state"):
        return None, {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_STATE_STALE",
            "accepted": False,
            "promoted": False,
        }
    for key in ("input", "output", "retry_of", "orphan"):
        if value.get(key) != trusted.get(key):
            return None, {
                **_job_projection(value),
                "state": "REJECTED",
                "reason": "JOB_SNAPSHOT_TAMPERED",
                "accepted": False,
                "promoted": False,
            }
    if value.get("owner_id") != trusted.get("owner_id") or value.get("revision") != trusted.get("revision"):
        return None, {
            **_job_projection(value),
            "state": "REJECTED",
            "reason": "JOB_SNAPSHOT_STALE",
            "accepted": False,
            "promoted": False,
        }
    return trusted, None


def _register_job(result: JsonObject) -> JsonObject:
    job_id = result.get("job_id")
    if not isinstance(job_id, str):
        return result
    request = result.get("input")
    request_id = request.get("request_id") if isinstance(request, Mapping) else None
    with _JOB_REGISTRY_LOCK:
        existing = _LOCAL_JOB_REGISTRY.get(job_id)
        if existing is not None:
            if existing.get("input") != request:
                return {
                    **_job_projection(existing),
                    "state": "REJECTED",
                    "reason": "REQUEST_ID_REUSE",
                    "accepted": False,
                    "promoted": False,
                }
            return copy.deepcopy(existing)
        stored = copy.deepcopy(result)
        stored["operation_token"] = uuid.uuid4().hex
        stored["owner_id"] = f"JOB-OWNER-{uuid.uuid4().hex}"
        stored["revision"] = 0
        _LOCAL_JOB_REGISTRY[job_id] = stored
        if isinstance(request_id, str):
            _LOCAL_JOB_REQUEST_INDEX[request_id] = job_id
        return copy.deepcopy(stored)


def _transition_job(
    trusted: JsonObject,
    *,
    state: str,
    reason: str,
    output: object,
    orphan: bool,
) -> JsonObject:
    job_id = trusted.get("job_id")
    if not isinstance(job_id, str):
        return _rejected_job(_TIMEFRAME_GENERATION, "JOB_REFERENCE_INVALID", {})
    with _JOB_REGISTRY_LOCK:
        current = _LOCAL_JOB_REGISTRY.get(job_id)
        if current is None or current.get("revision") != trusted.get("revision"):
            return {
                **_job_projection(trusted),
                "state": "REJECTED",
                "reason": "JOB_SNAPSHOT_STALE",
                "accepted": False,
                "promoted": False,
            }
        updated = copy.deepcopy(current)
        updated["state"] = state
        updated["reason"] = reason
        updated["accepted"] = True
        updated["promoted"] = False
        updated["orphan"] = orphan
        updated["output"] = copy.deepcopy(output)
        raw_revision = current.get("revision", 0)
        revision = raw_revision if isinstance(raw_revision, int) and not isinstance(raw_revision, bool) else 0
        updated["revision"] = revision + 1
        _LOCAL_JOB_REGISTRY[job_id] = updated
        return copy.deepcopy(updated)


def _normalise_generation_request(value: Mapping[str, object]) -> tuple[JsonObject | None, str | None]:
    source_dataset_id = _safe_text(value.get("source_dataset_id"))
    symbol = _safe_text(value.get("symbol"))
    request_id = _safe_text(value.get("request_id"))
    reason = _safe_text(value.get("reason"))
    retry_of = value.get("retry_of")
    attempt = value.get("attempt", 0)
    failure_injection = value.get("failure_injection")
    if not all((_valid_identifier(source_dataset_id), _valid_identifier(symbol), _valid_identifier(request_id))):
        return None, "JOB_REQUEST_INVALID"
    if not reason or len(reason) > 512:
        return None, "JOB_REASON_REQUIRED"
    if retry_of is not None and not _valid_identifier(_safe_text(retry_of)):
        return None, "RETRY_REFERENCE_INVALID"
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 0 or attempt > 9999:
        return None, "JOB_REQUEST_INVALID"
    if failure_injection not in {None, "PARTIAL_AFTER_VALIDATION"}:
        return None, "JOB_REQUEST_INVALID"

    raw_timeframes = value.get("timeframes")
    if isinstance(raw_timeframes, str) or not isinstance(raw_timeframes, Sequence) or not raw_timeframes:
        return None, "STRATEGY_TIMEFRAME_INVALID"
    timeframes = [item for item in raw_timeframes if isinstance(item, str)]
    if len(timeframes) != len(raw_timeframes) or len(set(timeframes)) != len(timeframes):
        return None, "STRATEGY_TIMEFRAME_INVALID"
    if any(timeframe not in _SUPPORTED_TIMEFRAMES for timeframe in timeframes):
        return None, "STRATEGY_TIMEFRAME_INVALID"

    if value.get("use_default_range") is True or not isinstance(value.get("requested_range"), Mapping):
        return None, "DEFAULT_RANGE_UNRESOLVED"
    requested_range = value["requested_range"]
    assert isinstance(requested_range, Mapping)
    start = _safe_text(requested_range.get("start"))
    end = _safe_text(requested_range.get("end"))
    if not start or not end or not _valid_utc_range(start, end):
        return None, "REQUESTED_RANGE_INVALID"
    assert source_dataset_id is not None
    assert symbol is not None

    source_dataset, source_reason = _validate_source_dataset(
        value.get("source_dataset"), source_dataset_id, symbol, start, end
    )
    if source_reason is not None:
        return None, source_reason
    assert source_dataset is not None

    return {
        "source_dataset_id": source_dataset_id,
        "symbol": symbol,
        "timeframes": list(timeframes),
        "requested_range": {"start": start, "end": end},
        "request_id": request_id,
        "reason": "provided",
        "retry_of": retry_of,
        "attempt": attempt,
        "failure_injection": failure_injection,
        "source_dataset": source_dataset,
        "external_io_allowed": False,
    }, None


def _derived_dataset(request: JsonObject, job_id: str, timeframe: str) -> JsonObject:
    symbol = str(request["symbol"])
    request_id = str(request["request_id"])
    dataset_id = f"DATASET-DERIVED-{symbol}-{timeframe}-{request_id}"
    raw_range = request["requested_range"]
    assert isinstance(raw_range, Mapping)
    return {
        "dataset_id": dataset_id,
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": symbol,
            "source_timeframe": "1m",
            "data_timeframe": timeframe,
            "schema": "ohlcv-v1",
        },
        "coverage": {"start": raw_range.get("start"), "end": raw_range.get("end")},
        "quality": "PENDING_CATALOG_VALIDATION",
        "usable": False,
        "legacy": False,
        "provenance": {
            "source_dataset_id": request["source_dataset_id"],
            "job_id": job_id,
            "generation_mode": "LOCAL_FAKE",
            "quality": "PENDING_CATALOG_VALIDATION",
        },
    }


def _rejected_job(job_type: str, reason: str, value: Mapping[str, object]) -> JsonObject:
    request = _safe_job_input(value)
    return {
        "job_id": None,
        "job_type": job_type,
        "state": "REJECTED",
        "reason": reason,
        "input": request,
        "output": None,
        "retry_of": request.get("retry_of"),
        "orphan": False,
        "external_io_performed": False,
    }


def _safe_job_input(value: Mapping[str, object]) -> JsonObject:
    raw_range = value.get("requested_range")
    requested_range = (
        {"start": raw_range.get("start"), "end": raw_range.get("end")} if isinstance(raw_range, Mapping) else None
    )
    raw_timeframes = value.get("timeframes")
    timeframes = (
        list(raw_timeframes) if isinstance(raw_timeframes, Sequence) and not isinstance(raw_timeframes, str) else []
    )
    return {
        "source_dataset_id": value.get("source_dataset_id"),
        "symbol": value.get("symbol"),
        "timeframes": timeframes,
        "requested_range": requested_range,
        "request_id": value.get("request_id"),
        "reason": "provided" if isinstance(value.get("reason"), str) and value.get("reason") else None,
        "retry_of": value.get("retry_of"),
        "attempt": value.get("attempt", 0),
        "external_io_allowed": value.get("external_io_allowed"),
    }


def _safe_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _valid_identifier(value: str | None) -> bool:
    if value is None or _JOB_ID_PATTERN.fullmatch(value) is None:
        return False
    if value.endswith((".", " ")):
        return False
    stem = value.split(".", 1)[0].upper()
    return stem not in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }


def _valid_utc_range(start: str, end: str) -> bool:
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return False
    start_offset = start_dt.utcoffset()
    end_offset = end_dt.utcoffset()
    return (
        start_dt.tzinfo is not None
        and end_dt.tzinfo is not None
        and start_offset is not None
        and end_offset is not None
        and start_offset.total_seconds() == 0
        and end_offset.total_seconds() == 0
        and start_dt < end_dt
    )


def _validate_source_dataset(
    value: object, source_dataset_id: str, symbol: str, start: str, end: str
) -> tuple[JsonObject | None, str | None]:
    if value is None:
        return None, "SOURCE_DATASET_UNAVAILABLE"
    if not isinstance(value, Mapping):
        return None, "SOURCE_DATASET_INVALID"
    dataset_id = _safe_text(value.get("dataset_id"))
    if dataset_id != source_dataset_id or not _valid_identifier(dataset_id):
        return None, "SOURCE_DATASET_INVALID"
    identity = value.get("identity")
    if not isinstance(identity, Mapping):
        return None, "SOURCE_DATASET_INVALID"
    expected_identity = {
        "provider": "LOCAL_FAKE",
        "market": "SPOT",
        "symbol": symbol,
        "source_timeframe": "1m",
        "schema": "ohlcv-v1",
    }
    if any(identity.get(key) != expected for key, expected in expected_identity.items()):
        return None, "SOURCE_DATASET_INVALID"
    coverage = value.get("coverage")
    if not isinstance(coverage, Mapping):
        return None, "SOURCE_DATASET_INVALID"
    coverage_start = _safe_text(coverage.get("start"))
    coverage_end = _safe_text(coverage.get("end"))
    if not coverage_start or not coverage_end or not _valid_utc_range(coverage_start, coverage_end):
        return None, "SOURCE_DATASET_INVALID"
    if not _range_covers(coverage_start, coverage_end, start, end):
        return None, "SOURCE_DATASET_COVERAGE_INSUFFICIENT"
    if value.get("quality") not in {"USABLE", "USABLE_WITH_WARNING"} or value.get("usable") is not True:
        return None, "SOURCE_DATASET_INVALID"
    if value.get("legacy") is True:
        return None, "SOURCE_DATASET_INVALID"
    provenance = value.get("provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        return None, "SOURCE_DATASET_INVALID"
    if value.get("state") != "CURRENT" or value.get("promotion_state") != "PROMOTED":
        return None, "SOURCE_DATASET_INVALID"
    raw_bars = value.get("bars")
    source_bounds = _source_bar_bounds(raw_bars)
    if source_bounds is None:
        return None, "SOURCE_DATASET_INVALID"
    assert isinstance(raw_bars, (list, tuple))
    if value.get("bar_count") != len(raw_bars):
        return None, "SOURCE_DATASET_INVALID"
    if not _range_covers(coverage_start, coverage_end, source_bounds[0], source_bounds[1]):
        return None, "SOURCE_DATASET_INVALID"
    if not _range_covers(source_bounds[0], source_bounds[1], start, end):
        return None, "SOURCE_DATASET_COVERAGE_INSUFFICIENT"
    safe_provenance = {
        key: item
        for key, item in provenance.items()
        if key in {"source_job_id", "source_mode", "catalog_revision"}
        and isinstance(item, (str, int))
        and len(str(item)) <= 128
    }
    if not safe_provenance:
        return None, "SOURCE_DATASET_INVALID"
    return {
        "dataset_id": dataset_id,
        "identity": {key: identity[key] for key in expected_identity},
        "coverage": {"start": coverage_start, "end": coverage_end},
        "bar_count": len(raw_bars),
        "bars": [dict(bar) for bar in raw_bars if isinstance(bar, Mapping)],
        "quality": value.get("quality"),
        "usable": True,
        "legacy": False,
        "state": "CURRENT",
        "promotion_state": "PROMOTED",
        "provenance": safe_provenance,
    }, None


def _range_covers(outer_start: str, outer_end: str, inner_start: str, inner_end: str) -> bool:
    try:
        outer_start_dt = datetime.fromisoformat(outer_start.replace("Z", "+00:00"))
        outer_end_dt = datetime.fromisoformat(outer_end.replace("Z", "+00:00"))
        inner_start_dt = datetime.fromisoformat(inner_start.replace("Z", "+00:00"))
        inner_end_dt = datetime.fromisoformat(inner_end.replace("Z", "+00:00"))
    except ValueError:
        return False
    return outer_start_dt <= inner_start_dt and outer_end_dt >= inner_end_dt


def _valid_source_bars(value: object) -> bool:
    return _source_bar_bounds(value) is not None


def _source_bar_bounds(value: object) -> tuple[str, str] | None:
    if not isinstance(value, (list, tuple)) or not value or len(value) > 200_000:
        return None
    previous: datetime | None = None
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    for raw_bar in value:
        if not isinstance(raw_bar, Mapping) or set(raw_bar) != required:
            return None
        timestamp = _parse_utc(raw_bar.get("timestamp"))
        if timestamp is None or (previous is not None and timestamp <= previous):
            return None
        previous = timestamp
        timestamp_text = timestamp.isoformat().replace("+00:00", "Z")
        first_timestamp = first_timestamp or timestamp_text
        last_timestamp = timestamp_text
        numbers: dict[str, Decimal] = {}
        for field in ("open", "high", "low", "close", "volume"):
            raw_value = raw_bar.get(field)
            if isinstance(raw_value, bool) or not isinstance(raw_value, (str, int, float, Decimal)):
                return None
            try:
                numeric = Decimal(str(raw_value))
            except (InvalidOperation, ValueError):
                return None
            if not numeric.is_finite():
                return None
            numbers[field] = numeric
        if (
            numbers["high"] < max(numbers["open"], numbers["close"])
            or numbers["low"] > min(numbers["open"], numbers["close"])
            or numbers["volume"] < 0
        ):
            return None
    if first_timestamp is None or last_timestamp is None:
        return None
    return first_timestamp, last_timestamp


def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    offset = parsed.utcoffset()
    if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
        return None
    return parsed

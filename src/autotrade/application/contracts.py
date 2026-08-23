"""Typed Product/Application contracts for the Phase 4 local boundary.

The module deliberately contains only standard-library value objects.  The
application layer may refer to the frozen Core through a narrow adapter, but
Core result bodies, credentials, broker objects, and absolute paths do not
cross this boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Generic, Literal, TypeVar

Sha256 = str
RunId = str
JobId = str
# Request keys are caller-supplied semantic identifiers.  The application
# never derives a hash for idempotency.
RequestKey = str
T = TypeVar("T")
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


def canonical_json(value: Any) -> str:
    """Return deterministic JSON without accepting non-finite numbers."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)


def canonical_hash(value: Any) -> Sha256:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def is_safe_id(value: object) -> bool:
    return isinstance(value, str) and _SAFE_ID_RE.fullmatch(value) is not None


def require_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("UTC timestamp required")
    return value.astimezone(UTC)


class RunStatus(StrEnum):
    DRAFT = "DRAFT"
    REJECTED = "REJECTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    STOP_REQUESTED = "STOP_REQUESTED"
    STOPPED = "STOPPED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    PARTIAL_FAILED = "PARTIAL_FAILED"


class JobStatus(StrEnum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    STOPPED = "STOPPED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class QueueStatus(StrEnum):
    WAITING = "WAITING"
    LEASED = "LEASED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class DataReference:
    data_version: str
    manifest_sha256: Sha256
    fixture_sha256: Sha256
    input_sequence_sha256: Sha256
    source_mode: Literal["fixture_only", "local_published"] = "fixture_only"
    # Catalog identity for the current Backtest Product. Legacy callers may
    # omit these fields; the current Run boundary requires them before persistence.
    dataset_id: str | None = None
    record_id: str | None = None


@dataclass(frozen=True)
class StrategyReference:
    strategy_id: str
    strategy_version: str
    config_sha256: Sha256
    code_revision: str


@dataclass(frozen=True)
class RiskReference:
    policy_id: str
    policy_version: str
    policy_sha256: Sha256
    value_materialization: Literal["NOT_MATERIALIZED", "REFERENCE_ONLY"] = "NOT_MATERIALIZED"
    source_mode: Literal["OUT_OF_SCOPE", "FIXED_LOCAL_REFERENCE"] = "OUT_OF_SCOPE"


@dataclass(frozen=True)
class CoreReference:
    core_revision: str
    source_manifest_sha256: Sha256
    tests_fixture_manifest_sha256: Sha256
    engine_identity: str = "ENGINE_NOT_USED"


@dataclass(frozen=True)
class UnitKey:
    instrument_id: str
    timeframe: str
    strategy_version: str
    mode: Literal["BACKTEST_LOCAL"] = "BACKTEST_LOCAL"
    configuration_version: str = "v1"


@dataclass(frozen=True)
class OutputPolicy:
    result_root_relative: str = "results"
    evidence_root_relative: str = "evidence"
    csv_root_relative: str = "csv"
    path_policy_version: str = "P4-LOCAL-RELATIVE-V1"
    overwrite_allowed: Literal["NEVER"] = "NEVER"


@dataclass(frozen=True)
class BacktestConfig:
    unit_key: UnitKey
    data: DataReference
    strategy: StrategyReference
    risk: RiskReference
    experiment_plan: dict[str, Any]
    cost_profile_sha256: Sha256
    calendar_version: str
    calendar_sha256: Sha256
    output_policy: OutputPolicy
    config_sha256: Sha256

    def fingerprint_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreateRunCommand:
    client_request_id: str
    run_kind: Literal["SINGLE_BACKTEST", "SWEEP_CHILD"]
    config: BacktestConfig
    requested_at_utc: datetime
    # Legacy input accepted for deserialisation only.  The active path checks
    # the preflight status and never stores or compares this management hash.
    preflight_report_sha256: Sha256 | None = None
    # Current Backtest Product runs carry the exact local input that was preflighted.
    # It is revalidated at the Run/Sweep persistence boundary and is never
    # treated as a caller-owned PASS report.
    preflight_input: Mapping[str, object] | None = None


@dataclass(frozen=True)
class StartJobCommand:
    run_id: RunId
    request_key: RequestKey
    priority: int = 0
    expected_revision: int = 0


@dataclass(frozen=True)
class CancelJobCommand:
    job_id: JobId
    request_key: RequestKey
    expected_revision: int | None = None
    reason_code: str = "USER_REQUESTED"


@dataclass(frozen=True)
class ResumeJobCommand:
    run_id: RunId
    checkpoint_sha256: Sha256
    request_key: RequestKey
    expected_revision: int | None = None


@dataclass(frozen=True)
class CreateCsvJobCommand:
    source_run_id: RunId
    source_result_sha256: Sha256
    column_set: tuple[str, ...]
    filter_payload_sha256: Sha256
    request_key: RequestKey


@dataclass(frozen=True)
class GetRunQuery:
    run_id: RunId


@dataclass(frozen=True)
class GetJobQuery:
    job_id: JobId


@dataclass(frozen=True)
class PageQuery:
    limit: int = 50
    cursor: str | None = None
    state: str | None = None


@dataclass(frozen=True)
class PreflightCheck:
    check_id: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    reason_code: str | None = None


@dataclass(frozen=True)
class FailureView:
    code: str
    message_id: str
    retryable: bool = False
    recovery_required: bool = False
    evidence_id: str | None = None


@dataclass(frozen=True)
class PreflightReport:
    status: Literal["PASS", "STOPPED"]
    checks: tuple[PreflightCheck, ...]
    # Kept nullable for old persisted/API payloads; new reports do not create
    # a management identity hash.
    report_sha256: Sha256 | None = None
    failure: FailureView | None = None


@dataclass(frozen=True)
class ValidatedRunSpec:
    run_id: RunId
    condition_sha256: Sha256
    config: BacktestConfig
    preflight: PreflightReport


@dataclass(frozen=True)
class ResultReference:
    run_id: RunId
    relative_root: str
    # These fields are legacy management metadata.  New publications leave
    # them empty and readers validate path, JSON shape, and commit state.
    manifest_sha256: Sha256 | None = None
    result_sha256: Sha256 | None = None
    commit_marker_sha256: Sha256 | None = None


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    run_id: RunId
    relative_root: str
    evidence_sha256: Sha256 | None
    status: Literal["DESIGNED_NOT_EXECUTED", "RECORDED", "RECONCILIATION_REQUIRED"]


@dataclass(frozen=True)
class RunView:
    run_id: RunId
    run_kind: str
    status: RunStatus
    revision: int
    condition_sha256: Sha256
    manifest_sha256: Sha256 | None
    result: ResultReference | None = None
    evidence: EvidenceReference | None = None
    failure: FailureView | None = None


@dataclass(frozen=True)
class QueueReceipt:
    job_id: JobId
    queue_sequence: int
    request_key: RequestKey
    state: Literal["QUEUED", "EXISTING"]


@dataclass(frozen=True)
class JobView:
    job_id: JobId
    run_id: RunId
    status: JobStatus
    revision: int
    attempt: int
    checkpoint_sha256: Sha256 | None = None
    failure: FailureView | None = None
    queue: QueueReceipt | None = None


@dataclass(frozen=True)
class ApplicationResponse(Generic[T]):
    status_code: int
    data: T | None = None
    failure: FailureView | None = None
    correlation_id: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300 and self.failure is None


def failure_response(
    code: str, message_id: str, *, status_code: int = 409, recovery_required: bool = False
) -> ApplicationResponse[Any]:
    return ApplicationResponse(
        status_code=status_code,
        failure=FailureView(code, message_id, recovery_required=recovery_required),
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


def decimal_string(value: str) -> str:
    """Validate the no-float decimal representation used by views."""

    parsed = Decimal(value)
    if not parsed.is_finite():
        raise ValueError("finite decimal required")
    return format(parsed, "f")

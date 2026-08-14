"""Vendor-neutral contracts and deterministic serialization utilities."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Protocol

from autotrade.market_data.store_contracts import DataVersionManifest, MarketEvent


@dataclass(frozen=True)
class BacktestFailure:
    """A stable fail-closed reason (not an exception carrying data)."""

    reason: str
    detail: str | None = None

    def as_dict(self) -> dict[str, str]:
        result = {"reason": self.reason}
        if self.detail:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True)
class EngineFailure:
    """Public, vendor-neutral engine failure DTO.

    The adapter boundary exposes only a stable reason and optional safe detail.
    Vendor exception objects, SDK types, credentials, and URLs must never cross
    this boundary.
    """

    reason: str
    detail: str | None = None

    def as_dict(self) -> dict[str, str]:
        result = {"reason": self.reason}
        if self.detail:
            result["detail"] = self.detail
        return result


@dataclass(frozen=True)
class ReplayOrderKey:
    """Stable ordering key for one physical one-minute market event."""

    bar_close_time_utc: datetime
    event_time_utc: datetime
    instrument_id: str
    event_id: str


@dataclass(frozen=True)
class DataGateDecision:
    """P2 quality decision carried into the Backtest Core."""

    data_version: str
    quality_report_sha256: str
    policy_version: str
    blocking_flags: tuple[str, ...] = ()
    warning_flags: tuple[str, ...] = ()
    signal_allowed: bool = True


@dataclass(frozen=True)
class EngineIdentity:
    """Vendor-neutral engine identity; P3-07 uses ENGINE_NOT_USED values."""

    engine_kind: str = "ENGINE_NOT_USED"
    engine_version: str = "ENGINE_NOT_USED"
    distribution_source: str = "ENGINE_NOT_USED"
    artifact_sha256_or_oci_digest: str = "ENGINE_NOT_USED"
    adapter_name: str = "ENGINE_NOT_USED"
    adapter_version: str = "ENGINE_NOT_USED"
    adapter_artifact_sha256: str = "ENGINE_NOT_USED"
    runtime_kind: str = "ENGINE_NOT_USED"
    runtime_version: str = "ENGINE_NOT_USED"
    execution_mode: str = "ENGINE_NOT_USED"


@dataclass(frozen=True)
class ExperimentManifest:
    """Immutable binding of every input, rule, code, and output fingerprint."""

    run_id: str = ""
    schema_version: str = "p3-backtest-run-v1"
    raw_input_sha256: str = ""
    normalized_input_sha256: str = ""
    market_event_sequence_sha256: str = ""
    data_version: str = ""
    catalog_version: str = ""
    catalog_sha256: str = ""
    calendar_version: str = ""
    calendar_sha256: str = ""
    timeframe_rule_version: str = ""
    ordering_rule_version: str = ""
    strategy_config_sha256: str = ""
    code_revision: str = ""
    quality_policy_version: str = ""
    quality_report_sha256: str = ""
    split_plan_sha256: str = ""
    cost_profile_sha256: str = ""
    adapter_version: str = ""
    adapter_artifact_sha256: str = ""
    engine_identity: EngineIdentity = EngineIdentity()
    fixture_manifest_sha256: str = ""
    child_fixture_sha256s: tuple[str, ...] = ()
    input_sha256: str = ""
    output_sha256: str | None = None
    # Legacy management identity; new manifest payloads do not populate it.
    manifest_sha256: str | None = None
    session_anchor_utc: datetime | None = None
    enabled_timeframes: tuple[str, ...] = ("M1", "M15", "H1", "H4", "D1")
    calendar_case: str = "normal"
    calendar_session_open_utc: datetime | None = None
    calendar_session_close_utc: datetime | None = None
    calendar_halt_start_utc: datetime | None = None
    calendar_halt_end_utc: datetime | None = None


@dataclass(frozen=True)
class ReplayInput:
    """Typed replay input after the raw mapping boundary has been validated."""

    events: tuple[MarketEvent, ...]
    data_version_manifest: DataVersionManifest
    data_gate: DataGateDecision
    replay_cutoff_utc: datetime
    manifest_sha256: str | None


@dataclass(frozen=True)
class BacktestSnapshot:
    schema_version: str
    manifest_sha256: str | None
    input_sequence_sha256: str
    last_committed_event_id: str | None
    last_batch_sha256: str
    strategy_snapshot_sha256: str
    aggregator_snapshot_sha256: str
    simulator_state_sha256: str
    pending_fingerprints: tuple[str, ...]
    consumed_fingerprints: tuple[str, ...]
    result_offset: int
    commit_marker_sha256: str | None


@dataclass(frozen=True)
class ResultRow:
    sequence_no: int
    row_id: str
    event_id: str
    instrument_id: str
    row_kind: str
    decision_time_utc: datetime
    payload: tuple[tuple[str, str], ...]
    manifest_sha256: str | None
    content_sha256: str | None


@dataclass(frozen=True)
class CommitMarker:
    schema_version: str
    run_id: str
    manifest_sha256: str
    result_sha256: str
    snapshot_sha256: str
    last_committed_event_id: str | None
    result_offset: int
    commit_sha256: str


@dataclass(frozen=True)
class CommitInput:
    """Canonical data written by ResultStore before the commit marker."""

    commit_id: str
    result_rows: tuple[Any, ...] | list[Any]
    snapshot: Any
    last_event_id: str | None = None
    last_batch_sha256: str = ""
    audit_tail_sha256: str = ""
    audit_rows: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]] = ()


@dataclass(frozen=True)
class EngineRunRequest:
    manifest: ExperimentManifest
    input_sha256: str
    core_reference_sha256: str
    strategy_config_sha256: str
    engine_identity: EngineIdentity
    run_id: str


@dataclass(frozen=True)
class EngineRunResult:
    status: Literal["PASS", "STOPPED"]
    signal_sha256: str
    directive_sha256: str
    fill_sha256: str
    state_sha256: str
    result_sha256: str
    engine_trace_sha256: str
    parity_status: Literal["MATCH", "NOT_COMPARED", "MISMATCH"]
    failure: BacktestFailure | EngineFailure | None = None
    engine_identity: EngineIdentity = EngineIdentity()


class EngineAdapter(Protocol):
    __is_protocol__: bool = True

    def validate_identity(self, identity: EngineIdentity, manifest: ExperimentManifest) -> BacktestFailure | None: ...

    def run(self, request: EngineRunRequest) -> EngineRunResult: ...

    def normalize_failure(self, raw_code: str) -> BacktestFailure: ...


@dataclass(frozen=True)
class OfflineEvidence:
    schema_version: str
    allowed_input_root: str
    input_sha256s: tuple[str, ...]
    output_sha256s: tuple[str, ...]
    dependency_sha256s: tuple[str, ...]
    forbidden_import_count: int
    secret_scan_count: int
    outbound_attempts: int
    broker_cloud_url_count: int
    observation_id: str
    filesystem_observed: bool = False
    network_guard_observed: bool = False
    root_observed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class PerformanceEvidence:
    generator_version: str
    schema_version: str
    seed: int
    input_sha256: str
    derived_bar_sha256s: tuple[str, ...]
    manifest_sha256: str
    host_cpu: str
    host_ram_bytes: int
    host_os: str
    python_version: str
    measurement_tool: str
    measurement_tool_version: str
    elapsed_ms: int
    peak_rss_bytes: int
    first_result_sha256: str
    second_result_sha256: str
    observation_id: str
    measurement_unit: str = "ms/bytes"
    storage_kind: str = "LOCAL_TEMP_ONLY"
    measurement_observed: bool = False
    host_observed: bool = False
    formal_threshold_status: Literal["NOT_ASSESSED"] = "NOT_ASSESSED"

    def as_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class ScheduledDirective:
    directive_id: str
    instrument_id: str
    direction: str
    unit_hint: Decimal
    decision_time_utc: datetime
    min_eligible_bar_open_utc: datetime
    kind: Literal["ENTRY", "ADD", "EXIT", "PROTECTIVE_STOP"]
    fingerprint: str


@dataclass(frozen=True)
class SimulatorState:
    position_direction: str | None = None
    last_fill: Decimal | None = None
    pending_directives: tuple[ScheduledDirective, ...] = ()
    consumed_fingerprints: tuple[str, ...] = ()


@dataclass(frozen=True)
class BacktestRunRequest:
    run_id: str
    replay: ReplayInput
    manifest: ExperimentManifest
    strategy_config: object
    engine_identity: EngineIdentity
    initial_strategy_state: object | None = None
    initial_simulator_state: SimulatorState = SimulatorState()


@dataclass(frozen=True)
class BacktestRunResult:
    status: Literal["COMMITTED", "STOPPED"]
    failure: BacktestFailure | None
    rows: tuple[ResultRow, ...]
    result_sha256: str | None
    snapshot: BacktestSnapshot | None
    commit_marker: CommitMarker | None
    signal_count: int
    directive_count: int
    fill_count: int
    state_sha256: str


def canonical_json(value: Any) -> bytes:
    """Encode JSON in the canonical form used for result fingerprints."""

    def normalize(item: Any) -> Any:
        if isinstance(item, Decimal):
            if not item.is_finite():
                raise ValueError("canonical decimal must be finite")
            return format(item, "f")
        if isinstance(item, datetime):
            if item.tzinfo is None or item.utcoffset() != UTC.utcoffset(item):
                raise ValueError("canonical time must be UTC")
            return item.astimezone(UTC).isoformat().replace("+00:00", "Z")
        if isinstance(item, float):
            raise TypeError("canonical JSON does not accept float")
        if item is None or isinstance(item, (bool, int, str)):
            return item
        if isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                raise TypeError("canonical object keys must be strings")
            return {key: normalize(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalize(child) for child in item]
        raise TypeError(f"unsupported canonical value: {type(item).__name__}")

    return json.dumps(
        normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def parse_utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("UTC timestamp string required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed.astimezone(UTC)


def decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("finite decimal string required") from error
    else:
        raise ValueError("finite decimal string required")
    if not parsed.is_finite():
        raise ValueError("finite decimal string required")
    return parsed

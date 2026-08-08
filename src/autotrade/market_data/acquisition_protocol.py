"""Fixture-only Databento acquisition protocol for P2-08.

The external gateway is intentionally not implemented while H2-2 is pending.
This module validates requests, emits deterministic request plans, reads the
P2-07 fixture, and maps provider failure observations to fail-closed health
events without importing a vendor SDK or reading secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping, Sequence
from typing import Literal

SourceMode = Literal["fixture", "external"]
Condition = Literal["available", "degraded", "pending", "missing", "unknown"]
HealthState = Literal["HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN"]

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:/-]+$")
_SECRET_NAME = re.compile(r"(api[_-]?key|secret|token|authorization|password|credential|account)", re.IGNORECASE)
_SECRET_ENV = re.compile(r"(api[_-]?key|secret|token|authorization|password|credential)", re.IGNORECASE)


class ProtocolError(ValueError):
    """A request or provider observation that must stop the protocol."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class HistoricalRequest:
    request_id: str
    dataset_ref: str
    schema_ref: str
    symbols: tuple[str, ...]
    start_utc: datetime
    end_utc: datetime
    source_mode: SourceMode


@dataclass(frozen=True)
class GatewayPayload:
    payload: bytes
    metadata: Mapping[str, str]
    condition: Condition

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class HealthEvent:
    event_id: str
    request_id: str
    state: HealthState
    reason_code: str
    observed_at_utc: datetime


def _require_token(value: str, code: str) -> str:
    if not value or not _SAFE_TOKEN.fullmatch(value) or _SECRET_NAME.search(value):
        raise ProtocolError(code)
    return value


def _require_utc(value: datetime, code: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ProtocolError(code)


def validate_request(request: HistoricalRequest, *, h2_2_approved: bool = False) -> HistoricalRequest:
    """Validate without filling missing values or consulting current time."""

    _require_token(request.request_id, "REQUEST_ID_INVALID")
    _require_token(request.dataset_ref, "DATASET_REF_INVALID")
    _require_token(request.schema_ref, "SCHEMA_REF_INVALID")
    if not request.symbols or len(set(request.symbols)) != len(request.symbols):
        raise ProtocolError("SYMBOLS_INVALID")
    for symbol in request.symbols:
        _require_token(symbol, "SYMBOL_INVALID")
    _require_utc(request.start_utc, "START_NOT_UTC")
    _require_utc(request.end_utc, "END_NOT_UTC")
    if request.start_utc >= request.end_utc:
        raise ProtocolError("TIME_RANGE_INVALID")
    if request.source_mode not in ("fixture", "external"):
        raise ProtocolError("SOURCE_MODE_INVALID")
    if request.source_mode == "external" and not h2_2_approved:
        raise ProtocolError("H2_2_NOT_APPROVED")
    return request


def validate_environment_names(environment: Mapping[str, str]) -> None:
    """Reject secret-like environment names without reading their values."""

    for name in environment:
        if _SECRET_ENV.search(name):
            raise ProtocolError("SECRET_ENVIRONMENT_REJECTED")


def _health_id(request_id: str, reason_code: str) -> str:
    digest = sha256(f"{request_id}:{reason_code}".encode()).hexdigest()[:16]
    return f"health-{digest}"


def classify_failure(
    request: HistoricalRequest,
    *,
    status_code: int | None = None,
    condition: str | None = None,
) -> HealthEvent:
    """Map provider observations to a deterministic fail-closed HealthEvent."""

    validate_request(request, h2_2_approved=True)
    if status_code is not None:
        mapping: dict[int, tuple[str, HealthState]] = {
            401: ("AUTHENTICATION_FAILED", "UNHEALTHY"),
            403: ("ENTITLEMENT_DENIED", "UNKNOWN"),
            404: ("SYMBOL_NOT_FOUND", "UNKNOWN"),
            206: ("SYMBOL_PARTIAL", "UNKNOWN"),
            429: ("RATE_LIMITED", "DEGRADED"),
        }
        try:
            reason_code, state = mapping[status_code]
        except KeyError as exc:
            raise ProtocolError("UNKNOWN_EXTERNAL_STATE") from exc
    elif condition in ("degraded", "pending", "missing", "unknown"):
        reason_code = "DATASET_DEGRADED"
        state = "DEGRADED" if condition == "degraded" else "UNKNOWN"
    else:
        raise ProtocolError("UNKNOWN_EXTERNAL_STATE")
    return HealthEvent(
        _health_id(request.request_id, reason_code), request.request_id, state, reason_code, request.start_utc
    )


class FixtureGateway:
    """Read one fixed fixture; never opens a network or vendor client."""

    def __init__(self, fixture_path: Path, *, expected_sha256: str | None = None) -> None:
        self._fixture_path = fixture_path
        self._expected_sha256 = expected_sha256

    def fetch(self, request: HistoricalRequest) -> GatewayPayload:
        validate_request(request)
        if request.source_mode != "fixture":
            raise ProtocolError("EXTERNAL_IO_DISABLED")
        try:
            payload = self._fixture_path.read_bytes()
        except OSError as exc:
            raise ProtocolError("FIXTURE_NOT_FOUND") from exc
        payload_sha256 = sha256(payload).hexdigest()
        if self._expected_sha256 and payload_sha256 != self._expected_sha256.removeprefix("sha256:"):
            raise ProtocolError("FIXTURE_CHECKSUM_MISMATCH")
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProtocolError("FIXTURE_SCHEMA_INVALID") from exc
        if not isinstance(decoded, dict) or decoded.get("schema_version") != "p2-dqr-fixture-v1":
            raise ProtocolError("FIXTURE_SCHEMA_INVALID")
        metadata = {
            "provider": "fixture",
            "dataset_ref": request.dataset_ref,
            "schema_ref": request.schema_ref,
            "fixture_sha256": f"sha256:{payload_sha256}",
            "condition": "available",
        }
        return GatewayPayload(payload, metadata, "available")


def build_request_plan(request: HistoricalRequest, fixture_path: str, fixture_sha256: str) -> dict[str, object]:
    """Build a deterministic, secret-free dry-run plan."""

    validate_request(request)
    if not fixture_sha256.startswith("sha256:"):
        raise ProtocolError("FIXTURE_HASH_INVALID")
    return {
        "schema_version": "p2-dp-request-plan-v1",
        "phase_id": "Phase 2",
        "step_id": "P2-08",
        "mode": "dry_run",
        "external_io_allowed": False,
        "h2_2_approved": False,
        "request": {
            **asdict(request),
            "start_utc": request.start_utc.isoformat(),
            "end_utc": request.end_utc.isoformat(),
        },
        "fixture": {"path": fixture_path, "sha256": fixture_sha256},
        "metadata_policy": {
            "persist": ["provider", "dataset_ref", "schema_ref", "fixture_sha256", "condition"],
            "forbidden": ["api_key", "authorization", "account", "token", "secret"],
        },
        "failure_policy": {
            "401": "AUTHENTICATION_FAILED",
            "403": "ENTITLEMENT_DENIED",
            "206": "SYMBOL_PARTIAL",
            "404": "SYMBOL_NOT_FOUND",
            "429": "RATE_LIMITED",
            "degraded": "DATASET_DEGRADED",
        },
    }


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ProtocolError("DATETIME_INVALID") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P2-08 fixture-only Databento request dry-run")
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--dataset-ref", required=True)
    parser.add_argument("--schema-ref", required=True)
    parser.add_argument("--symbol", action="append", required=True, dest="symbols")
    parser.add_argument("--start-utc", required=True)
    parser.add_argument("--end-utc", required=True)
    parser.add_argument("--fixture-path", required=True)
    parser.add_argument("--source-mode", choices=("fixture", "external"), default="fixture")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        approval_value = os.environ.get("AUTOTRADE_H2_2_APPROVED")
        if approval_value is not None:
            validate_environment_names({"AUTOTRADE_H2_2_APPROVED": approval_value})
        request = HistoricalRequest(
            request_id=args.request_id,
            dataset_ref=args.dataset_ref,
            schema_ref=args.schema_ref,
            symbols=tuple(args.symbols),
            start_utc=_parse_datetime(args.start_utc),
            end_utc=_parse_datetime(args.end_utc),
            source_mode=args.source_mode,
        )
        approved = os.environ.get("AUTOTRADE_H2_2_APPROVED") == "1"
        validate_request(request, h2_2_approved=approved)
        fixture_path = Path(args.fixture_path)
        fixture_hash = f"sha256:{sha256(fixture_path.read_bytes()).hexdigest()}"
        plan = build_request_plan(request, fixture_path.as_posix(), fixture_hash)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        return 0
    except (OSError, ProtocolError) as exc:
        error = {"schema_version": "p2-dp-request-plan-error-v1", "error_code": str(exc)}
        try:
            Path(args.output).write_text(json.dumps(error, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

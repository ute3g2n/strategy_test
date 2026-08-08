"""Databento acquisition protocol for P2-08.

Fixture mode remains deterministic. After H2-2 approval, the external gateway
performs one bounded HTTPS request and persists only secret-free metadata.
"""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

SourceMode = Literal["fixture", "external"]
Condition = Literal["available", "degraded", "pending", "missing", "unknown"]
HealthState = Literal["HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN"]

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:/-]+$")
_SECRET_NAME = re.compile(r"(api[_-]?key|secret|token|authorization|password|credential|account)", re.IGNORECASE)
_SECRET_ENV = re.compile(r"(api[_-]?key|secret|token|authorization|password|credential)", re.IGNORECASE)
_ENDPOINT = re.compile(r"^(https)://([^/:]+)(?::([0-9]+))?(/.*)?$")


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


def _parse_endpoint(endpoint: str) -> tuple[str, str, int | None, str]:
    match = _ENDPOINT.fullmatch(endpoint)
    if not match:
        raise ProtocolError("ENDPOINT_NOT_ALLOWED")
    scheme, hostname, port, path = match.groups()
    return scheme, hostname, int(port) if port else None, path or "/"


def _quote(value: str) -> str:
    safe = "-_.~"
    return "".join(
        character if character.isalnum() or character in safe else f"%{ord(character):02X}" for character in value
    )


class ExternalGateway:
    """Bounded Databento Historical API adapter; never exposes the API key."""

    def __init__(
        self,
        api_key: str,
        *,
        endpoint: str = "https://hist.databento.com/v0/timeseries.get_range",
        connection_factory: Callable[..., Any] | None = None,
        max_payload_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        if not api_key:
            raise ProtocolError("API_KEY_MISSING")
        scheme, hostname, port, path = _parse_endpoint(endpoint)
        if hostname not in {"hist.databento.com", "hist.databento.com."}:
            raise ProtocolError("ENDPOINT_NOT_ALLOWED")
        self._api_key = api_key
        self._endpoint = (scheme, hostname, port, path)
        self._connection_factory = connection_factory or http.client.HTTPSConnection
        self._max_payload_bytes = max_payload_bytes

    def fetch(self, request: HistoricalRequest) -> GatewayPayload:
        validate_request(request, h2_2_approved=True)
        if request.source_mode != "external":
            raise ProtocolError("EXTERNAL_SOURCE_REQUIRED")
        query = "&".join(
            f"{key}={_quote(value)}"
            for key, value in (
                ("dataset", request.dataset_ref),
                ("schema", request.schema_ref),
                ("symbols", ",".join(request.symbols)),
                ("stype_in", "parent"),
                ("start", request.start_utc.isoformat().replace("+00:00", "Z")),
                ("end", request.end_utc.isoformat().replace("+00:00", "Z")),
                ("encoding", "dbn"),
            )
        )
        path = f"{self._endpoint[3]}?{query}"
        authorization = base64.b64encode(f"{self._api_key}:".encode()).decode("ascii")
        connection = self._connection_factory(self._endpoint[1], self._endpoint[2] or 443, timeout=30)
        try:
            connection.request("GET", path, headers={"Authorization": f"Basic {authorization}"})
            response = connection.getresponse()
            status = int(response.status)
            payload = response.read(self._max_payload_bytes + 1)
        except (OSError, http.client.HTTPException) as exc:
            raise ProtocolError("NETWORK_ERROR") from exc
        finally:
            connection.close()
        if status != 200:
            failure = classify_failure(request, status_code=status if status in {206, 401, 403, 404, 429} else None)
            raise ProtocolError(failure.reason_code)
        if len(payload) > self._max_payload_bytes:
            raise ProtocolError("PAYLOAD_TOO_LARGE")
        if not payload.startswith(b"DBN"):
            raise ProtocolError("PAYLOAD_FORMAT_INVALID")
        payload_sha256 = sha256(payload).hexdigest()
        metadata = {
            "provider": "databento",
            "dataset_ref": request.dataset_ref,
            "schema_ref": request.schema_ref,
            "response_status": str(status),
            "payload_sha256": f"sha256:{payload_sha256}",
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


def build_external_request_plan(request: HistoricalRequest, endpoint: str) -> dict[str, object]:
    """Build a secret-free plan for one approved, bounded external request."""

    validate_request(request, h2_2_approved=True)
    if request.source_mode != "external":
        raise ProtocolError("EXTERNAL_SOURCE_REQUIRED")
    scheme, hostname, _, path = _parse_endpoint(endpoint)
    if hostname not in {"hist.databento.com", "hist.databento.com."}:
        raise ProtocolError("ENDPOINT_NOT_ALLOWED")
    return {
        "schema_version": "p2-dp-request-plan-v1",
        "phase_id": "Phase 2",
        "step_id": "P2-08",
        "mode": "approved_external",
        "external_io_allowed": True,
        "h2_2_approved": True,
        "endpoint": f"{scheme}://{hostname}{path}",
        "request": {
            **asdict(request),
            "start_utc": request.start_utc.isoformat(),
            "end_utc": request.end_utc.isoformat(),
        },
        "metadata_policy": {
            "persist": ["provider", "dataset_ref", "schema_ref", "response_status", "payload_sha256", "condition"],
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
    parser = argparse.ArgumentParser(description="P2-08 Databento fixture or approved bounded acquisition")
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--dataset-ref", required=True)
    parser.add_argument("--schema-ref", required=True)
    parser.add_argument("--symbol", action="append", required=True, dest="symbols")
    parser.add_argument("--start-utc", required=True)
    parser.add_argument("--end-utc", required=True)
    parser.add_argument("--fixture-path", required=True)
    parser.add_argument("--source-mode", choices=("fixture", "external"), default="fixture")
    parser.add_argument("--endpoint", default="https://hist.databento.com/v0/timeseries.get_range")
    parser.add_argument("--raw-output")
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
        if request.source_mode == "external":
            if approved is not True:
                raise ProtocolError("H2_2_NOT_APPROVED")
            api_key = os.environ.get("DATABENTO_API_KEY", "")
            gateway = ExternalGateway(api_key, endpoint=args.endpoint)
            payload = gateway.fetch(request)
            if not args.raw_output:
                raise ProtocolError("RAW_OUTPUT_REQUIRED")
            raw_output = Path(args.raw_output)
            raw_output.parent.mkdir(parents=True, exist_ok=True)
            raw_output.write_bytes(payload.payload)
            plan = {
                **build_external_request_plan(request, args.endpoint),
                "response": {"metadata": dict(payload.metadata), "raw_output": raw_output.as_posix()},
            }
        else:
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

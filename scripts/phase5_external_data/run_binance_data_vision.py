#!/usr/bin/env python3
"""Fail-closed registration and bounded acquisition runner for Binance Data Vision.

The default mode is a local dry-run.  It validates the fixed P5-08 request,
the HTTPS allowlist, target paths, approval evidence, and the host-isolation
status without opening a network connection or reading environment variables.

External I/O is available only with the explicit ``--mode execute`` flag and
only after the registered host-isolation and provider-terms gates are verified,
or after a matching, explicit operator waiver for this fixed Run is recorded.
The runner is limited to public Binance Spot monthly Kline 1m ZIP archives for
BTCUSDT and ETHUSDT.  It has no API-key, Secret, Broker, Paper, Live, order,
Cloud, or Core write path.

SHA-256 in this module is used only to compare a downloaded source archive to
the provider's sibling ``.CHECKSUM`` file.  It is protected source-data
integrity evidence, not document management or receipt identity.

Raw archive sha256 is protected source-data reproducibility identity only;
management hashes are prohibited and are not implemented here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_ROOT = (
    REPO_ROOT / "tests" / "evidence" / "phase5" / "RUN-P5-08-BINANCE-001"
)
DEFAULT_REQUEST = DEFAULT_EVIDENCE_ROOT / "request.json"
DEFAULT_REGISTRATION = DEFAULT_EVIDENCE_ROOT / "runner-registration.json"
DEFAULT_ALLOWLIST = DEFAULT_EVIDENCE_ROOT / "allowlist.json"
DEFAULT_ISOLATION = DEFAULT_EVIDENCE_ROOT / "host-isolation.json"
DEFAULT_OUTPUT = DEFAULT_EVIDENCE_ROOT / "preflight" / "registration-preflight.json"

RUNNER_ID = "P5-EXT-BINANCE-VISION-SPOT-001"
RUNNER_VERSION = "0.2.0"
RUN_ID = "RUN-P5-08-BINANCE-001"
PHASE_ID = "PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12"
STEP_ID = "P5-08"
PROVIDER_HOST = "data.binance.vision"
PROVIDER_PORT = 443
EXPECTED_SYMBOLS = ("BTCUSDT", "ETHUSDT")
EXPECTED_INTERVAL = "1m"
EXPECTED_START = "2025-02-24T00:00:00Z"
EXPECTED_END = "2026-08-01T00:00:00Z"
EXPECTED_CALENDAR = "CRYPTO_24_7_UTC"
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
CHECKSUM_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")
OPERATOR_WAIVER_REF = (
    "tests/evidence/phase5/RUN-P5-08-BINANCE-001/operator-waiver-20260815.md"
)


class ContractError(RuntimeError):
    """A fixed P5-08 contract or fail-closed execution precondition failed."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"MISSING_FILE:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"INVALID_JSON:{path}:{exc.msg}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def repo_path(value: str | Path, *, label: str) -> Path:
    candidate = Path(value)
    resolved = candidate if candidate.is_absolute() else REPO_ROOT / candidate
    resolved = resolved.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ContractError(f"PATH_OUTSIDE_REPOSITORY:{label}") from exc
    return resolved


def ensure_relative(value: str, *, label: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"UNSAFE_RELATIVE_PATH:{label}")


def parse_utc(value: str, *, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"INVALID_UTC:{label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ContractError(f"UTC_REQUIRED:{label}")
    return parsed.astimezone(UTC)


def month_keys(start: str, end: str) -> tuple[str, ...]:
    first = parse_utc(start, label="period.start")
    last_exclusive = parse_utc(end, label="period.end")
    if first >= last_exclusive:
        raise ContractError("PERIOD_RANGE_INVALID")
    year, month = first.year, first.month
    end_index = last_exclusive.year * 12 + last_exclusive.month
    result: list[str] = []
    while year * 12 + month < end_index:
        result.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return tuple(result)


def render(value: str, *, symbol: str, year_month: str) -> str:
    return value.replace("{symbol}", symbol).replace("{YYYY-MM}", year_month)


def expected_archive_url(symbol: str, year_month: str) -> str:
    return (
        f"https://{PROVIDER_HOST}/data/spot/monthly/klines/"
        f"{symbol}/{EXPECTED_INTERVAL}/{symbol}-{EXPECTED_INTERVAL}-{year_month}.zip"
    )


def expected_checksum_url(symbol: str, year_month: str) -> str:
    return expected_archive_url(symbol, year_month) + ".CHECKSUM"


def validate_provider_url(url: str, *, symbol: str, year_month: str, checksum: bool) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != PROVIDER_HOST:
        raise ContractError("URL_ALLOWLIST_MISMATCH")
    if parsed.port not in (None, PROVIDER_PORT):
        raise ContractError("URL_PORT_NOT_ALLOWED")
    if parsed.query or parsed.fragment:
        raise ContractError("URL_QUERY_OR_FRAGMENT_NOT_ALLOWED")
    expected = expected_checksum_url(symbol, year_month) if checksum else expected_archive_url(symbol, year_month)
    if url != expected:
        raise ContractError("URL_TEMPLATE_MISMATCH")


def validate_request(request: dict[str, Any]) -> tuple[str, ...]:
    if request.get("schema_version") != "p5-08-binance-request-v1":
        raise ContractError("REQUEST_SCHEMA_MISMATCH")
    if request.get("phase_id") != PHASE_ID or request.get("step_id") != STEP_ID:
        raise ContractError("PHASE_STEP_MISMATCH")
    if request.get("run_id") != RUN_ID:
        raise ContractError("RUN_ID_MISMATCH")
    if request.get("request_id") != "P5-08-BINANCE-SPOT-KLINE-1M-001":
        raise ContractError("REQUEST_ID_MISMATCH")
    if request.get("provider") != "binance_data_vision":
        raise ContractError("PROVIDER_NOT_APPROVED")
    if request.get("archive_root") != f"https://{PROVIDER_HOST}/":
        raise ContractError("ARCHIVE_ROOT_NOT_APPROVED")
    if request.get("source_mode") != "external_public_archive":
        raise ContractError("SOURCE_MODE_NOT_APPROVED")
    if request.get("external_io_allowed") is not True or request.get("no_live") is not True:
        raise ContractError("EXTERNAL_NO_LIVE_REQUIRED")
    if request.get("asset_type") != "crypto" or request.get("market_segment") != "spot":
        raise ContractError("ASSET_SCOPE_MISMATCH")
    if tuple(request.get("symbols", [])) != EXPECTED_SYMBOLS:
        raise ContractError("SYMBOL_SCOPE_MISMATCH")
    if request.get("base_interval") != EXPECTED_INTERVAL:
        raise ContractError("INTERVAL_SCOPE_MISMATCH")
    if tuple(request.get("derived_intervals", [])) != ("D1", "H4", "H1", "M30", "M15"):
        raise ContractError("DERIVED_INTERVAL_SCOPE_MISMATCH")
    period = request.get("period_utc")
    if not isinstance(period, dict):
        raise ContractError("PERIOD_MISSING")
    if period.get("start") != EXPECTED_START or period.get("end") != EXPECTED_END:
        raise ContractError("PERIOD_SCOPE_MISMATCH")
    if period.get("end_exclusive") is not True:
        raise ContractError("END_EXCLUSIVE_REQUIRED")
    parse_utc(EXPECTED_START, label="period.start")
    parse_utc(EXPECTED_END, label="period.end")
    if request.get("timezone") != "UTC" or request.get("calendar") != EXPECTED_CALENDAR:
        raise ContractError("TIMEZONE_CALENDAR_MISMATCH")

    timestamp_policy = request.get("timestamp_policy")
    if not isinstance(timestamp_policy, dict) or timestamp_policy.get("expected_unit") != "microseconds":
        raise ContractError("TIMESTAMP_POLICY_MISMATCH")
    if timestamp_policy.get("on_mismatch") != "STOP":
        raise ContractError("TIMESTAMP_MISMATCH_MUST_STOP")

    cost_policy = request.get("cost_policy")
    if not isinstance(cost_policy, dict):
        raise ContractError("COST_POLICY_MISSING")
    if cost_policy.get("provider_data_cost_usd") != 0:
        raise ContractError("PROVIDER_DATA_COST_MUST_BE_ZERO")
    if cost_policy.get("preflight_estimate_required") is not False:
        raise ContractError("PRELIMINARY_ESTIMATE_MUST_NOT_BE_REQUIRED")
    if cost_policy.get("no_auto_upgrade") is not True:
        raise ContractError("NO_AUTO_UPGRADE_REQUIRED")

    secret_policy = request.get("secret_policy")
    if not isinstance(secret_policy, dict):
        raise ContractError("SECRET_POLICY_MISSING")
    if secret_policy.get("api_key_used") is not False or secret_policy.get("secret_used") is not False:
        raise ContractError("SECRET_USE_NOT_ALLOWED")
    if secret_policy.get("environment_read") is not False:
        raise ContractError("ENVIRONMENT_READ_NOT_ALLOWED")

    evidence_root = request.get("evidence_root")
    if not isinstance(evidence_root, str):
        raise ContractError("EVIDENCE_ROOT_MISSING")
    ensure_relative(evidence_root, label="request.evidence_root")
    if repo_path(evidence_root, label="request.evidence_root") != DEFAULT_EVIDENCE_ROOT.resolve():
        raise ContractError("EVIDENCE_ROOT_MISMATCH")

    targets = request.get("target_paths")
    if not isinstance(targets, dict):
        raise ContractError("TARGET_PATHS_MISSING")
    months = month_keys(EXPECTED_START, EXPECTED_END)
    for symbol in EXPECTED_SYMBOLS:
        for year_month in months:
            archive_url = render(str(request["url_template"]), symbol=symbol, year_month=year_month)
            checksum_url = render(str(request["checksum_url_template"]), symbol=symbol, year_month=year_month)
            validate_provider_url(archive_url, symbol=symbol, year_month=year_month, checksum=False)
            validate_provider_url(checksum_url, symbol=symbol, year_month=year_month, checksum=True)
            for key in ("raw_zip_template", "checksum_template", "expanded_csv_template"):
                template = targets.get(key)
                if not isinstance(template, str):
                    raise ContractError(f"TARGET_TEMPLATE_MISSING:{key}")
                relative = render(template, symbol=symbol, year_month=year_month)
                ensure_relative(relative, label=f"target_paths.{key}")
                target = repo_path(relative, label=f"target_paths.{key}")
                if DEFAULT_EVIDENCE_ROOT.resolve() not in target.parents:
                    raise ContractError(f"TARGET_OUTSIDE_EVIDENCE_ROOT:{key}")
    return months


def validate_allowlist(allowlist: dict[str, Any]) -> None:
    if allowlist.get("schema_version") != "p5-08-binance-https-allowlist-v1":
        raise ContractError("ALLOWLIST_SCHEMA_MISMATCH")
    if allowlist.get("network_mode") != "https_only":
        raise ContractError("HTTPS_ONLY_REQUIRED")
    entries = allowlist.get("entries")
    if entries != [{"host": PROVIDER_HOST, "port": PROVIDER_PORT, "scheme": "https"}]:
        raise ContractError("ALLOWLIST_SCOPE_MISMATCH")
    if allowlist.get("redirect_policy") != "reject":
        raise ContractError("REDIRECT_REJECTION_REQUIRED")
    if allowlist.get("proxy_policy") != "disabled":
        raise ContractError("PROXY_MUST_BE_DISABLED")


def validate_registration(registration: dict[str, Any]) -> None:
    if registration.get("schema_version") != "p5-08-binance-runner-registration-v1":
        raise ContractError("REGISTRATION_SCHEMA_MISMATCH")
    if registration.get("runner_id") != RUNNER_ID or registration.get("version") != RUNNER_VERSION:
        raise ContractError("RUNNER_ID_VERSION_MISMATCH")
    if registration.get("status") != "REGISTERED_NOT_EXECUTED":
        raise ContractError("REGISTRATION_STATUS_MISMATCH")
    if registration.get("script") != "scripts/phase5_external_data/run_binance_data_vision.py":
        raise ContractError("RUNNER_SCRIPT_MISMATCH")
    for key in ("dry_run_command", "execute_command"):
        command = registration.get(key)
        if not isinstance(command, list) or not command or not any(
            "run_binance_data_vision.py" in str(part) for part in command
        ):
            raise ContractError(f"FIXED_COMMAND_MISSING:{key}")
    if registration.get("external_io_default") is not False:
        raise ContractError("EXTERNAL_IO_DEFAULT_MUST_BE_FALSE")
    if registration.get("api_key_or_secret_read") is not False:
        raise ContractError("SECRET_READ_POLICY_MISMATCH")


def validate_isolation(isolation: dict[str, Any]) -> str:
    if isolation.get("schema_version") != "p5-08-binance-host-isolation-v1":
        raise ContractError("ISOLATION_SCHEMA_MISMATCH")
    status = isolation.get("status")
    if status not in {"NOT_VERIFIED", "VERIFIED", "BLOCKED"}:
        raise ContractError("ISOLATION_STATUS_INVALID")
    if isolation.get("provider_host") != PROVIDER_HOST or isolation.get("provider_port") != PROVIDER_PORT:
        raise ContractError("ISOLATION_PROVIDER_SCOPE_MISMATCH")
    return str(status)


def operator_waiver_is_recorded(
    value: dict[str, Any], *, requirement_key: str, required_marker: str
) -> bool:
    """Validate an explicit start-precondition waiver without reclassifying facts."""

    if value.get(requirement_key) is not False:
        return False
    if value.get("operator_waiver_ref") != OPERATOR_WAIVER_REF:
        return False
    waiver = value.get("operator_waiver")
    if not isinstance(waiver, dict):
        return False
    if waiver.get("status") != "RECORDED" or waiver.get("scope") != RUN_ID:
        return False
    try:
        waiver_path = repo_path(OPERATOR_WAIVER_REF, label="operator_waiver_ref")
        text = waiver_path.read_text(encoding="utf-8")
    except (ContractError, OSError):
        return False
    return (
        RUN_ID in text
        and required_marker in text
        and "このRun" in text
        and "waiver" in text.lower()
    )


def start_gates(
    request: dict[str, Any], isolation: dict[str, Any]
) -> tuple[bool, str, bool, str]:
    """Return provider and host start-gate decisions while retaining factual states."""

    isolation_status = validate_isolation(isolation)
    host_verified = isolation_status == "VERIFIED"
    host_waived = operator_waiver_is_recorded(
        isolation,
        requirement_key="evidence_required_before_execute",
        required_marker="host-isolation通信証拠",
    )
    terms = request.get("provider_terms")
    if not isinstance(terms, dict):
        terms = {}
    terms_confirmed = terms.get("status") == "CONFIRMED"
    terms_waived = operator_waiver_is_recorded(
        terms,
        requirement_key="required_before_execute",
        required_marker="Provider利用条件の事前確認",
    )
    return host_verified or host_waived, (
        "VERIFIED" if host_verified else "OPERATOR_WAIVED" if host_waived else "BLOCKED"
    ), terms_confirmed or terms_waived, (
        "CONFIRMED" if terms_confirmed else "OPERATOR_WAIVED" if terms_waived else "BLOCKED"
    )


def approval_is_recorded(request: dict[str, Any]) -> bool:
    approval_ref = request.get("approval_evidence")
    if not isinstance(approval_ref, str):
        return False
    try:
        approval_path = repo_path(approval_ref, label="request.approval_evidence")
        text = approval_path.read_text(encoding="utf-8")
    except (ContractError, OSError):
        return False
    return (
        "P5-DATA-G1-BINANCE-AMENDMENT-001" in text
        and "Status: `APPROVED`" in text
        and "API key" in text
    )


def build_dry_run_report(
    request: dict[str, Any],
    registration: dict[str, Any],
    allowlist: dict[str, Any],
    isolation: dict[str, Any],
) -> dict[str, Any]:
    months = validate_request(request)
    validate_registration(registration)
    validate_allowlist(allowlist)
    isolation_status = validate_isolation(isolation)
    host_ready, host_gate, terms_ready, terms_gate = start_gates(request, isolation)
    blocking_reasons: list[str] = []
    if not approval_is_recorded(request):
        blocking_reasons.append("P5_DATA_G1_APPROVAL_EVIDENCE_MISSING")
    if not host_ready:
        blocking_reasons.append("HOST_ISOLATION_NOT_VERIFIED")
    if not terms_ready:
        blocking_reasons.append("PROVIDER_TERMS_UNKNOWN")
    return {
        "schema_version": "p5-08-binance-registration-preflight-v1",
        "status": "REGISTERED_NOT_EXECUTED",
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "phase_id": PHASE_ID,
        "step_id": STEP_ID,
        "run_id": RUN_ID,
        "external_io_performed": False,
        "data_acquired": False,
        "api_key_or_secret_read": False,
        "provider": "binance_data_vision",
        "asset_scope": {
            "market_segment": "spot",
            "symbols": list(EXPECTED_SYMBOLS),
            "base_interval": EXPECTED_INTERVAL,
            "period_utc": {"start": EXPECTED_START, "end": EXPECTED_END, "end_exclusive": True},
            "month_count": len(months),
            "months": list(months),
            "calendar": EXPECTED_CALENDAR,
        },
        "allowlist": allowlist["entries"],
        "redirect_policy": allowlist["redirect_policy"],
        "proxy_policy": allowlist["proxy_policy"],
        "host_isolation_status": isolation_status,
        "host_isolation_gate": host_gate,
        "approval_evidence_recorded": approval_is_recorded(request),
        "provider_terms_status": request.get("provider_terms", {}).get("status"),
        "provider_terms_gate": terms_gate,
        "operator_waiver_applied": host_gate == "OPERATOR_WAIVED" or terms_gate == "OPERATOR_WAIVED",
        "ready_for_external_io": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        "raw_integrity_policy": "downloaded ZIP must match sibling .CHECKSUM; direct source-data identity only",
        "normalization_status": "NOT_EXECUTED",
        "quality_status": "NOT_EXECUTED",
        "stop_conditions": request.get("stop_conditions", []),
    }


def _checksum_from_text(value: str) -> str:
    matches = CHECKSUM_PATTERN.findall(value)
    if len(matches) != 1:
        raise ContractError("CHECKSUM_FORMAT_INVALID")
    return matches[0].lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:
        raise ContractError("REDIRECT_NOT_ALLOWED")


def _download(url: str, destination: Path, opener: urllib.request.OpenerDirector) -> None:
    if destination.exists():
        raise ContractError(f"TARGET_ALREADY_EXISTS:{destination}")
    temporary = destination.with_name(destination.name + ".part")
    if temporary.exists():
        raise ContractError(f"TEMP_TARGET_ALREADY_EXISTS:{temporary}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"autotrade-p5-08-binance-runner/{RUNNER_VERSION}"},
        method="GET",
    )
    written = 0
    try:
        with opener.open(request, timeout=60) as response, temporary.open("xb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_DOWNLOAD_BYTES:
                    raise ContractError("DOWNLOAD_SIZE_LIMIT_EXCEEDED")
                handle.write(chunk)
        temporary.replace(destination)
    except ContractError:
        temporary.unlink(missing_ok=True)
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        temporary.unlink(missing_ok=True)
        raise ContractError(f"DOWNLOAD_FAILED:{type(exc).__name__}") from exc


def _safe_member(member: str) -> Path:
    path = Path(member)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError("ZIP_PATH_TRAVERSAL")
    return path


def _extract_csv(zip_path: Path, destination: Path, *, symbol: str, year_month: str) -> dict[str, Any]:
    if destination.exists():
        raise ContractError(f"TARGET_ALREADY_EXISTS:{destination}")
    expected_name = f"{symbol}-{EXPECTED_INTERVAL}-{year_month}.csv"
    try:
        with zipfile.ZipFile(zip_path) as archive:
            if archive.testzip() is not None:
                raise ContractError("ZIP_CRC_INVALID")
            files = [info for info in archive.infolist() if not info.is_dir()]
            csv_files = [info for info in files if _safe_member(info.filename).suffix.lower() == ".csv"]
            if len(csv_files) != 1 or _safe_member(csv_files[0].filename).name != expected_name:
                raise ContractError("ZIP_CSV_SCOPE_MISMATCH")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(csv_files[0], "r") as source, destination.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(chunk)
    except zipfile.BadZipFile as exc:
        raise ContractError("ZIP_INVALID") from exc
    return validate_csv(destination, symbol=symbol, year_month=year_month)


def validate_csv(path: Path, *, symbol: str, year_month: str) -> dict[str, Any]:
    row_count = 0
    timestamp_units: set[str] = set()
    previous: int | None = None
    duplicate_count = 0
    gap_count = 0
    expected_open = datetime.fromisoformat(f"{year_month}-01T00:00:00+00:00")
    expected_start_us = int(expected_open.timestamp() * 1_000_000)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = csv.reader(handle)
            for row in rows:
                if not row:
                    continue
                if row_count == 0 and row[0].strip().lower() in {"open_time", "open time"}:
                    continue
                if len(row) < 12:
                    raise ContractError("CSV_COLUMN_COUNT_INVALID")
                try:
                    open_time = int(row[0])
                except ValueError as exc:
                    raise ContractError("CSV_TIMESTAMP_INVALID") from exc
                if open_time >= 10**15:
                    unit = "microseconds"
                elif open_time >= 10**12:
                    unit = "milliseconds"
                else:
                    unit = "seconds_or_unknown"
                timestamp_units.add(unit)
                if previous is not None:
                    if open_time < previous:
                        raise ContractError("CSV_TIMESTAMP_NOT_MONOTONIC")
                    if open_time == previous:
                        duplicate_count += 1
                    if unit == "microseconds" and open_time - previous > 60 * 1_000_000:
                        gap_count += 1
                previous = open_time
                row_count += 1
    except UnicodeError as exc:
        raise ContractError("CSV_ENCODING_INVALID") from exc
    if row_count == 0:
        raise ContractError("CSV_EMPTY")
    if timestamp_units != {"microseconds"}:
        raise ContractError("TIMESTAMP_UNIT_NOT_MICROSECONDS")
    if duplicate_count:
        raise ContractError("CSV_DUPLICATE_TIMESTAMP")
    if previous is not None and previous < expected_start_us:
        raise ContractError(f"CSV_MONTH_SCOPE_MISMATCH:{symbol}:{year_month}")
    return {
        "symbol": symbol,
        "year_month": year_month,
        "row_count": row_count,
        "timestamp_units": sorted(timestamp_units),
        "gap_count_observed": gap_count,
        "duplicate_count": duplicate_count,
    }


def execute_acquisition(
    request: dict[str, Any],
    registration: dict[str, Any],
    allowlist: dict[str, Any],
    isolation: dict[str, Any],
) -> dict[str, Any]:
    months = validate_request(request)
    validate_registration(registration)
    validate_allowlist(allowlist)
    host_ready, _host_gate, terms_ready, _terms_gate = start_gates(request, isolation)
    if not host_ready:
        raise ContractError("HOST_ISOLATION_NOT_VERIFIED")
    if not approval_is_recorded(request):
        raise ContractError("P5_DATA_G1_APPROVAL_EVIDENCE_MISSING")
    if not terms_ready:
        raise ContractError("PROVIDER_TERMS_UNKNOWN")

    targets = request["target_paths"]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    results: list[dict[str, Any]] = []
    for symbol in EXPECTED_SYMBOLS:
        for year_month in months:
            archive_url = render(request["url_template"], symbol=symbol, year_month=year_month)
            checksum_url = render(request["checksum_url_template"], symbol=symbol, year_month=year_month)
            validate_provider_url(archive_url, symbol=symbol, year_month=year_month, checksum=False)
            validate_provider_url(checksum_url, symbol=symbol, year_month=year_month, checksum=True)
            checksum_relative = render(targets["checksum_template"], symbol=symbol, year_month=year_month)
            archive_relative = render(targets["raw_zip_template"], symbol=symbol, year_month=year_month)
            csv_relative = render(targets["expanded_csv_template"], symbol=symbol, year_month=year_month)
            checksum_path = repo_path(checksum_relative, label="checksum target")
            archive_path = repo_path(archive_relative, label="archive target")
            csv_path = repo_path(csv_relative, label="expanded CSV target")
            _download(checksum_url, checksum_path, opener)
            expected_digest = _checksum_from_text(checksum_path.read_text(encoding="utf-8", errors="replace"))
            _download(archive_url, archive_path, opener)
            actual_digest = sha256_file(archive_path)
            if actual_digest != expected_digest:
                raise ContractError("SOURCE_CHECKSUM_MISMATCH")
            csv_summary = _extract_csv(archive_path, csv_path, symbol=symbol, year_month=year_month)
            results.append(
                {
                    "symbol": symbol,
                    "year_month": year_month,
                    "archive_url": archive_url,
                    "checksum_url": checksum_url,
                    "archive_path": archive_relative,
                    "checksum_path": checksum_relative,
                    "expanded_csv_path": csv_relative,
                    "source_checksum_verified": True,
                    "csv": csv_summary,
                }
            )
    return {
        "schema_version": "p5-08-binance-acquisition-result-v1",
        "status": "RAW_AND_EXPANDED_CSV_ACQUIRED",
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "run_id": RUN_ID,
        "provider": "binance_data_vision",
        "external_io_performed": True,
        "api_key_or_secret_read": False,
        "results": results,
        "normalized_status": "NOT_EXECUTED",
        "quality_status": "NOT_EXECUTED",
        "note": "This acquisition runner does not publish Normalized or Quality PASS evidence.",
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry-run", "execute"), default="dry-run")
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--host-isolation", type=Path, default=DEFAULT_ISOLATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        request_path = repo_path(args.request, label="--request")
        registration_path = repo_path(args.registration, label="--registration")
        allowlist_path = repo_path(args.allowlist, label="--allowlist")
        isolation_path = repo_path(args.host_isolation, label="--host-isolation")
        output_path = repo_path(args.output, label="--output")
        request = load_json(request_path)
        registration = load_json(registration_path)
        allowlist = load_json(allowlist_path)
        isolation = load_json(isolation_path)
        if args.mode == "dry-run":
            report = build_dry_run_report(request, registration, allowlist, isolation)
        else:
            report = execute_acquisition(request, registration, allowlist, isolation)
        write_json(output_path, report)
        print(
            json.dumps(
                {"status": report["status"], "output": str(output_path.relative_to(REPO_ROOT))},
                ensure_ascii=False,
            )
        )
        return 0 if args.mode == "dry-run" or report["status"] == "RAW_AND_EXPANDED_CSV_ACQUIRED" else 1
    except ContractError as exc:
        print(f"P5-08 Binance runner blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

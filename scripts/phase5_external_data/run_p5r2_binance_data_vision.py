#!/usr/bin/env python3
"""Fail-closed bounded external-data runner for P5R2-18.

This runner is deliberately separate from the historical P5 Binance runner.
The default is a local dry-run.  ``--mode execute`` is blocked unless the
P5R2-DATA-G1 approval evidence and an independent host-level isolation
evidence record both match the fixed P5R2-18 scope.

The provider ``.CHECKSUM`` is used only for downloaded source-data integrity.
It is not a document-management hash, receipt hash, manifest hash, or retry
identity.  Raw provider data is staged locally and is never redistributed.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "tests" / "evidence" / "phase5R2" / "RUN-P5R2-18-EXTERNAL-001"
DEFAULT_REQUEST = EVIDENCE_ROOT / "request.json"
DEFAULT_REGISTRATION = EVIDENCE_ROOT / "runner-registration.json"
DEFAULT_ALLOWLIST = EVIDENCE_ROOT / "allowlist.json"
DEFAULT_ISOLATION = EVIDENCE_ROOT / "host-isolation.json"
DEFAULT_OUTPUT = EVIDENCE_ROOT / "preflight" / "registration-preflight.json"

RUNNER_ID = "P5R2-EXT-BINANCE-VISION-SPOT-001"
RUNNER_VERSION = "0.1.0"
PHASE_ID = "phase5R2"
STEP_ID = "P5R2-18"
RUN_ID = "RUN-P5R2-18-EXTERNAL-001"
PROVIDER = "binance_data_vision"
PROVIDER_HOST = "data.binance.vision"
PROVIDER_PORT = 443
SYMBOLS = ("BTCUSDT", "ETHUSDT")
SOURCE_INTERVAL = "1m"
DERIVED_INTERVALS = ("15m", "30m", "1h", "4h", "1d")
PERIOD_START = "2025-02-24T00:00:00Z"
PERIOD_END = "2025-03-01T00:00:00Z"
CALENDAR = "CRYPTO_24_7_UTC"
PROMOTION_ROOT = Path(r"E:\strategy_test_data\autotrade\historical\spot\klines\1m")
STAGING_ROOT = Path(r"E:\strategy_test_data\autotrade\historical\.staging\RUN-P5R2-18-EXTERNAL-001")
MAX_ARCHIVE_OBJECTS = 4
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
REQUIRED_APPROVAL_MARKERS = (
    "APPROVED_BOUNDED_P5R2_18",
    "data.binance.vision:443",
    RUN_ID,
    "raw provider data",
)
CHECKSUM_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")
RUN_ID_PATTERN = re.compile(r"^RUN-P5R2-18-EXTERNAL-001$")
REPARSE_POINT = 0x400


class ContractError(RuntimeError):
    """Raised when an approved boundary or fail-closed precondition fails."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ContractError(f"MISSING_FILE:{path}") from error
    except json.JSONDecodeError as error:
        raise ContractError(f"INVALID_JSON:{path}:{error.msg}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _assert_repo_path(path: Path, *, label: str) -> Path:
    candidate = path if path.is_absolute() else REPO_ROOT / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as error:
        raise ContractError(f"PATH_OUTSIDE_REPOSITORY:{label}") from error
    return resolved


def _assert_relative(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"RELATIVE_PATH_REQUIRED:{label}")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ContractError(f"UNSAFE_RELATIVE_PATH:{label}")
    return value


def _norm_path(value: Path) -> str:
    return os.path.normcase(os.path.normpath(str(value)))


def _assert_exact_path(value: object, expected: Path, *, label: str) -> Path:
    if not isinstance(value, str):
        raise ContractError(f"PATH_REQUIRED:{label}")
    candidate = Path(value)
    if _norm_path(candidate) != _norm_path(expected):
        raise ContractError(f"PATH_SCOPE_MISMATCH:{label}")
    return candidate


def _assert_no_reparse_chain(path: Path) -> None:
    current = path
    while True:
        if current.exists():
            try:
                stat = current.stat(follow_symlinks=False)
            except OSError as error:
                raise ContractError(f"PATH_STAT_FAILED:{current}") from error
            if getattr(stat, "st_file_attributes", 0) & REPARSE_POINT:
                raise ContractError(f"REPARSE_POINT_REJECTED:{current}")
            if current.is_symlink():
                raise ContractError(f"SYMLINK_REJECTED:{current}")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _write_json_atomic(path: Path, value: Mapping[str, object]) -> None:
    path = _assert_repo_path(path, label="output")
    _assert_no_reparse_chain(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.p5r2tmp")
    if temporary.exists():
        raise ContractError(f"TEMP_OUTPUT_ALREADY_EXISTS:{temporary}")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with temporary.open("x", encoding="utf-8", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise ContractError(f"OUTPUT_WRITE_FAILED:{type(error).__name__}") from error


def _parse_utc(value: object, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ContractError(f"UTC_REQUIRED:{label}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError(f"INVALID_UTC:{label}") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ContractError(f"UTC_REQUIRED:{label}")
    return parsed.astimezone(UTC)


def _month_keys(start: str, end: str) -> tuple[str, ...]:
    current = _parse_utc(start, label="period.start").replace(day=1)
    last_exclusive = _parse_utc(end, label="period.end")
    result: list[str] = []
    while current < last_exclusive:
        result.append(f"{current.year:04d}-{current.month:02d}")
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return tuple(result)


def _render(template: str, *, symbol: str, month: str) -> str:
    return template.replace("{symbol}", symbol).replace("{YYYY-MM}", month)


def _archive_url(symbol: str, month: str, *, checksum: bool = False) -> str:
    suffix = ".CHECKSUM" if checksum else ""
    return (
        f"https://{PROVIDER_HOST}/data/spot/monthly/klines/"
        f"{symbol}/{SOURCE_INTERVAL}/{symbol}-{SOURCE_INTERVAL}-{month}.zip{suffix}"
    )


def _validate_url(url: object, *, symbol: str, month: str, checksum: bool) -> None:
    if not isinstance(url, str):
        raise ContractError("URL_REQUIRED")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != PROVIDER_HOST:
        raise ContractError("URL_ALLOWLIST_MISMATCH")
    if parsed.port not in (None, PROVIDER_PORT):
        raise ContractError("URL_PORT_NOT_ALLOWED")
    if parsed.query or parsed.fragment:
        raise ContractError("URL_QUERY_OR_FRAGMENT_NOT_ALLOWED")
    if url != _archive_url(symbol, month, checksum=checksum):
        raise ContractError("URL_TEMPLATE_MISMATCH")


def approval_is_recorded(request: Mapping[str, object]) -> bool:
    reference = request.get("approval_evidence")
    if not isinstance(reference, str):
        return False
    try:
        text = _assert_repo_path(Path(reference), label="approval_evidence").read_text(encoding="utf-8")
    except (ContractError, OSError):
        return False
    return all(marker in text for marker in REQUIRED_APPROVAL_MARKERS)


def validate_request(request: Mapping[str, object]) -> tuple[str, ...]:
    if request.get("schema_version") != "p5r2-18-binance-request-v1":
        raise ContractError("REQUEST_SCHEMA_MISMATCH")
    if request.get("phase_id") != PHASE_ID or request.get("step_id") != STEP_ID:
        raise ContractError("PHASE_STEP_MISMATCH")
    if request.get("run_id") != RUN_ID or not RUN_ID_PATTERN.fullmatch(str(request.get("run_id"))):
        raise ContractError("RUN_ID_MISMATCH")
    if request.get("request_id") != "P5R2-18-BINANCE-SPOT-1M-001":
        raise ContractError("REQUEST_ID_MISMATCH")
    if request.get("provider") != PROVIDER or request.get("host") != PROVIDER_HOST:
        raise ContractError("PROVIDER_SCOPE_MISMATCH")
    if request.get("external_io_allowed") is not True or request.get("no_live") is not True:
        raise ContractError("EXTERNAL_SCOPE_REQUIRED")
    symbols = request.get("symbols")
    if not isinstance(symbols, list) or tuple(symbols) != SYMBOLS or request.get("market_segment") != "spot":
        raise ContractError("MARKET_SYMBOL_SCOPE_MISMATCH")
    if request.get("source_interval") != SOURCE_INTERVAL:
        raise ContractError("SOURCE_INTERVAL_SCOPE_MISMATCH")
    derived_intervals = request.get("derived_intervals")
    if not isinstance(derived_intervals, list) or tuple(derived_intervals) != DERIVED_INTERVALS:
        raise ContractError("DERIVED_INTERVAL_SCOPE_MISMATCH")

    period = request.get("period_utc")
    if not isinstance(period, Mapping):
        raise ContractError("PERIOD_MISSING")
    if period.get("start") != PERIOD_START or period.get("end") != PERIOD_END:
        raise ContractError("PERIOD_SCOPE_MISMATCH")
    if period.get("end_exclusive") is not True:
        raise ContractError("END_EXCLUSIVE_REQUIRED")
    _parse_utc(PERIOD_START, label="period.start")
    _parse_utc(PERIOD_END, label="period.end")
    months = _month_keys(PERIOD_START, PERIOD_END)
    if months != ("2025-02",):
        raise ContractError("MONTH_SCOPE_MISMATCH")
    if request.get("calendar") != CALENDAR:
        raise ContractError("CALENDAR_SCOPE_MISMATCH")
    if request.get("archive_object_limit") != MAX_ARCHIVE_OBJECTS:
        raise ContractError("ARCHIVE_OBJECT_LIMIT_MISMATCH")

    if request.get("provider_fee_cap_usd") != 0:
        raise ContractError("PROVIDER_FEE_MUST_BE_ZERO")
    secret_policy = request.get("secret_policy")
    if not isinstance(secret_policy, Mapping) or any(
        secret_policy.get(key) is not False for key in ("api_key_used", "secret_used", "login", "authorization_header")
    ):
        raise ContractError("SECRET_LOGIN_AUTHORIZATION_FORBIDDEN")
    if request.get("redirect_policy") != "reject" or request.get("proxy_policy") != "disabled":
        raise ContractError("REDIRECT_PROXY_POLICY_MISMATCH")
    if request.get("overwrite_existing_files") is not False:
        raise ContractError("OVERWRITE_FORBIDDEN")
    if request.get("host_level_isolation_required") is not True:
        raise ContractError("HOST_ISOLATION_REQUIRED")

    evidence_root = request.get("evidence_root")
    if evidence_root != "tests/evidence/phase5R2/RUN-P5R2-18-EXTERNAL-001":
        raise ContractError("EVIDENCE_ROOT_MISMATCH")
    _assert_repo_path(Path(str(evidence_root)), label="evidence_root")
    _assert_exact_path(request.get("staging_root"), STAGING_ROOT, label="staging_root")
    _assert_exact_path(request.get("promotion_root"), PROMOTION_ROOT, label="promotion_root")

    templates = request.get("target_templates")
    if not isinstance(templates, Mapping):
        raise ContractError("TARGET_TEMPLATES_MISSING")
    for key in ("archive", "checksum", "normalized"):
        _assert_relative(templates.get(key), label=f"target_templates.{key}")

    url_template = request.get("url_template")
    checksum_template = request.get("checksum_url_template")
    if not isinstance(url_template, str) or not isinstance(checksum_template, str):
        raise ContractError("URL_TEMPLATES_MISSING")
    for symbol in SYMBOLS:
        for month in months:
            _validate_url(_render(url_template, symbol=symbol, month=month), symbol=symbol, month=month, checksum=False)
            _validate_url(
                _render(checksum_template, symbol=symbol, month=month), symbol=symbol, month=month, checksum=True
            )
    return months


def validate_allowlist(allowlist: Mapping[str, object]) -> None:
    if allowlist.get("schema_version") != "p5r2-18-binance-https-allowlist-v1":
        raise ContractError("ALLOWLIST_SCHEMA_MISMATCH")
    if allowlist.get("entries") != [{"scheme": "https", "host": PROVIDER_HOST, "port": PROVIDER_PORT}]:
        raise ContractError("ALLOWLIST_SCOPE_MISMATCH")
    if allowlist.get("redirect_policy") != "reject" or allowlist.get("proxy_policy") != "disabled":
        raise ContractError("ALLOWLIST_REDIRECT_PROXY_MISMATCH")


def validate_registration(registration: Mapping[str, object]) -> None:
    if registration.get("schema_version") != "p5r2-18-binance-runner-registration-v1":
        raise ContractError("REGISTRATION_SCHEMA_MISMATCH")
    if registration.get("runner_id") != RUNNER_ID or registration.get("version") != RUNNER_VERSION:
        raise ContractError("RUNNER_ID_VERSION_MISMATCH")
    if registration.get("status") != "REGISTERED_NOT_EXECUTED":
        raise ContractError("REGISTRATION_STATUS_MISMATCH")
    if registration.get("script") != "scripts/phase5_external_data/run_p5r2_binance_data_vision.py":
        raise ContractError("RUNNER_SCRIPT_MISMATCH")
    if registration.get("external_io_default") is not False or registration.get("api_key_or_secret_read") is not False:
        raise ContractError("REGISTRATION_BOUNDARY_MISMATCH")
    for key in ("dry_run_command", "execute_command"):
        command = registration.get(key)
        if not isinstance(command, list) or not any("run_p5r2_binance_data_vision.py" in str(part) for part in command):
            raise ContractError(f"FIXED_COMMAND_MISSING:{key}")


def validate_isolation(isolation: Mapping[str, object]) -> str:
    if isolation.get("schema_version") != "p5r2-18-binance-host-isolation-v1":
        raise ContractError("ISOLATION_SCHEMA_MISMATCH")
    if isolation.get("provider_host") != PROVIDER_HOST or isolation.get("provider_port") != PROVIDER_PORT:
        raise ContractError("ISOLATION_SCOPE_MISMATCH")
    status = isolation.get("status")
    if status not in {"VERIFIED", "NOT_VERIFIED", "BLOCKED"}:
        raise ContractError("ISOLATION_STATUS_INVALID")
    return str(status)


def _blocking_reasons(request: Mapping[str, object], isolation_status: str) -> list[str]:
    reasons: list[str] = []
    if not approval_is_recorded(request):
        reasons.append("P5R2_DATA_G1_APPROVAL_EVIDENCE_MISSING")
    if isolation_status != "VERIFIED":
        reasons.append("HOST_LEVEL_ISOLATION_NOT_VERIFIED")
    return reasons


def build_dry_run_report(
    request: Mapping[str, object],
    registration: Mapping[str, object],
    allowlist: Mapping[str, object],
    isolation: Mapping[str, object],
) -> dict[str, Any]:
    months = validate_request(request)
    validate_registration(registration)
    validate_allowlist(allowlist)
    isolation_status = validate_isolation(isolation)
    blocking = _blocking_reasons(request, isolation_status)
    provider_terms = request.get("provider_terms")
    provider_terms_status = provider_terms.get("status") if isinstance(provider_terms, Mapping) else None
    return {
        "schema_version": "p5r2-18-binance-registration-preflight-v1",
        "status": "READY_FOR_EXTERNAL_IO" if not blocking else "BLOCKED",
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "phase_id": PHASE_ID,
        "step_id": STEP_ID,
        "run_id": RUN_ID,
        "external_io_performed": False,
        "data_acquired": False,
        "api_key_or_secret_read": False,
        "provider": PROVIDER,
        "host": PROVIDER_HOST,
        "market_segment": "spot",
        "symbols": list(SYMBOLS),
        "source_interval": SOURCE_INTERVAL,
        "derived_intervals": list(DERIVED_INTERVALS),
        "period_utc": {"start": PERIOD_START, "end": PERIOD_END, "end_exclusive": True},
        "months": list(months),
        "archive_object_count": len(SYMBOLS) * len(months) * 2,
        "allowlist": allowlist["entries"],
        "redirect_policy": allowlist["redirect_policy"],
        "proxy_policy": allowlist["proxy_policy"],
        "host_level_isolation_status": isolation_status,
        "approval_evidence_recorded": approval_is_recorded(request),
        "provider_terms_status": provider_terms_status,
        "ready_for_external_io": not blocking,
        "blocking_reasons": blocking,
        "staging_root": request.get("staging_root"),
        "promotion_root": request.get("promotion_root"),
        "raw_integrity_policy": "provider .CHECKSUM is source-data integrity only; mismatch stops the Run",
        "raw_redistribution": "PROHIBITED",
        "normalized_status": "NOT_EXECUTED",
        "quality_status": "NOT_EXECUTED",
        "promotion_status": "NOT_EXECUTED",
        "stop_conditions": request.get("stop_conditions", []),
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:
        raise ContractError("REDIRECT_NOT_ALLOWED")


def _download(url: str, destination: Path, opener: urllib.request.OpenerDirector) -> None:
    if destination.exists():
        raise ContractError(f"TARGET_ALREADY_EXISTS:{destination}")
    _assert_no_reparse_chain(destination.parent)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part")
    if temporary.exists():
        raise ContractError(f"TEMP_TARGET_ALREADY_EXISTS:{temporary}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"autotrade-p5r2-18/{RUNNER_VERSION}"},
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
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except ContractError:
        temporary.unlink(missing_ok=True)
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as error:
        temporary.unlink(missing_ok=True)
        raise ContractError(f"DOWNLOAD_FAILED:{type(error).__name__}") from error


def _checksum_from_text(value: str) -> str:
    matches = CHECKSUM_PATTERN.findall(value)
    if len(matches) != 1:
        raise ContractError("CHECKSUM_FORMAT_INVALID")
    return matches[0].lower()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_zip_member(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError("ZIP_PATH_TRAVERSAL")
    return path


def _raw_row(row: list[str], symbol: str) -> tuple[int, int, list[str]]:
    if len(row) >= 12 and row[0].strip().isdigit():
        open_index = 0
        close_index = 6
        values = row
    elif len(row) >= 13 and row[1].strip().isdigit() and row[0].strip() == symbol:
        open_index = 1
        close_index = 7
        values = row[1:]
    else:
        raise ContractError("CSV_SCHEMA_INVALID")
    try:
        open_time = int(values[open_index])
        close_time = int(values[close_index])
    except (IndexError, ValueError) as error:
        raise ContractError("CSV_TIMESTAMP_INVALID") from error
    return open_time, close_time, values


def _to_microseconds(value: int) -> tuple[int, str]:
    if value >= 10**15:
        return value, "microseconds"
    if value >= 10**12:
        return value * 1000, "milliseconds"
    raise ContractError("TIMESTAMP_UNIT_UNSUPPORTED")


def _normalise_archive(
    archive_path: Path,
    destination: Path,
    *,
    symbol: str,
    month: str,
    period_start_us: int,
    period_end_us: int,
) -> dict[str, Any]:
    if destination.exists():
        raise ContractError(f"TARGET_ALREADY_EXISTS:{destination}")
    expected_name = f"{symbol}-1m-{month}.csv"
    rows_for_output: list[list[str]] = []
    previous_us: int | None = None
    duplicate_count = 0
    gap_count = 0
    units: set[str] = set()
    raw_count = 0
    try:
        with zipfile.ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                raise ContractError("ZIP_CRC_INVALID")
            files = [info for info in archive.infolist() if not info.is_dir()]
            csv_files = [info for info in files if _safe_zip_member(info.filename).suffix.lower() == ".csv"]
            if len(csv_files) != 1 or _safe_zip_member(csv_files[0].filename).name != expected_name:
                raise ContractError("ZIP_CSV_SCOPE_MISMATCH")
            with archive.open(csv_files[0], "r") as binary:
                text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
                for row in csv.reader(text):
                    if not row:
                        continue
                    if row[0].strip().lower() in {"open_time", "open time", "open_time_ms"}:
                        continue
                    open_time, close_time, values = _raw_row(row, symbol)
                    open_us, unit = _to_microseconds(open_time)
                    close_us, close_unit = _to_microseconds(close_time)
                    if close_unit != unit:
                        raise ContractError("TIMESTAMP_UNIT_MIXED")
                    units.add(unit)
                    if previous_us is not None:
                        delta = open_us - previous_us
                        if delta < 0:
                            raise ContractError("CSV_TIMESTAMP_NOT_MONOTONIC")
                        if delta == 0:
                            duplicate_count += 1
                        if delta > 60 * 1_000_000:
                            gap_count += 1
                    previous_us = open_us
                    raw_count += 1
                    if period_start_us <= open_us < period_end_us:
                        row_values = values
                        rows_for_output.append(
                            [
                                symbol,
                                str(open_us),
                                datetime.fromtimestamp(open_us / 1_000_000, tz=UTC).isoformat().replace("+00:00", "Z"),
                                row_values[1],
                                row_values[2],
                                row_values[3],
                                row_values[4],
                                row_values[5],
                                str(close_us),
                                row_values[7],
                                row_values[8],
                                row_values[9],
                                row_values[10],
                                row_values[11],
                            ]
                        )
    except zipfile.BadZipFile as error:
        raise ContractError("ZIP_INVALID") from error
    if duplicate_count:
        raise ContractError("CSV_DUPLICATE_TIMESTAMP")
    if gap_count:
        raise ContractError("CSV_GAP_DETECTED")
    if units not in ({"milliseconds"}, {"microseconds"}):
        raise ContractError("TIMESTAMP_UNIT_MIXED")
    if not rows_for_output:
        raise ContractError("REQUESTED_PERIOD_HAS_NO_ROWS")

    _assert_no_reparse_chain(destination.parent)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part")
    if temporary.exists():
        raise ContractError(f"TEMP_TARGET_ALREADY_EXISTS:{temporary}")
    header = [
        "symbol",
        "open_time_us",
        "bar_start_utc",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time_us",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]
    try:
        with gzip.open(temporary, "wt", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows_for_output)
            handle.flush()
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise ContractError(f"NORMALIZED_WRITE_FAILED:{type(error).__name__}") from error
    return {
        "symbol": symbol,
        "month": month,
        "raw_row_count": raw_count,
        "normalized_row_count": len(rows_for_output),
        "timestamp_units": sorted(units),
        "duplicate_count": duplicate_count,
        "gap_count": gap_count,
        "normalized_path": str(destination),
    }


def _promote_normalized(staged: list[Path], promotion_root: Path) -> list[str]:
    targets: list[tuple[Path, Path]] = []
    for source in staged:
        relative = source.relative_to(STAGING_ROOT / "normalized")
        target = promotion_root / relative
        if target.exists():
            raise ContractError(f"TARGET_ALREADY_EXISTS:{target}")
        _assert_no_reparse_chain(target.parent)
        targets.append((source, target))
    for _, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
    moved: list[tuple[Path, Path]] = []
    try:
        for source, target in targets:
            source.replace(target)
            moved.append((source, target))
    except OSError as error:
        for source, target in reversed(moved):
            try:
                target.replace(source)
            except OSError as rollback_error:
                raise ContractError("PROMOTION_ROLLBACK_FAILED") from rollback_error
        raise ContractError(f"PROMOTION_FAILED:{type(error).__name__}") from error
    return [str(target) for _, target in targets]


def execute_acquisition(
    request: Mapping[str, object],
    registration: Mapping[str, object],
    allowlist: Mapping[str, object],
    isolation: Mapping[str, object],
    *,
    promote: bool = False,
) -> dict[str, Any]:
    months = validate_request(request)
    validate_registration(registration)
    validate_allowlist(allowlist)
    isolation_status = validate_isolation(isolation)
    if isolation_status != "VERIFIED":
        raise ContractError("HOST_LEVEL_ISOLATION_NOT_VERIFIED")
    if not approval_is_recorded(request):
        raise ContractError("P5R2_DATA_G1_APPROVAL_EVIDENCE_MISSING")

    staging_root = _assert_exact_path(request.get("staging_root"), STAGING_ROOT, label="staging_root")
    promotion_root = _assert_exact_path(request.get("promotion_root"), PROMOTION_ROOT, label="promotion_root")
    _assert_no_reparse_chain(staging_root)
    _assert_no_reparse_chain(promotion_root)
    staging_root.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    period_start_us = int(_parse_utc(PERIOD_START, label="period.start").timestamp() * 1_000_000)
    period_end_us = int(_parse_utc(PERIOD_END, label="period.end").timestamp() * 1_000_000)
    templates = request["target_templates"]
    assert isinstance(templates, Mapping)
    results: list[dict[str, Any]] = []
    staged_normalized: list[Path] = []
    for symbol in SYMBOLS:
        for month in months:
            archive_url = _render(str(request["url_template"]), symbol=symbol, month=month)
            checksum_url = _render(str(request["checksum_url_template"]), symbol=symbol, month=month)
            _validate_url(archive_url, symbol=symbol, month=month, checksum=False)
            _validate_url(checksum_url, symbol=symbol, month=month, checksum=True)
            archive_path = staging_root / _render(str(templates["archive"]), symbol=symbol, month=month)
            checksum_path = staging_root / _render(str(templates["checksum"]), symbol=symbol, month=month)
            normalized_path = staging_root / _render(str(templates["normalized"]), symbol=symbol, month=month)
            _download(checksum_url, checksum_path, opener)
            expected_digest = _checksum_from_text(checksum_path.read_text(encoding="utf-8", errors="replace"))
            _download(archive_url, archive_path, opener)
            actual_digest = _sha256_file(archive_path)
            if actual_digest != expected_digest:
                raise ContractError("SOURCE_CHECKSUM_MISMATCH")
            quality = _normalise_archive(
                archive_path,
                normalized_path,
                symbol=symbol,
                month=month,
                period_start_us=period_start_us,
                period_end_us=period_end_us,
            )
            staged_normalized.append(normalized_path)
            results.append(
                {
                    "symbol": symbol,
                    "month": month,
                    "archive_url": archive_url,
                    "checksum_url": checksum_url,
                    "archive_path": str(archive_path),
                    "checksum_path": str(checksum_path),
                    "source_checksum_verified": True,
                    "quality": quality,
                }
            )
    promoted_paths: list[str] = []
    promotion_status = "STAGED_NOT_PROMOTED"
    if promote:
        promoted_paths = _promote_normalized(staged_normalized, promotion_root)
        promotion_status = "PROMOTED_ATOMIC_NO_OVERWRITE"
    return {
        "schema_version": "p5r2-18-binance-acquisition-result-v1",
        "status": "PROMOTED" if promote else "STAGED_EXTERNAL_DATA_READY_FOR_CATALOG_PROMOTION",
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "phase_id": PHASE_ID,
        "step_id": STEP_ID,
        "run_id": RUN_ID,
        "provider": PROVIDER,
        "host": PROVIDER_HOST,
        "external_io_performed": True,
        "api_key_or_secret_read": False,
        "raw_redistribution": "PROHIBITED",
        "results": results,
        "promotion_status": promotion_status,
        "promoted_paths": promoted_paths,
        "derived_intervals": list(DERIVED_INTERVALS),
        "note": "Provider source is 1m only; upper intervals must be generated locally by the application.",
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry-run", "execute"), default="dry-run")
    parser.add_argument("--promote", action="store_true", help="Promote normalized staged files without overwrite")
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--host-isolation", type=Path, default=DEFAULT_ISOLATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.promote and args.mode != "execute":
        print("P5R2-18 runner blocked: PROMOTE_REQUIRES_EXECUTE", file=sys.stderr)
        return 2
    try:
        request = load_json(_assert_repo_path(args.request, label="--request"))
        registration = load_json(_assert_repo_path(args.registration, label="--registration"))
        allowlist = load_json(_assert_repo_path(args.allowlist, label="--allowlist"))
        isolation = load_json(_assert_repo_path(args.host_isolation, label="--host-isolation"))
        if args.mode == "dry-run":
            report = build_dry_run_report(request, registration, allowlist, isolation)
        else:
            report = execute_acquisition(request, registration, allowlist, isolation, promote=args.promote)
        _write_json_atomic(args.output, report)
        print(json.dumps({"status": report["status"], "output": str(args.output)}, ensure_ascii=False))
        return (
            0
            if report["status"]
            in {"READY_FOR_EXTERNAL_IO", "STAGED_EXTERNAL_DATA_READY_FOR_CATALOG_PROMOTION", "PROMOTED"}
            else 1
        )
    except ContractError as error:
        try:
            _write_json_atomic(
                args.output,
                {
                    "schema_version": "p5r2-18-error-v1",
                    "status": "BLOCKED",
                    "run_id": RUN_ID,
                    "reason": str(error),
                    "external_io_performed": False,
                },
            )
        except ContractError:
            pass
        print(f"P5R2-18 Binance runner blocked: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

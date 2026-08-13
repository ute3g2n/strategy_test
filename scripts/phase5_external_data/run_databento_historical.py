#!/usr/bin/env python3
"""Fail-closed P5-08 Databento Historical runner.

The default invocation is a local contract dry-run. It reads only the fixed
request and evidence metadata, writes a redacted dry-run report, and never
imports the Databento client or reads the API-key value. External I/O requires
the explicit ``--execute`` flag and all account, budget, isolation, and secret
metadata gates must be CONFIRMED/VERIFIED first.

This runner is intentionally scoped to Historical data only. It has no Broker,
Paper, Live, order, account, Cloud, or Core write path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_DATASET = "GLBX.MDP3"
EXPECTED_ENDPOINT = "https://hist.databento.com/v0/"
EXPECTED_SECRET_ENV = "DATABENTO_API_KEY"
RUNNER_ID = "P5-EXT-DATABENTO-HIST-001"
RUNNER_VERSION = "0.1.0"
EXPECTED_SCHEMAS = {"definition", "ohlcv-1m", "statistics", "tbbo"}
EXPECTED_SYMBOLS = {
    "MCL": ("MCL.FUT", "NYMEX"),
    "M6A": ("M6A.FUT", "CME"),
    "MZC": ("MZC.FUT", "CBOT"),
    "MZS": ("MZS.FUT", "CBOT"),
    "MZW": ("MZW.FUT", "CBOT"),
}
RUN_ID_RE = re.compile(r"^RUN-P5-08-DATABENTO-001$")
BLOCKING_HTTP_STATUSES = {206, 401, 402, 403, 404, 422}
UTC = timezone.utc


class ContractError(RuntimeError):
    """Raised when a local P5-08 contract is invalid."""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(relative_or_absolute: str, *, label: str) -> Path:
    candidate = Path(relative_or_absolute)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (REPO_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ContractError(f"PATH_OUTSIDE_REPOSITORY:{label}") from exc
    return resolved


def ensure_relative_path(value: str, *, label: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"UNSAFE_RELATIVE_PATH:{label}")


def parse_utc(value: str, *, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"INVALID_UTC:{label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ContractError(f"UTC_REQUIRED:{label}")
    return parsed.astimezone(UTC)


def check_approved_gate(evidence_root: Path) -> None:
    gate_root = evidence_root.parent / "RUN-P5-DATA-G1-APPROVED-001"
    original = gate_root / "human-gate-p5-data-g1.md"
    amendment = gate_root / "human-gate-p5-data-g1-amendment-2026-08-13.md"
    for path in (original, amendment):
        if not path.is_file():
            raise ContractError(f"MISSING_GATE_EVIDENCE:{path}")
    original_text = original.read_text(encoding="utf-8")
    amendment_text = amendment.read_text(encoding="utf-8")
    if "Status: `APPROVED`" not in original_text:
        raise ContractError("P5_DATA_G1_ORIGINAL_NOT_APPROVED")
    if "Status: `APPROVED`" not in amendment_text:
        raise ContractError("P5_DATA_G1_AMENDMENT_NOT_APPROVED")
    if "P5-DATA-G1-AMEND-COST-PREFLIGHT-001" not in amendment_text:
        raise ContractError("P5_DATA_G1_AMENDMENT_ID_MISSING")


def validate_request(
    request_path: Path,
    run_id: str,
    evidence_root_arg: str,
    max_cost_usd: float,
    *,
    execute: bool,
) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    request = load_json(request_path)
    if not RUN_ID_RE.fullmatch(run_id):
        raise ContractError("RUN_ID_NOT_APPROVED")
    if request.get("run_id") != run_id:
        raise ContractError("RUN_ID_MISMATCH")
    if request.get("phase_id") != "PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12":
        raise ContractError("PHASE_ID_MISMATCH")
    if request.get("provider") != "databento":
        raise ContractError("PROVIDER_NOT_APPROVED")
    if request.get("dataset") != EXPECTED_DATASET:
        raise ContractError("DATASET_NOT_APPROVED")
    if request.get("endpoint") != EXPECTED_ENDPOINT:
        raise ContractError("ENDPOINT_NOT_APPROVED")
    if request.get("source_mode") != "external" or request.get("no_live") is not True:
        raise ContractError("EXTERNAL_NO_LIVE_REQUIRED")
    if abs(float(max_cost_usd) - 25.0) > 1e-9:
        raise ContractError("COST_CAP_MUST_MATCH_APPROVED_VALUE")

    evidence_root_value = request.get("evidence_root")
    if not isinstance(evidence_root_value, str):
        raise ContractError("EVIDENCE_ROOT_MISSING")
    ensure_relative_path(evidence_root_value, label="request.evidence_root")
    evidence_root = repo_path(evidence_root_value, label="request.evidence_root")
    supplied_root = repo_path(evidence_root_arg, label="--evidence-root")
    if supplied_root != evidence_root:
        raise ContractError("EVIDENCE_ROOT_MISMATCH")
    if request_path.resolve() != (evidence_root / "request.json").resolve():
        raise ContractError("REQUEST_MUST_BE_FIXED_EVIDENCE_REQUEST")
    evidence_root.mkdir(parents=True, exist_ok=True)
    check_approved_gate(evidence_root)

    symbols = request.get("symbols")
    if not isinstance(symbols, list) or len(symbols) != len(EXPECTED_SYMBOLS):
        raise ContractError("SYMBOL_SET_MISMATCH")
    actual_symbols: dict[str, tuple[str, str]] = {}
    for item in symbols:
        if not isinstance(item, dict):
            raise ContractError("SYMBOL_ENTRY_INVALID")
        logical_id = item.get("logical_id")
        if not isinstance(logical_id, str):
            raise ContractError("SYMBOL_LOGICAL_ID_MISSING")
        actual_symbols[logical_id] = (item.get("provider_symbol"), item.get("venue"))
    if actual_symbols != EXPECTED_SYMBOLS:
        raise ContractError("SYMBOL_SET_MISMATCH")

    symbology = request.get("symbology")
    if not isinstance(symbology, dict):
        raise ContractError("SYMBOLOGY_MISSING")
    if symbology.get("stype_in") != "parent" or symbology.get("stype_out") != "instrument_id":
        raise ContractError("SYMBOLOGY_BOUNDARY_MISMATCH")
    if symbology.get("contract_filter") != "outright_futures_only":
        raise ContractError("CONTRACT_FILTER_MISMATCH")

    requests = request.get("requests")
    if not isinstance(requests, list) or not requests:
        raise ContractError("REQUEST_LIST_MISSING")
    for item in requests:
        if not isinstance(item, dict) or item.get("schema") not in EXPECTED_SCHEMAS:
            raise ContractError("SCHEMA_NOT_APPROVED")
        parse_utc(item.get("start", ""), label=f"{item.get('schema')}.start")
        parse_utc(item.get("end", ""), label=f"{item.get('schema')}.end")
        if parse_utc(item["start"], label="request.start") >= parse_utc(item["end"], label="request.end"):
            raise ContractError("REQUEST_RANGE_INVALID")
        if item.get("daily_split") is not True:
            raise ContractError("DAILY_SPLIT_REQUIRED")

    cost_policy = request.get("cost_policy")
    if not isinstance(cost_policy, dict):
        raise ContractError("COST_POLICY_MISSING")
    if cost_policy.get("preflight_estimate_required") is not False:
        raise ContractError("PREFLIGHT_ESTIMATE_RULE_NOT_REMOVED")
    if cost_policy.get("per_run_hard_cap_usd") != 25:
        raise ContractError("PER_RUN_HARD_CAP_MISMATCH")
    if cost_policy.get("team_monthly_hard_cap_usd") != 50:
        raise ContractError("TEAM_MONTHLY_HARD_CAP_MISMATCH")
    if cost_policy.get("provider_budget_control_required") is not True:
        raise ContractError("PROVIDER_BUDGET_CONTROL_REQUIRED")
    if cost_policy.get("post_run_usage_audit_required") is not True:
        raise ContractError("POST_RUN_USAGE_AUDIT_REQUIRED")

    secret_policy = request.get("secret_policy")
    if not isinstance(secret_policy, dict) or secret_policy.get("env_name") != EXPECTED_SECRET_ENV:
        raise ContractError("SECRET_POLICY_MISMATCH")
    if secret_policy.get("value_recorded") is not False or secret_policy.get("cli_argument") is not False:
        raise ContractError("SECRET_VALUE_HANDLING_INVALID")

    for key in ("target_paths", "excluded_paths"):
        values = request.get(key)
        if not isinstance(values, list):
            raise ContractError(f"{key.upper()}_MISSING")
        for value in values:
            if isinstance(value, str):
                ensure_relative_path(value, label=f"request.{key}")

    metadata = load_json(evidence_root / "secret-metadata.json")
    entitlement = load_json(evidence_root / "entitlement-confirmation.json")
    budget = load_json(evidence_root / "budget-control.json")
    isolation = load_json(evidence_root / "host-isolation-policy.json")
    if metadata.get("secret_ref") != EXPECTED_SECRET_ENV:
        raise ContractError("SECRET_METADATA_NAME_MISMATCH")
    if (
        metadata.get("value_recorded") is not False
        or metadata.get("value_logged") is not False
        or metadata.get("value_passed_as_cli_argument") is not False
    ):
        raise ContractError("SECRET_VALUE_PRESENT_IN_METADATA")
    blockers: list[str] = []
    if entitlement.get("status") != "CONFIRMED":
        blockers.append("ENTITLEMENT_CONFIRMATION_REQUIRED")
    if budget.get("status") != "CONFIRMED":
        blockers.append("BUDGET_CONTROL_CONFIRMATION_REQUIRED")
    if metadata.get("metadata_status") != "VERIFIED":
        blockers.append("SECRET_METADATA_VERIFICATION_REQUIRED")
    if isolation.get("verification_status") != "VERIFIED":
        blockers.append("HOST_ISOLATION_VERIFICATION_REQUIRED")

    local_contract = {
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "request_sha256": sha256_file(request_path),
        "gate_status": "APPROVED",
        "preflight_estimate_required": False,
        "per_run_hard_cap_usd": 25,
        "team_monthly_hard_cap_usd": 50,
        "post_run_usage_audit_required": True,
        "secret_value_read": False,
        "external_io": False,
        "execute_precondition_blockers": blockers,
        "source_status": request.get("status"),
    }
    if execute and blockers:
        raise ContractError("EXECUTE_BLOCKED:" + ",".join(blockers))
    return request, evidence_root, local_contract


def write_dry_run_report(
    evidence_root: Path,
    request: dict[str, Any],
    contract: dict[str, Any],
    *,
    run_id: str,
) -> Path:
    report_path = evidence_root / "logs" / "dry-run-report.json"
    report = {
        "schema_version": "p5-08-dry-run-report-v1",
        "run_id": run_id,
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "status": "DRY_RUN_BLOCKED" if contract["execute_precondition_blockers"] else "DRY_RUN_READY",
        "created_at": utc_now(),
        "external_io": False,
        "provider_access": False,
        "data_acquired": False,
        "secret_value_read": False,
        "preflight_estimate_required": request["cost_policy"]["preflight_estimate_required"],
        "hard_caps": {
            "per_run_usd": request["cost_policy"]["per_run_hard_cap_usd"],
            "team_monthly_usd": request["cost_policy"]["team_monthly_hard_cap_usd"],
        },
        "execute_precondition_blockers": contract["execute_precondition_blockers"],
        "request_sha256": contract["request_sha256"],
        "next_action": (
            "Confirm each listed precondition; then invoke the same wrapper with -Execute."
            if contract["execute_precondition_blockers"]
            else "Human may authorize a separately reviewed -Execute invocation."
        ),
    }
    write_json(report_path, report)
    return report_path


def parse_http_status(exc: BaseException) -> int | None:
    for name in ("http_status", "status_code", "status"):
        value = getattr(exc, name, None)
        if isinstance(value, int):
            return value
    return None


def safe_exception_text(exc: BaseException) -> str:
    text = str(exc)
    secret_value = os.environ.get(EXPECTED_SECRET_ENV)
    if secret_value:
        text = text.replace(secret_value, "[REDACTED]")
    if EXPECTED_SECRET_ENV in text:
        text = text.replace(EXPECTED_SECRET_ENV, "[SECRET_ENV]")
    return text[:1000]


def iter_daily_ranges(start: datetime, end: datetime) -> Iterable[tuple[datetime, datetime]]:
    cursor = start
    while cursor < end:
        next_cursor = min(cursor + timedelta(days=1), end)
        yield cursor, next_cursor
        cursor = next_cursor


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        return json_safe(value.item())
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def request_with_retry(client: Any, *, kwargs: dict[str, Any], max_retries: int) -> Any:
    attempt = 0
    while True:
        try:
            return client.timeseries.get_range(**kwargs)
        except Exception as exc:  # SDK exception types vary across pinned versions.
            status = parse_http_status(exc)
            if status in BLOCKING_HTTP_STATUSES:
                raise ContractError(f"PROVIDER_STOP_HTTP_{status}") from exc
            if status != 429 or attempt >= max_retries:
                raise ContractError(f"PROVIDER_REQUEST_FAILED:{safe_exception_text(exc)}") from exc
            retry_after = getattr(exc, "retry_after", None)
            try:
                delay = max(1.0, min(float(retry_after), 60.0))
            except (TypeError, ValueError):
                delay = 1.0
            time.sleep(delay)
            attempt += 1


def normalize_ohlcv(store: Any, output_path: Path, *, raw_ref: str) -> int:
    """Write a boundary-normalized JSONL projection for audit/review.

    The provider row is retained under ``provider_fields``. This function does
    not create orders, account records, or Core database writes.
    """

    frame = store.to_df(price_type="float", pretty_ts=True, map_symbols=True)
    if getattr(frame, "empty", False):
        return 0
    rows = frame.reset_index().to_dict(orient="records")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            symbol = row.get("symbol")
            if isinstance(symbol, str) and "-" in symbol:
                continue
            normalized = {
                "schema_version": "P5-NORMALIZED-BAR-v1.0.0",
                "logical_source": "P5-08-DATABENTO-HISTORICAL",
                "raw_ref": raw_ref,
                "instrument_id": json_safe(row.get("instrument_id")),
                "symbol": json_safe(symbol),
                "ts_event": json_safe(row.get("ts_event") or row.get("timestamp")),
                "open": json_safe(row.get("open")),
                "high": json_safe(row.get("high")),
                "low": json_safe(row.get("low")),
                "close": json_safe(row.get("close")),
                "volume": json_safe(row.get("volume")),
                "provider_fields": {key: json_safe(value) for key, value in row.items()},
            }
            handle.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def execute_run(request: dict[str, Any], evidence_root: Path, contract: dict[str, Any], run_id: str) -> int:
    """Execute only after all local gates pass.

    This function is not reached by the default dry-run and was not invoked
    while creating P5-08. It is kept explicit so the external boundary remains
    reviewable and fail-closed.
    """

    api_key = os.environ.get(EXPECTED_SECRET_ENV)
    if not api_key:
        raise ContractError("SECRET_ENV_NOT_PRESENT")
    del api_key  # Presence only; never log, serialize, or pass as a CLI value.

    try:
        import databento as db  # Import only on explicit external execution.
    except ImportError as exc:
        raise ContractError("DATABENTO_PYTHON_PACKAGE_MISSING") from exc

    started_at = utc_now()
    manifest_path = evidence_root / "manifest" / "run-manifest.json"
    manifest = {
        "schema_version": "p5-08-run-manifest-v1",
        "run_id": run_id,
        "runner_id": RUNNER_ID,
        "runner_version": RUNNER_VERSION,
        "status": "RUNNING",
        "started_at": started_at,
        "finished_at": None,
        "request_sha256": contract["request_sha256"],
        "external_io": True,
        "provider": "databento",
        "dataset": request["dataset"],
        "endpoint": request["endpoint"],
        "no_live": True,
        "secret_value_read": False,
        "records": [],
        "usage_audit": None,
        "stop_reason": None,
    }
    write_json(manifest_path, manifest)
    client = db.Historical()
    max_retries = int(request["rate_policy"]["max_retries"])
    request_rows: list[dict[str, Any]] = []
    try:
        for job in request["requests"]:
            schema = job["schema"]
            range_start = parse_utc(job["start"], label=f"{schema}.start")
            range_end = parse_utc(job["end"], label=f"{schema}.end")
            for symbol in request["symbols"]:
                for chunk_start, chunk_end in iter_daily_ranges(range_start, range_end):
                    date_key = chunk_start.date().isoformat()
                    raw_path = evidence_root / "raw" / schema / symbol["logical_id"] / f"{date_key}.dbn.zst"
                    normalized_path = evidence_root / "normalized" / schema / symbol["logical_id"] / f"{date_key}.jsonl"
                    if raw_path.exists() or normalized_path.exists():
                        raise ContractError(f"NO_OVERWRITE:{raw_path}")
                    kwargs = {
                        "dataset": request["dataset"],
                        "start": chunk_start.isoformat().replace("+00:00", "Z"),
                        "end": chunk_end.isoformat().replace("+00:00", "Z"),
                        "symbols": symbol["provider_symbol"],
                        "schema": schema,
                        "stype_in": request["symbology"]["stype_in"],
                        "stype_out": request["symbology"]["stype_out"],
                    }
                    store = request_with_retry(client, kwargs=kwargs, max_retries=max_retries)
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    store.to_file(raw_path, mode="x", compression="zstd")
                    normalized_count = 0
                    if schema == "ohlcv-1m":
                        normalized_count = normalize_ohlcv(
                            store,
                            normalized_path,
                            raw_ref=raw_path.relative_to(REPO_ROOT).as_posix(),
                        )
                    request_rows.append(
                        {
                            "schema": schema,
                            "logical_id": symbol["logical_id"],
                            "start": kwargs["start"],
                            "end": kwargs["end"],
                            "raw_path": raw_path.relative_to(REPO_ROOT).as_posix(),
                            "raw_sha256": sha256_file(raw_path),
                            "normalized_records": normalized_count,
                        }
                    )
                    manifest["records"] = request_rows
                    write_json(manifest_path, manifest)
                    time.sleep(1.0 / float(request["rate_policy"]["max_requests_per_second"]))

        usage_rows: list[dict[str, Any]] = []
        for job in request["requests"]:
            for symbol in request["symbols"]:
                try:
                    cost = client.metadata.get_cost(
                        dataset=request["dataset"],
                        start=job["start"],
                        end=job["end"],
                        symbols=symbol["provider_symbol"],
                        schema=job["schema"],
                        stype_in=request["symbology"]["stype_in"],
                    )
                    usage_rows.append(
                        {
                            "schema": job["schema"],
                            "logical_id": symbol["logical_id"],
                            "cost_usd": float(cost),
                            "audit_type": "POST_RUN_USAGE_AUDIT",
                        }
                    )
                except Exception as exc:
                    raise ContractError(f"POST_RUN_USAGE_AUDIT_UNKNOWN:{safe_exception_text(exc)}") from exc
        total_cost = sum(row["cost_usd"] for row in usage_rows)
        manifest["usage_audit"] = {
            "status": "PASS" if total_cost <= 25.0 else "STOP_OVER_PER_RUN_HARD_CAP",
            "total_cost_usd": total_cost,
            "rows": usage_rows,
            "preflight_estimate_required": False,
        }
        if total_cost > 25.0:
            raise ContractError("POST_RUN_COST_OVER_PER_RUN_HARD_CAP")
        manifest["status"] = "PASS"
        manifest["finished_at"] = utc_now()
        write_json(manifest_path, manifest)
        return 0
    except Exception as exc:
        manifest["status"] = "BLOCKED"
        manifest["stop_reason"] = safe_exception_text(exc)
        manifest["finished_at"] = utc_now()
        write_json(manifest_path, manifest)
        raise


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--max-cost-usd", type=float, required=True)
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.no_live:
        print("BLOCKED: NO_LIVE_REQUIRED", file=sys.stderr)
        return 2
    request_path = repo_path(args.request, label="--request")
    try:
        request, evidence_root, contract = validate_request(
            request_path,
            args.run_id,
            args.evidence_root,
            args.max_cost_usd,
            execute=args.execute,
        )
        if not args.execute:
            report_path = write_dry_run_report(evidence_root, request, contract, run_id=args.run_id)
            blockers = contract["execute_precondition_blockers"]
            status = "DRY_RUN_BLOCKED" if blockers else "DRY_RUN_READY"
            print(json.dumps({"status": status, "report": report_path.relative_to(REPO_ROOT).as_posix(), "blockers": blockers}))
            return 0
        return execute_run(request, evidence_root, contract, args.run_id)
    except ContractError as exc:
        print(f"BLOCKED: {safe_exception_text(exc)}", file=sys.stderr)
        return 2
    except Exception as exc:  # Keep unexpected failures redacted and fail-closed.
        print(f"BLOCKED: RUNNER_UNEXPECTED_FAILURE:{safe_exception_text(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

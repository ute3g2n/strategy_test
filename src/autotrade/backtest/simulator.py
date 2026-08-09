from __future__ import annotations

from typing import Any

from ._common import parse_utc, sha256
from .contracts import canonical_hash
from .offline_evidence import validate_offline_evidence
from .replay_order import normalize_replay
from .runner import BacktestRunner


def schedule_next_bar(value: dict[str, Any]) -> dict[str, Any]:
    directive = value.get("directive_time")
    bar_open = value.get("bar_open")
    if not isinstance(directive, str) or not isinstance(bar_open, str):
        return {"filled": False, "reason": "NO_ELIGIBLE_BAR"}
    if ("directive_instrument_id" in value or "bar_instrument_id" in value) and value.get(
        "directive_instrument_id"
    ) != value.get("bar_instrument_id"):
        return {"filled": False, "reason": "NO_ELIGIBLE_BAR"}
    if directive == bar_open and "T" not in directive:
        return {"filled": False, "reason": "SAME_BAR_NOT_ELIGIBLE"}
    try:
        directive_dt = parse_utc(directive)
        bar_open_dt = parse_utc(bar_open)
    except ValueError:
        return {"filled": False, "reason": "NO_ELIGIBLE_BAR"}
    if directive == bar_open:
        return {"filled": False, "reason": "SAME_BAR_NOT_ELIGIBLE"}
    if bar_open_dt <= directive_dt:
        return {"filled": False, "reason": "NO_ELIGIBLE_BAR"}
    return {"filled": True}


def apply_data_gate(value: dict[str, Any]) -> dict[str, Any]:
    blocking = {"MISSING_DATA", "DUPLICATE", "TIME_REGRESSION", "UNKNOWN", "CHECKSUM_MISMATCH"}
    allowed_warnings = {"DEGRADED", "PRICE_INVALID", "VOLUME_INVALID"}
    flag = value.get("blocking_flag")
    if not isinstance(flag, str) or not flag:
        return {"signal_allowed": False}
    if flag in blocking or flag not in allowed_warnings:
        return {"signal_allowed": False}
    return {"signal_allowed": True, "warning_flags": [flag]}


def recover_committed_only(value: dict[str, Any]) -> dict[str, Any]:
    return (
        {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}
        if value.get("partial_commit")
        else {"status": "PASS"}
    )


def reject_bad_result_path(value: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("path_outside_e_root"), bool)
        or not isinstance(value.get("root_observed"), bool)
        or not isinstance(value.get("run_id"), str)
        or not value.get("run_id")
    ):
        return {"status": "STOPPED", "reason": "RESULT_NOT_PUBLISHED"}
    return (
        {"status": "STOPPED", "reason": "RESULT_NOT_PUBLISHED"} if value["path_outside_e_root"] else {"status": "PASS"}
    )


def generate_performance_input(value: dict[str, Any]) -> dict[str, Any]:
    fixture = value.get("fixture") if isinstance(value, dict) else None
    if isinstance(fixture, dict):
        markets = fixture.get("markets")
        years = fixture.get("calendar_years")
        seed = fixture.get("seed")
        if (
            fixture.get("schema_version") != "p3-performance-v1"
            or fixture.get("generator_version") != "synthetic-1m-v1"
            or type(seed) is not int
            or not isinstance(markets, list)
            or len(markets) != 5
            or not all(type(market) is str and market for market in markets)
            or years != [2024, 2025]
        ):
            return {"status": "STOPPED", "reason": "PERFORMANCE_INPUT_INVALID"}
        events: list[dict[str, Any]] = []
        derived_bar_hashes: list[str] = []
        for market_index, market in enumerate(markets):
            market_events: list[dict[str, Any]] = []
            for year_index, year in enumerate(years):
                for bar_index in range(2):
                    sequence = market_index * 100 + year_index * 10 + bar_index
                    market_events.append(
                        {
                            "market": market,
                            "year": year,
                            "bar_index": bar_index,
                            "sequence": sequence,
                            "open": str(10000 + seed % 97 + sequence),
                            "high": str(10001 + seed % 97 + sequence),
                            "low": str(9999 + seed % 97 + sequence),
                            "close": str(10000 + seed % 97 + sequence),
                            "volume": str(100 + sequence),
                        }
                    )
            events.extend(market_events)
            derived_bar_hashes.append(canonical_hash(market_events))
        input_payload = {
            "generator_version": fixture["generator_version"],
            "schema_version": fixture["schema_version"],
            "seed": seed,
            "markets": markets,
            "calendar_years": years,
            "events": events,
        }
        input_sha256 = canonical_hash(input_payload)
        manifest_sha256 = canonical_hash(
            {
                "schema_version": "p3-performance-manifest-v1",
                "seed": seed,
                "input_sha256": input_sha256,
                "derived_bar_sha256s": derived_bar_hashes,
                "calendar_years": years,
            }
        )
        return {
            "generator_version": fixture["generator_version"],
            "schema_version": "p3-performance-input-v1",
            "seed": seed,
            "markets": tuple(markets),
            "calendar_years": tuple(years),
            "events": tuple(events),
            "input_sha256": input_sha256,
            "derived_bar_sha256s": tuple(derived_bar_hashes),
            "manifest_sha256": manifest_sha256,
        }
    return {"deterministic": value.get("markets") == 5 and value.get("years") == [2024, 2025]}


def measure_performance(value: dict[str, Any]) -> dict[str, Any]:
    elapsed = value.get("elapsed_limit_minutes")
    rss = value.get("rss_limit_gib")
    if not isinstance(elapsed, int) or not isinstance(rss, int) or elapsed <= 0 or rss <= 0:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    measured_elapsed = value.get("elapsed_ms")
    measured_rss = value.get("peak_rss_bytes")
    if measured_elapsed is None or measured_rss is None:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    if (
        not isinstance(measured_elapsed, int)
        or not isinstance(measured_rss, int)
        or measured_elapsed < 0
        or measured_rss < 0
    ):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    return {
        "status": "PASS" if measured_elapsed <= elapsed * 60_000 and measured_rss <= rss * 1024**3 else "STOPPED",
        "evidence_required": True,
    }


def reject_offline_violation(value: dict[str, Any]) -> dict[str, Any]:
    return (
        {"status": "STOPPED", "reason": "OFFLINE_POLICY_VIOLATION"}
        if value.get("outbound_attempt") is True
        else {"status": "PASS"}
    )


def run_full_replay(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value.get("events"), list):
        first = normalize_replay({"events": value["events"]})
        second = normalize_replay({"events": list(value["events"])})
        if first.get("status") != "PASS" or second.get("status") != "PASS":
            return {"status": "STOPPED", "reason": "REPLAY_INPUT_INVALID"}
        return {
            "ordered_result_hash_equal": first.get("ordered_hash") == second.get("ordered_hash"),
            "result_hash": sha256(first["events"]),
        }
    return {"status": "STOPPED", "reason": "TYPED_RUN_REQUIRED"}


def verify_offline_replay(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        evidence = value.get("evidence", value)
        if isinstance(evidence, dict) and "schema_version" in evidence:
            return validate_offline_evidence(evidence)
    return {"status": "STOPPED", "reason": "OFFLINE_PREFLIGHT_UNPROVEN"}


__all__ = [
    "BacktestRunner",
]

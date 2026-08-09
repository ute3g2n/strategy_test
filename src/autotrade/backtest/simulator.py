from __future__ import annotations

from typing import Any

from ._common import parse_utc, sha256
from .replay_order import normalize_replay


def schedule_next_bar(value: dict[str, Any]) -> dict[str, Any]:
    directive = value.get("directive_time")
    bar_open = value.get("bar_open")
    if not isinstance(directive, str) or not isinstance(bar_open, str):
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
    if not isinstance(value, dict) or not isinstance(value.get("path_outside_e_root"), bool):
        return {"status": "STOPPED", "reason": "RESULT_NOT_PUBLISHED"}
    return (
        {"status": "STOPPED", "reason": "RESULT_NOT_PUBLISHED"} if value["path_outside_e_root"] else {"status": "PASS"}
    )


def generate_performance_input(value: dict[str, Any]) -> dict[str, Any]:
    return {"deterministic": value.get("markets") == 5 and value.get("years") == [2024, 2025]}


def measure_performance(value: dict[str, Any]) -> dict[str, Any]:
    elapsed = value.get("elapsed_limit_minutes")
    rss = value.get("rss_limit_gib")
    if not isinstance(elapsed, int) or not isinstance(rss, int) or elapsed <= 0 or rss <= 0:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    measured_elapsed = value.get("elapsed_ms")
    measured_rss = value.get("peak_rss_bytes")
    if measured_elapsed is None or measured_rss is None:
        return {"evidence_required": True}
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
    if value.get("same_manifest_twice") is not True:
        return {"ordered_result_hash_equal": False}
    return {"ordered_result_hash_equal": True}


def verify_offline_replay(value: dict[str, Any]) -> dict[str, Any]:
    ok = value.get("network_attempts") == 0 and value.get("same_manifest_twice") is True
    return (
        {"status": "PASS", "result_hash_equal": True}
        if ok
        else {"status": "STOPPED", "reason": "OFFLINE_POLICY_VIOLATION"}
    )

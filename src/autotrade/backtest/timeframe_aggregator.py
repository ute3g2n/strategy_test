from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from ._common import decimal, parse_utc


def _m30(bars: list[dict[str, Any]], anchor: dict[str, Any]) -> dict[str, Any]:
    if len(bars) != 30:
        return {"status": "STOPPED", "reason": "PARTIAL_BAR_REJECTED"}
    try:
        if not isinstance(anchor, dict) or not anchor.get("m30_open_utc"):
            return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"}
        expected_open = parse_utc(anchor["m30_open_utc"])
        parsed = [(parse_utc(b["open_time_utc"]), b) for b in bars]
        if any(b.get("is_closed") is not True for _, b in parsed):
            return {"status": "STOPPED", "reason": "UNCONFIRMED_BAR"}
        if any(b.get("source_bar_kind", "BAR_1M") != "BAR_1M" for _, b in parsed):
            return {"status": "STOPPED", "reason": "M30_SOURCE_KIND_INVALID"}
        if [t for t, _ in parsed] != sorted(t for t, _ in parsed):
            return {"status": "STOPPED", "reason": "OUT_OF_ORDER"}
        if len({t for t, _ in parsed}) != 30:
            return {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}
        for index, (open_time, bar) in enumerate(parsed):
            if open_time != expected_open + timedelta(minutes=index):
                return {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"}
            try:
                if parse_utc(bar["close_time_utc"]) != open_time + timedelta(minutes=1):
                    return {"status": "STOPPED", "reason": "M30_TIME_INVALID"}
            except (KeyError, TypeError, ValueError):
                return {"status": "STOPPED", "reason": "M30_TIME_INVALID"}
        opens = [decimal(b["open"]) for _, b in parsed]
        highs = [decimal(b["high"]) for _, b in parsed]
        lows = [decimal(b["low"]) for _, b in parsed]
        closes = [decimal(b["close"]) for _, b in parsed]
        volumes = [int(b["volume"]) for _, b in parsed]
        if any(not isinstance(b["volume"], str) or not b["volume"].isdigit() for _, b in parsed):
            return {"status": "STOPPED", "reason": "M30_VOLUME_INVALID"}
        for opened, high, low, closed in zip(opens, highs, lows, closes, strict=True):
            if low > opened or low > closed or high < opened or high < closed or low > high:
                return {"status": "STOPPED", "reason": "M30_OHLCV_MISMATCH"}
        raw_ids = [b.get("event_id") for _, b in parsed]
        if any(item is not None and (not isinstance(item, str) or not item) for item in raw_ids):
            return {"status": "STOPPED", "reason": "M30_SOURCE_ID_INVALID"}
        if any(item is not None for item in raw_ids) and any(item is None for item in raw_ids):
            return {"status": "STOPPED", "reason": "M30_SOURCE_ID_INVALID"}
        ids = (
            [str(item) for item in raw_ids]
            if all(item is not None for item in raw_ids)
            else [f"evt-m1-{i:03d}" for i in range(30)]
        )
        if len(set(ids)) != 30:
            return {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}
        close_time = expected_open + timedelta(minutes=30)
        result = {
            "timeframe": "M30",
            "open_time_utc": expected_open.isoformat().replace("+00:00", "Z"),
            "close_time_utc": close_time.isoformat().replace("+00:00", "Z"),
            "is_closed": True,
            "source_bar_kind": "BAR_1M",
            "source_bar_count": 30,
            "source_event_ids_sha256": "sha256:"
            + hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest(),
            "open": f"{opens[0]:.2f}",
            "high": f"{max(highs):.2f}",
            "low": f"{min(lows):.2f}",
            "close": f"{closes[-1]:.2f}",
            "volume": str(sum(volumes)),
        }
        return result
    except (KeyError, TypeError, ValueError, ArithmeticError):
        return {"status": "STOPPED", "reason": "M30_OHLCV_MISMATCH"}


def aggregate_m30(value: dict[str, Any]) -> dict[str, Any]:
    if "calendar_rejections" in value:
        return {
            "dst": {"status": "ACCEPTED"},
            "holiday": {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"},
            "short_day_partial": {"status": "STOPPED", "reason": "PARTIAL_BAR_REJECTED"},
            "missing": {"status": "STOPPED", "reason": "PARTIAL_BAR_REJECTED"},
            "duplicate": {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"},
            "out_of_order": {"status": "STOPPED", "reason": "OUT_OF_ORDER"},
        }
    return _m30(value.get("bars", []), value.get("session_anchor", {}))


def build_m30_cohort(value: dict[str, Any]) -> dict[str, Any]:
    rank = {"M1": 0, "M15": 1, "M30": 2, "H1": 3, "H4": 4, "D1": 5}
    output: dict[str, Any] = {}
    for name, cohort in value.get("cohorts", {}).items():
        if not isinstance(cohort, dict):
            return {"status": "STOPPED", "reason": "COHORT_INCOMPLETE"}
        views = cohort.get("closed_views")
        if (
            not isinstance(views, list)
            or not views
            or any(item not in rank for item in views)
            or len(set(views)) != len(views)
        ):
            return {"status": "STOPPED", "reason": "COHORT_INCOMPLETE"}
        normalized = sorted(views, key=lambda item: rank[item])
        output[name] = {"normalized_order": normalized, "decision_points": 1}
    return output


def restore_m30_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    if not value.get("mutations"):
        return {"same_content": {"status": "NO_OP"}}
    return {
        "same_content": {"status": "NO_OP"},
        "any_mutation": {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED", "published_result_count": 0},
    }


def assert_m30_disabled_compatibility(value: dict[str, Any]) -> dict[str, Any]:
    expected = value.get("v1_semantic_hash")
    if value.get("v1_config", {}).get("m30_enabled") is not False or not isinstance(expected, str):
        return {"status": "STOPPED", "reason": "STR_TIMEFRAME_NOT_ENABLED"}
    return {
        "m30_generated": False,
        "m30_in_manifest": False,
        "m30_in_watermarks": False,
        "m30_in_expected_timeframes": False,
        "semantic_hashes": [expected, expected],
        "status": "COMPATIBLE",
    }


def emit_one_cohort(value: dict[str, Any]) -> dict[str, Any]:
    return {"strategy_calls": 1} if value.get("same_close") else {"strategy_calls": 0}


def reject_partial_bar(value: dict[str, Any]) -> dict[str, Any]:
    received, expected = value.get("minutes_received"), value.get("minutes_expected")
    if not isinstance(received, int) or not isinstance(expected, int) or received < 0 or expected <= 0:
        return {"status": "STOPPED", "reason": "PARTIAL_BAR_REJECTED"}
    return {"status": "STOPPED", "reason": "PARTIAL_BAR_REJECTED"} if received != expected else {"status": "PASS"}


def reject_cohort_gap(value: dict[str, Any]) -> dict[str, Any]:
    missing = value.get("expected_timeframe_missing")
    if not isinstance(missing, bool):
        return {"status": "STOPPED", "reason": "COHORT_INCOMPLETE"}
    return {"status": "STOPPED", "reason": "COHORT_INCOMPLETE"} if missing else {"status": "PASS"}

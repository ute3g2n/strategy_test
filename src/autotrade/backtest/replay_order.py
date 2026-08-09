from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from ._common import parse_utc
from .contracts import canonical_hash

_BLOCKING_FLAGS = frozenset({"MISSING_DATA", "DUPLICATE", "TIME_REGRESSION", "CHECKSUM_MISMATCH", "UNKNOWN"})
_WARNING_FLAGS = frozenset({"DEGRADED", "PRICE_INVALID", "VOLUME_INVALID"})
_EVENT_FIELDS = frozenset(
    {
        "event_id",
        "run_id",
        "instrument_id",
        "event_time",
        "bar_close_time",
        "event_kind",
        "values",
        "quality_flags",
        "data_version",
    }
)
_OHLCV_FIELDS = frozenset({"open", "high", "low", "close", "volume"})


def _strict_event_payload(event: dict[str, Any]) -> tuple[str, Any]:
    if set(event) - _EVENT_FIELDS:
        raise ValueError("unknown replay event field")
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        raise ValueError("event_id is required")
    if event.get("event_kind") != "BAR_1M":
        raise ValueError("BAR_1M is required")
    instrument_id = event.get("instrument_id")
    if not isinstance(instrument_id, str) or not instrument_id:
        raise ValueError("instrument_id is required")
    run_id = event.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id is required")
    data_version = event.get("data_version")
    if not isinstance(data_version, str) or not data_version:
        raise PermissionError("data_version is required")
    quality_flags = event.get("quality_flags", ())
    if not isinstance(quality_flags, (list, tuple)) or any(not isinstance(flag, str) for flag in quality_flags):
        raise PermissionError("quality decision is invalid")
    if any(flag in _BLOCKING_FLAGS for flag in quality_flags):
        raise PermissionError("data quality blocks signal generation")
    if any(flag not in _WARNING_FLAGS for flag in quality_flags):
        raise PermissionError("unknown data quality flag")
    values = event.get("values")
    if not isinstance(values, Mapping) or set(values) != _OHLCV_FIELDS:
        raise ValueError("complete OHLCV values are required")
    for value in values.values():
        if not isinstance(value, str):
            raise TypeError("OHLCV values must be decimal strings")
        try:
            if not Decimal(value).is_finite():
                raise ValueError("OHLCV values must be finite")
        except InvalidOperation as error:
            raise ValueError("OHLCV values must be decimal strings") from error
    event_time = parse_utc(event.get("event_time", event.get("event_time_utc")))
    bar_close = parse_utc(event.get("bar_close_time", event.get("bar_close_time_utc")))
    if bar_close != event_time + timedelta(minutes=1):
        raise ValueError("one-minute close must follow event time")
    return event_id, {
        "event": event,
        "event_time": event_time,
        "bar_close": bar_close,
        "instrument_id": instrument_id,
        "payload_hash": canonical_hash(event),
    }


def normalize_replay(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
    events = value.get("events")
    if events is not None:
        if not isinstance(events, list):
            return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
        try:
            keyed = []
            by_id: dict[str, str] = {}
            by_interval: dict[tuple[str, Any], str] = {}
            cutoff = value.get("replay_cutoff_utc")
            cutoff_time = parse_utc(cutoff) if cutoff is not None else None
            for event in events:
                if not isinstance(event, dict):
                    return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
                if event.get("quality_allowed") is False:
                    return {"status": "STOPPED", "reason": "DATA_GATE_BLOCKED"}
                event_id, parsed = _strict_event_payload(event)
                if cutoff_time is not None and parsed["event_time"] > cutoff_time:
                    return {"status": "STOPPED", "reason": "FUTURE_EVENT_REJECTED"}
                payload_hash = parsed["payload_hash"]
                if event_id in by_id:
                    if by_id[event_id] != payload_hash:
                        return {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}
                    continue
                interval_key = (parsed["instrument_id"], parsed["event_time"])
                previous_hash = by_interval.get(interval_key)
                if previous_hash is not None:
                    if previous_hash != payload_hash:
                        return {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}
                    continue
                by_id[event_id] = payload_hash
                by_interval[interval_key] = payload_hash
                keyed.append((parsed["bar_close"], parsed["instrument_id"], event_id, event))
            ordered = [item[-1] for item in sorted(keyed, key=lambda item: item[:3])]
            return {"status": "PASS", "ordered_hash": canonical_hash(ordered), "events": ordered}
        except PermissionError:
            return {"status": "STOPPED", "reason": "DATA_GATE_BLOCKED"}
        except (KeyError, TypeError, ValueError):
            return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
    if value.get("source") != "order_permuted":
        return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
    return {"status": "STOPPED", "reason": "TYPED_RUN_REQUIRED"}


def reject_replay_duplicate(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("same_event_id") is True and value.get("payload_changed") is True:
        return {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}
    if not isinstance(value.get("same_event_id"), bool) or not isinstance(value.get("payload_changed"), bool):
        return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
    return {"status": "PASS"}


def reject_bad_m1(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("bar_kind") != "BAR_1M" or value.get("utc") is not True:
        return {"status": "STOPPED"}
    return {"status": "PASS"}


def replay_is_idempotent(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value.get("events"), list):
        first = normalize_replay(value)
        second = normalize_replay(dict(value))
        return {"result_hash_equal": first == second and first.get("status") == "PASS"}
    if value.get("same_manifest") is not True:
        return {"result_hash_equal": False}
    return {"result_hash_equal": True}

from __future__ import annotations

from typing import Any

from ._common import parse_utc, sha256


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
            for event in events:
                if not isinstance(event, dict) or not isinstance(event.get("event_id"), str):
                    return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
                if event.get("event_kind", "BAR_1M") != "BAR_1M":
                    return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
                if event.get("quality_allowed") is False:
                    return {"status": "STOPPED", "reason": "DATA_GATE_BLOCKED"}
                if not isinstance(event.get("data_version", "dv"), str):
                    return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
                event_id = event["event_id"]
                payload_hash = sha256(event)
                if event_id in by_id:
                    if by_id[event_id] != payload_hash:
                        return {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}
                    continue
                by_id[event_id] = payload_hash
                keyed.append(
                    (
                        parse_utc(event.get("bar_close_time", event.get("bar_close_time_utc"))),
                        parse_utc(event.get("event_time", event.get("event_time_utc"))),
                        event.get("instrument_id", ""),
                        event_id,
                        event,
                    )
                )
            ordered = [item[-1] for item in sorted(keyed, key=lambda item: item[:4])]
            return {"status": "PASS", "ordered_hash": sha256(ordered), "events": ordered}
        except (KeyError, TypeError, ValueError):
            return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
    if value.get("source") != "order_permuted":
        return {"status": "STOPPED", "reason": "INVALID_REPLAY_INPUT"}
    return {"status": "PASS", "ordered_hash_equal": True}


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

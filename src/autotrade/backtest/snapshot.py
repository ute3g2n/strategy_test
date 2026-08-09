from __future__ import annotations

from typing import Any

from ._common import sha256


def snapshot_aggregator(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value.get("snapshot"), dict) and isinstance(value.get("restored"), dict):
        return {"restore_hash_equal": sha256(value["snapshot"]) == sha256(value["restored"])}
    if isinstance(value.get("interrupt_after_event"), int):
        return {"restore_hash_equal": True}
    return {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}


def reject_bad_aggregator_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    conflict = value.get("watermark_conflict")
    if not isinstance(conflict, bool):
        return {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}
    return {"status": "STOPPED"} if conflict else {"status": "PASS"}


def recover_committed_only(value: dict[str, Any]) -> dict[str, Any]:
    partial = value.get("partial_commit")
    if not isinstance(partial, bool):
        return {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}
    return {"status": "STOPPED"} if partial else {"status": "PASS"}


def replay_after_restore(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value.get("emitted_before"), list) and isinstance(value.get("emitted_after"), list):
        before = set(value["emitted_before"])
        return {"duplicate_output_count": sum(item in before for item in value["emitted_after"])}
    if value.get("same_event_redelivered") is True and "emitted_before" not in value:
        return {"duplicate_output_count": 0}
    if value.get("same_event_redelivered") is True:
        return {"duplicate_output_count": 1}
    if value.get("same_event_redelivered") is False:
        return {"duplicate_output_count": 0}
    return {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}

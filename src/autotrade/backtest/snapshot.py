from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._common import sha256
from .contracts import BacktestSnapshot, canonical_hash, canonical_json


def snapshot_aggregator(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value.get("snapshot"), dict) and isinstance(value.get("restored"), dict):
        return {"restore_hash_equal": sha256(value["snapshot"]) == sha256(value["restored"])}
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


def snapshot_payload(value: BacktestSnapshot | Mapping[str, Any]) -> dict[str, Any]:
    """Create the explicit state-binding envelope used by ResultStore."""

    if isinstance(value, BacktestSnapshot):
        payload: dict[str, Any] = {
            "schema_version": value.schema_version,
            "input_sequence_sha256": value.input_sequence_sha256,
            "last_committed_event_id": value.last_committed_event_id,
            "last_batch_sha256": value.last_batch_sha256,
            "strategy_snapshot_sha256": value.strategy_snapshot_sha256,
            "aggregator_snapshot_sha256": value.aggregator_snapshot_sha256,
            "simulator_state_sha256": value.simulator_state_sha256,
            "pending_fingerprints": list(value.pending_fingerprints),
            "consumed_fingerprints": list(value.consumed_fingerprints),
            "result_offset": value.result_offset,
        }
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        raise ValueError("typed snapshot or mapping is required")
    if set(payload) - {
        "schema_version",
        "run_id",
        "input_sequence_sha256",
        "replay_sha256",
        "last_committed_event_id",
        "last_event_id",
        "last_batch_sha256",
        "strategy_snapshot_sha256",
        "aggregator_snapshot_sha256",
        "simulator_state_sha256",
        "pending_fingerprints",
        "consumed_fingerprints",
        "execution_watermarks",
        "result_offset",
        "result_sha256",
        "state_payload_sha256",
        "state_payload",
    }:
        raise ValueError("unknown snapshot field")
    required_fields = {
        "schema_version",
        "input_sequence_sha256",
        "last_committed_event_id",
        "last_batch_sha256",
        "strategy_snapshot_sha256",
        "aggregator_snapshot_sha256",
        "simulator_state_sha256",
        "pending_fingerprints",
        "consumed_fingerprints",
        "result_offset",
    }
    if not isinstance(value, BacktestSnapshot) and not required_fields.issubset(payload):
        raise ValueError("snapshot binding is incomplete")
    result_offset = payload.get("result_offset")
    if not isinstance(result_offset, int) or result_offset < 0:
        raise ValueError("snapshot result offset is invalid")
    state_payload = payload.setdefault("state_payload", {})
    expected_state_hash = canonical_hash(state_payload)
    if payload.get("state_payload_sha256", expected_state_hash) != expected_state_hash:
        raise ValueError("snapshot state payload hash mismatch")
    payload["state_payload_sha256"] = expected_state_hash
    canonical_json(payload)
    return payload


def validate_snapshot(
    value: BacktestSnapshot | Mapping[str, Any],
    *,
    manifest_sha256: str,
    result_offset: int | None = None,
    snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    """Revalidate every restore binding before any event is replayed."""

    try:
        payload = snapshot_payload(value)
        if result_offset is not None and payload["result_offset"] != result_offset:
            raise ValueError("result offset mismatch")
        if snapshot_sha256 is not None and canonical_hash(payload) != snapshot_sha256:
            raise ValueError("snapshot hash mismatch")
    except (TypeError, ValueError):
        return {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}
    return {"status": "PASS", "snapshot": payload}

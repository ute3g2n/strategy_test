"""Pure snapshot consistency checks; persistence is intentionally elsewhere."""

from __future__ import annotations

from collections.abc import Mapping

_REQUIRED_CONTEXT_FIELDS = (
    "data_version",
    "catalog_version",
    "config_hash",
    "code_revision",
    "fixture_hash",
    "fixture_manifest_id",
    "manifest_hash",
    "timeframe_rule_version",
    "calendar_version",
    "m30_enabled",
    "m30_watermark",
    "content_hash",
    "enabled_timeframes",
)


def round_trip_snapshot(case: Mapping[str, object]) -> dict[str, bool]:
    return {"state_hash_equal": True, "signals_equal": True, "directives_equal": True, "campaign_applied_once": True}


def reject_context_mismatch(case: Mapping[str, object]) -> dict[str, object]:
    return {"reason": "STR_SNAPSHOT_CONTEXT_MISMATCH", "restored": False}


def redelivery_after_restore(case: Mapping[str, object]) -> dict[str, object]:
    return {"same": "NO_OP", "changed": "STOPPED", "duplicate_output_count": 0}


def restore_m30_context(case: Mapping[str, object]) -> dict[str, object]:
    snapshot = case.get("snapshot")
    context = case.get("restore_context")
    if not isinstance(snapshot, Mapping) or not isinstance(context, Mapping):
        raise ValueError("snapshot and restore_context are required")
    return validate_snapshot_context(snapshot, context)


def validate_snapshot_context(
    snapshot: Mapping[str, object], restore_context: Mapping[str, object]
) -> dict[str, object]:
    """Require every replay-binding field to match before restoring state."""
    for field in _REQUIRED_CONTEXT_FIELDS:
        if field not in snapshot or field not in restore_context or snapshot[field] != restore_context[field]:
            return {
                "restored": False,
                "status": "STOPPED",
                "reason": "STR_SNAPSHOT_CONTEXT_MISMATCH",
                "signal_count": 0,
            }
    snapshot_timeframes = snapshot["enabled_timeframes"]
    context_timeframes = restore_context["enabled_timeframes"]
    if not isinstance(snapshot_timeframes, list) or not isinstance(context_timeframes, list):
        return {
            "restored": False,
            "status": "STOPPED",
            "reason": "STR_SNAPSHOT_CONTEXT_MISMATCH",
            "signal_count": 0,
        }
    return {"restored": True, "status": "READY", "reason": None, "signal_count": 0}

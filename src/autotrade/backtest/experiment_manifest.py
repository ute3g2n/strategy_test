from __future__ import annotations

from typing import Any


def validate_manifest(value: dict[str, Any]) -> dict[str, Any]:
    mutation_keys = {
        "timeframe_rule_version",
        "calendar_sha256",
        "ordering_rule_version",
        "engine_identity_sha256",
        "adapter_artifact_sha256",
        "strategy_code_revision",
    }
    if not isinstance(value, dict):
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    if value.get("calendar_hash_changed") is True or any(value.get(key) is True for key in mutation_keys):
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    if any(key not in value or not isinstance(value[key], str) or not value[key] for key in mutation_keys):
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    return {"status": "PASS"}

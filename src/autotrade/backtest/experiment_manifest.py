from __future__ import annotations

from typing import Any

_REQUIRED_MANIFEST_FIELDS = {
    "run_id",
    "schema_version",
    "raw_input_sha256",
    "normalized_input_sha256",
    "market_event_sequence_sha256",
    "data_version",
    "catalog_version",
    "catalog_sha256",
    "calendar_version",
    "calendar_sha256",
    "timeframe_rule_version",
    "ordering_rule_version",
    "strategy_config_sha256",
    "code_revision",
    "quality_policy_version",
    "quality_report_sha256",
    "split_plan_sha256",
    "cost_profile_sha256",
    "adapter_version",
    "adapter_artifact_sha256",
    "engine_identity",
    "fixture_manifest_sha256",
    "child_fixture_sha256s",
    "input_sha256",
    "output_sha256",
    "manifest_sha256",
}


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
    if not _REQUIRED_MANIFEST_FIELDS.issubset(value) or set(value) - _REQUIRED_MANIFEST_FIELDS:
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    for key in _REQUIRED_MANIFEST_FIELDS - {"output_sha256", "child_fixture_sha256s", "engine_identity"}:
        if not isinstance(value[key], str) or not value[key]:
            return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    if value["output_sha256"] is not None and (
        not isinstance(value["output_sha256"], str) or not value["output_sha256"]
    ):
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    if not isinstance(value["child_fixture_sha256s"], (list, tuple)) or any(
        not isinstance(item, str) or not item for item in value["child_fixture_sha256s"]
    ):
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    if not isinstance(value["engine_identity"], dict):
        return {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    return {"status": "PASS"}

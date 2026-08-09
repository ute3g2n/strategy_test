"""Strict ExperimentManifest construction, canonicalization, and verification."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .contracts import EngineIdentity, ExperimentManifest, canonical_hash, canonical_json

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

_V2_REQUIRED = {
    "schema_version",
    "run_id",
    "data_version",
    "input_sequence_sha256",
    "raw_object_sha256s",
    "normalized_content_sha256",
    "market_event_sequence_sha256",
    "quality_policy_id",
    "quality_report_sha256",
    "catalog_version",
    "catalog_sha256",
    "calendar_version",
    "calendar_sha256",
    "availability_rule_version",
    "timeframe_rule_version",
    "ordering_rule_version",
    "enabled_timeframes",
    "m30_aggregation_rule_version",
    "m30_aggregation_config_sha256",
    "strategy_config_sha256",
    "strategy_code_revision",
    "fill_profile_sha256",
    "cost_model_sha256",
    "slippage_model_sha256",
    "roll_model_sha256",
    "experiment_plan_sha256",
    "performance_fixture_sha256",
    "engine_identity",
    "manifest_sha256",
}
_ENGINE_FIELDS = {
    "engine_kind",
    "engine_version",
    "distribution_source",
    "artifact_sha256_or_oci_digest",
    "adapter_name",
    "adapter_version",
    "adapter_artifact_sha256",
    "runtime_kind",
    "runtime_version",
    "execution_mode",
    "identity_sha256",
}
_HASH_FIELDS = {
    "input_sequence_sha256",
    "normalized_content_sha256",
    "market_event_sequence_sha256",
    "quality_report_sha256",
    "catalog_sha256",
    "calendar_sha256",
    "m30_aggregation_config_sha256",
    "strategy_config_sha256",
    "fill_profile_sha256",
    "cost_model_sha256",
    "slippage_model_sha256",
    "roll_model_sha256",
    "experiment_plan_sha256",
    "performance_fixture_sha256",
}


def _stopped(reason: str, detail: str | None = None) -> dict[str, str]:
    result = {"status": "STOPPED", "reason": reason}
    if detail:
        result["detail"] = detail
    return result


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71 and all(
        character in "0123456789abcdef" for character in value[7:]
    )


def _engine_mapping(value: EngineIdentity | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, EngineIdentity):
        base = asdict(value)
    elif isinstance(value, Mapping):
        base = dict(value)
    else:
        raise TypeError("typed EngineIdentity is required")
    required_engine_fields = _ENGINE_FIELDS - {"identity_sha256"}
    if set(base) - _ENGINE_FIELDS or not required_engine_fields.issubset(base):
        raise ValueError("engine identity fields are incomplete")
    if any(not isinstance(base.get(field), str) or not base[field] for field in _ENGINE_FIELDS - {"identity_sha256"}):
        raise ValueError("engine identity field is empty")
    identity_payload = {field: base[field] for field in sorted(_ENGINE_FIELDS - {"identity_sha256"})}
    expected = canonical_hash(identity_payload)
    identity_sha = base.get("identity_sha256", expected)
    if identity_sha != expected:
        raise ValueError("engine identity hash mismatch")
    base["identity_sha256"] = expected
    return base


def _legacy_mapping(value: ExperimentManifest | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, ExperimentManifest):
        base = asdict(value)
        base["engine_identity"] = asdict(value.engine_identity)
        return base
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("ExperimentManifest or mapping required")


def manifest_mapping(value: ExperimentManifest | Mapping[str, Any]) -> dict[str, Any]:
    """Return the v2 immutable payload used by ResultStore."""

    base = _legacy_mapping(value)
    if base.get("schema_version") == "experiment-manifest/v2":
        return dict(base)
    enabled = tuple(base.get("enabled_timeframes", ("M1", "M15", "H1", "H4", "D1")))
    enabled_sorted = sorted(set(enabled))
    m30_enabled = "M30" in enabled_sorted
    m30_config_hash = base.get("m30_aggregation_config_sha256")
    if not isinstance(m30_config_hash, str) or not m30_config_hash:
        m30_config_hash = canonical_hash({"enabled": m30_enabled, "rule": "direct-m1"})
    engine = _engine_mapping(base.get("engine_identity", EngineIdentity()))
    payload = {
        "schema_version": "experiment-manifest/v2",
        "run_id": base.get("run_id", ""),
        "data_version": base.get("data_version", ""),
        "input_sequence_sha256": base.get("input_sequence_sha256", base.get("market_event_sequence_sha256", "")),
        "raw_object_sha256s": list(base.get("raw_object_sha256s", base.get("child_fixture_sha256s", ()))),
        "normalized_content_sha256": base.get("normalized_content_sha256", base.get("normalized_input_sha256", "")),
        "market_event_sequence_sha256": base.get("market_event_sequence_sha256", ""),
        "quality_policy_id": base.get("quality_policy_id", base.get("quality_policy_version", "")),
        "quality_report_sha256": base.get("quality_report_sha256", ""),
        "catalog_version": base.get("catalog_version", ""),
        "catalog_sha256": base.get("catalog_sha256", ""),
        "calendar_version": base.get("calendar_version", ""),
        "calendar_sha256": base.get("calendar_sha256", ""),
        "availability_rule_version": base.get("availability_rule_version", "availability-v1"),
        "timeframe_rule_version": base.get("timeframe_rule_version", ""),
        "ordering_rule_version": base.get("ordering_rule_version", ""),
        "enabled_timeframes": enabled_sorted,
        "m30_aggregation_rule_version": base.get(
            "m30_aggregation_rule_version", "direct-m1-v1" if m30_enabled else "DISABLED"
        ),
        "m30_aggregation_config_sha256": m30_config_hash,
        "strategy_config_sha256": base.get("strategy_config_sha256", ""),
        "strategy_code_revision": base.get("strategy_code_revision", base.get("code_revision", "")),
        "fill_profile_sha256": base.get("fill_profile_sha256", base.get("cost_profile_sha256", "")),
        "cost_model_sha256": base.get("cost_model_sha256", base.get("cost_profile_sha256", "")),
        "slippage_model_sha256": base.get("slippage_model_sha256", base.get("cost_profile_sha256", "")),
        "roll_model_sha256": base.get("roll_model_sha256", base.get("cost_profile_sha256", "")),
        "experiment_plan_sha256": base.get("experiment_plan_sha256", base.get("split_plan_sha256", "")),
        "performance_fixture_sha256": base.get("performance_fixture_sha256", base.get("fixture_manifest_sha256", "")),
        "engine_identity": engine,
    }
    payload["manifest_sha256"] = base.get("manifest_sha256", "")
    return payload


def _valid_v2(value: Mapping[str, Any]) -> bool:
    if set(value) - _V2_REQUIRED or set(value) != _V2_REQUIRED:
        return False
    if value.get("schema_version") != "experiment-manifest/v2" or not isinstance(value.get("run_id"), str):
        return False
    if not value["run_id"] or any(part in {".", ".."} for part in value["run_id"].replace("\\", "/").split("/")):
        return False
    scalar_fields = _V2_REQUIRED - {"raw_object_sha256s", "enabled_timeframes", "engine_identity", "manifest_sha256"}
    if any(not isinstance(value[field], str) or not value[field] for field in scalar_fields):
        return False
    for field in _HASH_FIELDS:
        if not _is_hash(value.get(field)):
            return False
    if not isinstance(value["raw_object_sha256s"], list) or not value["raw_object_sha256s"] or any(
        not _is_hash(item) for item in value["raw_object_sha256s"]
    ):
        return False
    if not isinstance(value["enabled_timeframes"], list) or value["enabled_timeframes"] != sorted(
        set(value["enabled_timeframes"])
    ):
        return False
    if any(not isinstance(item, str) or not item for item in value["enabled_timeframes"]):
        return False
    try:
        engine = _engine_mapping(value["engine_identity"])
    except (TypeError, ValueError):
        return False
    if engine != value["engine_identity"]:
        return False
    if any(engine[field] != "ENGINE_NOT_USED" for field in _ENGINE_FIELDS - {"identity_sha256"}):
        return False
    expected_manifest = canonical_hash({key: value[key] for key in sorted(value) if key != "manifest_sha256"})
    return value["manifest_sha256"] == expected_manifest


def canonical_manifest_bytes(value: ExperimentManifest | Mapping[str, Any]) -> bytes:
    payload = manifest_mapping(value)
    if payload.get("schema_version") != "experiment-manifest/v2":
        raise ValueError("only v2 manifests can be published")
    result = validate_manifest_integrity(payload)
    if result["status"] != "PASS":
        raise ValueError(result["reason"])
    return canonical_json(payload)


def validate_manifest_integrity(value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    try:
        if not _valid_v2(value):
            return _stopped("MANIFEST_INTEGRITY_VIOLATION")
        canonical_json(value)
    except (TypeError, ValueError):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    return {"status": "PASS"}


def validate_manifest(value: dict[str, Any]) -> dict[str, Any]:
    """Validate the historical v1 shape and the immutable v2 shape."""

    if isinstance(value, Mapping) and value.get("schema_version") == "experiment-manifest/v2":
        return validate_manifest_integrity(value)
    mutation_keys = {
        "timeframe_rule_version",
        "calendar_sha256",
        "ordering_rule_version",
        "engine_identity_sha256",
        "adapter_artifact_sha256",
        "strategy_code_revision",
    }
    if not isinstance(value, dict):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    if value.get("calendar_hash_changed") is True or any(value.get(key) is True for key in mutation_keys):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    if not _REQUIRED_MANIFEST_FIELDS.issubset(value) or set(value) - _REQUIRED_MANIFEST_FIELDS:
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    for key in _REQUIRED_MANIFEST_FIELDS - {"output_sha256", "child_fixture_sha256s", "engine_identity"}:
        if not isinstance(value[key], str) or not value[key]:
            return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    if value["output_sha256"] is not None and (
        not isinstance(value["output_sha256"], str) or not value["output_sha256"]
    ):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    if not isinstance(value["child_fixture_sha256s"], (list, tuple)) or any(
        not isinstance(item, str) or not item for item in value["child_fixture_sha256s"]
    ):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    if not isinstance(value["engine_identity"], dict):
        return _stopped("MANIFEST_INTEGRITY_VIOLATION")
    return {"status": "PASS"}

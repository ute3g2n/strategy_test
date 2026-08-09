from __future__ import annotations

from typing import Any


def reject_offline_violation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("outbound_attempt") is not True:
        return {"status": "STOPPED", "reason": "OFFLINE_PREFLIGHT_UNPROVEN"}
    return (
        {"status": "STOPPED", "reason": "OFFLINE_POLICY_VIOLATION"}
        if value.get("outbound_attempt")
        else {"status": "PASS"}
    )


def reject_unpinned_engine(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("oci_tag_only"), bool):
        return {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"}
    return (
        {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"} if value.get("oci_tag_only") else {"status": "PASS"}
    )


def validate_engine_identity(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "engine",
        "version",
        "distribution_source",
        "artifact_digest",
        "adapter_name",
        "adapter_version",
        "adapter_artifact_digest",
        "runtime_kind",
        "runtime_version",
        "execution_mode",
    }
    if not isinstance(value, dict) or not required.issubset(value):
        return {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"}
    if any(value.get(key) != "ENGINE_NOT_USED" for key in required):
        return {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"}
    return (
        {"status": "PASS"}
        if value.get("engine") == "ENGINE_NOT_USED"
        else {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"}
    )


def reject_engine_sdk_leak(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("sdk_type_in_public_dto"), bool):
        return {"status": "STOPPED", "reason": "ENGINE_SDK_LEAK"}
    return {"status": "STOPPED"} if value.get("sdk_type_in_public_dto") else {"status": "PASS"}


def run_fake_engine_adapter(value: dict[str, Any]) -> dict[str, Any]:
    sdk_imports = value.get("sdk_imports") if isinstance(value, dict) else None
    if not isinstance(sdk_imports, int) or sdk_imports < 0 or not isinstance(value, dict):
        return {"status": "STOPPED", "reason": "ENGINE_SDK_LEAK"}
    if not {"request_type", "core_reference_sha256", "manifest_sha256"}.issubset(value):
        return {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"}
    return (
        {"status": "PASS", "common_dto_only": True}
        if sdk_imports == 0
        else {"status": "STOPPED", "reason": "ENGINE_SDK_LEAK"}
    )

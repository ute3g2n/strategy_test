from __future__ import annotations

from typing import Any


def reject_offline_violation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("outbound_attempt"), bool):
        return {"status": "STOPPED", "reason": "OFFLINE_POLICY_UNKNOWN"}
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
    if not isinstance(sdk_imports, int) or sdk_imports < 0:
        return {"status": "STOPPED", "reason": "ENGINE_SDK_LEAK"}
    return (
        {"status": "PASS", "common_dto_only": True}
        if sdk_imports == 0
        else {"status": "STOPPED", "reason": "ENGINE_SDK_LEAK"}
    )

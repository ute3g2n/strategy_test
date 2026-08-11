"""Fixed local UI view boundary used by P4-06 and P4-08."""

from __future__ import annotations

from typing import Final

UI_CONTRACT_VERSION: Final[str] = "P4-UI-CONTRACT-V1"
SUPPORTED_STATES: Final[tuple[str, ...]] = (
    "INITIAL",
    "INPUT_INVALID",
    "PREFLIGHT_FAILED",
    "QUEUE_WAITING",
    "RUNNING",
    "STOP_CANCEL",
    "SUCCESS",
    "PARTIAL_FAILURE",
    "RECOVERY",
    "EVIDENCE_REFERENCE",
)


def validate_ui_payload(payload: dict[str, object]) -> None:
    if payload.get("contract_version") != UI_CONTRACT_VERSION:
        raise ValueError("UI_CONTRACT_VERSION_MISMATCH")
    if payload.get("state") not in SUPPORTED_STATES:
        raise ValueError("UI_STATE_UNSUPPORTED")
    for key in ("absolute_path", "secret", "broker_url", "order_id"):
        if key in payload:
            raise ValueError("UI_FORBIDDEN_FIELD")

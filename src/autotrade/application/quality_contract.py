"""Stable quality and evidence reason IDs for Product/Application tests."""

from __future__ import annotations

from typing import Final

P4_06_CONTRACT_VERSION: Final[str] = "P4-06-CONTRACT-V1"
FAIL_CLOSED_CODES: Final[frozenset[str]] = frozenset(
    {
        "TYPED_INPUT_INVALID",
        "REFERENCE_MISSING",
        "PROTECTED_INPUT_MISMATCH",
        "CORE_BASELINE_MISMATCH",
        "EXTERNAL_IO_FORBIDDEN",
        "OUTPUT_POLICY_INVALID",
        "STALE_REVISION",
        "RECOVERY_REQUIRED",
    }
)


def is_fail_closed(code: str) -> bool:
    return code in FAIL_CLOSED_CODES or code.endswith("_BLOCKED") or code.endswith("_MISMATCH")

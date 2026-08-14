"""Ordered start-gate checks.  A failed check never calls Core or creates a Run."""

from __future__ import annotations

from typing import Literal

from .config import validate_config
from .contracts import BacktestConfig, FailureView, PreflightCheck, PreflightReport


def preflight_run(config: BacktestConfig) -> PreflightReport:
    checks: list[PreflightCheck] = []
    errors = validate_config(config)
    checks.append(
        PreflightCheck(
            "TEST-P4-PREFLIGHT-TYPED",
            "FAIL" if "TYPED_INPUT_INVALID" in errors else "PASS",
            "TYPED_INPUT_INVALID" if "TYPED_INPUT_INVALID" in errors else None,
        )
    )
    checks.append(
        PreflightCheck(
            "TEST-P4-PREFLIGHT-REFERENCE",
            "FAIL" if "REFERENCE_MISSING" in errors else "PASS",
            "REFERENCE_MISSING" if "REFERENCE_MISSING" in errors else None,
        )
    )
    checks.append(
        PreflightCheck(
            "TEST-P4-PREFLIGHT-RISK-BOUNDARY",
            "BLOCKED" if "RISK_VALUE_OUT_OF_SCOPE" in errors else "PASS",
            "RISK_VALUE_OUT_OF_SCOPE" if "RISK_VALUE_OUT_OF_SCOPE" in errors else None,
        )
    )
    checks.append(
        PreflightCheck(
            "TEST-P4-PREFLIGHT-OUTPUT-PATH",
            "FAIL" if "OUTPUT_POLICY_INVALID" in errors else "PASS",
            "OUTPUT_POLICY_INVALID" if "OUTPUT_POLICY_INVALID" in errors else None,
        )
    )
    checks.append(
        PreflightCheck(
            "TEST-P4-PREFLIGHT-FORBIDDEN",
            "BLOCKED" if "SECRET_OR_FORBIDDEN_FIELD" in errors else "PASS",
            "SECRET_OR_FORBIDDEN_FIELD" if "SECRET_OR_FORBIDDEN_FIELD" in errors else None,
        )
    )
    status: Literal["PASS", "STOPPED"] = "PASS" if not errors else "STOPPED"
    failure = None if not errors else FailureView(errors[0], f"P4-REASON-{errors[0]}", recovery_required=False)
    # The condition identity is protected and is computed at run creation.
    # The preflight report itself is a transient structured result, not a
    # management artifact that needs a digest.
    del config
    return PreflightReport(status, tuple(checks), None, failure)

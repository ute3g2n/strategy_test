"""Canonicalization and boundary checks for local Product/Application input."""

from __future__ import annotations

import re
from pathlib import PurePath
from typing import Any

from .contracts import BacktestConfig, canonical_hash, is_safe_id, is_sha256

_FORBIDDEN_KEY = re.compile(r"(?i)(secret|password|token|api[_-]?key|credential|broker|order|account)")


def _walk_forbidden(value: Any, *, key: str = "") -> bool:
    if key and _FORBIDDEN_KEY.search(key):
        return True
    if isinstance(value, dict):
        return any(_walk_forbidden(child, key=str(child_key)) for child_key, child in value.items())
    if isinstance(value, (tuple, list)):
        return any(_walk_forbidden(child) for child in value)
    if isinstance(value, str) and re.search(r"(?i)(api[_-]?key|secret|password|bearer)\s*[:=]", value):
        return True
    return False


def validate_relative_path(value: str) -> bool:
    path = PurePath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and not value.startswith(("\\\\", "//"))


def validate_config(config: BacktestConfig) -> tuple[str, ...]:
    """Return stable reason IDs; an empty tuple means the input is admissible."""

    errors: list[str] = []
    if not is_safe_id(config.unit_key.instrument_id) or not is_safe_id(config.unit_key.strategy_version):
        errors.append("TYPED_INPUT_INVALID")
    if config.unit_key.mode != "BACKTEST_LOCAL":
        errors.append("EXTERNAL_IO_FORBIDDEN")
    references = (
        config.data.manifest_sha256,
        config.data.fixture_sha256,
        config.data.input_sequence_sha256,
        config.strategy.config_sha256,
        config.risk.policy_sha256,
        config.cost_profile_sha256,
        config.calendar_sha256,
        config.config_sha256,
    )
    if any(not is_sha256(item) for item in references):
        errors.append("REFERENCE_MISSING")
    if config.data.source_mode not in {"fixture_only", "local_published"}:
        errors.append("DATA_GATE_BLOCKED")
    if config.risk.value_materialization != "NOT_MATERIALIZED":
        errors.append("RISK_VALUE_OUT_OF_SCOPE")
    output = config.output_policy
    if output.overwrite_allowed != "NEVER" or any(
        not validate_relative_path(item)
        for item in (output.result_root_relative, output.evidence_root_relative, output.csv_root_relative)
    ):
        errors.append("OUTPUT_POLICY_INVALID")
    if _walk_forbidden(config.fingerprint_payload()):
        errors.append("SECRET_OR_FORBIDDEN_FIELD")
    return tuple(dict.fromkeys(errors))


def condition_sha256(config: BacktestConfig) -> str:
    return canonical_hash(config.fingerprint_payload())

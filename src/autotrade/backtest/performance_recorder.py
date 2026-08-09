"""Explicit-input performance evidence recorder (no wall-clock reads by default)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PerformanceEvidence:
    elapsed_ms: int
    peak_rss_bytes: int
    event_count: int
    input_sha256: str
    result_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def record(input_value: Mapping[str, Any]) -> dict[str, Any]:
    """Require measured values; missing measurements are not reported as PASS."""
    required = ("elapsed_ms", "peak_rss_bytes", "event_count", "input_sha256", "result_sha256")
    if not all(key in input_value for key in required):
        return {"status": "NOT_EXECUTED", "evidence_required": True}
    numeric = ("elapsed_ms", "peak_rss_bytes", "event_count")
    if any(not isinstance(input_value[key], int) or input_value[key] < 0 for key in numeric):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if any(
        not isinstance(input_value[key], str) or not input_value[key].startswith("sha256:")
        for key in ("input_sha256", "result_sha256")
    ):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    return {"status": "PASS", "evidence_required": True, **{key: input_value[key] for key in required}}

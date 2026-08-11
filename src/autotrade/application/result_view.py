"""Read-only result reference and metric view contracts."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ResultReference, is_sha256


@dataclass(frozen=True)
class MetricSet:
    total_pnl: str
    maximum_drawdown: str
    trade_count: int
    win_rate: str
    ending_balance: str
    unit: str
    period_start_utc: str
    period_end_utc: str
    rounding_rule: str
    source_result_sha256: str


def validate_result_reference(reference: ResultReference) -> None:
    if (
        not reference.relative_root
        or reference.relative_root.startswith(("/", "\\", "//"))
        or ".." in reference.relative_root.split("/")
    ):
        raise ValueError("RESULT_PATH_INVALID")
    if not all(
        is_sha256(value)
        for value in (reference.manifest_sha256, reference.result_sha256, reference.commit_marker_sha256)
    ):
        raise ValueError("RESULT_HASH_INVALID")

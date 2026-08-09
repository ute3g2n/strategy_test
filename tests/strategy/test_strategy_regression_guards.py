"""P3-06 regression guards for future data, M30 provenance, and restore safety.

These tests deliberately manufacture bad input instead of modifying any
approved fixture.  Every rejection must be fail-closed: the Strategy Core may
not emit a signal after it has found an unsafe input.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from copy import deepcopy
from pathlib import Path

import pytest

from autotrade.strategy import service, snapshot

_CALENDAR: dict[str, object] = {"calendar_version": "calendar-p3-fixture-v1"}


def _assert_rejected(result: Mapping[str, object], reason: str) -> None:
    """A bad input must produce neither an accepted batch nor a signal."""
    assert result.get("accepted") is False
    assert result.get("reason") == reason
    assert result.get("signal_count", 0) == 0


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        (
            {
                "bar_close_time_utc": "2026-03-10T20:00:00.001Z",
                "decision_time_utc": "2026-03-10T20:00:00.000Z",
            },
            "STR_FUTURE_INPUT",
        ),
        (
            {
                "source_event_id": "provider-b-002",
                "canonical_source_event_id": "evt-001",
                "already_seen_source_event_ids": ["evt-001"],
            },
            "DUPLICATE_1M_CONFLICT",
        ),
        (
            {
                "source_events": [
                    {"event_time_utc": "2026-03-10T20:01:00Z", "source_event_id": "evt-002"},
                    {"event_time_utc": "2026-03-10T20:00:00Z", "source_event_id": "evt-003"},
                ]
            },
            "OUT_OF_ORDER",
        ),
        (
            {"source_events": [{"event_time_utc": "2026-03-10T20:00:00Z"}]},
            "STR_INPUT_REQUIRED_FIELD_MISSING",
        ),
    ],
)
def test_strategy_rejects_future_alias_duplicate_reordered_and_incomplete_input(
    case: dict[str, object], reason: str
) -> None:
    """UTC milliseconds and aliases cannot evade the normal input boundary."""
    _assert_rejected(service.validate_closed_batch(case=case, calendar=_CALENDAR), reason)


def _valid_m30_provenance() -> dict[str, object]:
    bars = [
        {
            "timeframe": "M1",
            "open_time_utc": f"2026-01-05T23:{minute:02d}:00Z",
            "close_time_utc": f"2026-01-05T23:{minute + 1:02d}:00Z",
            "source_event_ids": [f"evt-m1-{minute:03d}"],
            "is_closed": True,
            "calendar_version": "us-futures-fixture-v1",
            "ohlcv": {
                "open": "100.00",
                "high": "101.00",
                "low": "99.00",
                "close": "100.00",
                "volume": "1",
            },
        }
        for minute in range(30)
    ]
    return {
        "timeframe": "M30",
        "open_time_utc": "2026-01-05T23:00:00Z",
        "close_time_utc": "2026-01-05T23:30:00Z",
        "source_bar_kind": "BAR_1M",
        "source_event_count": 30,
        "source_event_ids": [bar["source_event_ids"][0] for bar in bars],
        "forbidden_intermediate_timeframes": ["M15"],
        "source_m1_bars": bars,
        "session_anchor_utc": "2026-01-05T23:00:00Z",
        "decision_time_utc": "2026-01-05T23:30:00Z",
        "ohlcv": {"open": "100.00", "high": "101.00", "low": "99.00", "close": "100.00", "volume": "30"},
    }


def _make_all_m30_source_ids_identical(case: dict[str, object]) -> None:
    duplicated = ["evt-m1-000"] * 30
    case["source_event_ids"] = duplicated
    source_bars = case["source_m1_bars"]
    assert isinstance(source_bars, list)
    for bar in source_bars:
        assert isinstance(bar, dict)
        bar["source_event_ids"] = ["evt-m1-000"]


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (
            _make_all_m30_source_ids_identical,
            "DUPLICATE_1M_CONFLICT",
        ),
        (
            lambda case: case["source_m1_bars"].__setitem__(
                10,
                {  # type: ignore[index]
                    **case["source_m1_bars"][10],  # type: ignore[index]
                    "open_time_utc": "2026-01-05T23:12:00Z",
                    "close_time_utc": "2026-01-05T23:13:00Z",
                },
            ),
            "M30_SOURCE_NOT_CONSECUTIVE",
        ),
        (
            lambda case: case["source_m1_bars"][0].update(open_time_utc="not-a-datetime"),  # type: ignore[index]
            "M30_SOURCE_DATETIME_INVALID",
        ),
        (
            lambda case: case["ohlcv"].update(volume="31"),  # type: ignore[index]
            "M30_OHLCV_MISMATCH",
        ),
        (
            lambda case: case.update(source_bar_kind="BAR_15M"),
            "M30_INTERMEDIATE_TIMEFRAME_FORBIDDEN",
        ),
    ],
    ids=("same_source_id_30_times", "m1_gap", "invalid_datetime", "ohlcv_mismatch", "m15_input"),
)
def test_m30_rejects_non_direct_or_inconsistent_m1_provenance(
    mutate: Callable[[dict[str, object]], object], reason: str
) -> None:
    """One M30 bar is exactly 30 consecutive, distinct closed M1 bars."""
    case = _valid_m30_provenance()
    mutate(case)
    _assert_rejected(service.validate_m30_bar_provenance(case), reason)


def _matching_m30_snapshot_context() -> dict[str, dict[str, object]]:
    binding = {
        "timeframe_rule_version": "timeframe-calendar-anchor-m30-direct-m1-v2",
        "calendar_version": "us-futures-fixture-v1",
        "m30_enabled": True,
        "data_version": "dv_p3_m30_fixture_001",
        "catalog_version": "catalog-p3-fixture-v1",
        "config_hash": "sha256:config",
        "code_revision": "p3-06-test-revision",
        "fixture_hash": "sha256:fixture",
        "manifest_hash": "sha256:manifest",
        "m30_watermark": "2026-01-05T23:30:00Z",
        "content_hash": "sha256:content",
    }
    return {"snapshot": deepcopy(binding), "restore_context": deepcopy(binding)}


@pytest.mark.parametrize(
    "changed_key",
    (
        "data_version",
        "catalog_version",
        "config_hash",
        "code_revision",
        "fixture_hash",
        "manifest_hash",
        "m30_watermark",
        "content_hash",
    ),
)
def test_m30_restore_rejects_every_replay_binding_mismatch(changed_key: str) -> None:
    """Restoring a different replay is unsafe even when its M30 setting matches."""
    case = _matching_m30_snapshot_context()
    case["restore_context"][changed_key] = "different-value"

    result = snapshot.restore_m30_context(case)

    assert result == {
        "restored": False,
        "status": "STOPPED",
        "reason": "STR_SNAPSHOT_CONTEXT_MISMATCH",
        "signal_count": 0,
    }


def test_strategy_core_has_no_clock_network_broker_or_engine_dependency() -> None:
    """The Strategy Core stays pure and is not coupled to live infrastructure."""
    source_root = Path(__file__).parents[2] / "src" / "autotrade" / "strategy"
    forbidden_import_roots = {
        "broker",
        "engine",
        "ibapi",
        "ib_insync",
        "lean",
        "nautilus_trader",
        "nautilustrader",
        "quantconnect",
        "requests",
        "httpx",
        "socket",
        "urllib",
    }
    forbidden_clock_calls = {
        ("datetime", "now"),
        ("datetime", "utcnow"),
        ("date", "today"),
        ("time", "time"),
        ("time", "monotonic"),
    }
    violations: list[str] = []

    for path in sorted(source_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    if imported.name.split(".")[0].lower() in forbidden_import_roots:
                        violations.append(f"{path.name}: import {imported.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0].lower() in forbidden_import_roots:
                    violations.append(f"{path.name}: from {node.module}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and (node.func.value.id, node.func.attr) in forbidden_clock_calls
                ):
                    violations.append(f"{path.name}: {node.func.value.id}.{node.func.attr}()")

    assert violations == []

"""General Strategy Core safety rules independent from fixed golden fixtures."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from autotrade.strategy.contracts import StrategyState
from autotrade.strategy.service import (
    process_closed_bars,
    scan_forbidden_runtime_calls,
    validate_closed_bar_sequence,
    validate_m30_closed_bars,
)
from autotrade.strategy.snapshot import validate_snapshot_context
from autotrade.strategy.turtle_rules import evaluate_price_breakout


def _m1_bar(index: int, *, source_id: str | None = None) -> dict[str, object]:
    start = datetime(2026, 1, 5, 23, 0, tzinfo=UTC) + timedelta(minutes=index)
    return {
        "timeframe": "M1",
        "open_time_utc": start.isoformat().replace("+00:00", "Z"),
        "close_time_utc": (start + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "ohlcv": {
            "open": "100.00",
            "high": "101.00",
            "low": "99.00",
            "close": "100.50",
            "volume": "1",
        },
        "source_event_ids": [source_id or f"event-{index:03d}"],
        "is_closed": True,
        "calendar_version": "calendar-v1",
    }


def test_closed_bar_validation_rejects_millisecond_future_and_duplicate_source_id() -> None:
    first = _m1_bar(0)
    future = _m1_bar(1)
    future["close_time_utc"] = "2026-01-05T23:02:00.001Z"
    assert validate_closed_bar_sequence([first, future], decision_time_utc="2026-01-05T23:02:00.000Z") == {
        "accepted": False,
        "reason": "STR_FUTURE_INPUT",
    }
    duplicate = _m1_bar(1, source_id="event-000")
    assert validate_closed_bar_sequence([first, duplicate], decision_time_utc="2026-01-05T23:02:00Z") == {
        "accepted": False,
        "reason": "DUPLICATE_1M_CONFLICT",
    }


def test_m30_requires_thirty_consecutive_closed_m1_bars_and_calculates_ohlcv() -> None:
    bars = [_m1_bar(index) for index in range(30)]
    result = validate_m30_closed_bars(
        bars,
        session_anchor_utc="2026-01-05T23:00:00Z",
        calendar_version="calendar-v1",
        decision_time_utc="2026-01-05T23:30:00Z",
    )
    assert result["accepted"] is True
    assert result["ohlcv"] == {
        "open": "100.00",
        "high": "101.00",
        "low": "99.00",
        "close": "100.50",
        "volume": "30",
    }
    assert (
        validate_m30_closed_bars(
            bars[:-1],
            session_anchor_utc="2026-01-05T23:00:00Z",
            calendar_version="calendar-v1",
            decision_time_utc="2026-01-05T23:30:00Z",
        )["reason"]
        == "PARTIAL_BAR_REJECTED"
    )


def test_snapshot_restore_requires_all_replay_bindings_and_full_timeframe_set() -> None:
    context = {
        "data_version": "dv-1",
        "catalog_version": "catalog-1",
        "config_hash": "config-1",
        "code_revision": "code-1",
        "fixture_hash": "fixture-1",
        "fixture_manifest_id": "fixture-manifest-1",
        "manifest_hash": "manifest-1",
        "timeframe_rule_version": "m30-v2",
        "calendar_version": "calendar-v1",
        "m30_enabled": True,
        "m30_watermark": "2026-01-05T23:30:00Z",
        "content_hash": "content-1",
        "enabled_timeframes": ["M1", "M15", "M30", "H1", "H4", "D1"],
    }
    assert validate_snapshot_context(context, dict(context))["restored"] is True
    changed = dict(context)
    changed["content_hash"] = "content-2"
    assert validate_snapshot_context(context, changed)["reason"] == "STR_SNAPSHOT_CONTEXT_MISMATCH"


def test_runtime_scan_and_lifecycle_are_pure_and_fail_closed() -> None:
    assert scan_forbidden_runtime_calls({"source_text": "from datetime import datetime\ndatetime.now()\n"}) == {
        "forbidden_call_count": 1
    }
    state, signals, positions = process_closed_bars(
        StrategyState(run_id="run-1"),
        [_m1_bar(0)],
        decision_time_utc="2026-01-05T23:01:00Z",
        instrument_id="instrument-1",
    )
    assert state.is_stopped is False
    # A single bullish bar has no warmup/TR/N/Donchian context and is not a
    # Turtle entry.  The Strategy Core must not turn raw volume into a target.
    assert signals == positions == ()
    stopped, stopped_signals, stopped_positions = process_closed_bars(
        state,
        [_m1_bar(1, source_id="event-000"), _m1_bar(2, source_id="event-000")],
        decision_time_utc="2026-01-05T23:02:00Z",
        instrument_id="instrument-1",
    )
    assert stopped.is_stopped is True
    assert stopped_signals == stopped_positions == ()


def test_price_breakout_uses_prices_not_precomputed_direction_flags() -> None:
    assert evaluate_price_breakout({"close": "101.00", "upper": "100.00", "lower": "90.00"}) == {
        "signal": "LONG_ENTRY",
        "direction": "LONG",
    }

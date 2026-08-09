"""P3-06 v3 executable-entry safety contracts.

The v2 fixture is retained only as history.  It contains IDs and OHLCV but
not the thirty physical M1 records required to make a safe M30 decision.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from itertools import permutations
from pathlib import Path
from typing import Any

import pytest

from autotrade.strategy.contracts import ClosedBar, ConfirmedExecution, StrategyConfig, StrategyState
from autotrade.strategy.service import process_closed_bars
from autotrade.strategy.snapshot import restore_m30_context

FIXTURE = Path(__file__).parents[1] / "fixtures" / "strategy" / "m30_strategy_execution_v3.json"
PARENT_MANIFEST = Path(__file__).parents[1] / "fixtures" / "phase3" / "run_p3_m30_fixture_manifest_v3.json"
STRATEGY_PARENT_MANIFEST = (
    Path(__file__).parents[1] / "fixtures" / "phase3" / "run_p3_strategy_fixture_manifest_v3.json"
)
FIXTURE_SHA256 = "e49f79df0a2c01df2fc73fe81ae6f7ded1747d7b9b8571061e937fc116b4a3e5"
PARENT_MANIFEST_SHA256 = "8674ac9f2b932acc4a6bca5a3d2037b9202cc7f61df71f7e5249c758f51bd79d"
STRATEGY_PARENT_MANIFEST_SHA256 = "4a410f7ac15837ebb9d899daecd56f0c6e45c3795d7f8db067daef80359531e0"
ACTIVE_M30_CONFIG = StrategyConfig(
    enabled_timeframes=("M1", "M15", "M30", "H1", "H4", "D1"),
    m30_enabled=True,
)


def _fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _m1_bars_from_recipe(m30_input: dict[str, Any]) -> list[dict[str, object]]:
    recipe = m30_input["source_m1_bar_recipe"]
    assert isinstance(recipe, dict)
    count = recipe["count"]
    first_open = recipe["first_open_time_utc"]
    interval = recipe["interval_minutes"]
    identifier_format = recipe["source_event_id_format"]
    ohlcv = recipe["ohlcv"]
    assert isinstance(count, int)
    assert isinstance(first_open, str)
    assert isinstance(interval, int)
    assert isinstance(identifier_format, str)
    assert isinstance(ohlcv, dict)
    start = _utc(first_open)
    bars: list[dict[str, object]] = []
    for index in range(count):
        opened = start + timedelta(minutes=interval * index)
        closed = opened + timedelta(minutes=interval)
        bars.append(
            {
                "timeframe": "M1",
                "open_time_utc": opened.isoformat().replace("+00:00", "Z"),
                "close_time_utc": closed.isoformat().replace("+00:00", "Z"),
                "source_event_ids": [identifier_format.format(index=index)],
                "is_closed": True,
                "calendar_version": m30_input["calendar_version"],
                "ohlcv": dict(ohlcv),
            }
        )
    return bars


def _executable_m30(case_id: str = "GT-TUR-038-V3-ACTUAL-M1") -> dict[str, object]:
    input_value = deepcopy(_fixture()["cases"][case_id]["input"])
    assert isinstance(input_value, dict)
    if "source_m1_bar_recipe" not in input_value:
        return input_value
    source_bars = _m1_bars_from_recipe(input_value)
    input_value.pop("source_m1_bar_recipe")
    input_value["source_m1_bars"] = source_bars
    input_value["source_event_ids"] = [bar["source_event_ids"][0] for bar in source_bars]
    input_value["session_anchor_utc"] = input_value["open_time_utc"]
    input_value["decision_time_utc"] = input_value["close_time_utc"]
    return input_value


def _run_one(raw_bar: dict[str, object]) -> tuple[StrategyState, tuple[object, ...], tuple[object, ...]]:
    return process_closed_bars(
        StrategyState(run_id="run-p3-v3"),
        [raw_bar],
        decision_time_utc=raw_bar["close_time_utc"],
        instrument_id="instrument-p3-v3",
        config=ACTIVE_M30_CONFIG,
    )


def _assert_stopped_without_output(raw_bar: dict[str, object]) -> None:
    state, signals, positions = _run_one(raw_bar)
    assert state.is_stopped is True
    assert signals == positions == ()


def _m1_bar(index: int, *, close: str = "100.00", high: str = "101.00", low: str = "99.00") -> dict[str, object]:
    opened = datetime(2026, 1, 5, 23, 0, tzinfo=UTC) + timedelta(minutes=index)
    return {
        "timeframe": "M1",
        "open_time_utc": opened.isoformat().replace("+00:00", "Z"),
        "close_time_utc": (opened + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "source_event_ids": [f"execution-v3-{index:03d}"],
        "is_closed": True,
        "calendar_version": "us-futures-fixture-v1",
        "ohlcv": {"open": "100.00", "high": high, "low": low, "close": close, "volume": "999999"},
    }


def test_v3_fixture_parent_child_hashes_and_actual_m1_recipe_are_pinned() -> None:
    fixture = _fixture()
    parent = json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))
    strategy_parent = json.loads(STRATEGY_PARENT_MANIFEST.read_text(encoding="utf-8"))
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == FIXTURE_SHA256
    assert hashlib.sha256(PARENT_MANIFEST.read_bytes()).hexdigest() == PARENT_MANIFEST_SHA256
    assert hashlib.sha256(STRATEGY_PARENT_MANIFEST.read_bytes()).hexdigest() == STRATEGY_PARENT_MANIFEST_SHA256
    assert fixture["schema_version"] == "p3-m30-strategy-execution-fixture-v3"
    assert fixture["fixture_status"] == "APPROVED_H3_1R_REVISION"
    assert parent["run_id"] == "RUN-P3-M30-002"
    assert parent["children"] == [
        {
            "path": "tests/fixtures/strategy/m30_strategy_execution_v3.json",
            "schema_version": "p3-m30-strategy-execution-fixture-v3",
            "sha256": FIXTURE_SHA256,
        }
    ]
    assert strategy_parent["manifests"]["m30_v3_executable_safety"] == {
        "path": "tests/fixtures/phase3/run_p3_m30_fixture_manifest_v3.json",
        "sha256": f"sha256:{PARENT_MANIFEST_SHA256}",
    }
    valid = _executable_m30()
    source_bars = valid["source_m1_bars"]
    assert isinstance(source_bars, list)
    assert len(source_bars) == 30
    assert [bar["source_event_ids"] for bar in source_bars] == [[f"evt-m1-{index:03d}"] for index in range(30)]
    assert source_bars[0]["open_time_utc"] == valid["open_time_utc"]
    assert source_bars[-1]["close_time_utc"] == valid["close_time_utc"]


def test_v2_compact_gt038_is_historical_and_stops_at_the_executable_entrypoint() -> None:
    compact = _executable_m30("GT-TUR-038-V3-COMPACT-V2")
    v2 = json.loads((FIXTURE.parents[0] / "m30_strategy_v2.json").read_text(encoding="utf-8"))
    expected = _fixture()["cases"]["GT-TUR-038-V3-COMPACT-V2"]["expected"]
    assert v2["cases"]["GT-TUR-038"]["expected"]["accepted"] is True
    state, signals, positions = _run_one(compact)
    assert state.is_stopped is True
    assert state.stopped_reason == expected["reason"]
    assert signals == positions == ()


def test_only_thirty_consecutive_physical_m1_bars_are_accepted_for_m30() -> None:
    state, signals, positions = _run_one(_executable_m30())
    assert state.is_stopped is False
    assert signals == positions == ()


@pytest.mark.parametrize("mutation", ("single", "duplicate", "noncontiguous", "m15"))
def test_invalid_m30_sources_stop_at_the_executable_entrypoint(mutation: str) -> None:
    raw_bar = _executable_m30()
    source_bars = raw_bar["source_m1_bars"]
    assert isinstance(source_bars, list)
    if mutation == "single":
        raw_bar["source_m1_bars"] = source_bars[:1]
    elif mutation == "duplicate":
        duplicate = deepcopy(source_bars)
        duplicate[1]["source_event_ids"] = duplicate[0]["source_event_ids"]
        raw_bar["source_m1_bars"] = duplicate
        raw_bar["source_event_ids"] = [bar["source_event_ids"][0] for bar in duplicate]
    elif mutation == "noncontiguous":
        noncontiguous = deepcopy(source_bars)
        noncontiguous[10]["open_time_utc"] = "2026-01-05T23:12:00Z"
        noncontiguous[10]["close_time_utc"] = "2026-01-05T23:13:00Z"
        raw_bar["source_m1_bars"] = noncontiguous
    else:
        raw_bar["source_bar_kind"] = "BAR_15M"
    _assert_stopped_without_output(raw_bar)


def test_simple_bullish_or_bearish_bar_does_not_create_a_trade_before_turtle_warmup() -> None:
    state, signals, positions = _run_one(_m1_bar(0, close="100.50"))
    assert state.is_stopped is False
    assert signals == positions == ()


def test_turtle_entry_and_stop_precedence_use_continuous_bars_not_bar_direction_or_volume() -> None:
    warmup = [_m1_bar(index) for index in range(55)]
    trigger = _m1_bar(55, close="120.00", high="121.00", low="100.00")
    state, signals, positions = process_closed_bars(
        StrategyState(run_id="run-p3-turtle"),
        [*warmup, trigger],
        decision_time_utc=trigger["close_time_utc"],
        instrument_id="instrument-p3-turtle",
    )
    assert [signal.reason for signal in signals] == ["SYS1_ENTRY"]
    assert positions == ()
    assert state.position_direction == "LONG"

    stop = _m1_bar(56, close="90.00", high="121.00", low="1.00")
    stopped, stop_signals, stop_positions = process_closed_bars(
        state,
        [stop],
        decision_time_utc=stop["close_time_utc"],
        instrument_id="instrument-p3-turtle",
    )
    assert [signal.reason for signal in stop_signals] == ["TWO_N_STOP"]
    assert stop_positions == ()
    assert stopped.position_direction is None


def test_restore_rejects_missing_replay_binding() -> None:
    context = {
        "data_version": "dv-1",
        "catalog_version": "catalog-1",
        "config_hash": "config-1",
        "code_revision": "code-1",
        "fixture_hash": "fixture-1",
        "fixture_manifest_id": "fixture-manifest-1",
        "manifest_hash": "manifest-1",
        "timeframe_rule_version": "m30-v3",
        "calendar_version": "calendar-v1",
        "m30_enabled": True,
        "m30_watermark": "2026-01-05T23:30:00Z",
        "content_hash": "content-1",
        "enabled_timeframes": ["M1", "M15", "M30", "H1", "H4", "D1"],
    }
    missing = dict(context)
    missing.pop("content_hash")
    assert restore_m30_context({"snapshot": context, "restore_context": missing}) == {
        "restored": False,
        "status": "STOPPED",
        "reason": "STR_SNAPSHOT_CONTEXT_MISMATCH",
        "signal_count": 0,
    }


def test_m30_requires_explicit_enablement_and_never_uses_an_omitted_v1_config_as_opt_in() -> None:
    """M30 changes behaviour, so it must not appear when callers omit v1 config."""
    omitted = _executable_m30()
    omitted_state, omitted_signals, omitted_positions = process_closed_bars(
        StrategyState(run_id="run-p3-v3-m30-omitted"),
        [omitted],
        decision_time_utc=omitted["close_time_utc"],
        instrument_id="instrument-p3-v3",
    )
    assert omitted_state.is_stopped is True
    assert omitted_state.stopped_reason == "STR_TIMEFRAME_NOT_ENABLED"
    assert omitted_signals == omitted_positions == ()

    v1_state, v1_signals, v1_positions = process_closed_bars(
        StrategyState(run_id="run-p3-v3-m30-v1"),
        [_executable_m30()],
        decision_time_utc="2026-01-05T23:30:00Z",
        instrument_id="instrument-p3-v3",
        config=StrategyConfig(),
    )
    assert v1_state.is_stopped is True
    assert v1_state.stopped_reason == "STR_TIMEFRAME_NOT_ENABLED"
    assert v1_signals == v1_positions == ()

    enabled_state, enabled_signals, enabled_positions = process_closed_bars(
        StrategyState(run_id="run-p3-v3-m30-enabled"),
        [_executable_m30()],
        decision_time_utc="2026-01-05T23:30:00Z",
        instrument_id="instrument-p3-v3",
        config=ACTIVE_M30_CONFIG,
    )
    assert enabled_state.is_stopped is False
    assert enabled_signals == enabled_positions == ()


def test_campaign_watermark_rejects_regression_is_noop_when_same_and_stops_on_conflict() -> None:
    """A past campaign fact cannot replace a newer fact in the same run."""
    config = StrategyConfig(enabled_timeframes=("M1",))
    initial = ConfirmedExecution(
        campaign_outcome="LOSS",
        campaign_watermark="2026-01-05T23:01:00Z",
        campaign_fingerprint="sha256:campaign-one",
    )
    state, signals, positions = process_closed_bars(
        StrategyState(run_id="run-p3-campaign"),
        [_m1_bar(0)],
        decision_time_utc="2026-01-05T23:01:00Z",
        instrument_id="instrument-p3-campaign",
        config=config,
        confirmed_execution=initial,
    )
    assert state.campaign_watermark == initial.campaign_watermark
    assert state.campaign_fingerprint == initial.campaign_fingerprint
    assert signals == positions == ()

    same_state, same_signals, same_positions = process_closed_bars(
        state,
        [_m1_bar(1)],
        decision_time_utc="2026-01-05T23:02:00Z",
        instrument_id="instrument-p3-campaign",
        config=config,
        confirmed_execution=initial,
    )
    assert same_state.is_stopped is False
    assert same_state.campaign_watermark == state.campaign_watermark
    assert same_state.campaign_fingerprint == state.campaign_fingerprint
    assert same_signals == same_positions == ()

    regression = ConfirmedExecution(
        campaign_outcome="WIN",
        campaign_watermark="2026-01-05T23:00:00Z",
        campaign_fingerprint="sha256:campaign-older",
    )
    regressed, regressed_signals, regressed_positions = process_closed_bars(
        same_state,
        [_m1_bar(2)],
        decision_time_utc="2026-01-05T23:03:00Z",
        instrument_id="instrument-p3-campaign",
        config=config,
        confirmed_execution=regression,
    )
    assert regressed.is_stopped is True
    assert regressed.stopped_reason == "STR_CAMPAIGN_WATERMARK_REGRESSION"
    assert regressed_signals == regressed_positions == ()

    conflict = ConfirmedExecution(
        campaign_outcome="LOSS",
        campaign_watermark=initial.campaign_watermark,
        campaign_fingerprint="sha256:campaign-conflict",
    )
    conflicted, conflict_signals, conflict_positions = process_closed_bars(
        same_state,
        [_m1_bar(2)],
        decision_time_utc="2026-01-05T23:03:00Z",
        instrument_id="instrument-p3-campaign",
        config=config,
        confirmed_execution=conflict,
    )
    assert conflicted.is_stopped is True
    assert conflicted.stopped_reason == "STR_DUPLICATE_CONFLICT"
    assert conflict_signals == conflict_positions == ()


def test_same_campaign_fact_on_every_batch_does_not_repeat_campaign_update_but_advances_bars() -> None:
    """Campaign facts and market bars are separate timelines in one run."""
    campaign = ConfirmedExecution(
        campaign_outcome="LOSS",
        campaign_watermark="2026-01-05T23:01:00Z",
        campaign_fingerprint="sha256:campaign-stable",
    )
    config = StrategyConfig(enabled_timeframes=("M1",))
    state = StrategyState(run_id="run-p3-campaign-every-batch")
    for index in range(3):
        bar = _m1_bar(index)
        state, signals, positions = process_closed_bars(
            state,
            [bar],
            decision_time_utc=bar["close_time_utc"],
            instrument_id="instrument-p3-campaign",
            config=config,
            confirmed_execution=campaign,
        )
        assert state.is_stopped is False
        assert state.prior_campaign_outcome == campaign.campaign_outcome
        assert state.campaign_watermark == campaign.campaign_watermark
        assert state.campaign_fingerprint == campaign.campaign_fingerprint
        assert len(state.bars_by_timeframe["M1"]) == index + 1
        assert state.watermarks["M1"] == bar["close_time_utc"]
        assert signals == positions == ()


def _warmed_history(timeframe: str) -> tuple[ClosedBar, ...]:
    start = datetime(2025, 12, 1, tzinfo=UTC)
    return tuple(
        ClosedBar(
            timeframe=timeframe,
            open_time_utc=start + timedelta(minutes=index),
            close_time_utc=start + timedelta(minutes=index + 1),
            open=Decimal("100.00"),
            high=Decimal("101.00"),
            low=Decimal("99.00"),
            close=Decimal("100.00"),
            volume=Decimal("1"),
            source_event_ids=(f"warm-{timeframe}-{index:03d}",),
            is_closed=True,
            calendar_version="us-futures-fixture-v1",
        )
        for index in range(55)
    )


def _same_close_non_m30_bar(timeframe: str, open_time_utc: str) -> dict[str, object]:
    return {
        "timeframe": timeframe,
        "open_time_utc": open_time_utc,
        "close_time_utc": "2026-01-05T23:30:00Z",
        "source_event_ids": [f"same-close-{timeframe.lower()}"],
        "is_closed": True,
        "calendar_version": "us-futures-fixture-v1",
        "ohlcv": {"open": "100.00", "high": "101.00", "low": "99.00", "close": "100.00", "volume": "1"},
    }


def _state_hash(state: StrategyState) -> str:
    payload = {
        "stopped_reason": state.stopped_reason,
        "watermarks": sorted(state.watermarks.items()),
        "histories": {
            timeframe: [bar.close_time_utc.isoformat() for bar in bars]
            for timeframe, bars in sorted(state.bars_by_timeframe.items())
        },
        "position_direction": state.position_direction,
        "last_fill": str(state.last_fill),
        "n_value": str(state.n_value),
        "pending_add": state.pending_add,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_same_close_multitimeframe_permutations_have_one_identical_decision() -> None:
    """Input order cannot duplicate or change a simultaneous-close decision."""
    bars = (
        _same_close_non_m30_bar("M15", "2026-01-05T23:15:00Z"),
        _executable_m30(),
        _same_close_non_m30_bar("H1", "2026-01-05T22:30:00Z"),
        _same_close_non_m30_bar("H4", "2026-01-05T19:30:00Z"),
        _same_close_non_m30_bar("D1", "2026-01-04T23:30:00Z"),
    )
    config = ACTIVE_M30_CONFIG
    fingerprints: set[tuple[tuple[tuple[str, str, str], ...], tuple[tuple[str, str, str], ...], str]] = set()

    for order in permutations(bars):
        state, signals, positions = process_closed_bars(
            StrategyState(run_id="run-p3-same-close"),
            list(order),
            decision_time_utc="2026-01-05T23:30:00Z",
            instrument_id="instrument-p3-same-close",
            config=config,
        )
        assert state.is_stopped is False
        assert len(signals) <= 1
        assert len(positions) <= 1
        fingerprints.add(
            (
                tuple((signal.signal_id, signal.direction, signal.reason) for signal in signals),
                tuple((position.instrument_id, position.direction, str(position.unit_hint)) for position in positions),
                _state_hash(state),
            )
        )

    assert len(fingerprints) == 1


def test_warmed_same_close_candidate_conflicts_have_one_identical_decision_in_all_permutations() -> None:
    """Every view updates, then stop/exit/add conflict resolves once after all views close."""
    m30 = _executable_m30()
    source_bars = m30["source_m1_bars"]
    assert isinstance(source_bars, list)
    source_bars[0]["ohlcv"] = {"open": "100.00", "high": "110.00", "low": "90.00", "close": "100.00", "volume": "1"}
    m30["ohlcv"] = {"open": "100.00", "high": "110.00", "low": "90.00", "close": "100.00", "volume": "30"}

    def candidate(timeframe: str, opened: str) -> dict[str, object]:
        value = _same_close_non_m30_bar(timeframe, opened)
        value["ohlcv"] = {"open": "100.00", "high": "110.00", "low": "90.00", "close": "100.00", "volume": "999999"}
        return value

    bars = (
        candidate("M15", "2026-01-05T23:15:00Z"),
        m30,
        candidate("H1", "2026-01-05T22:30:00Z"),
        candidate("H4", "2026-01-05T19:30:00Z"),
        candidate("D1", "2026-01-04T23:30:00Z"),
    )
    histories = {timeframe: _warmed_history(timeframe) for timeframe in ("M15", "M30", "H1", "H4", "D1")}
    baseline = StrategyState(
        run_id="run-p3-warmed-same-close",
        bars_by_timeframe=histories,
        position_direction="LONG",
        last_fill=Decimal("100.00"),
    )
    fingerprints: set[tuple[tuple[tuple[str, str, str], ...], tuple[tuple[str, str, str], ...], str]] = set()
    for order in permutations(bars):
        state, signals, positions = process_closed_bars(
            baseline,
            list(order),
            decision_time_utc="2026-01-05T23:30:00Z",
            instrument_id="instrument-p3-warmed-same-close",
            config=ACTIVE_M30_CONFIG,
        )
        assert state.is_stopped is False
        assert len(signals) == 1
        assert signals[0].reason == "TWO_N_STOP"
        assert positions == ()
        assert {timeframe: len(history) for timeframe, history in state.bars_by_timeframe.items()} == {
            timeframe: 56 for timeframe in histories
        }
        fingerprints.add(
            (
                tuple((signal.signal_id, signal.direction, signal.reason) for signal in signals),
                tuple((position.instrument_id, position.direction, str(position.unit_hint)) for position in positions),
                _state_hash(state),
            )
        )
    assert len(fingerprints) == 1


@pytest.mark.parametrize("invalid_decimal", ("NaN", "Infinity", "not-a-decimal"))
def test_invalid_m1_ohlcv_stops_safely_without_raising_or_emitting_output(invalid_decimal: str) -> None:
    raw_bar = _m1_bar(0)
    raw_bar["ohlcv"] = {"open": "100.00", "high": "101.00", "low": "99.00", "close": invalid_decimal, "volume": "1"}
    _assert_stopped_without_output(raw_bar)


@pytest.mark.parametrize("field", ("open", "high", "low", "close", "volume"))
@pytest.mark.parametrize("invalid_decimal", ("NaN", "Infinity", "not-a-decimal"))
def test_every_invalid_m30_source_ohlcv_field_stops_with_specific_safe_reason(field: str, invalid_decimal: str) -> None:
    raw_bar = _executable_m30()
    source_bars = raw_bar["source_m1_bars"]
    assert isinstance(source_bars, list)
    ohlcv = {
        "open": "100.00",
        "high": "101.00",
        "low": "99.00",
        "close": "100.00",
        "volume": "1",
    }
    ohlcv[field] = invalid_decimal
    source_bars[0]["ohlcv"] = ohlcv

    state, signals, positions = _run_one(raw_bar)

    assert state.is_stopped is True
    expected_reason = "M30_OHLCV_INVALID" if invalid_decimal in {"NaN", "Infinity"} else "M30_OHLCV_MISMATCH"
    assert state.stopped_reason == expected_reason
    assert signals == positions == ()


def _target_position_config() -> StrategyConfig:
    return StrategyConfig(
        output_contract="TARGET_POSITION",
        enabled_timeframes=("M1",),
        strategy_unit_hint=Decimal("7"),
    )


def _target_candidate(index: int, *, high: str, low: str) -> dict[str, object]:
    return _m1_bar(index, close="100.00", high=high, low=low)


@pytest.mark.parametrize(
    ("position_direction", "high", "low", "expected_reason"),
    (
        ("LONG", "100.50", "98.00", "EXIT_LONG"),
        ("SHORT", "102.00", "99.50", "EXIT_SHORT"),
        ("LONG", "100.50", "95.00", "TWO_N_STOP"),
        ("SHORT", "105.00", "99.50", "TWO_N_STOP"),
    ),
)
def test_target_position_emits_deterministic_flat_zero_for_every_exit_kind(
    position_direction: str, high: str, low: str, expected_reason: str
) -> None:
    """Strategy tells the outer boundary to hold nothing; it never sizes an exit."""
    candidate = _target_candidate(100, high=high, low=low)
    initial = StrategyState(
        run_id="run-p3-target-flat",
        bars_by_timeframe={"M1": _warmed_history("M1")},
        position_direction=position_direction,
        last_fill=Decimal("100.00"),
    )
    first = process_closed_bars(
        initial,
        [candidate],
        decision_time_utc=candidate["close_time_utc"],
        instrument_id="instrument-p3-target-flat",
        config=_target_position_config(),
    )
    second = process_closed_bars(
        initial,
        [candidate],
        decision_time_utc=candidate["close_time_utc"],
        instrument_id="instrument-p3-target-flat",
        config=_target_position_config(),
    )
    first_state, first_signals, first_positions = first
    second_state, second_signals, second_positions = second
    assert first_state.position_direction is None
    assert [signal.reason for signal in first_signals] == [expected_reason]
    assert len(first_positions) == 1
    assert first_positions[0].direction == "FLAT"
    assert first_positions[0].unit_hint == Decimal("0")
    assert first_signals == second_signals
    assert first_positions == second_positions
    assert _state_hash(first_state) == _state_hash(second_state)


@pytest.mark.parametrize(
    ("position_direction", "high", "low", "expected_reason"),
    (
        (None, "120.00", "100.00", "SYS1_ENTRY"),
        ("LONG", "102.00", "99.50", "ADD_LONG"),
    ),
)
def test_target_position_uses_only_approved_positive_strategy_hint_for_entry_and_add(
    position_direction: str | None, high: str, low: str, expected_reason: str
) -> None:
    candidate = _target_candidate(101, high=high, low=low)
    state, signals, positions = process_closed_bars(
        StrategyState(
            run_id="run-p3-target-positive",
            bars_by_timeframe={"M1": _warmed_history("M1")},
            position_direction=position_direction,
            last_fill=Decimal("100.00") if position_direction else None,
        ),
        [candidate],
        decision_time_utc=candidate["close_time_utc"],
        instrument_id="instrument-p3-target-positive",
        config=_target_position_config(),
    )
    assert state.is_stopped is False
    assert [signal.reason for signal in signals] == [expected_reason]
    assert len(positions) == 1
    assert positions[0].direction == "LONG"
    assert positions[0].unit_hint == Decimal("7")
    assert positions[0].unit_hint != Decimal("999999")

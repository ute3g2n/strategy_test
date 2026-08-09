"""P3-07R-02 typed Backtest Core integration contracts."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from autotrade.backtest.contracts import (
    BacktestRunRequest,
    DataGateDecision,
    EngineIdentity,
    ExperimentManifest,
    ReplayInput,
    ScheduledDirective,
    SimulatorState,
    canonical_hash,
)
from autotrade.backtest.replay_order import normalize_replay
from autotrade.backtest.runner import BacktestRunner
from autotrade.market_data.store_contracts import DataVersionManifest, MarketEvent
from autotrade.strategy.contracts import StrategyConfig, StrategyState

RUN_ID = "RUN-P3-BT-REPAIR-002"
DATA_VERSION = "dv-p3-repair-002"
CALENDAR_VERSION = "us-futures-fixture-v1"
MANIFEST_SHA256 = "sha256:" + "a" * 64
ZERO_SHA256 = "sha256:" + "b" * 64


def _event(index: int, *, instrument_id: str = "MKT-A") -> MarketEvent:
    opened = datetime(2026, 1, 5, 23, 0, tzinfo=UTC) + timedelta(minutes=index)
    close = Decimal("100.00") + Decimal(index) / Decimal("10")
    return MarketEvent(
        event_id=f"evt-repair-{index:03d}",
        run_id=RUN_ID,
        instrument_id=instrument_id,
        event_time_utc=opened,
        received_at_utc=opened,
        exchange_time_local=None,
        bar_close_time=opened + timedelta(minutes=1),
        event_kind="BAR_1M",
        values={
            "open": format(close, "f"),
            "high": format(close + Decimal("0.25"), "f"),
            "low": format(close - Decimal("0.25"), "f"),
            "close": format(close + Decimal("0.05"), "f"),
            "volume": "1",
        },
        quality_flags=(),
        data_version=DATA_VERSION,
    )


def _config(*, m30_enabled: bool = False) -> StrategyConfig:
    enabled = ("M1", "M15", "M30", "H1") if m30_enabled else ("M1",)
    return StrategyConfig(
        output_contract="SIGNAL_EVENT",
        enabled_timeframes=enabled,
        m30_enabled=m30_enabled,
    )


def _manifest(config: StrategyConfig) -> ExperimentManifest:
    return ExperimentManifest(
        run_id=RUN_ID,
        raw_input_sha256=ZERO_SHA256,
        normalized_input_sha256=ZERO_SHA256,
        market_event_sequence_sha256=ZERO_SHA256,
        data_version=DATA_VERSION,
        catalog_version="catalog-p3-repair-002",
        catalog_sha256=ZERO_SHA256,
        calendar_version=CALENDAR_VERSION,
        calendar_sha256=ZERO_SHA256,
        timeframe_rule_version="timeframe-calendar-anchor-m30-direct-m1-v2",
        ordering_rule_version="m1-m15-m30-h1-h4-d1-v2",
        strategy_config_sha256=canonical_hash(vars(config)),
        code_revision="working-tree-p3-07r-02",
        quality_policy_version="quality-policy-p2-v1",
        quality_report_sha256=ZERO_SHA256,
        split_plan_sha256=ZERO_SHA256,
        cost_profile_sha256=ZERO_SHA256,
        adapter_version="ENGINE_NOT_USED",
        adapter_artifact_sha256="ENGINE_NOT_USED",
        engine_identity=EngineIdentity(),
        fixture_manifest_sha256=ZERO_SHA256,
        child_fixture_sha256s=(ZERO_SHA256,),
        input_sha256=ZERO_SHA256,
        manifest_sha256=MANIFEST_SHA256,
        session_anchor_utc=datetime(2026, 1, 5, 23, 0, tzinfo=UTC),
    )


def _request(
    events: tuple[MarketEvent, ...],
    *,
    config: StrategyConfig | None = None,
    initial_strategy_state: StrategyState | None = None,
    initial_simulator_state: SimulatorState | None = None,
) -> BacktestRunRequest:
    active_config = config or _config()
    manifest = _manifest(active_config)
    data_manifest = DataVersionManifest(
        data_version=DATA_VERSION,
        raw_sha256s=(ZERO_SHA256,),
        normalization_rule_version="normalization-p3-v1",
        catalog_version=manifest.catalog_version,
        catalog_sha256=manifest.catalog_sha256,
        quality_report_sha256=manifest.quality_report_sha256,
        normalized_content_sha256=ZERO_SHA256,
    )
    replay = ReplayInput(
        events=events,
        data_version_manifest=data_manifest,
        data_gate=DataGateDecision(
            data_version=DATA_VERSION,
            quality_report_sha256=manifest.quality_report_sha256,
            policy_version=manifest.quality_policy_version,
        ),
        replay_cutoff_utc=max((event.bar_close_time for event in events), default=manifest.session_anchor_utc)
        if events
        else manifest.session_anchor_utc + timedelta(minutes=1),
        manifest_sha256=manifest.manifest_sha256,
    )
    return BacktestRunRequest(
        run_id=RUN_ID,
        replay=replay,
        manifest=manifest,
        strategy_config=active_config,
        engine_identity=EngineIdentity(),
        initial_strategy_state=initial_strategy_state or StrategyState(run_id=RUN_ID),
        initial_simulator_state=initial_simulator_state or SimulatorState(),
    )


def test_typed_runner_commits_and_replay_permutation_is_identical() -> None:
    events = tuple(_event(index) for index in range(3))
    runner = BacktestRunner()

    first = runner.run(_request(events))
    second = runner.run(_request(tuple(reversed(events))))

    assert first.status == "COMMITTED"
    assert second.status == "COMMITTED"
    assert first.result_sha256 == second.result_sha256
    assert first.snapshot is not None
    assert first.commit_marker is not None
    assert first.failure is None


def test_runner_rejects_data_manifest_mismatch_before_strategy() -> None:
    request = _request((_event(0),))
    bad_data_manifest = replace(request.replay.data_version_manifest, data_version="wrong-data-version")
    request = replace(request, replay=replace(request.replay, data_version_manifest=bad_data_manifest))

    result = BacktestRunner().run(request)

    assert result.status == "STOPPED"
    assert result.failure is not None
    assert result.failure.reason == "DATA_GATE_BLOCKED"
    assert result.rows == ()


def test_raw_replay_boundary_rejects_unknown_fields_and_float_values() -> None:
    event = {
        "event_id": "raw-001",
        "run_id": RUN_ID,
        "instrument_id": "MKT-A",
        "event_time": "2026-01-05T23:00:00Z",
        "bar_close_time": "2026-01-05T23:01:00Z",
        "event_kind": "BAR_1M",
        "values": {"open": "100", "high": "101", "low": "99", "close": "100", "volume": "1"},
        "quality_flags": [],
        "data_version": DATA_VERSION,
    }

    assert normalize_replay({"events": [{**event, "unexpected": "stop"}]}) == {
        "status": "STOPPED",
        "reason": "INVALID_REPLAY_INPUT",
    }
    assert normalize_replay({"events": [{**event, "values": {**event["values"], "close": 100.0}}]}) == {
        "status": "STOPPED",
        "reason": "INVALID_REPLAY_INPUT",
    }


def test_replay_duplicate_same_payload_is_noop_but_conflict_is_sticky_stop() -> None:
    event = {
        "event_id": "raw-duplicate",
        "run_id": RUN_ID,
        "instrument_id": "MKT-A",
        "event_time": "2026-01-05T23:00:00Z",
        "bar_close_time": "2026-01-05T23:01:00Z",
        "event_kind": "BAR_1M",
        "values": {"open": "100", "high": "101", "low": "99", "close": "100", "volume": "1"},
        "quality_flags": [],
        "data_version": DATA_VERSION,
    }

    duplicate = normalize_replay({"events": [event, dict(event)]})
    conflict = normalize_replay({"events": [event, {**event, "values": {**event["values"], "close": "101"}}]})

    assert duplicate["status"] == "PASS"
    assert len(duplicate["events"]) == 1
    assert conflict == {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}


def test_same_close_strategy_cohort_is_processed_once_in_fixed_view_order(monkeypatch: pytest.MonkeyPatch) -> None:
    import autotrade.backtest.runner as runner_module

    calls: list[tuple[str, ...]] = []
    original = runner_module.process_closed_bars

    def spy(*args, **kwargs):
        calls.append(tuple(bar["timeframe"] for bar in args[1]))
        return original(*args, **kwargs)

    monkeypatch.setattr(runner_module, "process_closed_bars", spy)
    events = tuple(_event(index) for index in range(60))
    result = BacktestRunner().run(_request(events, config=_config(m30_enabled=True)))
    permuted = BacktestRunner().run(_request(tuple(reversed(events)), config=_config(m30_enabled=True)))

    assert result.status == "COMMITTED"
    assert permuted.status == "COMMITTED"
    assert result.result_sha256 == permuted.result_sha256
    assert calls[59] == ("M1", "M15", "M30", "H1")
    assert calls[-1] == ("M1", "M15", "M30", "H1")
    assert len(calls) == 120
    assert result.failure is None


def test_m30_is_directly_aggregated_from_thirty_consecutive_m1_events(monkeypatch: pytest.MonkeyPatch) -> None:
    import autotrade.backtest.runner as runner_module

    events = tuple(_event(index) for index in range(30))
    config = _config(m30_enabled=True)
    captured: list[dict[str, object]] = []
    original = runner_module.process_closed_bars

    def spy(*args, **kwargs):
        captured.extend(bar for bar in args[1] if bar["timeframe"] == "M30")
        return original(*args, **kwargs)

    monkeypatch.setattr(runner_module, "process_closed_bars", spy)

    result = BacktestRunner().run(_request(events, config=config))

    assert result.status == "COMMITTED"
    assert result.failure is None
    assert len(captured) == 1
    assert captured[0]["source_bar_kind"] == "BAR_1M"
    assert len(captured[0]["source_m1_bars"]) == 30


def test_m30_fixture_ohlcv_is_recomputed_from_direct_m1_source(monkeypatch: pytest.MonkeyPatch) -> None:
    import autotrade.backtest.runner as runner_module

    fixture_path = Path(__file__).parents[1] / "fixtures" / "phase3" / "m30_backtest_v2.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    raw_bars = fixture["direct_m1_bars"]
    events = tuple(
        MarketEvent(
            event_id=fixture["source_event_ids"][index],
            run_id=RUN_ID,
            instrument_id="MKT-A",
            event_time_utc=datetime.fromisoformat(bar["open_time_utc"].replace("Z", "+00:00")),
            received_at_utc=datetime.fromisoformat(bar["open_time_utc"].replace("Z", "+00:00")),
            exchange_time_local=None,
            bar_close_time=datetime.fromisoformat(bar["close_time_utc"].replace("Z", "+00:00")),
            event_kind="BAR_1M",
            values={key: bar[key] for key in ("open", "high", "low", "close", "volume")},
            quality_flags=(),
            data_version=DATA_VERSION,
        )
        for index, bar in enumerate(raw_bars)
    )
    captured: list[dict[str, object]] = []
    original = runner_module.process_closed_bars

    def spy(*args, **kwargs):
        captured.extend(bar for bar in args[1] if bar["timeframe"] == "M30")
        return original(*args, **kwargs)

    monkeypatch.setattr(runner_module, "process_closed_bars", spy)
    result = BacktestRunner().run(_request(events, config=_config(m30_enabled=True)))

    assert result.status == "COMMITTED"
    assert len(captured) == 1
    assert captured[0]["source_event_ids"] == fixture["source_event_ids"]
    assert captured[0]["ohlcv"] == {
        "open": fixture["expected_normal_m30"]["open"],
        "high": fixture["expected_normal_m30"]["high"],
        "low": fixture["expected_normal_m30"]["low"],
        "close": fixture["expected_normal_m30"]["close"],
        "volume": fixture["expected_normal_m30"]["volume"],
    }


def test_scheduled_directive_fills_only_on_the_next_eligible_bar() -> None:
    decision_time = datetime(2026, 1, 5, 23, 0, tzinfo=UTC)
    directive = ScheduledDirective(
        directive_id="directive-next-bar",
        instrument_id="MKT-A",
        direction="LONG",
        unit_hint=Decimal("1"),
        decision_time_utc=decision_time,
        min_eligible_bar_open_utc=decision_time + timedelta(minutes=1),
        kind="ENTRY",
        fingerprint=canonical_hash({"directive_id": "directive-next-bar"}),
    )
    state = SimulatorState(pending_directives=(directive,))
    result = BacktestRunner().run(_request((_event(0), _event(1)), initial_simulator_state=state))

    assert result.status == "COMMITTED"
    assert result.fill_count == 1
    assert [row.row_kind for row in result.rows].count("FILL") == 1
    assert result.rows[0].decision_time_utc == _event(1).bar_close_time


def test_target_position_strategy_is_scheduled_then_filled_on_next_bar() -> None:
    from autotrade.strategy.contracts import ClosedBar

    start = datetime(2026, 1, 5, 22, 40, tzinfo=UTC)
    warm_bars = tuple(
        ClosedBar(
            timeframe="M1",
            open_time_utc=start + timedelta(minutes=index),
            close_time_utc=start + timedelta(minutes=index + 1),
            open=Decimal("100.00"),
            high=Decimal("100.10"),
            low=Decimal("99.90"),
            close=Decimal("100.00"),
            volume=Decimal("1"),
            source_event_ids=(f"warm-{index:03d}",),
            is_closed=True,
            calendar_version=CALENDAR_VERSION,
        )
        for index in range(20)
    )
    strategy_state = StrategyState(
        run_id=RUN_ID,
        watermarks={"M1": "2026-01-05T23:00:00Z"},
        bars_by_timeframe={"M1": warm_bars},
    )
    config = replace(_config(), output_contract="TARGET_POSITION", strategy_unit_hint=Decimal("2"))

    result = BacktestRunner().run(
        _request(
            (_event(0), _event(1)),
            config=config,
            initial_strategy_state=strategy_state,
        )
    )

    assert result.status == "COMMITTED"
    assert result.directive_count >= 1
    assert result.fill_count == 1
    assert [row.row_kind for row in result.rows].count("DIRECTIVE") >= 1
    assert [row.row_kind for row in result.rows].count("FILL") == 1


def test_protective_stop_is_allowed_on_the_current_bar() -> None:
    decision_time = datetime(2026, 1, 5, 23, 0, tzinfo=UTC)
    directive = ScheduledDirective(
        directive_id="protective-stop-current-bar",
        instrument_id="MKT-A",
        direction="FLAT",
        unit_hint=Decimal("0"),
        decision_time_utc=decision_time,
        min_eligible_bar_open_utc=decision_time + timedelta(minutes=5),
        kind="PROTECTIVE_STOP",
        fingerprint=canonical_hash({"directive_id": "protective-stop-current-bar"}),
    )

    result = BacktestRunner().run(
        _request(
            (_event(0),),
            initial_simulator_state=SimulatorState(
                position_direction="LONG",
                last_fill=Decimal("100"),
                pending_directives=(directive,),
            ),
        )
    )

    assert result.status == "COMMITTED"
    assert result.fill_count == 1
    assert [row.row_kind for row in result.rows] == ["FILL"]

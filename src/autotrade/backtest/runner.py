"""Typed, deterministic Backtest Core execution path for P3-07R-02."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, DecimalException
from typing import Any

from autotrade.market_data.store_contracts import MarketEvent
from autotrade.strategy.contracts import StrategyConfig, StrategyState
from autotrade.strategy.service import process_closed_bars, validate_m30_closed_bars

from .calendar_port import evaluate_calendar_case, validate_calendar_window
from .contracts import (
    BacktestFailure,
    BacktestRunRequest,
    BacktestRunResult,
    BacktestSnapshot,
    CommitMarker,
    DataGateDecision,
    DataVersionManifest,
    EngineIdentity,
    ExperimentManifest,
    ReplayInput,
    ResultRow,
    ScheduledDirective,
    SimulatorState,
    canonical_hash,
)
from .replay_order import normalize_replay

_TIMEFRAME_ORDER = ("M1", "M15", "M30", "H1", "H4", "D1")
_ALLOWED_TIMEFRAMES = frozenset(_TIMEFRAME_ORDER)
_TIMEFRAME_MINUTES = {"M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
_WARNING_FLAGS = frozenset({"DEGRADED", "PRICE_INVALID", "VOLUME_INVALID"})


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("UTC timestamp required")
    return value.astimezone(UTC)


def _event_mapping(event: MarketEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "run_id": event.run_id,
        "instrument_id": event.instrument_id,
        "event_time": _utc(event.event_time_utc).isoformat().replace("+00:00", "Z"),
        "bar_close_time": _utc(event.bar_close_time).isoformat().replace("+00:00", "Z"),
        "event_kind": event.event_kind,
        "values": dict(event.values),
        "quality_flags": list(event.quality_flags),
        "data_version": event.data_version,
    }


def _raw_m1_bar(event: MarketEvent, calendar_version: str) -> dict[str, Any]:
    values = dict(event.values)
    required = ("open", "high", "low", "close", "volume")
    if any(not isinstance(values.get(key), str) for key in required):
        raise ValueError("M1 OHLCV must be decimal strings")
    return {
        "timeframe": "M1",
        "open_time_utc": _utc(event.event_time_utc).isoformat().replace("+00:00", "Z"),
        "close_time_utc": _utc(event.bar_close_time).isoformat().replace("+00:00", "Z"),
        "is_closed": True,
        "calendar_version": calendar_version,
        "source_event_ids": [event.event_id],
        "ohlcv": {key: values[key] for key in required},
    }


def _aggregate_bar(
    events: list[MarketEvent], timeframe: str, calendar_version: str, anchor: datetime
) -> dict[str, Any]:
    minutes = _TIMEFRAME_MINUTES[timeframe]
    if len(events) != minutes:
        raise ValueError("PARTIAL_BAR_REJECTED")
    ordered = sorted(events, key=lambda item: item.event_time_utc)
    expected = anchor
    for event in ordered:
        if _utc(event.event_time_utc) != expected:
            raise ValueError("OUT_OF_ORDER")
        expected += timedelta(minutes=1)
    raw = [_raw_m1_bar(event, calendar_version) for event in ordered]
    if timeframe == "M30":
        result = validate_m30_closed_bars(
            raw,
            session_anchor_utc=anchor.isoformat().replace("+00:00", "Z"),
            calendar_version=calendar_version,
            decision_time_utc=ordered[-1].bar_close_time.isoformat().replace("+00:00", "Z"),
        )
        if result.get("accepted") is not True:
            raise ValueError(str(result.get("reason", "PARTIAL_BAR_REJECTED")))
    values = [event.values for event in ordered]
    try:
        opens = [Decimal(item["open"]) for item in values]
        highs = [Decimal(item["high"]) for item in values]
        lows = [Decimal(item["low"]) for item in values]
        closes = [Decimal(item["close"]) for item in values]
        volumes = [Decimal(item["volume"]) for item in values]
    except (KeyError, DecimalException, TypeError, ValueError) as error:
        raise ValueError("M30_OHLCV_INVALID" if timeframe == "M30" else "STR_INPUT_INVALID") from error
    all_values = (*opens, *highs, *lows, *closes, *volumes)
    if not all(value.is_finite() for value in all_values) or any(value < 0 for value in volumes):
        raise ValueError("M30_OHLCV_INVALID" if timeframe == "M30" else "STR_INPUT_INVALID")
    if any(
        low > min(opened, closed) or high < max(opened, closed) or low > high
        for opened, high, low, closed in zip(opens, highs, lows, closes, strict=True)
    ):
        raise ValueError("M30_OHLCV_MISMATCH" if timeframe == "M30" else "STR_INPUT_INVALID")
    ohlcv = {
        "open": format(opens[0], "f"),
        "high": format(max(highs), "f"),
        "low": format(min(lows), "f"),
        "close": format(closes[-1], "f"),
        "volume": format(sum(volumes), "f"),
    }
    result = {
        "timeframe": timeframe,
        "open_time_utc": _utc(ordered[0].event_time_utc).isoformat().replace("+00:00", "Z"),
        "close_time_utc": _utc(ordered[-1].bar_close_time).isoformat().replace("+00:00", "Z"),
        "is_closed": True,
        "calendar_version": calendar_version,
        "source_event_ids": [event.event_id for event in ordered],
        "ohlcv": ohlcv,
    }
    if timeframe == "M30":
        result.update(
            {
                "source_bar_kind": "BAR_1M",
                "source_bar_count": minutes,
                "source_m1_bars": raw,
                "session_anchor_utc": anchor.isoformat().replace("+00:00", "Z"),
                "decision_time_utc": _utc(ordered[-1].bar_close_time).isoformat().replace("+00:00", "Z"),
            }
        )
    return result


def _row(
    sequence_no: int,
    event: MarketEvent,
    kind: str,
    manifest_sha256: str | None,
    payload: dict[str, str],
) -> ResultRow:
    payload_items = tuple(sorted(payload.items()))
    row_id = f"{event.run_id}:{sequence_no}:{kind}"
    return ResultRow(
        sequence_no=sequence_no,
        row_id=row_id,
        event_id=event.event_id,
        instrument_id=event.instrument_id,
        row_kind=kind,
        decision_time_utc=_utc(event.bar_close_time),
        payload=payload_items,
        # Row payload identity is recalculated by ResultStore as a protected
        # data/replay check.  No management row/content hash is emitted here.
        manifest_sha256=None,
        content_sha256=None,
    )


def _state_hash(strategy_state: StrategyState, simulator_state: SimulatorState) -> str:
    payload = {
        "position_direction": strategy_state.position_direction,
        "last_fill": str(strategy_state.last_fill) if strategy_state.last_fill is not None else None,
        "watermarks": sorted(strategy_state.watermarks.items()),
        "pending": [directive.fingerprint for directive in simulator_state.pending_directives],
        "consumed": simulator_state.consumed_fingerprints,
    }
    return canonical_hash(payload)


def _failure(reason: str, detail: str | None = None) -> BacktestRunResult:
    return BacktestRunResult(
        status="STOPPED",
        failure=BacktestFailure(reason, detail),
        rows=(),
        result_sha256=None,
        snapshot=None,
        commit_marker=None,
        signal_count=0,
        directive_count=0,
        fill_count=0,
        state_sha256="",
    )


def _manifest_failure(request: BacktestRunRequest) -> BacktestFailure | None:
    manifest = request.manifest
    if (
        not isinstance(manifest, ExperimentManifest)
        or not isinstance(request.engine_identity, EngineIdentity)
        or not isinstance(manifest.engine_identity, EngineIdentity)
    ):
        return BacktestFailure("MANIFEST_INTEGRITY_VIOLATION", "typed manifest and engine identity are required")
    required = (
        manifest.run_id,
        manifest.schema_version,
        manifest.data_version,
        manifest.catalog_version,
        manifest.catalog_sha256,
        manifest.calendar_version,
        manifest.calendar_sha256,
        manifest.timeframe_rule_version,
        manifest.ordering_rule_version,
        manifest.strategy_config_sha256,
        manifest.code_revision,
        manifest.quality_policy_version,
        manifest.quality_report_sha256,
        manifest.split_plan_sha256,
        manifest.cost_profile_sha256,
        manifest.adapter_version,
        manifest.adapter_artifact_sha256,
        manifest.fixture_manifest_sha256,
        manifest.input_sha256,
    )
    if any(not isinstance(value, str) or not value for value in required):
        return BacktestFailure("MANIFEST_INTEGRITY_VIOLATION", "required binding is missing")
    if manifest.run_id != request.run_id:
        return BacktestFailure("RUN_BINDING_INVALID", "request and manifest run bindings differ")
    if any(value != "ENGINE_NOT_USED" for value in vars(request.engine_identity).values()) or any(
        value != "ENGINE_NOT_USED" for value in vars(manifest.engine_identity).values()
    ):
        return BacktestFailure("ENGINE_IDENTITY_UNPINNED", "P3-07 Core does not use an external engine")
    if manifest.session_anchor_utc is None:
        return BacktestFailure("CALENDAR_BOUNDARY_INVALID", "session anchor is required")
    try:
        _utc(manifest.session_anchor_utc)
    except ValueError as error:
        return BacktestFailure("CALENDAR_BOUNDARY_INVALID", str(error))
    calendar_result = evaluate_calendar_case(_calendar_context(manifest, manifest.session_anchor_utc))
    if calendar_result.get("status") != "PASS":
        return BacktestFailure(
            str(calendar_result.get("reason", "CALENDAR_BOUNDARY_INVALID")),
            f"calendar case {manifest.calendar_case} is not executable",
        )
    return None


def _calendar_context(manifest: ExperimentManifest, anchor: datetime) -> dict[str, Any]:
    context: dict[str, Any] = {
        "case": manifest.calendar_case,
        "session_open_utc": (manifest.calendar_session_open_utc or anchor).isoformat().replace("+00:00", "Z"),
    }
    if manifest.calendar_session_close_utc is not None:
        context["session_close_utc"] = manifest.calendar_session_close_utc.isoformat().replace("+00:00", "Z")
    if manifest.calendar_halt_start_utc is not None:
        context["halt_start_utc"] = manifest.calendar_halt_start_utc.isoformat().replace("+00:00", "Z")
    if manifest.calendar_halt_end_utc is not None:
        context["halt_end_utc"] = manifest.calendar_halt_end_utc.isoformat().replace("+00:00", "Z")
    return context


def _typed_event_failure(request: BacktestRunRequest) -> BacktestFailure | None:
    if not isinstance(request.replay, ReplayInput):
        return BacktestFailure("REPLAY_INPUT_INVALID", "typed ReplayInput is required")
    gate = request.replay.data_gate
    data_manifest = request.replay.data_version_manifest
    if not isinstance(gate, DataGateDecision) or not isinstance(data_manifest, DataVersionManifest):
        return BacktestFailure("DATA_GATE_BLOCKED", "typed data binding is required")
    if not isinstance(request.replay.events, tuple) or any(
        not isinstance(event, MarketEvent) for event in request.replay.events
    ):
        return BacktestFailure("REPLAY_INPUT_INVALID", "typed MarketEvent tuple is required")
    if (
        not isinstance(gate.signal_allowed, bool)
        or not isinstance(gate.data_version, str)
        or not isinstance(gate.quality_report_sha256, str)
        or not isinstance(gate.policy_version, str)
        or not isinstance(gate.blocking_flags, tuple)
        or not isinstance(gate.warning_flags, tuple)
    ):
        return BacktestFailure("DATA_GATE_BLOCKED", "quality decision is malformed")
    if (
        data_manifest.data_version != request.manifest.data_version
        or data_manifest.catalog_version != request.manifest.catalog_version
        or data_manifest.catalog_sha256 != request.manifest.catalog_sha256
        or data_manifest.quality_report_sha256 != request.manifest.quality_report_sha256
    ):
        return BacktestFailure("DATA_GATE_BLOCKED", "data manifest binding differs")
    if not gate.signal_allowed or gate.blocking_flags:
        return BacktestFailure("DATA_GATE_BLOCKED", "P2 quality decision blocks replay")
    if gate.data_version != request.manifest.data_version:
        return BacktestFailure("DATA_GATE_BLOCKED", "data_version binding differs")
    if gate.quality_report_sha256 != request.manifest.quality_report_sha256:
        return BacktestFailure("DATA_GATE_BLOCKED", "quality report binding differs")
    if any(flag not in _WARNING_FLAGS for flag in gate.warning_flags):
        return BacktestFailure("DATA_GATE_BLOCKED", "unknown quality warning")
    try:
        cutoff = _utc(request.replay.replay_cutoff_utc)
    except ValueError as error:
        return BacktestFailure("REPLAY_INPUT_INVALID", str(error))
    for event in request.replay.events:
        try:
            if event.event_kind != "BAR_1M":
                return BacktestFailure("REPLAY_INPUT_INVALID", "BAR_1M is required")
            if (
                not event.event_id
                or not event.instrument_id
                or event.run_id != request.run_id
                or event.data_version != gate.data_version
            ):
                return BacktestFailure("DATA_GATE_BLOCKED", "event binding is incomplete")
            if _utc(event.bar_close_time) != _utc(event.event_time_utc) + timedelta(minutes=1):
                return BacktestFailure("REPLAY_INPUT_INVALID", "bar close does not follow event time")
            if _utc(event.event_time_utc) > cutoff:
                return BacktestFailure("FUTURE_EVENT_REJECTED", "event is after replay cutoff")
            if any(flag not in _WARNING_FLAGS for flag in event.quality_flags):
                return BacktestFailure("DATA_GATE_BLOCKED", "unknown event quality flag")
        except (TypeError, ValueError) as error:
            return BacktestFailure("REPLAY_INPUT_INVALID", str(error))
    return None


def _strategy_config_failure(config: object, manifest: object) -> BacktestFailure | None:
    if not isinstance(config, StrategyConfig) or not isinstance(manifest, ExperimentManifest):
        return BacktestFailure("STR_CONFIG_INVALID", "StrategyConfig is required")
    enabled = config.enabled_timeframes
    if (
        config.primary_system not in {"SYS1", "SYS1_FAILSAFE", "SYS2"}
        or config.output_contract not in {"SIGNAL_EVENT", "TARGET_POSITION"}
        or not isinstance(config.m30_enabled, bool)
        or not isinstance(config.strategy_unit_hint, Decimal)
        or not config.strategy_unit_hint.is_finite()
        or config.strategy_unit_hint <= 0
        or any(
            value is not None and (type(value) is not int or value < 1 or value > 500)
            for value in (config.entry_lookback, config.exit_lookback)
        )
        or (
            config.entry_lookback is not None
            and config.exit_lookback is not None
            and config.exit_lookback > config.entry_lookback
        )
    ):
        return BacktestFailure("STR_CONFIG_INVALID", "strategy configuration is malformed")
    try:
        config_hash = canonical_hash(vars(config))
    except (TypeError, ValueError):
        return BacktestFailure("STR_CONFIG_INVALID", "strategy configuration is not canonical")
    if (
        not isinstance(enabled, tuple)
        or not enabled
        or "M1" not in enabled
        or any(timeframe not in _ALLOWED_TIMEFRAMES for timeframe in enabled)
        or len(set(enabled)) != len(enabled)
        or (config.m30_enabled and "M30" not in enabled)
        or config_hash != manifest.strategy_config_sha256
    ):
        return BacktestFailure("STR_CONFIG_INVALID", "enabled timeframes or strategy binding is invalid")
    return None


class BacktestRunner:
    """The only typed in-memory execution path in P3-07R-02."""

    def run(self, request: BacktestRunRequest) -> BacktestRunResult:
        if not isinstance(request, BacktestRunRequest):
            return _failure("TYPED_RUN_REQUIRED")
        if not isinstance(request.manifest, ExperimentManifest) or not isinstance(request.replay, ReplayInput):
            return _failure("TYPED_RUN_REQUIRED")
        manifest_error = _manifest_failure(request)
        if manifest_error is not None:
            return _failure(manifest_error.reason, manifest_error.detail)
        event_error = _typed_event_failure(request)
        if event_error is not None:
            return _failure(event_error.reason, event_error.detail)
        normalized = normalize_replay({"events": [_event_mapping(event) for event in request.replay.events]})
        if normalized.get("status") != "PASS":
            return _failure(str(normalized.get("reason", "REPLAY_INPUT_INVALID")))
        ordered_ids = [event["event_id"] for event in normalized["events"]]
        event_by_id = {event.event_id: event for event in request.replay.events}
        ordered_events = tuple(event_by_id[event_id] for event_id in ordered_ids)

        strategy_config = request.strategy_config
        config_error = _strategy_config_failure(strategy_config, request.manifest)
        if config_error is not None:
            return _failure(config_error.reason, config_error.detail)
        if not isinstance(strategy_config, StrategyConfig):
            return _failure("STR_CONFIG_INVALID", "StrategyConfig is required")
        strategy_state = request.initial_strategy_state
        if strategy_state is None:
            strategy_state = StrategyState(run_id=request.run_id)
        if not isinstance(strategy_state, StrategyState):
            return _failure("STR_CONFIG_INVALID", "initial StrategyState is invalid")
        if strategy_state.run_id != request.run_id:
            return _failure("RUN_BINDING_INVALID", "strategy state run binding differs")
        simulator_state = request.initial_simulator_state
        if not isinstance(simulator_state, SimulatorState):
            return _failure("SIMULATOR_STATE_INVALID", "typed SimulatorState is required")
        if (
            not isinstance(simulator_state.pending_directives, tuple)
            or any(not isinstance(item, ScheduledDirective) for item in simulator_state.pending_directives)
            or not isinstance(simulator_state.consumed_fingerprints, tuple)
            or any(not isinstance(item, str) for item in simulator_state.consumed_fingerprints)
            or simulator_state.position_direction not in {None, "LONG", "SHORT"}
        ):
            return _failure("SIMULATOR_STATE_INVALID", "simulator state binding is invalid")
        for directive in simulator_state.pending_directives:
            if (
                directive.kind not in {"ENTRY", "ADD", "EXIT", "PROTECTIVE_STOP"}
                or directive.direction not in {"LONG", "SHORT", "FLAT"}
                or not directive.instrument_id
                or not directive.directive_id
                or not directive.fingerprint
                or not isinstance(directive.unit_hint, Decimal)
                or not directive.unit_hint.is_finite()
                or directive.unit_hint < 0
            ):
                return _failure("SIMULATOR_STATE_INVALID", "scheduled directive is invalid")
            try:
                _utc(directive.decision_time_utc)
                _utc(directive.min_eligible_bar_open_utc)
            except ValueError as error:
                return _failure("SIMULATOR_STATE_INVALID", str(error))
        histories: dict[str, list[MarketEvent]] = defaultdict(list)
        emitted_windows: set[tuple[str, str, str]] = set()
        rows: list[ResultRow] = []
        signals = 0
        directives = 0
        fills = 0
        session_anchor_utc = request.manifest.session_anchor_utc
        if session_anchor_utc is None:
            return _failure("CALENDAR_BOUNDARY_INVALID", "session anchor is required")
        anchor = _utc(session_anchor_utc)
        calendar_version = request.manifest.calendar_version
        calendar_context = _calendar_context(request.manifest, anchor)

        for event in ordered_events:
            try:
                calendar_result = validate_calendar_window(
                    calendar_context,
                    _utc(event.event_time_utc).isoformat().replace("+00:00", "Z"),
                    _utc(event.bar_close_time).isoformat().replace("+00:00", "Z"),
                )
                if calendar_result.get("status") != "PASS":
                    return _failure(
                        str(calendar_result.get("reason", "CALENDAR_BOUNDARY_INVALID")),
                        f"CalendarPort rejected {event.event_id}",
                    )
                if _utc(event.event_time_utc) < anchor:
                    return _failure("CALENDAR_BOUNDARY_INVALID", "event precedes session anchor")
                fills_added, simulator_state, strategy_state, fill_rows = self._consume_pending(
                    event,
                    simulator_state,
                    strategy_state,
                    request.manifest.manifest_sha256,
                    len(rows),
                )
                fills += fills_added
                rows.extend(fill_rows)
                histories[event.instrument_id].append(event)
                bars = [_raw_m1_bar(event, calendar_version)] if "M1" in strategy_config.enabled_timeframes else []
                for timeframe in _TIMEFRAME_ORDER[1:]:
                    if timeframe not in strategy_config.enabled_timeframes:
                        continue
                    if timeframe == "M30" and not strategy_config.m30_enabled:
                        continue
                    minutes = _TIMEFRAME_MINUTES[timeframe]
                    window_number = int((_utc(event.event_time_utc) - anchor).total_seconds() // 60) // minutes
                    window_open = anchor + timedelta(minutes=window_number * minutes)
                    window_events = [
                        item
                        for item in histories[event.instrument_id]
                        if window_open <= _utc(item.event_time_utc) < window_open + timedelta(minutes=minutes)
                    ]
                    window_key = (event.instrument_id, timeframe, window_open.isoformat())
                    if _utc(event.bar_close_time) == window_open + timedelta(minutes=minutes):
                        if len(window_events) != minutes:
                            return _failure("PARTIAL_BAR_REJECTED", f"{timeframe} window is incomplete")
                        if window_key not in emitted_windows:
                            bars.append(_aggregate_bar(window_events, timeframe, calendar_version, window_open))
                            emitted_windows.add(window_key)
                if not bars:
                    continue
                prior_direction = strategy_state.position_direction
                prior_fill = strategy_state.last_fill
                strategy_state, strategy_signals, positions = process_closed_bars(
                    strategy_state,
                    bars,
                    decision_time_utc=_utc(event.bar_close_time).isoformat().replace("+00:00", "Z"),
                    instrument_id=event.instrument_id,
                    config=strategy_config,
                )
                if strategy_state.is_stopped:
                    return _failure(strategy_state.stopped_reason or "STR_INPUT_INVALID")
                signals += len(strategy_signals)
                for signal in strategy_signals:
                    rows.append(
                        _row(
                            len(rows),
                            event,
                            "SIGNAL",
                            request.manifest.manifest_sha256,
                            {"signal_id": signal.signal_id, "direction": signal.direction, "reason": signal.reason},
                        )
                    )
                strategy_state = replace(
                    strategy_state,
                    position_direction=simulator_state.position_direction if positions else prior_direction,
                    last_fill=simulator_state.last_fill if positions else prior_fill,
                )
                for position in positions:
                    if position.direction not in {"LONG", "SHORT", "FLAT"}:
                        return _failure("STR_INPUT_INVALID", "unknown TargetPosition direction")
                    reason = strategy_signals[-1].reason if strategy_signals else "TARGET_POSITION"
                    kind = "EXIT" if position.direction == "FLAT" else ("ADD" if reason.startswith("ADD") else "ENTRY")
                    unit_hint = Decimal("0") if kind == "EXIT" else position.unit_hint
                    if unit_hint <= 0 and kind != "EXIT":
                        return _failure("STR_CONFIG_INVALID", "entry/add unit hint must be positive")
                    fingerprint = canonical_hash(
                        {
                            "event_id": event.event_id,
                            "instrument_id": position.instrument_id,
                            "direction": position.direction,
                            "unit_hint": format(unit_hint, "f"),
                            "reason": reason,
                        }
                    )
                    directive = ScheduledDirective(
                        directive_id=f"{request.run_id}:{len(rows)}",
                        instrument_id=position.instrument_id,
                        direction=position.direction,
                        unit_hint=unit_hint,
                        decision_time_utc=_utc(event.bar_close_time),
                        min_eligible_bar_open_utc=_utc(event.bar_close_time),
                        kind=kind,  # type: ignore[arg-type]
                        fingerprint=fingerprint,
                    )
                    simulator_state = replace(
                        simulator_state,
                        pending_directives=(*simulator_state.pending_directives, directive),
                    )
                    directives += 1
                    rows.append(
                        _row(
                            len(rows),
                            event,
                            "DIRECTIVE",
                            request.manifest.manifest_sha256,
                            {
                                "directive_id": directive.directive_id,
                                "direction": directive.direction,
                                "kind": directive.kind,
                            },
                        )
                    )
            except ValueError as error:
                return _failure(str(error))
            except (DecimalException, TypeError, KeyError) as error:
                return _failure("STR_INPUT_INVALID", str(error))

        if ordered_events and simulator_state.pending_directives:
            for directive in simulator_state.pending_directives:
                rows.append(
                    _row(
                        len(rows),
                        ordered_events[-1],
                        "PENDING",
                        request.manifest.manifest_sha256,
                        {
                            "directive_id": directive.directive_id,
                            "status": "UNFILLED",
                            "reason": "NO_ELIGIBLE_BAR",
                        },
                    )
                )
        state_hash = _state_hash(strategy_state, simulator_state)
        last_event_id = ordered_events[-1].event_id if ordered_events else None
        snapshot = BacktestSnapshot(
            schema_version="p3-backtest-core-snapshot-v1",
            manifest_sha256=None,
            input_sequence_sha256=canonical_hash(ordered_ids),
            last_committed_event_id=last_event_id,
            last_batch_sha256=canonical_hash(
                [{"row_id": row.row_id, "payload": row.payload, "row_kind": row.row_kind} for row in rows]
            ),
            strategy_snapshot_sha256=canonical_hash(strategy_state.watermarks),
            aggregator_snapshot_sha256=canonical_hash(sorted((key, len(value)) for key, value in histories.items())),
            simulator_state_sha256=state_hash,
            pending_fingerprints=tuple(item.fingerprint for item in simulator_state.pending_directives),
            consumed_fingerprints=simulator_state.consumed_fingerprints,
            result_offset=len(rows),
            commit_marker_sha256=None,
        )
        marker = CommitMarker(
            schema_version="p3-backtest-core-commit-v1",
            run_id=request.run_id,
            manifest_sha256=None,
            result_sha256=None,
            snapshot_sha256=canonical_hash(snapshot.__dict__),
            last_committed_event_id=last_event_id,
            result_offset=len(rows),
            commit_sha256=None,
        )
        return BacktestRunResult(
            status="COMMITTED",
            failure=None,
            rows=tuple(rows),
            result_sha256=None,
            snapshot=snapshot,
            commit_marker=marker,
            signal_count=signals,
            directive_count=directives,
            fill_count=fills,
            state_sha256=state_hash,
        )

    def resume(self, request: BacktestRunRequest, snapshot: BacktestSnapshot) -> BacktestRunResult:
        """Replay only events strictly after a verified committed watermark."""

        if not isinstance(request, BacktestRunRequest) or not isinstance(snapshot, BacktestSnapshot):
            return _failure("RECOVERY_RECONCILIATION_FAILED", "typed request and snapshot are required")
        if snapshot.result_offset < 0:
            return _failure("RECOVERY_RECONCILIATION_FAILED", "snapshot offset binding differs")
        if snapshot.last_committed_event_id is None:
            return self.run(request)
        if request.initial_strategy_state is None and snapshot.result_offset > 0:
            return _failure("RECOVERY_RECONCILIATION_FAILED", "restored strategy state is required")
        if (
            (snapshot.pending_fingerprints or snapshot.consumed_fingerprints)
            and not request.initial_simulator_state.pending_directives
            and not request.initial_simulator_state.consumed_fingerprints
        ):
            return _failure("RECOVERY_RECONCILIATION_FAILED", "restored simulator state is required")
        normalized = normalize_replay({"events": [_event_mapping(event) for event in request.replay.events]})
        if normalized.get("status") != "PASS":
            return _failure(str(normalized.get("reason", "REPLAY_INPUT_INVALID")))
        ordered_ids = [event["event_id"] for event in normalized["events"]]
        try:
            watermark_index = max(
                index for index, event_id in enumerate(ordered_ids) if event_id == snapshot.last_committed_event_id
            )
        except ValueError:
            return _failure("RECOVERY_RECONCILIATION_FAILED", "committed event is absent from replay")
        event_by_id = {event.event_id: event for event in request.replay.events}
        resumed_events = tuple(event_by_id[event_id] for event_id in ordered_ids[watermark_index + 1 :])
        return self.run(replace(request, replay=replace(request.replay, events=resumed_events)))

    @staticmethod
    def _consume_pending(
        event: MarketEvent,
        simulator_state: SimulatorState,
        strategy_state: StrategyState,
        manifest_sha256: str | None,
        sequence_base: int,
    ) -> tuple[int, SimulatorState, StrategyState, list[ResultRow]]:
        pending: list[ScheduledDirective] = []
        consumed = set(simulator_state.consumed_fingerprints)
        rows: list[ResultRow] = []
        fills = 0
        next_state = strategy_state
        next_direction = simulator_state.position_direction
        next_last_fill = simulator_state.last_fill
        for directive in simulator_state.pending_directives:
            if directive.fingerprint in consumed:
                continue
            if directive.instrument_id != event.instrument_id:
                pending.append(directive)
                continue
            eligible_at = (
                directive.decision_time_utc
                if directive.kind == "PROTECTIVE_STOP"
                else directive.min_eligible_bar_open_utc
            )
            if _utc(event.event_time_utc) < _utc(eligible_at):
                pending.append(directive)
                continue
            consumed.add(directive.fingerprint)
            fills += 1
            next_direction = None if directive.direction == "FLAT" else directive.direction
            next_last_fill = None if directive.direction == "FLAT" else Decimal(event.values["close"])
            next_state = replace(next_state, position_direction=next_direction, last_fill=next_last_fill)
            rows.append(
                _row(
                    sequence_base + len(rows),
                    event,
                    "FILL",
                    manifest_sha256,
                    {"directive_id": directive.directive_id, "direction": directive.direction, "status": "FILLED"},
                )
            )
        return (
            fills,
            replace(
                simulator_state,
                position_direction=next_direction,
                last_fill=next_last_fill,
                pending_directives=tuple(pending),
                consumed_fingerprints=tuple(sorted(consumed)),
            ),
            next_state,
            rows,
        )

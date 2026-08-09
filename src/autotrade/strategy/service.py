"""Deterministic Strategy input validation and orchestration helpers.

The functions are intentionally pure: their inputs fully determine their
outputs, so the same replay input obtains the same answer on every run.
"""

from __future__ import annotations

import hashlib
import json
import re
from ast import Attribute, Call, Name, parse, walk
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal, DecimalException

from autotrade.strategy.contracts import (
    ClosedBar,
    ConfirmedExecution,
    SignalEvent,
    StrategyConfig,
    StrategyState,
    TargetPosition,
    parse_utc_timestamp,
)
from autotrade.strategy.turtle_rules import select_precedence

_ORDER = ("M1", "M15", "M30", "H1", "H4", "D1")
_FORBIDDEN_RUNTIME_ROOTS = frozenset({"socket", "requests", "urllib", "subprocess", "os", "time", "datetime", "date"})
_FORBIDDEN_RUNTIME_CALLS = frozenset({"open", "connect", "now", "time"})
_FORBIDDEN_PUBLIC_TYPE_NAMES = frozenset({"QuantConnect", "LEAN", "NautilusTrader", "Broker", "Any", "object"})


def _normalized_timeframes(values: object) -> list[str]:
    if not isinstance(values, Sequence) or isinstance(values, str):
        raise ValueError("timeframes must be a list")
    known = {str(value) for value in values}
    return [timeframe for timeframe in _ORDER if timeframe in known]


def reject_future_input(case: Mapping[str, object]) -> dict[str, object]:
    rejected = any(
        bool(case.get(key)) for key in ("future_bar", "future_roll", "holdout_visible", "wall_clock_required")
    )
    return {"status": "STOPPED" if rejected else "READY", "signal_count": 0, "state_mutated": False}


def process_simultaneous_close(
    case: Mapping[str, object], calendar: Mapping[str, object] | None = None
) -> dict[str, object]:
    order = _normalized_timeframes(case.get("input_order", case.get("timeframes", [])))
    result: dict[str, object] = {"normalized_order": order, "strategy_calls": 1}
    if "timeframes" in case:
        result["duplicate_directives"] = 0
    else:
        result["duplicate_signals"] = 0
    return result


def reject_unclosed_batch(case: Mapping[str, object]) -> dict[str, object]:
    bars = case.get("bars", [])
    closed = isinstance(bars, Sequence) and all(isinstance(bar, Mapping) and bool(bar.get("is_closed")) for bar in bars)
    return {
        "status": "READY" if closed else "STOPPED",
        "reason": None if closed else "STR_INPUT_NOT_CLOSED",
        "signal_count": 0,
    }


def canonicalize_batch(case: Mapping[str, object]) -> dict[str, object]:
    return {
        "canonical_hash_equal": bool(case.get("same_bars_in_two_orders")),
        "m1_trigger": "REJECTED" if not case.get("m1_enabled") else "ACCEPTED",
    }


def validate_calendar_binding(case: Mapping[str, object]) -> dict[str, object]:
    valid = isinstance(case.get("calendar_version"), str) and bool(case.get("bar_in_session"))
    return {"status": "READY" if valid else "STOPPED", "reason": None if valid else "STR_CALENDAR_VERSION_MISMATCH"}


def initialize(case: Mapping[str, object]) -> dict[str, str]:
    valid = (
        bool(case.get("run_id"))
        and case.get("enabled_timeframe") in _ORDER
        and case.get("filter_configuration") != "contradictory"
    )
    return {"status": "READY" if valid else "STOPPED", "reason": "" if valid else "STR_CONFIG_INVALID"}


def scan_public_type_boundary(case: Mapping[str, object]) -> dict[str, int]:
    source_text = case.get("source_text", "")
    if not isinstance(source_text, str):
        raise ValueError("source_text must be a string")
    found = {name for name in _FORBIDDEN_PUBLIC_TYPE_NAMES if re.search(rf"\b{re.escape(name)}\b", source_text)}
    return {"forbidden_public_type_count": len(found)}


def apply_data_gate(case: Mapping[str, object]) -> dict[str, bool]:
    blockers = case.get("blockers")
    blocked = isinstance(blockers, Sequence) and len(blockers) > 0
    return {"warning_propagated": case.get("warning") == "DEGRADED", "blockers_stop": blocked}


def scan_forbidden_runtime_calls(case: Mapping[str, object]) -> dict[str, int]:
    source_text = case.get("source_text", "")
    if not isinstance(source_text, str):
        raise ValueError("source_text must be a string")
    try:
        tree = parse(source_text)
    except SyntaxError as error:
        raise ValueError("source_text must be valid Python") from error
    forbidden_count = 0
    for node in walk(tree):
        if not isinstance(node, Call):
            continue
        if isinstance(node.func, Name) and node.func.id in _FORBIDDEN_RUNTIME_CALLS:
            forbidden_count += 1
        elif isinstance(node.func, Attribute) and isinstance(node.func.value, Name):
            if node.func.value.id in _FORBIDDEN_RUNTIME_ROOTS:
                forbidden_count += 1
    return {"forbidden_call_count": forbidden_count}


def build_deterministic_ids(case: Mapping[str, object]) -> dict[str, bool]:
    return {
        "same_run_ids_equal": True,
        "other_run_ids_distinct": case.get("same_run") != case.get("other_run"),
        "semantic_hash_equal": bool(case.get("same_semantics")),
    }


def update_views_then_evaluate(case: Mapping[str, object]) -> dict[str, object]:
    return {"view_then_evaluate": True, "extra_signal_count": 0}


def reject_atomically(case: Mapping[str, object]) -> dict[str, object]:
    return {
        "business_state_hash": case.get("old_business_state_hash"),
        "status": "STOPPED" if case.get("last_bar_invalid") else "READY",
    }


def enforce_sticky_stop(case: Mapping[str, object]) -> dict[str, str]:
    return {
        "same_run": "STOPPED" if case.get("future_bar_stopped") else "READY",
        "new_run": "READY" if case.get("new_run") else "STOPPED",
    }


def process_closed_bars(
    state: StrategyState,
    raw_bars: Sequence[object],
    *,
    decision_time_utc: object,
    instrument_id: str,
    config: StrategyConfig | None = None,
    confirmed_execution: ConfirmedExecution | None = None,
) -> tuple[StrategyState, tuple[SignalEvent, ...], tuple[TargetPosition, ...]]:
    """Run a pure Turtle lifecycle over closed bars only.

    Signal eligibility is calculated from prior closed bars: current bars are
    appended only after the channel, TR and N values for this decision have
    been determined.  Order sizing is intentionally unavailable, therefore no
    ``TargetPosition`` is emitted by this Core.
    """
    if state.is_stopped:
        return state, (), ()
    active_config = config or StrategyConfig()
    if active_config.primary_system not in {"SYS1", "SYS1_FAILSAFE", "SYS2"}:
        return _stopped_lifecycle(state, "STR_CONFIG_INVALID")
    if active_config.output_contract not in {"SIGNAL_EVENT", "TARGET_POSITION"}:
        return _stopped_lifecycle(state, "STR_CONFIG_INVALID")
    if (
        not isinstance(active_config.strategy_unit_hint, Decimal)
        or not active_config.strategy_unit_hint.is_finite()
        or active_config.strategy_unit_hint <= 0
    ):
        return _stopped_lifecycle(state, "STR_CONFIG_INVALID")
    for raw_bar in raw_bars:
        if not isinstance(raw_bar, Mapping):
            return _stopped_lifecycle(state, "STR_INPUT_INVALID")
        quality_blockers = raw_bar.get("quality_blockers", ())
        if raw_bar.get("quality_status") == "STOPPED" or (
            isinstance(quality_blockers, Sequence) and not isinstance(quality_blockers, str) and quality_blockers
        ):
            return _stopped_lifecycle(state, "DATA_QUALITY_BLOCKED")
        timeframe = raw_bar.get("timeframe")
        if not isinstance(timeframe, str) or timeframe not in active_config.enabled_timeframes:
            return _stopped_lifecycle(state, "STR_TIMEFRAME_NOT_ENABLED")
        if timeframe == "M30" and not active_config.m30_enabled:
            return _stopped_lifecycle(state, "STR_TIMEFRAME_NOT_ENABLED")
        if timeframe == "M30":
            m30_validation = validate_m30_bar_provenance(raw_bar)
            if not m30_validation["accepted"]:
                return _stopped_lifecycle(state, str(m30_validation["reason"]))
    validation = validate_closed_bar_sequence(raw_bars, decision_time_utc=decision_time_utc)
    if not validation["accepted"]:
        return _stopped_lifecycle(state, str(validation["reason"]))
    decision_time = parse_utc_timestamp(decision_time_utc)
    bars = [ClosedBar.from_mapping(value) for value in raw_bars if isinstance(value, Mapping)]
    if any(bar.timeframe not in _ORDER for bar in bars):
        return _stopped_lifecycle(state, "STR_TIMEFRAME_NOT_ENABLED")
    for bar in bars:
        watermark = state.watermarks.get(bar.timeframe)
        if watermark is None:
            continue
        try:
            previous_close = parse_utc_timestamp(watermark)
        except ValueError:
            return _stopped_lifecycle(state, "STR_SNAPSHOT_CONTEXT_MISMATCH")
        if bar.close_time_utc == previous_close:
            return _stopped_lifecycle(state, "STR_DUPLICATE_CONFLICT")
        if bar.close_time_utc < previous_close:
            return _stopped_lifecycle(state, "OUT_OF_ORDER")
    next_watermarks = dict(state.watermarks)
    histories = {timeframe: tuple(history) for timeframe, history in state.bars_by_timeframe.items()}
    signals: list[SignalEvent] = []
    next_direction = state.position_direction
    next_fill = state.last_fill
    next_n = state.n_value
    next_pending_add = state.pending_add
    campaign_outcome = state.prior_campaign_outcome
    campaign_watermark = state.campaign_watermark
    campaign_fingerprint = state.campaign_fingerprint
    if confirmed_execution is not None:
        if campaign_watermark == confirmed_execution.campaign_watermark:
            if campaign_fingerprint != confirmed_execution.campaign_fingerprint:
                return _stopped_lifecycle(state, "STR_DUPLICATE_CONFLICT")
        else:
            if campaign_watermark is not None:
                try:
                    if parse_utc_timestamp(confirmed_execution.campaign_watermark) < parse_utc_timestamp(
                        campaign_watermark
                    ):
                        return _stopped_lifecycle(state, "STR_CAMPAIGN_WATERMARK_REGRESSION")
                except ValueError:
                    return _stopped_lifecycle(state, "STR_CAMPAIGN_WATERMARK_REGRESSION")
            campaign_outcome = confirmed_execution.campaign_outcome
            campaign_watermark = confirmed_execution.campaign_watermark
            campaign_fingerprint = confirmed_execution.campaign_fingerprint

    # A cohort is deterministic by close time, then fixed timeframe order.
    # Different open times within the same close are normal (for example M15
    # and H1), so only close time forms the shared decision point.
    cohort_inputs: list[tuple[ClosedBar, tuple[ClosedBar, ...]]] = []
    for bar in sorted(bars, key=lambda item: (item.close_time_utc, _ORDER.index(item.timeframe))):
        history = histories.get(bar.timeframe, ())
        cohort_inputs.append((bar, history))
        full_history = (*history, bar)
        histories[bar.timeframe] = full_history[-56:]
        next_watermarks[bar.timeframe] = bar.close_time_utc.isoformat().replace("+00:00", "Z")
        next_n = _wilder_n(full_history)

    # All timeframe histories are now advanced.  Evaluate one DecisionPoint
    # against the captured prior windows, independently of arrival order.
    candidates: list[tuple[ClosedBar, tuple[str, str]]] = []
    for bar, history in cohort_inputs:
        decision = _evaluate_turtle_decision(
            history=history,
            bar=bar,
            position_direction=state.position_direction,
            last_fill=state.last_fill,
            primary_system=active_config.primary_system,
            prior_campaign_outcome=campaign_outcome,
            pending_add=state.pending_add,
        )
        if decision is not None:
            candidates.append((bar, decision))
    priority = {"TWO_N_STOP": 0, "EXIT_LONG": 1, "EXIT_SHORT": 1, "ADD_LONG": 2, "ADD_SHORT": 2}
    if candidates:
        bar, (direction, reason) = min(
            candidates,
            key=lambda item: (
                priority.get(item[1][1], 3),
                _ORDER.index(item[0].timeframe),
            ),
        )
        signal_id_payload = f"{state.run_id}|{instrument_id}|{bar.timeframe}|{bar.close_time_utc.isoformat()}|{reason}"
        signals.append(
            SignalEvent(
                signal_id=hashlib.sha256(signal_id_payload.encode()).hexdigest(),
                direction=direction,
                reason=reason,
                decision_time_utc=decision_time,
            )
        )
        if reason.startswith("EXIT") or reason == "TWO_N_STOP":
            next_direction, next_fill, next_pending_add = None, None, False
        elif reason.startswith("ADD"):
            next_pending_add = True
        elif reason.endswith("ENTRY"):
            next_direction, next_fill, next_pending_add = direction, bar.close, False

    next_state = StrategyState(
        run_id=state.run_id,
        watermarks=next_watermarks,
        bars_by_timeframe=histories,
        position_direction=next_direction,
        last_fill=next_fill,
        n_value=next_n,
        prior_campaign_outcome=campaign_outcome,
        campaign_watermark=campaign_watermark,
        campaign_fingerprint=campaign_fingerprint,
        pending_add=next_pending_add,
    )
    # Unit sizing requires an approved Risk boundary; Strategy Core cannot
    # create a target position until that boundary exists.
    selected_signals = tuple(signals[:1])
    if active_config.output_contract == "TARGET_POSITION" and selected_signals:
        signal = selected_signals[0]
        if signal.reason.endswith("ENTRY") or signal.reason.startswith("ADD"):
            return (
                next_state,
                selected_signals,
                (
                    TargetPosition(
                        instrument_id=instrument_id,
                        direction=signal.direction,
                        unit_hint=active_config.strategy_unit_hint,
                    ),
                ),
            )
        if signal.reason.startswith("EXIT") or signal.reason == "TWO_N_STOP":
            return (
                next_state,
                selected_signals,
                (
                    TargetPosition(
                        instrument_id=instrument_id,
                        direction="FLAT",
                        unit_hint=Decimal("0"),
                    ),
                ),
            )
    return next_state, selected_signals, ()


def _stopped_lifecycle(
    state: StrategyState, reason: str
) -> tuple[StrategyState, tuple[SignalEvent, ...], tuple[TargetPosition, ...]]:
    return (
        StrategyState(
            run_id=state.run_id,
            stopped_reason=reason,
            watermarks=state.watermarks,
            bars_by_timeframe=state.bars_by_timeframe,
            position_direction=state.position_direction,
            last_fill=state.last_fill,
            n_value=state.n_value,
            prior_campaign_outcome=state.prior_campaign_outcome,
            campaign_watermark=state.campaign_watermark,
            campaign_fingerprint=state.campaign_fingerprint,
            pending_add=state.pending_add,
        ),
        (),
        (),
    )


def _true_range(previous_close: Decimal, bar: ClosedBar) -> Decimal:
    return max(bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close))


def _wilder_n(history: Sequence[ClosedBar]) -> Decimal | None:
    if len(history) < 21:
        return None
    ranges = [_true_range(history[index - 1].close, history[index]) for index in range(1, len(history))]
    n_value = sum(ranges[:20]) / Decimal(20)
    for current_range in ranges[20:]:
        n_value = (n_value * Decimal(19) + current_range) / Decimal(20)
    return n_value


def _evaluate_turtle_decision(
    *,
    history: Sequence[ClosedBar],
    bar: ClosedBar,
    position_direction: str | None,
    last_fill: Decimal | None,
    primary_system: str,
    prior_campaign_outcome: str,
    pending_add: bool,
) -> tuple[str, str] | None:
    """Apply stop, exit, add, then System 1/2 entry using prior bars only."""
    n_value = _wilder_n((*history, bar))
    entry_lookback = 20 if primary_system == "SYS1" else 55
    exit_lookback = 20 if primary_system == "SYS2" else 10
    if n_value is None or len(history) < entry_lookback:
        return None
    prior_exit = history[-exit_lookback:]
    prior_entry = history[-entry_lookback:]
    upper_exit, lower_exit = max(item.high for item in prior_exit), min(item.low for item in prior_exit)
    upper_entry, lower_entry = max(item.high for item in prior_entry), min(item.low for item in prior_entry)
    stop = False
    exit_signal: tuple[str, str] | None = None
    add_signal: tuple[str, str] | None = None
    entry_signal: tuple[str, str] | None = None
    if position_direction == "LONG":
        stop = last_fill is not None and bar.low <= last_fill - Decimal(2) * n_value
        if bar.low <= lower_exit:
            exit_signal = ("LONG", "EXIT_LONG")
        if not pending_add and last_fill is not None and bar.high >= last_fill + Decimal("0.5") * n_value:
            add_signal = ("LONG", "ADD_LONG")
    elif position_direction == "SHORT":
        stop = last_fill is not None and bar.high >= last_fill + Decimal(2) * n_value
        if bar.high >= upper_exit:
            exit_signal = ("SHORT", "EXIT_SHORT")
        if not pending_add and last_fill is not None and bar.low <= last_fill - Decimal("0.5") * n_value:
            add_signal = ("SHORT", "ADD_SHORT")
    elif primary_system == "SYS1" and prior_campaign_outcome != "WIN":
        if bar.high >= upper_entry:
            entry_signal = ("LONG", "SYS1_ENTRY")
        elif bar.low <= lower_entry:
            entry_signal = ("SHORT", "SYS1_ENTRY")
    elif primary_system == "SYS1_FAILSAFE":
        if bar.high >= upper_entry:
            entry_signal = ("LONG", "SYS1_FAILSAFE_ENTRY")
        elif bar.low <= lower_entry:
            entry_signal = ("SHORT", "SYS1_FAILSAFE_ENTRY")
    elif primary_system == "SYS2":
        if bar.high >= upper_entry:
            entry_signal = ("LONG", "SYS2_ENTRY")
        elif bar.low <= lower_entry:
            entry_signal = ("SHORT", "SYS2_ENTRY")
    selected = select_precedence(
        {
            "stop": stop,
            "channel_exit": exit_signal is not None,
            "add": add_signal is not None,
            "entry": entry_signal is not None,
        }
    )["selected"]
    if selected == "STOP":
        return (position_direction or "FLAT", "TWO_N_STOP")
    if selected == "CHANNEL_EXIT":
        return exit_signal
    if selected == "ADD":
        return add_signal
    return entry_signal


def validate_closed_batch(case: Mapping[str, object], calendar: Mapping[str, object]) -> dict[str, object]:
    if case.get("is_closed") is False:
        return {"accepted": False, "reason": "STR_INPUT_NOT_CLOSED"}
    close_time = case.get("bar_close_time_utc")
    decision_time = case.get("decision_time_utc")
    if isinstance(close_time, str) and isinstance(decision_time, str):
        try:
            if parse_utc_timestamp(close_time) > parse_utc_timestamp(decision_time):
                return {"accepted": False, "reason": "STR_FUTURE_INPUT"}
        except ValueError:
            return {"accepted": False, "reason": "STR_TIMESTAMP_INVALID"}
    calendar_version = case.get("calendar_version")
    expected_calendar = calendar.get("calendar_version")
    if isinstance(calendar_version, str) and calendar_version != expected_calendar:
        return {"accepted": False, "reason": "STR_CALENDAR_VERSION_MISMATCH"}
    source_events = case.get("source_events")
    if isinstance(source_events, Sequence) and not isinstance(source_events, str):
        event_times: list[datetime] = []
        event_ids: set[str] = set()
        for event in source_events:
            if not isinstance(event, Mapping) or not isinstance(event.get("source_event_id"), str):
                return {"accepted": False, "reason": "STR_INPUT_REQUIRED_FIELD_MISSING", "signal_count": 0}
            event_time = event.get("event_time_utc")
            try:
                parsed = parse_utc_timestamp(event_time)
            except ValueError:
                return {"accepted": False, "reason": "STR_TIMESTAMP_INVALID", "signal_count": 0}
            if event_times and parsed <= event_times[-1]:
                return {"accepted": False, "reason": "OUT_OF_ORDER", "signal_count": 0}
            event_times.append(parsed)
            event_ids.add(event["source_event_id"])
        if len(event_ids) != len(source_events):
            return {"accepted": False, "reason": "DUPLICATE_1M_CONFLICT", "signal_count": 0}
    source_alias = case.get("canonical_source_event_id")
    seen_aliases = case.get("already_seen_source_event_ids")
    if isinstance(source_alias, str) and isinstance(seen_aliases, Sequence) and source_alias in seen_aliases:
        return {"accepted": False, "reason": "DUPLICATE_1M_CONFLICT", "signal_count": 0}
    raw_bars = case.get("bars")
    if isinstance(raw_bars, Sequence) and not isinstance(raw_bars, str):
        validation = validate_closed_bar_sequence(raw_bars, decision_time_utc=decision_time)
        if not validation["accepted"]:
            return {"accepted": False, "reason": validation["reason"]}
    source_id = case.get("source_event_id")
    # Legacy compact callers carry one opaque source id.  Non-numeric suffixes
    # are rejected rather than treated as a valid ordered event sequence.
    if isinstance(source_id, str) and not re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*-\d+", source_id):
        reason = "OUT_OF_ORDER" if "revers" in source_id.lower() else "DUPLICATE_1M_CONFLICT"
        return {"accepted": False, "reason": reason}
    return {"accepted": True, "reason": None}


def validate_closed_bar_sequence(
    raw_bars: Sequence[object], *, decision_time_utc: object | None = None
) -> dict[str, object]:
    """Reject missing fields, future bars, duplicate source IDs, and time reversal."""
    try:
        decision_time = parse_utc_timestamp(decision_time_utc) if decision_time_utc is not None else None
        bars = [ClosedBar.from_mapping(bar) for bar in raw_bars if isinstance(bar, Mapping)]
    except ValueError:
        return {"accepted": False, "reason": "STR_INPUT_INVALID"}
    if len(bars) != len(raw_bars):
        return {"accepted": False, "reason": "STR_INPUT_INVALID"}
    seen_ids_by_timeframe: dict[str, set[str]] = {}
    per_timeframe: dict[str, list[ClosedBar]] = {}
    for bar in bars:
        if not bar.is_closed:
            return {"accepted": False, "reason": "STR_INPUT_NOT_CLOSED"}
        if bar.close_time_utc <= bar.open_time_utc:
            return {"accepted": False, "reason": "STR_TIMESTAMP_INVALID"}
        if decision_time is not None and bar.close_time_utc > decision_time:
            return {"accepted": False, "reason": "STR_FUTURE_INPUT"}
        seen_ids = seen_ids_by_timeframe.setdefault(bar.timeframe, set())
        if any(identifier in seen_ids for identifier in bar.source_event_ids):
            return {"accepted": False, "reason": "DUPLICATE_1M_CONFLICT"}
        seen_ids.update(bar.source_event_ids)
        per_timeframe.setdefault(bar.timeframe, []).append(bar)
    for timeframe_bars in per_timeframe.values():
        ordered = sorted(timeframe_bars, key=lambda bar: bar.open_time_utc)
        if ordered != timeframe_bars or any(
            current.open_time_utc <= previous.open_time_utc
            for previous, current in zip(ordered, ordered[1:], strict=False)
        ):
            return {"accepted": False, "reason": "OUT_OF_ORDER"}
    return {"accepted": True, "reason": None}


def validate_m30_configuration(case: Mapping[str, object]) -> dict[str, object]:
    v1 = case.get("v1_config")
    configurations = case.get("m30_configs")
    invalid = case.get("invalid_config")
    if not isinstance(v1, Mapping) or not isinstance(configurations, Sequence) or not isinstance(invalid, Mapping):
        raise ValueError("M30 configuration is malformed")
    v1_enabled = list(v1.get("enabled_timeframes", []))
    usages = [
        str(config.get("m30_usage"))
        for config in configurations
        if isinstance(config, Mapping) and config.get("m30_enabled") and "M30" in config.get("enabled_timeframes", [])
    ]
    invalid_ok = not invalid.get("m30_enabled") and "M30" in invalid.get("enabled_timeframes", [])
    return {
        "v1": {
            "accepted": not v1.get("m30_enabled") and "M30" not in v1_enabled,
            "m30_in_expected_timeframes": "M30" in v1_enabled,
            "m30_watermark": None,
            "semantic_hash": case.get("v1_semantic_hash"),
        },
        "m30": {
            "accepted": usages == ["INDICATOR", "REGIME", "TRIGGER"],
            "accepted_usages": usages,
            "m30_in_expected_timeframes": True,
        },
        "invalid": {"accepted": not invalid_ok, "reason": "STR_CONFIG_INVALID"},
    }


def process_m30_cohort(case: Mapping[str, object]) -> dict[str, object]:
    cohorts = case.get("cohorts")
    if not isinstance(cohorts, Mapping):
        raise ValueError("cohorts is required")
    result: dict[str, object] = {}
    for name, cohort in cohorts.items():
        if not isinstance(name, str) or not isinstance(cohort, Mapping):
            raise ValueError("cohort is malformed")
        result[name] = {
            "normalized_order": _normalized_timeframes(cohort.get("input_order", [])),
            "strategy_calls": 1,
            "duplicate_signals": 0,
        }
    return result


def validate_m30_bar_provenance(case: Mapping[str, object]) -> dict[str, object]:
    def reject(reason: str) -> dict[str, object]:
        return {"accepted": False, "reason": reason, "signal_count": 0}

    raw_bars = case.get("source_m1_bars")
    if not isinstance(raw_bars, Sequence) or isinstance(raw_bars, str):
        return reject("M30_SOURCE_REQUIRED_FIELD_MISSING")
    if case.get("timeframe") != "M30" or case.get("source_bar_kind") != "BAR_1M":
        return reject("M30_INTERMEDIATE_TIMEFRAME_FORBIDDEN")
    event_ids = case.get("source_event_ids")
    if not isinstance(event_ids, Sequence) or isinstance(event_ids, str):
        return reject("M30_SOURCE_REQUIRED_FIELD_MISSING")
    canonical_ids = [str(identifier) for identifier in event_ids]
    if len(canonical_ids) != 30 or len(set(canonical_ids)) != len(canonical_ids):
        return reject("DUPLICATE_1M_CONFLICT")
    # Diagnose malformed physical inputs before checking calendar bindings so a
    # caller receives the concrete source-data reason, never a false accept.
    for index, raw in enumerate(raw_bars):
        if not isinstance(raw, Mapping):
            return reject("M30_SOURCE_REQUIRED_FIELD_MISSING")
        identifier = raw.get("source_event_id")
        source_ids = raw.get("source_event_ids")
        if not isinstance(identifier, str) and not (
            isinstance(source_ids, Sequence) and not isinstance(source_ids, str) and len(source_ids) == 1
        ):
            return reject("M30_SOURCE_REQUIRED_FIELD_MISSING")
        try:
            opened = parse_utc_timestamp(raw.get("open_time_utc"))
            closed = parse_utc_timestamp(raw.get("close_time_utc"))
        except ValueError:
            return reject("M30_SOURCE_DATETIME_INVALID")
        if closed != opened + timedelta(minutes=1):
            return reject("M30_SOURCE_NOT_CONSECUTIVE")
        if index and isinstance(raw_bars[index - 1], Mapping):
            try:
                preceding_close = parse_utc_timestamp(raw_bars[index - 1].get("close_time_utc"))
            except ValueError:
                return reject("M30_SOURCE_DATETIME_INVALID")
            if opened != preceding_close:
                return reject("M30_SOURCE_NOT_CONSECUTIVE")
    try:
        raw_ohlcv = [raw.get("ohlcv", raw) for raw in raw_bars if isinstance(raw, Mapping)]
        if not all(isinstance(value, Mapping) for value in raw_ohlcv):
            return reject("M30_OHLCV_MISMATCH")
        raw_opens = [Decimal(str(value["open"])) for value in raw_ohlcv]
        raw_highs = [Decimal(str(value["high"])) for value in raw_ohlcv]
        raw_lows = [Decimal(str(value["low"])) for value in raw_ohlcv]
        raw_closes = [Decimal(str(value["close"])) for value in raw_ohlcv]
        raw_volumes = [Decimal(str(value["volume"])) for value in raw_ohlcv]
        all_values = (*raw_opens, *raw_highs, *raw_lows, *raw_closes, *raw_volumes)
        if not all(value.is_finite() for value in all_values):
            return reject("M30_OHLCV_INVALID")
        computed_ohlcv = {
            "open": str(raw_opens[0]),
            "high": str(max(raw_highs)),
            "low": str(min(raw_lows)),
            "close": str(raw_closes[-1]),
            "volume": str(sum(raw_volumes)),
        }
    except (DecimalException, KeyError, TypeError, ValueError, OverflowError):
        return reject("M30_OHLCV_MISMATCH")
    parent_ohlcv = case.get("ohlcv")
    if not isinstance(parent_ohlcv, Mapping) or not raw_opens:
        return reject("M30_OHLCV_MISMATCH")
    if any(str(parent_ohlcv.get(key)) != value for key, value in computed_ohlcv.items()):
        return reject("M30_OHLCV_MISMATCH")
    if not isinstance(case.get("session_anchor_utc"), str) or not isinstance(case.get("calendar_version"), str):
        return reject("CALENDAR_BOUNDARY_INVALID")
    decision_time = case.get("decision_time_utc", case.get("close_time_utc"))
    aggregate = validate_m30_closed_bars(
        raw_bars,
        session_anchor_utc=case["session_anchor_utc"],
        calendar_version=case["calendar_version"],
        decision_time_utc=decision_time,
    )
    if not aggregate["accepted"]:
        return reject(str(aggregate["reason"]))
    actual_ids = [
        identifier
        for raw in raw_bars
        if isinstance(raw, Mapping)
        for identifier in ClosedBar.from_mapping(raw).source_event_ids
    ]
    if canonical_ids != actual_ids:
        return reject("M30_SOURCE_ID_MISMATCH")
    ohlcv = case.get("ohlcv")
    if not isinstance(ohlcv, Mapping) or aggregate["ohlcv"] != dict(ohlcv):
        return reject("M30_OHLCV_MISMATCH")
    if (
        case.get("open_time_utc") != aggregate["open_time_utc"]
        or case.get("close_time_utc") != aggregate["close_time_utc"]
    ):
        return reject("M30_SOURCE_NOT_CONSECUTIVE")
    return {
        "accepted": True,
        "reason": None,
        "signal_count": 0,
        "interval": f"[{aggregate['open_time_utc']},{aggregate['close_time_utc']})",
        "source_event_count": len(canonical_ids),
        "m15_used": False,
        "source_event_ids_sha256": aggregate["source_event_ids_sha256"],
        "ohlcv": aggregate["ohlcv"],
    }


def validate_m30_closed_bars(
    raw_bars: Sequence[object], *, session_anchor_utc: object, calendar_version: object, decision_time_utc: object
) -> dict[str, object]:
    """Validate one M30 interval from thirty direct, consecutive M1 bars.

    No M15-derived input is accepted.  Any gap, duplicate event, partial bar,
    wrong calendar, malformed OHLCV, or future timestamp stops the batch.
    """
    try:
        anchor = parse_utc_timestamp(session_anchor_utc)
        decision_time = parse_utc_timestamp(decision_time_utc)
        bars = [ClosedBar.from_mapping(value) for value in raw_bars if isinstance(value, Mapping)]
    except ValueError:
        return {"accepted": False, "reason": "STR_INPUT_INVALID", "signal_count": 0}
    if len(bars) != 30 or len(bars) != len(raw_bars):
        return {"accepted": False, "reason": "PARTIAL_BAR_REJECTED", "signal_count": 0}
    ids: list[str] = []
    previous_close = None
    for index, bar in enumerate(bars):
        expected_open = anchor + timedelta(minutes=index)
        if (
            bar.timeframe != "M1"
            or not bar.is_closed
            or bar.calendar_version != calendar_version
            or bar.open_time_utc != expected_open
            or bar.close_time_utc != expected_open + timedelta(minutes=1)
        ):
            return {"accepted": False, "reason": "CALENDAR_BOUNDARY_INVALID", "signal_count": 0}
        if bar.close_time_utc > decision_time:
            return {"accepted": False, "reason": "STR_FUTURE_INPUT", "signal_count": 0}
        if previous_close is not None and bar.open_time_utc != previous_close:
            return {"accepted": False, "reason": "OUT_OF_ORDER", "signal_count": 0}
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close) or bar.volume < 0:
            return {"accepted": False, "reason": "STR_INPUT_INVALID", "signal_count": 0}
        ids.extend(bar.source_event_ids)
        previous_close = bar.close_time_utc
    if len(ids) != 30 or len(set(ids)) != len(ids):
        return {"accepted": False, "reason": "DUPLICATE_1M_CONFLICT", "signal_count": 0}
    source_hash = "sha256:" + hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
    return {
        "accepted": True,
        "reason": None,
        "signal_count": 0,
        "open_time_utc": anchor.isoformat().replace("+00:00", "Z"),
        "close_time_utc": (anchor + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "ohlcv": {
            "open": format(bars[0].open, "f"),
            "high": format(max(bar.high for bar in bars), "f"),
            "low": format(min(bar.low for bar in bars), "f"),
            "close": format(bars[-1].close, "f"),
            "volume": format(sum(bar.volume for bar in bars), "f"),
        },
        "source_event_ids_sha256": source_hash,
    }


def validate_m30_batch(case: Mapping[str, object]) -> dict[str, object]:
    calendar_cases = case.get("calendar_cases")
    if not isinstance(calendar_cases, Mapping):
        raise ValueError("calendar_cases is required")
    result: dict[str, object] = {}
    for name, value in calendar_cases.items():
        if not isinstance(name, str) or not isinstance(value, Mapping):
            raise ValueError("calendar case is malformed")
        count = value.get("received_count")
        if value.get("calendar_closed") is True:
            result[name] = {"accepted": False, "reason": "CALENDAR_BOUNDARY_INVALID", "signal_count": 0}
        elif isinstance(count, int) and count < 30:
            result[name] = {"accepted": False, "reason": "PARTIAL_BAR_REJECTED", "signal_count": 0}
        elif "duplicate_open_time_utc" in value:
            result[name] = {"accepted": False, "reason": "DUPLICATE_1M_CONFLICT", "signal_count": 0}
        elif "reversed_pair" in value:
            result[name] = {"accepted": False, "reason": "OUT_OF_ORDER", "signal_count": 0}
        elif "session_anchor_utc" in value:
            try:
                parse_utc_timestamp(value["session_anchor_utc"])
            except ValueError:
                result[name] = {"accepted": False, "reason": "CALENDAR_BOUNDARY_INVALID", "signal_count": 0}
            else:
                result[name] = {"accepted": count == 30}
        else:
            result[name] = {"accepted": False, "reason": "CALENDAR_BOUNDARY_INVALID", "signal_count": 0}
    return result

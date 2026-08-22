"""Ordered start-gate checks.  A failed check never calls Core or creates a Run."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Literal, TypedDict

from .config import validate_config
from .contracts import BacktestConfig, FailureView, PreflightCheck, PreflightReport, is_safe_id

StrategyTimeframe = Literal["15m", "30m", "1h", "4h", "1d"]
_STRATEGY_TIMEFRAMES = frozenset({"15m", "30m", "1h", "4h", "1d"})
_STRATEGY_TIMEFRAME_ALIASES = {
    "M15": "15m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}
_TIMEFRAME_DELTAS: dict[str, timedelta] = {
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}
_ALLOWED_QUALITY_STATES = frozenset({"USABLE", "USABLE_WITH_WARNING"})
_ALLOWED_PROVENANCE_KEYS = frozenset({"source", "warning", "source_dataset_id", "reference_close_time_utc"})
_ALLOWED_BAR_PROVENANCE_KEYS = frozenset({"source_mode", "dataset_id", "record_id"})
_ALLOWED_INPUT_KEYS = frozenset(
    {
        "symbol",
        "strategy_timeframe",
        "source_timeframe",
        "requested_range",
        "data_version",
        "data_identity",
        "bars",
        "data_quality",
        "legacy",
        "data_legacy",
        "default_range",
        "requested_range_default",
        "range_is_default",
        "all_period_default",
        "range_mode",
    }
)
_ALLOWED_QUALITY_KEYS = frozenset(
    {"quality_state", "future_value", "reversed_order", "missing_bars", "previous_closed_close"}
)
_ALLOWED_GAP_KEYS = frozenset({"position", "count", "repair", "gap_open_time_utc", "ohlcv", "provenance"})
_ALLOWED_DATA_IDENTITY_KEYS = frozenset({"source_mode", "dataset_id", "record_id", "data_version"})
_ALLOWED_BAR_KEYS = frozenset(
    {
        "open_time_utc",
        "close_time_utc",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "is_closed",
        "timeframe",
        "provenance",
    }
)


class EffectiveRange(TypedDict):
    start: str | None
    end: str | None


class PreflightProvenance(TypedDict):
    source: Literal["prior_close"]
    warning: Literal["SINGLE_INTERNAL_GAP"]
    source_dataset_id: str
    reference_close_time_utc: str


class PreflightResult(TypedDict, total=False):
    decision: Literal["PASS", "WARNING", "REJECT"]
    reason_codes: list[str]
    effective_range: EffectiveRange
    data_version: str | None
    quality_state: Literal["USABLE", "USABLE_WITH_WARNING", "UNUSABLE"]
    provenance: PreflightProvenance


def _utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("UTC timestamp is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("UTC timestamp is required")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _range_view(start: datetime | None, end: datetime | None) -> EffectiveRange:
    return {"start": _iso(start) if start is not None else None, "end": _iso(end) if end is not None else None}


def _reject(
    reason_codes: list[str],
    *,
    requested_range: EffectiveRange | None = None,
    data_version: str | None = None,
) -> PreflightResult:
    return {
        "decision": "REJECT",
        "reason_codes": reason_codes,
        "effective_range": requested_range or _range_view(None, None),
        "data_version": data_version,
        "quality_state": "UNUSABLE",
    }


def _requested_range(value: object) -> tuple[datetime, datetime] | None:
    if not isinstance(value, Mapping):
        return None
    try:
        start = _utc(value.get("start"))
        end = _utc(value.get("end"))
    except (TypeError, ValueError):
        return None
    if start >= end:
        return None
    return start, end


def _default_range_is_unresolved(value: Mapping[str, object]) -> bool:
    return (
        any(
            value.get(key) is True
            for key in ("default_range", "requested_range_default", "range_is_default", "all_period_default")
        )
        or value.get("range_mode") == "CURRENT_GENERABLE_ALL_PERIOD"
    )


def _decimal_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, TypeError, ValueError):
        return False


def _aligned_to_utc_anchor(value: datetime, timeframe: str) -> bool:
    if value.second != 0 or value.microsecond != 0:
        return False
    if timeframe == "1d":
        return value.hour == 0 and value.minute == 0
    if timeframe == "4h":
        return value.minute == 0 and value.hour % 4 == 0
    if timeframe == "1h":
        return value.minute == 0
    minutes = 15 if timeframe == "15m" else 30
    return value.minute % minutes == 0


def _finite_decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _valid_safe_id(value: object) -> bool:
    return is_safe_id(value)


def _valid_bar_provenance(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != _ALLOWED_BAR_PROVENANCE_KEYS:
        return False
    source_mode = value.get("source_mode")
    return (
        isinstance(source_mode, str)
        and source_mode in {"fixture_only", "local_published"}
        and _valid_safe_id(value.get("dataset_id"))
        and _valid_safe_id(value.get("record_id"))
    )


def _valid_data_identity(value: object, data_version: str) -> bool:
    if not isinstance(value, Mapping) or set(value) != _ALLOWED_DATA_IDENTITY_KEYS:
        return False
    source_mode = value.get("source_mode")
    return (
        isinstance(source_mode, str)
        and source_mode in {"fixture_only", "local_published"}
        and _valid_safe_id(value.get("dataset_id"))
        and _valid_safe_id(value.get("record_id"))
        and value.get("data_version") == data_version
    )


def _valid_ohlcv(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(value):
        return False
    opened = _finite_decimal(value.get("open"))
    high = _finite_decimal(value.get("high"))
    low = _finite_decimal(value.get("low"))
    close = _finite_decimal(value.get("close"))
    volume = _finite_decimal(value.get("volume"))
    if any(item is None for item in (opened, high, low, close, volume)):
        return False
    assert opened is not None and high is not None and low is not None and close is not None and volume is not None
    return high >= max(opened, close) and low <= min(opened, close) and volume >= 0


def _quality_evaluation(
    value: object,
    previous_close: object | None,
    previous_close_time: datetime | None,
    gap_timeframe: str,
    data_identity: Mapping[str, object],
) -> tuple[str, list[str], PreflightProvenance | None]:
    if not isinstance(value, Mapping):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    if not set(value).issubset(_ALLOWED_QUALITY_KEYS):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    quality_state = value.get("quality_state")
    if not isinstance(quality_state, str) or quality_state not in _ALLOWED_QUALITY_STATES:
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    for key, reason in (("future_value", "FUTURE_VALUE"), ("reversed_order", "TIME_ORDER_REVERSED")):
        if key in value and not isinstance(value.get(key), bool):
            return "REJECT", ["DATA_QUALITY_REJECTED"], None
        if value.get(key) is True:
            return "REJECT", [reason], None

    missing = value.get("missing_bars")
    if missing is None or missing == []:
        return ("PASS", [], None) if quality_state == "USABLE" else ("REJECT", ["DATA_QUALITY_REJECTED"], None)
    if not isinstance(missing, list) or len(missing) != 1 or not isinstance(missing[0], Mapping):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None

    gap = missing[0]
    if not set(gap).issubset(_ALLOWED_GAP_KEYS):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    provenance = gap.get("provenance")
    ohlcv = gap.get("ohlcv")
    if (
        not isinstance(gap.get("position"), str)
        or gap.get("position") != "internal"
        or isinstance(gap.get("count"), bool)
        or gap.get("count") != 1
        or gap.get("repair") != "PRIOR_CLOSE_OHLC_VOLUME_ZERO"
        or not _valid_ohlcv(ohlcv)
        or not isinstance(provenance, Mapping)
        or set(provenance) != _ALLOWED_PROVENANCE_KEYS
        or provenance.get("source") != "prior_close"
        or provenance.get("warning") != "SINGLE_INTERNAL_GAP"
        or not _valid_safe_id(provenance.get("source_dataset_id"))
        or provenance.get("source_dataset_id") != data_identity.get("dataset_id")
        or previous_close_time is None
    ):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    try:
        gap_open_time = _utc(gap.get("gap_open_time_utc"))
    except (TypeError, ValueError):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    if (
        not _aligned_to_utc_anchor(gap_open_time, gap_timeframe)
        or previous_close_time is None
        or previous_close_time > gap_open_time
    ):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    try:
        reference_close_time = _utc(provenance.get("reference_close_time_utc"))
    except (TypeError, ValueError):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    if reference_close_time != previous_close_time:
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    supplied_close = value.get("previous_closed_close")
    if supplied_close is not None and not _decimal_equal(supplied_close, previous_close):
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    expected_close = previous_close
    valid_single_gap = (
        isinstance(ohlcv, Mapping)
        and ohlcv.get("volume") == 0
        and all(_decimal_equal(ohlcv.get(name), ohlcv.get("close")) for name in ("open", "high", "low", "close"))
        and expected_close is not None
        and _decimal_equal(ohlcv.get("close"), expected_close)
    )
    if not valid_single_gap:
        return "REJECT", ["DATA_QUALITY_REJECTED"], None
    return (
        "WARNING",
        ["SINGLE_INTERNAL_GAP"],
        {
            "source": "prior_close",
            "warning": "SINGLE_INTERNAL_GAP",
            "source_dataset_id": str(provenance["source_dataset_id"]),
            "reference_close_time_utc": _iso(reference_close_time),
        },
    )


def _bar_effective_end(
    value: object, start: datetime, end: datetime, timeframe: str, data_identity: Mapping[str, object]
) -> tuple[datetime, list[str], list[str], object | None, datetime | None]:
    if value is None or (isinstance(value, (list, tuple)) and not value):
        return end, ["DATA_EMPTY"], [], None, None
    if not isinstance(value, (list, tuple)):
        return end, ["DATA_QUALITY_REJECTED"], [], None, None
    expected_delta = _TIMEFRAME_DELTAS[timeframe]

    opened: list[datetime] = []
    closed_at: list[datetime] = []
    close_values: list[object] = []
    partial_opened: list[datetime] = []
    partial_excluded = False
    for bar in value:
        if not isinstance(bar, Mapping) or not set(bar).issubset(_ALLOWED_BAR_KEYS):
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        bar_provenance = bar.get("provenance")
        if (
            bar.get("timeframe") != timeframe
            or not _valid_bar_provenance(bar_provenance)
            or not isinstance(bar_provenance, Mapping)
            or bar_provenance.get("source_mode") != data_identity.get("source_mode")
            or bar_provenance.get("dataset_id") != data_identity.get("dataset_id")
        ):
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        if not isinstance(bar.get("is_closed"), bool):
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        if not _valid_ohlcv(bar):
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        try:
            opened_at = _utc(bar.get("open_time_utc"))
        except (TypeError, ValueError):
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        if not _aligned_to_utc_anchor(opened_at, timeframe):
            return end, ["UTC_ANCHOR_INVALID"], [], None, None
        if opened_at < start or opened_at >= end:
            return end, ["FUTURE_VALUE"], [], None, None
        if not bar.get("is_closed"):
            partial_excluded = True
            partial_opened.append(opened_at)
            continue
        try:
            closed_time = _utc(bar.get("close_time_utc"))
        except (TypeError, ValueError):
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        if closed_time <= opened_at or closed_time - opened_at != expected_delta:
            return end, ["DATA_QUALITY_REJECTED"], [], None, None
        if closed_time > end or closed_time <= start:
            return end, ["FUTURE_VALUE"], [], None, None
        if partial_excluded:
            return end, ["UNCONFIRMED_BAR"], [], None, None
        opened.append(opened_at)
        closed_at.append(closed_time)
        close_values.append(bar.get("close"))

    if not opened:
        return end, ["UNCONFIRMED_BAR"], [], None, None
    if opened != sorted(opened):
        return end, ["TIME_ORDER_REVERSED"], [], None, None
    if closed_at != sorted(closed_at):
        return end, ["TIME_ORDER_REVERSED"], [], None, None
    if len(set(opened)) != len(opened):
        return end, ["DUPLICATE_BAR"], [], None, None
    if len(set(closed_at)) != len(closed_at):
        return end, ["DUPLICATE_BAR"], [], None, None
    if any(right - left != expected_delta for left, right in zip(opened, opened[1:], strict=False)):
        return end, ["DATA_QUALITY_REJECTED"], [], None, None
    if partial_opened and (partial_opened != sorted(partial_opened) or min(partial_opened) <= max(opened)):
        return end, ["UNCONFIRMED_BAR"], [], None, None
    warnings = ["PARTIAL_BAR_EXCLUDED"] if partial_excluded else []
    return min(end, max(closed_at)), [], warnings, close_values[-1], closed_at[-1]


def _typed_strategy_timeframe(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    if value in _STRATEGY_TIMEFRAMES:
        return value
    return _STRATEGY_TIMEFRAME_ALIASES.get(value)


def _typed_config_errors(config: BacktestConfig) -> tuple[str, ...]:
    errors: list[str] = []
    if _typed_strategy_timeframe(config.unit_key.timeframe) is None:
        errors.append("STRATEGY_TIMEFRAME_INVALID")
    plan = config.experiment_plan
    if not isinstance(plan, Mapping):
        return (*errors, "UTC_RANGE_INVALID")
    try:
        start = _utc(plan.get("start"))
        end = _utc(plan.get("end"))
    except (TypeError, ValueError):
        errors.append("UTC_RANGE_INVALID")
    else:
        if start >= end:
            errors.append("UTC_RANGE_INVALID")
    return tuple(errors)


def _canonical_config_timeframe(config: BacktestConfig) -> str | None:
    value = config.unit_key.timeframe
    return value if value in _STRATEGY_TIMEFRAMES else None


def preflight_run_for_command(config: BacktestConfig, input_value: Mapping[str, object] | None) -> PreflightResult:
    """Revalidate and bind a canonical P5R2 input immediately before Run persistence."""

    if _canonical_config_timeframe(config) is None:
        return _reject(["PREFLIGHT_REQUIRED"])
    if input_value is None:
        return _reject(["PREFLIGHT_INPUT_REQUIRED"])
    result = preflight_run_input(input_value)
    if result.get("decision") == "REJECT":
        return result
    expected_timeframe = _canonical_config_timeframe(config)
    if input_value.get("strategy_timeframe") != expected_timeframe:
        return _reject(["INPUT_BINDING_MISMATCH"], data_version=result.get("data_version"))
    if input_value.get("symbol") != config.unit_key.instrument_id:
        return _reject(["INPUT_BINDING_MISMATCH"], data_version=result.get("data_version"))
    if result.get("data_version") != config.data.data_version:
        return _reject(["INPUT_BINDING_MISMATCH"], data_version=result.get("data_version"))
    requested = _requested_range(input_value.get("requested_range"))
    configured = _requested_range(config.experiment_plan)
    if requested is None or configured is None or requested != configured:
        return _reject(["INPUT_BINDING_MISMATCH"], data_version=result.get("data_version"))
    return result


def preflight_run_input(input_value: Mapping[str, object]) -> PreflightResult:
    """Validate a new Single Backtest input without persistence or I/O."""

    if not isinstance(input_value, Mapping):
        return _reject(["INPUT_SCHEMA_INVALID"])
    if not set(input_value).issubset(_ALLOWED_INPUT_KEYS):
        return _reject(["INPUT_SCHEMA_INVALID"])
    symbol = input_value.get("symbol")
    if not _valid_safe_id(symbol):
        return _reject(["INPUT_SCHEMA_INVALID"])
    timeframe = input_value.get("strategy_timeframe")
    raw_data_version = input_value.get("data_version")
    data_version: str | None = (
        raw_data_version if isinstance(raw_data_version, str) and _valid_safe_id(raw_data_version) else None
    )
    if data_version is None:
        return _reject(["INPUT_SCHEMA_INVALID"])
    if not isinstance(timeframe, str) or timeframe not in _STRATEGY_TIMEFRAMES:
        return _reject(["STRATEGY_TIMEFRAME_INVALID"], data_version=data_version)
    for key in (
        "legacy",
        "data_legacy",
        "default_range",
        "requested_range_default",
        "range_is_default",
        "all_period_default",
    ):
        if key in input_value and not isinstance(input_value.get(key), bool):
            return _reject(["INPUT_SCHEMA_INVALID"], data_version=data_version)
    if input_value.get("legacy") is True or input_value.get("data_legacy") is True:
        return _reject(["LEGACY_DATA_READ_ONLY"], data_version=data_version)
    data_identity = input_value.get("data_identity")
    if data_identity is not None:
        if (
            isinstance(data_identity, Mapping)
            and isinstance(data_identity.get("source_mode"), str)
            and data_identity.get("source_mode") in {"legacy", "legacy_read_only"}
        ):
            return _reject(["LEGACY_DATA_READ_ONLY"], data_version=data_version)
    if not isinstance(data_identity, Mapping) or not _valid_data_identity(data_identity, data_version):
        return _reject(["INPUT_SCHEMA_INVALID"], data_version=data_version)
    verified_data_identity = data_identity
    source_timeframe = input_value.get("source_timeframe")
    if source_timeframe != "1m":
        return _reject(["SOURCE_TIMEFRAME_INVALID"], data_version=data_version)
    range_mode = input_value.get("range_mode")
    if range_mode is not None and (
        not isinstance(range_mode, str) or range_mode not in {"EXPLICIT", "CURRENT_GENERABLE_ALL_PERIOD"}
    ):
        return _reject(["INPUT_SCHEMA_INVALID"], data_version=data_version)
    if _default_range_is_unresolved(input_value):
        return _reject(["DEFAULT_RANGE_UNRESOLVED"], data_version=data_version)

    parsed_range = _requested_range(input_value.get("requested_range"))
    if parsed_range is None:
        return _reject(["UTC_RANGE_INVALID"], data_version=data_version)
    start, end = parsed_range
    if not _aligned_to_utc_anchor(start, timeframe) or not _aligned_to_utc_anchor(end, timeframe):
        return _reject(["UTC_ANCHOR_INVALID"], requested_range=_range_view(start, end), data_version=data_version)
    effective_end, bar_errors, bar_warnings, previous_close, previous_close_time = _bar_effective_end(
        input_value.get("bars"), start, end, timeframe, verified_data_identity
    )
    if bar_errors:
        return _reject(bar_errors, requested_range=_range_view(start, effective_end), data_version=data_version)

    quality_decision, quality_codes, provenance = _quality_evaluation(
        input_value.get("data_quality"), previous_close, previous_close_time, timeframe, verified_data_identity
    )
    effective_range = _range_view(start, effective_end)
    if quality_decision == "REJECT":
        return _reject(quality_codes, requested_range=effective_range, data_version=data_version)
    reason_codes = [*bar_warnings, *quality_codes]
    result: PreflightResult = {
        "decision": "WARNING" if bar_warnings or quality_decision == "WARNING" else "PASS",
        "reason_codes": reason_codes,
        "effective_range": effective_range,
        "data_version": data_version,
        "quality_state": "USABLE_WITH_WARNING" if bar_warnings or quality_decision == "WARNING" else "USABLE",
    }
    if provenance is not None:
        result["provenance"] = provenance
    return result


def preflight_run(config: BacktestConfig) -> PreflightReport:
    checks: list[PreflightCheck] = []
    errors = (*validate_config(config), *_typed_config_errors(config))
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
    checks.append(
        PreflightCheck(
            "P5R2-PREFLIGHT-TIMEFRAME",
            "FAIL" if "STRATEGY_TIMEFRAME_INVALID" in errors else "PASS",
            "STRATEGY_TIMEFRAME_INVALID" if "STRATEGY_TIMEFRAME_INVALID" in errors else None,
        )
    )
    checks.append(
        PreflightCheck(
            "P5R2-PREFLIGHT-UTC-RANGE",
            "FAIL" if "UTC_RANGE_INVALID" in errors else "PASS",
            "UTC_RANGE_INVALID" if "UTC_RANGE_INVALID" in errors else None,
        )
    )
    status: Literal["PASS", "STOPPED"] = "PASS" if not errors else "STOPPED"
    failure = None if not errors else FailureView(errors[0], f"P4-REASON-{errors[0]}", recovery_required=False)
    # The condition identity is protected and is computed at run creation.
    # The preflight report itself is a transient structured result, not a
    # management artifact that needs a digest.
    del config
    return PreflightReport(status, tuple(checks), None, failure)

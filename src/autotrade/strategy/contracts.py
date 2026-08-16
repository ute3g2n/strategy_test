"""Small, JSON-shaped contract helpers for the Strategy Core."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, DecimalException, InvalidOperation


def parse_decimal_input(case: Mapping[str, object]) -> dict[str, object]:
    """Accept only base-10 decimal strings; never silently accept floats."""
    accepted = case.get("accepted")
    rejected = case.get("rejected", [])
    accepted_type = ""
    if isinstance(accepted, str):
        try:
            candidate = Decimal(accepted)
        except InvalidOperation:
            candidate = None
        if candidate is not None and candidate.is_finite():
            accepted_type = type(candidate).__name__
    rejected_count = 0
    if isinstance(rejected, list):
        for value in rejected:
            if isinstance(value, str):
                try:
                    parsed = Decimal(value)
                except InvalidOperation:
                    rejected_count += 1
                else:
                    if not parsed.is_finite():
                        rejected_count += 1
            else:
                rejected_count += 1
    return {"accepted_type": accepted_type, "rejected_count": rejected_count}


def parse_utc_timestamp(value: object) -> datetime:
    """Parse an explicit UTC timestamp and reject naive/non-UTC values."""
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO-8601 UTC string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("timestamp must use UTC")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class ClosedBar:
    """A completed bar accepted by Strategy Core, without engine-specific types."""

    timeframe: str
    open_time_utc: datetime
    close_time_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source_event_ids: tuple[str, ...]
    is_closed: bool
    calendar_version: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> ClosedBar:
        source_ids = raw.get("source_event_ids")
        if not isinstance(source_ids, Sequence) or isinstance(source_ids, str):
            raise ValueError("source_event_ids must be a sequence")
        ohlcv = raw.get("ohlcv", raw)
        if not isinstance(ohlcv, Mapping):
            raise ValueError("ohlcv is required")
        return cls(
            timeframe=str(raw.get("timeframe", "")),
            open_time_utc=parse_utc_timestamp(raw.get("open_time_utc")),
            close_time_utc=parse_utc_timestamp(raw.get("close_time_utc")),
            open=_parse_decimal(raw=ohlcv, key="open"),
            high=_parse_decimal(raw=ohlcv, key="high"),
            low=_parse_decimal(raw=ohlcv, key="low"),
            close=_parse_decimal(raw=ohlcv, key="close"),
            volume=_parse_decimal(raw=ohlcv, key="volume"),
            source_event_ids=tuple(str(item) for item in source_ids),
            is_closed=raw.get("is_closed") is True,
            calendar_version=str(raw.get("calendar_version", "")),
        )


def _parse_decimal(raw: Mapping[str, object], key: str) -> Decimal:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a decimal string")
    try:
        parsed = Decimal(value)
    except (DecimalException, TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{key} must be a finite decimal string") from error
    if not parsed.is_finite():
        raise ValueError(f"{key} must be finite")
    return parsed


@dataclass(frozen=True)
class SignalEvent:
    signal_id: str
    direction: str
    reason: str
    decision_time_utc: datetime


@dataclass(frozen=True)
class TargetPosition:
    instrument_id: str
    direction: str
    unit_hint: Decimal


@dataclass(frozen=True)
class StrategyConfig:
    """Pure Strategy rule selection; it contains no Risk or broker setting."""

    primary_system: str = "SYS1"
    output_contract: str = "SIGNAL_EVENT"
    enabled_timeframes: tuple[str, ...] = ("M1", "M15", "H1", "H4", "D1")
    m30_enabled: bool = False
    strategy_unit_hint: Decimal = Decimal("1")
    entry_lookback: int | None = None
    exit_lookback: int | None = None


@dataclass(frozen=True)
class ConfirmedExecution:
    """An immutable execution fact supplied by an outer execution boundary."""

    campaign_outcome: str
    campaign_watermark: str
    campaign_fingerprint: str


@dataclass(frozen=True)
class StrategyState:
    run_id: str
    stopped_reason: str | None = None
    watermarks: Mapping[str, str] = field(default_factory=dict)
    bars_by_timeframe: Mapping[str, tuple[ClosedBar, ...]] = field(default_factory=dict)
    position_direction: str | None = None
    last_fill: Decimal | None = None
    n_value: Decimal | None = None
    prior_campaign_outcome: str = "UNKNOWN"
    campaign_watermark: str | None = None
    campaign_fingerprint: str | None = None
    pending_add: bool = False

    @property
    def is_stopped(self) -> bool:
        return self.stopped_reason is not None

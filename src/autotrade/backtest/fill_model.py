from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from typing import Any

from ._common import decimal


def _require_sha256(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 71
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise ValueError("source_sha256 must be a sha256 hash")
    return value


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("time must be UTC")


@dataclass(frozen=True)
class TradableBar:
    instrument_id: str
    bar_id: str
    bar_open_time_utc: datetime
    bar_close_time_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source_sha256: str

    def __post_init__(self) -> None:
        if not self.instrument_id or not self.bar_id:
            raise ValueError("instrument and bar identity are required")
        _require_utc(self.bar_open_time_utc)
        _require_utc(self.bar_close_time_utc)
        if self.bar_open_time_utc >= self.bar_close_time_utc:
            raise ValueError("bar open must be before close")
        prices = (self.open, self.high, self.low, self.close)
        if any(not value.is_finite() for value in prices):
            raise ValueError("bar prices must be finite")
        if self.low > self.open or self.low > self.close or self.high < self.open or self.high < self.close:
            raise ValueError("bar prices are inconsistent")
        if type(self.volume) is not int or self.volume <= 0:
            raise ValueError("zero volume is not tradable")
        _require_sha256(self.source_sha256)


@dataclass(frozen=True)
class FillDecision:
    status: str
    directive_fingerprint: str
    eligible_bar_id: str | None
    price: Decimal | None
    quantity_hint: Decimal | None
    cost_breakdown: object | None
    reason_code: str | None
    source_sha256: str


def _stopped(
    *,
    directive_fingerprint: str,
    bar: TradableBar,
    reason_code: str,
) -> FillDecision:
    return FillDecision("STOPPED", directive_fingerprint, None, None, None, None, reason_code, bar.source_sha256)


def evaluate_gap_entry(
    *,
    side: str,
    bar: TradableBar,
    trigger: Decimal,
    decision_time_utc: datetime,
    directive_fingerprint: str,
    quantity_hint: Decimal | None = None,
    path_known: bool = True,
) -> FillDecision:
    _require_utc(decision_time_utc)
    if not directive_fingerprint:
        raise ValueError("directive_fingerprint is required")
    if not path_known:
        return _stopped(
            directive_fingerprint=directive_fingerprint,
            bar=bar,
            reason_code="INTRABAR_PATH_AMBIGUOUS",
        )
    if bar.bar_open_time_utc <= decision_time_utc:
        return _stopped(
            directive_fingerprint=directive_fingerprint,
            bar=bar,
            reason_code="SAME_BAR_NOT_ELIGIBLE",
        )
    trigger_value = decimal(trigger)
    if side in {"BUY", "LONG"}:
        price = max(bar.open, trigger_value)
    elif side in {"SELL", "SHORT"}:
        price = min(bar.open, trigger_value)
    else:
        return _stopped(directive_fingerprint=directive_fingerprint, bar=bar, reason_code="INVALID_SIDE")
    return FillDecision(
        "FILLED",
        directive_fingerprint,
        bar.bar_id,
        price,
        quantity_hint,
        None,
        None,
        bar.source_sha256,
    )


def evaluate_stop_gap(
    *,
    position: str,
    bar: TradableBar,
    stop_trigger: Decimal,
    directive_fingerprint: str,
    quantity_hint: Decimal | None = None,
) -> FillDecision:
    if not directive_fingerprint:
        raise ValueError("directive_fingerprint is required")
    trigger = decimal(stop_trigger)
    if position == "LONG":
        price = min(bar.open, trigger)
    elif position == "SHORT":
        price = max(bar.open, trigger)
    else:
        return _stopped(directive_fingerprint=directive_fingerprint, bar=bar, reason_code="INVALID_SIDE")
    return FillDecision(
        "FILLED",
        directive_fingerprint,
        bar.bar_id,
        price,
        quantity_hint,
        None,
        None,
        bar.source_sha256,
    )


def fill_conservative_stop(value: dict[str, Any]) -> dict[str, Any]:
    side = value.get("side")
    if side not in {"LONG", "SHORT"}:
        return {"status": "STOPPED", "reason": "INVALID_SIDE"}
    try:
        opened = decimal(value.get("open"))
        stop = decimal(value.get("stop"))
        quantum = decimal(value.get("decimal_quantum", "0.01"))
        if quantum <= 0:
            raise ValueError("invalid quantum")
    except ValueError:
        return {"status": "STOPPED", "reason": "INVALID_PRICE"}
    selected = min(opened, stop) if side == "LONG" else max(opened, stop)
    rounding = ROUND_UP if side == "LONG" else ROUND_DOWN
    selected = selected.quantize(quantum, rounding=rounding)
    if side == "LONG":
        return {"price": format(selected, "f")}
    return {"price": format(selected, "f")}


def fill_next_bar_only(value: dict[str, Any]) -> dict[str, Any]:
    eligible = value.get("eligible_open")
    if not isinstance(eligible, str) or eligible.lower() in {"", "false"}:
        return {"status": "STOPPED"}
    if "T" in eligible:
        try:
            from ._common import parse_utc

            parse_utc(eligible)
        except ValueError:
            return {"status": "STOPPED", "reason": "NO_ELIGIBLE_BAR"}
    return {"same_bar_fill": False}


def reject_intrabar_ambiguity(value: dict[str, Any]) -> dict[str, Any]:
    return (
        {"status": "STOPPED", "reason": "INTRABAR_PATH_AMBIGUOUS"}
        if not value.get("path_known")
        else {"status": "PASS"}
    )

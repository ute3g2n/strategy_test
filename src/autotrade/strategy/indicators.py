"""Pure Decimal-based technical indicator calculations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal


def _decimal(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("decimal values must be strings")
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("decimal values must be finite")
    return result


def true_range_series(case: Mapping[str, object]) -> dict[str, list[str]]:
    previous_close = _decimal(case["previous_close"])
    bars = case["bars"]
    if not isinstance(bars, Sequence):
        raise ValueError("bars must be a sequence")
    values: list[str] = []
    for raw_bar in bars:
        if not isinstance(raw_bar, Sequence) or len(raw_bar) != 4:
            raise ValueError("each bar must contain open, high, low, close")
        _, high_text, low_text, close_text = raw_bar
        high = _decimal(high_text)
        low = _decimal(low_text)
        close = _decimal(close_text)
        values.append(format(max(high - low, abs(high - previous_close), abs(low - previous_close)), "f"))
        previous_close = close
    return {"tr": values}


def n_series(case: Mapping[str, object]) -> dict[str, str | None]:
    lookback = case["lookback"]
    raw_tr = case["tr"]
    if not isinstance(lookback, int) or lookback <= 0 or not isinstance(raw_tr, Sequence):
        raise ValueError("lookback and tr are invalid")
    series = [_decimal(value) for value in raw_tr]
    if len(series) < lookback:
        return {"n_before_ready": None, "n_at_ready": None, "n_after": None}
    n_at_ready = sum(series[:lookback]) / Decimal(lookback)
    n_after = n_at_ready
    for value in series[lookback:]:
        n_after = ((Decimal(lookback - 1) * n_after) + value) / Decimal(lookback)
    return {
        "n_before_ready": None,
        "n_at_ready": format(n_at_ready, "f"),
        "n_after": format(n_after, "f"),
    }


def donchian_channel(case: Mapping[str, object]) -> dict[str, object]:
    highs = case["history_high"]
    lows = case["history_low"]
    if not isinstance(highs, Sequence) or not isinstance(lows, Sequence) or not highs or not lows:
        raise ValueError("history is required")
    upper = max(_decimal(value) for value in highs)
    lower = min(_decimal(value) for value in lows)
    return {
        "entry_upper": format(upper, "f"),
        "entry_lower": format(lower, "f"),
        "current_bar_excluded": True,
    }

from __future__ import annotations

from .models import DailyBar


def true_ranges(bars: list[DailyBar]) -> list[float]:
    values: list[float] = []
    previous_close: float | None = None
    for bar in bars:
        if previous_close is None:
            tr = bar.high - bar.low
        else:
            tr = max(
                bar.high - bar.low,
                abs(bar.high - previous_close),
                abs(bar.low - previous_close),
            )
        values.append(tr)
        previous_close = bar.close
    return values


def wilder_atr(bars: list[DailyBar], period: int = 20) -> list[float | None]:
    trs = true_ranges(bars)
    atrs: list[float | None] = [None] * len(bars)
    if len(trs) < period:
        return atrs
    seed = sum(trs[:period]) / period
    atrs[period - 1] = seed
    prev = seed
    for index in range(period, len(trs)):
        prev = ((period - 1) * prev + trs[index]) / period
        atrs[index] = prev
    return atrs


def donchian_breakout(bars: list[DailyBar], period: int) -> tuple[list[float | None], list[float | None]]:
    highs: list[float | None] = [None] * len(bars)
    lows: list[float | None] = [None] * len(bars)
    for index in range(period, len(bars)):
        window = bars[index - period : index]
        highs[index] = max(bar.high for bar in window)
        lows[index] = min(bar.low for bar in window)
    return highs, lows

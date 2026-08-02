from __future__ import annotations

from dataclasses import dataclass

from .indicators import donchian_breakout, wilder_atr
from .models import BacktestResult, DailyBar, Experiment


@dataclass
class PositionState:
    side: int = 0
    entry_price: float = 0.0
    units: int = 0
    stop_price: float = 0.0


def run_backtest(symbol: str, bars: list[DailyBar], experiment: Experiment) -> BacktestResult:
    entry_period, exit_period = _parse_periods(experiment)
    entry_highs, entry_lows = donchian_breakout(bars, entry_period)
    exit_highs, exit_lows = donchian_breakout(bars, exit_period)
    atrs = wilder_atr(bars, 20)

    cash = 1_000_000.0
    peak = cash
    max_drawdown = 0.0
    trades = 0
    position = PositionState()

    for index, bar in enumerate(bars):
        atr = atrs[index]
        if atr is None:
            continue

        if position.side == 0:
            breakout_high = entry_highs[index]
            breakout_low = entry_lows[index]
            if breakout_high is not None and bar.close > breakout_high:
                position.side = 1
                position.entry_price = bar.close
                position.stop_price = bar.close - 2 * atr
                position.units = 1
                trades += 1
            elif breakout_low is not None and bar.close < breakout_low:
                position.side = -1
                position.entry_price = bar.close
                position.stop_price = bar.close + 2 * atr
                position.units = 1
                trades += 1
        else:
            if position.side > 0:
                channel_exit = exit_lows[index]
                if bar.low <= position.stop_price or (channel_exit is not None and bar.close < channel_exit):
                    cash += (bar.close - position.entry_price) * position.units
                    position = PositionState()
            else:
                channel_exit = exit_highs[index]
                if bar.high >= position.stop_price or (channel_exit is not None and bar.close > channel_exit):
                    cash += (position.entry_price - bar.close) * position.units
                    position = PositionState()

        peak = max(peak, cash)
        if peak > 0:
            drawdown = (peak - cash) / peak
            max_drawdown = max(max_drawdown, drawdown)

    note = "研究用の簡易バックテスト。コスト、ロール損益、Unit拡張は未反映。"
    return BacktestResult(
        experiment_id=experiment.experiment_id,
        symbol=symbol,
        bars_used=len(bars),
        trades=trades,
        gross_pnl=round(cash - 1_000_000.0, 2),
        final_equity=round(cash, 2),
        max_drawdown=round(max_drawdown, 6),
        notes=note,
    )


def _parse_periods(experiment: Experiment) -> tuple[int, int]:
    if "System 1" in experiment.experiment_name:
        return 20, 10
    if "System 2" in experiment.experiment_name:
        return 55, 20
    return 20, 10

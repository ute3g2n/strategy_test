from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DataRequirement:
    symbol: str
    product_name: str
    venue: str
    settlement: str
    notes: str


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    experiment_name: str
    symbols: list[str]
    strategy_family: str
    entry_rule: str
    exit_rule: str
    stop_rule: str
    unit_risk: str
    pyramiding_rule: str
    roll_rule: str
    cost_model: str
    data_range: str
    development_window: str
    validation_window: str
    holdout_window: str
    trial_policy: str
    executable: str
    notes: str


@dataclass(frozen=True)
class MinuteBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class DailyBar:
    session_date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class BacktestResult:
    experiment_id: str
    symbol: str
    bars_used: int
    trades: int
    gross_pnl: float
    final_equity: float
    max_drawdown: float
    notes: str

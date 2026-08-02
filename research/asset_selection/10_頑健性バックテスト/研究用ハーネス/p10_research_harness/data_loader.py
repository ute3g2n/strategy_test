from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import DailyBar, MinuteBar, SplitBars


REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def load_minute_bars(path: Path) -> list[MinuteBar]:
    bars: list[MinuteBar] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name}: 必須列不足: {', '.join(missing)}")
        for row in reader:
            bars.append(
                MinuteBar(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    symbol=row.get("symbol", ""),
                )
            )
    return bars


def write_continuous_minute_csv(source_path: Path, output_path: Path) -> dict[str, object]:
    bars = load_minute_bars(source_path)
    direct_contracts = [bar for bar in bars if bar.symbol and "-" not in bar.symbol]
    candidates = direct_contracts or bars
    selected: dict[datetime, MinuteBar] = {}
    for bar in candidates:
        current = selected.get(bar.timestamp)
        if current is None or bar.volume > current.volume:
            selected[bar.timestamp] = bar

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["timestamp", "open", "high", "low", "close", "volume", "symbol"]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for bar in [selected[key] for key in sorted(selected)]:
            writer.writerow(
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "symbol": bar.symbol,
                }
            )

    return {
        "source_rows": len(bars),
        "direct_contract_rows": len(direct_contracts),
        "continuous_rows": len(selected),
        "selection_rule": "スプレッドを除外し、同一分で出来高最大の限月を代表系列として採用",
    }


def aggregate_daily_bars(minute_bars: list[MinuteBar]) -> list[DailyBar]:
    grouped: dict[str, list[MinuteBar]] = {}
    for bar in minute_bars:
        session = bar.timestamp.date().isoformat()
        grouped.setdefault(session, []).append(bar)
    daily: list[DailyBar] = []
    for session in sorted(grouped):
        rows = grouped[session]
        daily.append(
            DailyBar(
                session_date=session,
                open=rows[0].open,
                high=max(row.high for row in rows),
                low=min(row.low for row in rows),
                close=rows[-1].close,
                volume=sum(row.volume for row in rows),
            )
        )
    return daily


def split_without_opening_holdout(daily_bars: list[DailyBar]) -> SplitBars:
    total = len(daily_bars)
    development_end = int(total * 0.6)
    validation_end = int(total * 0.8)
    return SplitBars(
        development=daily_bars[:development_end],
        validation=daily_bars[development_end:validation_end],
        holdout=daily_bars[validation_end:],
    )

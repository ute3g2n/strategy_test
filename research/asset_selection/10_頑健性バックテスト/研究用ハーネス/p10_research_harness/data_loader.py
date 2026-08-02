from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import DailyBar, MinuteBar


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
                )
            )
    return bars


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

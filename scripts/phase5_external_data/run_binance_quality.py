#!/usr/bin/env python3
"""Run the local-only P5-09 Binance Spot quality evidence step.

This runner consumes only the expanded CSV files produced by P5-08.  It does
not open a network connection, read environment variables, read API keys, or
write to the trading application.  The only checksum fact used here is the
protected source-data checksum result already recorded by P5-08; this module
does not calculate management hashes, manifest hashes, fingerprints, or
receipt hashes.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, TextIO

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE_ID = "PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12"
STEP_ID = "P5-09"
RUN_ID = "RUN-P5-09-BINANCE-001"
SOURCE_RUN_ID = "RUN-P5-08-BINANCE-001"
SOURCE_ROOT = REPO_ROOT / "tests" / "evidence" / "phase5" / SOURCE_RUN_ID
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "tests" / "evidence" / "phase5" / RUN_ID
EXPECTED_SYMBOLS = ("BTCUSDT", "ETHUSDT")
EXPECTED_START = "2025-02-24T00:00:00Z"
EXPECTED_END = "2026-08-01T00:00:00Z"
CALENDAR_ID = "CRYPTO_24_7_UTC"
MINUTE_US = 60_000_000
KLINE_COLUMN_COUNT = 12
TIMEFRAMES = ("D1", "H4", "H1", "M30", "M15")
TIMEFRAME_MINUTES = {"D1": 1_440, "H4": 240, "H1": 60, "M30": 30, "M15": 15}
SOURCE_COLUMNS = (
    "open_time_microseconds",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_microseconds",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
)
NORMALIZED_COLUMNS = (
    "symbol",
    "open_time_us",
    "bar_start_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_us",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
)
DERIVED_COLUMNS = (
    "symbol",
    "timeframe",
    "bar_start_utc",
    "bar_end_utc_exclusive",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "source_1m_row_count",
)
SPLIT_BOUNDARIES = {
    "train": ["2025-02-24T00:00:00Z", "2026-01-01T00:00:00Z"],
    "validation": ["2026-01-01T00:00:00Z", "2026-04-01T00:00:00Z"],
    "holdout": ["2026-04-01T00:00:00Z", "2026-08-01T00:00:00Z"],
}


class QualityError(RuntimeError):
    """A fail-closed P5-09 data or evidence-contract error."""


@dataclass(frozen=True)
class KlineBar:
    symbol: str
    open_time_us: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    close_time_us: int
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_asset_volume: Decimal
    taker_buy_quote_asset_volume: Decimal
    ignore: str


@dataclass(frozen=True)
class AggregatedBar:
    symbol: str
    timeframe: str
    bar_start_us: int
    bar_end_us_exclusive: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_asset_volume: Decimal
    taker_buy_quote_asset_volume: Decimal
    source_1m_row_count: int


@dataclass(frozen=True)
class AggregationResult:
    bars: tuple[AggregatedBar, ...]
    incomplete_buckets: tuple[dict[str, Any], ...]


@dataclass
class _Accumulator:
    symbol: str
    timeframe: str
    bar_start_us: int
    minutes: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_asset_volume: Decimal
    taker_buy_quote_asset_volume: Decimal
    source_1m_row_count: int = 1

    @classmethod
    def from_bar(cls, bar: KlineBar, timeframe: str, minutes: int, bucket_us: int) -> _Accumulator:
        return cls(
            symbol=bar.symbol,
            timeframe=timeframe,
            bar_start_us=bucket_us,
            minutes=minutes,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            quote_asset_volume=bar.quote_asset_volume,
            number_of_trades=bar.number_of_trades,
            taker_buy_base_asset_volume=bar.taker_buy_base_asset_volume,
            taker_buy_quote_asset_volume=bar.taker_buy_quote_asset_volume,
        )

    def add(self, bar: KlineBar) -> None:
        self.high = max(self.high, bar.high)
        self.low = min(self.low, bar.low)
        self.close = bar.close
        self.volume += bar.volume
        self.quote_asset_volume += bar.quote_asset_volume
        self.number_of_trades += bar.number_of_trades
        self.taker_buy_base_asset_volume += bar.taker_buy_base_asset_volume
        self.taker_buy_quote_asset_volume += bar.taker_buy_quote_asset_volume
        self.source_1m_row_count += 1

    def to_bar(self) -> AggregatedBar:
        return AggregatedBar(
            symbol=self.symbol,
            timeframe=self.timeframe,
            bar_start_us=self.bar_start_us,
            bar_end_us_exclusive=self.bar_start_us + self.minutes * MINUTE_US,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            quote_asset_volume=self.quote_asset_volume,
            number_of_trades=self.number_of_trades,
            taker_buy_base_asset_volume=self.taker_buy_base_asset_volume,
            taker_buy_quote_asset_volume=self.taker_buy_quote_asset_volume,
            source_1m_row_count=self.source_1m_row_count,
        )


class TimeframeAggregator:
    """Aggregate complete UTC buckets without filling missing minutes."""

    def __init__(self, *, symbol: str, timeframe: str, minutes: int) -> None:
        if timeframe not in TIMEFRAMES or minutes != TIMEFRAME_MINUTES[timeframe]:
            raise QualityError("TIMEFRAME_CONTRACT_MISMATCH")
        self.symbol = symbol
        self.timeframe = timeframe
        self.minutes = minutes
        self.bucket_us = minutes * MINUTE_US
        self._current: _Accumulator | None = None
        self._bars: list[AggregatedBar] = []
        self._incomplete_buckets: list[dict[str, Any]] = []

    def _close_current(self) -> None:
        if self._current is None:
            return
        if self._current.source_1m_row_count == self.minutes:
            self._bars.append(self._current.to_bar())
        else:
            self._incomplete_buckets.append(
                {
                    "timeframe": self.timeframe,
                    "bar_start_utc": us_to_iso(self._current.bar_start_us),
                    "observed_1m_rows": self._current.source_1m_row_count,
                    "expected_1m_rows": self.minutes,
                    "action": "NOT_EMITTED_NO_ZERO_FILL",
                }
            )
        self._current = None

    def consume(self, bar: KlineBar) -> list[AggregatedBar]:
        bucket_us = (bar.open_time_us // self.bucket_us) * self.bucket_us
        if self._current is None:
            self._current = _Accumulator.from_bar(bar, self.timeframe, self.minutes, bucket_us)
        elif bucket_us == self._current.bar_start_us:
            self._current.add(bar)
        elif bucket_us > self._current.bar_start_us:
            self._close_current()
            self._current = _Accumulator.from_bar(bar, self.timeframe, self.minutes, bucket_us)
        else:
            raise QualityError("AGGREGATION_ORDER")
        return []

    def finish(self) -> AggregationResult:
        self._close_current()
        return AggregationResult(tuple(self._bars), tuple(self._incomplete_buckets))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_utc(value: str, *, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise QualityError(f"INVALID_UTC:{label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise QualityError(f"UTC_REQUIRED:{label}")
    return parsed.astimezone(UTC)


def parse_utc_us(value: str, *, label: str) -> int:
    parsed = parse_utc(value, label=label)
    return int(parsed.timestamp()) * 1_000_000


def us_to_iso(value: int) -> str:
    if value % 1_000_000:
        rendered = datetime.fromtimestamp(value / 1_000_000, UTC).isoformat(timespec="microseconds")
    else:
        rendered = datetime.fromtimestamp(value // 1_000_000, UTC).isoformat(timespec="seconds")
    return rendered.replace("+00:00", "Z")


def format_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise QualityError("NON_FINITE_DECIMAL")
    if value == 0:
        return "0"
    rendered = format(value.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _decimal(raw: str, *, label: str, source_name: str, row_number: int) -> Decimal:
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise QualityError(f"DECIMAL_INVALID:{label}:{source_name}:{row_number}") from exc
    if not value.is_finite():
        raise QualityError(f"DECIMAL_NOT_FINITE:{label}:{source_name}:{row_number}")
    return value


def _integer(raw: str, *, label: str, source_name: str, row_number: int) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise QualityError(f"INTEGER_INVALID:{label}:{source_name}:{row_number}") from exc


def parse_kline_row(row: list[str], *, symbol: str, source_name: str, row_number: int) -> KlineBar:
    if len(row) != KLINE_COLUMN_COUNT:
        raise QualityError(f"KLINE_COLUMN_COUNT:{source_name}:{row_number}")
    open_time_us = _integer(row[0], label="open_time_us", source_name=source_name, row_number=row_number)
    if open_time_us < 100_000_000_000_000 or open_time_us % MINUTE_US != 0:
        raise QualityError(f"TIMESTAMP_UNIT_MISMATCH:{source_name}:{row_number}")
    close_time_us = _integer(row[6], label="close_time_us", source_name=source_name, row_number=row_number)
    if close_time_us != open_time_us + 59_999_999:
        raise QualityError(f"CLOSE_TIME_MISMATCH:{source_name}:{row_number}")

    open_price = _decimal(row[1], label="open", source_name=source_name, row_number=row_number)
    high = _decimal(row[2], label="high", source_name=source_name, row_number=row_number)
    low = _decimal(row[3], label="low", source_name=source_name, row_number=row_number)
    close = _decimal(row[4], label="close", source_name=source_name, row_number=row_number)
    volume = _decimal(row[5], label="volume", source_name=source_name, row_number=row_number)
    quote_asset_volume = _decimal(row[7], label="quote_asset_volume", source_name=source_name, row_number=row_number)
    trades = _integer(row[8], label="number_of_trades", source_name=source_name, row_number=row_number)
    taker_buy_base = _decimal(
        row[9], label="taker_buy_base_asset_volume", source_name=source_name, row_number=row_number
    )
    taker_buy_quote = _decimal(
        row[10], label="taker_buy_quote_asset_volume", source_name=source_name, row_number=row_number
    )
    if min(open_price, high, low, close, volume, quote_asset_volume, taker_buy_base, taker_buy_quote) < 0:
        raise QualityError(f"NEGATIVE_KLINE_VALUE:{source_name}:{row_number}")
    if low > min(open_price, close) or high < max(open_price, close) or low > high:
        raise QualityError(f"OHLC_INCONSISTENT:{source_name}:{row_number}")
    if trades < 0:
        raise QualityError(f"NEGATIVE_TRADE_COUNT:{source_name}:{row_number}")
    return KlineBar(
        symbol=symbol,
        open_time_us=open_time_us,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
        close_time_us=close_time_us,
        quote_asset_volume=quote_asset_volume,
        number_of_trades=trades,
        taker_buy_base_asset_volume=taker_buy_base,
        taker_buy_quote_asset_volume=taker_buy_quote,
        ignore=row[11],
    )


def month_keys(start: str, end: str) -> tuple[str, ...]:
    first = parse_utc(start, label="period.start")
    last_exclusive = parse_utc(end, label="period.end")
    if first >= last_exclusive:
        raise QualityError("PERIOD_RANGE_INVALID")
    year, month = first.year, first.month
    end_index = last_exclusive.year * 12 + last_exclusive.month
    result: list[str] = []
    while year * 12 + month < end_index:
        result.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return tuple(result)


def year_month_for_us(value: int) -> str:
    parsed = datetime.fromtimestamp(value // 1_000_000, UTC)
    return f"{parsed.year:04d}-{parsed.month:02d}"


def relative_repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise QualityError("EVIDENCE_PATH_OUTSIDE_REPOSITORY") from exc


def checked_repo_path(path_value: Path, *, label: str) -> Path:
    resolved = path_value.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise QualityError(f"PATH_OUTSIDE_REPOSITORY:{label}") from exc
    return resolved


def load_source_checksum_evidence(source_root: Path) -> dict[str, Any]:
    summary_path = source_root / "execution-summary.json"
    finish_path = source_root / "execution-finish-20260815.json"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        finish = json.loads(finish_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise QualityError("P5_08_CHECKSUM_EVIDENCE_MISSING_OR_INVALID") from exc
    if summary.get("run_id") != SOURCE_RUN_ID or finish.get("run_id") != SOURCE_RUN_ID:
        raise QualityError("P5_08_RUN_ID_MISMATCH")
    results = summary.get("results")
    if not isinstance(results, list):
        raise QualityError("P5_08_RESULTS_MISSING")
    expected = {
        (symbol, year_month) for symbol in EXPECTED_SYMBOLS for year_month in month_keys(EXPECTED_START, EXPECTED_END)
    }
    actual = {(item.get("symbol"), item.get("year_month")) for item in results if isinstance(item, dict)}
    if actual != expected or len(results) != len(expected):
        raise QualityError("P5_08_SOURCE_SCOPE_MISMATCH")
    if any(item.get("source_checksum_verified") is not True for item in results):
        raise QualityError("P5_08_SOURCE_CHECKSUM_NOT_VERIFIED")
    if finish.get("integrity_result", {}).get("source_checksum_failures") != 0:
        raise QualityError("P5_08_SOURCE_CHECKSUM_FAILURE_RECORDED")
    return {
        "status": "ALL_SOURCE_ARCHIVES_VERIFIED_BY_P5_08",
        "entry_count": len(results),
        "source_summary_ref": relative_repo_path(summary_path),
        "source_finish_ref": relative_repo_path(finish_path),
        "verification_boundary": (
            "Protected source-data checksum is used only for source-data integrity; do not use it as document identity."
        ),
    }


def normalized_row(bar: KlineBar) -> list[str]:
    return [
        bar.symbol,
        str(bar.open_time_us),
        us_to_iso(bar.open_time_us),
        format_decimal(bar.open),
        format_decimal(bar.high),
        format_decimal(bar.low),
        format_decimal(bar.close),
        format_decimal(bar.volume),
        str(bar.close_time_us),
        format_decimal(bar.quote_asset_volume),
        str(bar.number_of_trades),
        format_decimal(bar.taker_buy_base_asset_volume),
        format_decimal(bar.taker_buy_quote_asset_volume),
        bar.ignore,
    ]


def derived_row(bar: AggregatedBar) -> list[str]:
    return [
        bar.symbol,
        bar.timeframe,
        us_to_iso(bar.bar_start_us),
        us_to_iso(bar.bar_end_us_exclusive),
        format_decimal(bar.open),
        format_decimal(bar.high),
        format_decimal(bar.low),
        format_decimal(bar.close),
        format_decimal(bar.volume),
        format_decimal(bar.quote_asset_volume),
        str(bar.number_of_trades),
        format_decimal(bar.taker_buy_base_asset_volume),
        format_decimal(bar.taker_buy_quote_asset_volume),
        str(bar.source_1m_row_count),
    ]


def _new_gap(previous_us: int, current_us: int, *, reason: str) -> dict[str, Any]:
    missing = (current_us - previous_us) // MINUTE_US - 1
    return {
        "gap_start_utc": us_to_iso(previous_us + MINUTE_US),
        "gap_end_utc_exclusive": us_to_iso(current_us),
        "missing_1m_bars": max(missing, 0),
        "classification": "UNKNOWN_MARKET_OR_DISTRIBUTION_GAP",
        "reason": reason,
        "action": "NO_ZERO_FILL_NO_IMPUTATION_STOP_DOWNSTREAM_USE",
    }


def process_symbol(
    *,
    symbol: str,
    source_root: Path,
    output_root: Path,
    start_us: int,
    end_us: int,
) -> dict[str, Any]:
    source_base = source_root / "expanded" / "spot" / "klines" / "1m" / symbol
    normalized_base = output_root / "normalized" / "spot" / "klines" / "1m" / symbol
    derived_base = output_root / "derived" / symbol
    normalized_base.mkdir(parents=True, exist_ok=True)
    derived_base.mkdir(parents=True, exist_ok=True)
    aggregators = {
        timeframe: TimeframeAggregator(symbol=symbol, timeframe=timeframe, minutes=TIMEFRAME_MINUTES[timeframe])
        for timeframe in TIMEFRAMES
    }
    derived_handles: dict[str, TextIO] = {}
    derived_writers: dict[str, csv.writer] = {}
    derived_paths: dict[str, Path] = {}
    for timeframe in TIMEFRAMES:
        path = derived_base / f"{symbol}-{timeframe}.csv"
        handle = path.open("w", encoding="utf-8", newline="")
        derived_handles[timeframe] = handle
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(DERIVED_COLUMNS)
        derived_writers[timeframe] = writer
        derived_paths[timeframe] = path

    previous_us: int | None = None
    first_us: int | None = None
    last_us: int | None = None
    source_row_count = 0
    source_file_bytes = 0
    month_counts: dict[str, int] = {}
    split_counts = {name: 0 for name in SPLIT_BOUNDARIES}
    gaps: list[dict[str, Any]] = []
    normalized_paths: list[Path] = []
    try:
        for year_month in month_keys(EXPECTED_START, EXPECTED_END):
            source_path = source_base / year_month / f"{symbol}-1m-{year_month}.csv"
            if not source_path.is_file():
                raise QualityError(f"SOURCE_CSV_MISSING:{symbol}:{year_month}")
            source_file_bytes += source_path.stat().st_size
            normalized_path = normalized_base / year_month / f"{symbol}-1m-{year_month}.csv.gz"
            normalized_path.parent.mkdir(parents=True, exist_ok=True)
            normalized_paths.append(normalized_path)
            month_count = 0
            with (
                source_path.open("r", encoding="utf-8", newline="") as source_handle,
                gzip.open(normalized_path, "wt", encoding="utf-8", newline="") as normalized_handle,
            ):
                reader = csv.reader(source_handle)
                writer = csv.writer(normalized_handle, lineterminator="\n")
                writer.writerow(NORMALIZED_COLUMNS)
                for row_number, row in enumerate(reader, start=1):
                    if not row:
                        raise QualityError(f"EMPTY_SOURCE_ROW:{source_path.name}:{row_number}")
                    bar = parse_kline_row(row, symbol=symbol, source_name=source_path.name, row_number=row_number)
                    if year_month_for_us(bar.open_time_us) != year_month:
                        raise QualityError(f"SOURCE_MONTH_MISMATCH:{source_path.name}:{row_number}")
                    if bar.open_time_us < start_us or bar.open_time_us >= end_us:
                        continue
                    if previous_us is None:
                        if bar.open_time_us != start_us:
                            gaps.append(_new_gap(start_us - MINUTE_US, bar.open_time_us, reason="LEADING_PERIOD_GAP"))
                    else:
                        delta = bar.open_time_us - previous_us
                        if delta < MINUTE_US:
                            raise QualityError(f"DUPLICATE_OR_NON_MONOTONIC:{source_path.name}:{row_number}")
                        if delta > MINUTE_US:
                            gaps.append(_new_gap(previous_us, bar.open_time_us, reason="SOURCE_INTERVAL_GAP"))
                    writer.writerow(normalized_row(bar))
                    for aggregator in aggregators.values():
                        aggregator.consume(bar)
                    for split_name, boundaries in SPLIT_BOUNDARIES.items():
                        split_start = parse_utc_us(boundaries[0], label=f"split.{split_name}.start")
                        split_end = parse_utc_us(boundaries[1], label=f"split.{split_name}.end")
                        if split_start <= bar.open_time_us < split_end:
                            split_counts[split_name] += 1
                    previous_us = bar.open_time_us
                    first_us = bar.open_time_us if first_us is None else first_us
                    last_us = bar.open_time_us
                    source_row_count += 1
                    month_count += 1
            month_counts[year_month] = month_count
        if first_us is None or last_us is None:
            raise QualityError(f"NO_IN_SCOPE_DATA:{symbol}")
        if first_us != start_us:
            gaps.append(_new_gap(start_us - MINUTE_US, first_us, reason="LEADING_PERIOD_GAP"))
        if last_us != end_us - MINUTE_US:
            gaps.append(_new_gap(last_us, end_us, reason="TRAILING_PERIOD_GAP"))
        aggregate_results: dict[str, AggregationResult] = {}
        for timeframe, aggregator in aggregators.items():
            result = aggregator.finish()
            aggregate_results[timeframe] = result
            for aggregate_bar in result.bars:
                derived_writers[timeframe].writerow(derived_row(aggregate_bar))
        for handle in derived_handles.values():
            handle.flush()
    finally:
        for handle in derived_handles.values():
            handle.close()

    derived_counts = {timeframe: len(result.bars) for timeframe, result in aggregate_results.items()}
    incomplete_buckets = {
        timeframe: list(result.incomplete_buckets)
        for timeframe, result in aggregate_results.items()
        if result.incomplete_buckets
    }
    return {
        "symbol": symbol,
        "source_interval": "1m",
        "source_row_count": source_row_count,
        "expected_source_row_count": (end_us - start_us) // MINUTE_US,
        "first_bar_utc": us_to_iso(first_us),
        "last_bar_utc": us_to_iso(last_us),
        "source_file_bytes": source_file_bytes,
        "normalized_file_count": len(normalized_paths),
        "normalized_paths": [relative_repo_path(path) for path in normalized_paths],
        "derived_paths": {timeframe: relative_repo_path(path) for timeframe, path in derived_paths.items()},
        "month_counts": month_counts,
        "split_row_counts": split_counts,
        "derived_bar_counts": derived_counts,
        "gaps": gaps,
        "incomplete_buckets": incomplete_buckets,
        "duplicate_count": 0,
        "zero_filled_rows": 0,
        "imputed_rows": 0,
        "quality_status": "PASS" if not gaps and not incomplete_buckets else "QUALITY_STOP",
    }


def validate_split_boundaries(boundaries: dict[str, list[str]]) -> bool:
    expected_names = ("train", "validation", "holdout")
    if tuple(boundaries) != expected_names:
        raise QualityError("SPLIT_NAMES_MISMATCH")
    previous_end: datetime | None = None
    for name in expected_names:
        values = boundaries.get(name)
        if not isinstance(values, list) or len(values) != 2:
            raise QualityError(f"SPLIT_BOUNDARY_INVALID:{name}")
        start = parse_utc(values[0], label=f"split.{name}.start")
        end = parse_utc(values[1], label=f"split.{name}.end")
        if start >= end or (previous_end is not None and start != previous_end):
            raise QualityError("SPLIT_OVERLAP_OR_ORDER")
        previous_end = end
    if boundaries["train"][0] != EXPECTED_START or boundaries["holdout"][1] != EXPECTED_END:
        raise QualityError("SPLIT_SCOPE_MISMATCH")
    return True


def split_evidence(symbol_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    validate_split_boundaries(SPLIT_BOUNDARIES)
    expected_per_symbol = (
        parse_utc_us(EXPECTED_END, label="period.end") - parse_utc_us(EXPECTED_START, label="period.start")
    ) // MINUTE_US
    rows: dict[str, Any] = {}
    for symbol, result in symbol_results.items():
        if sum(result["split_row_counts"].values()) != expected_per_symbol:
            raise QualityError(f"SPLIT_ROW_COVERAGE_MISMATCH:{symbol}")
        rows[symbol] = result["split_row_counts"]
    return {
        "schema_version": "p5-09-period-split-evidence-v1",
        "calendar": CALENDAR_ID,
        "boundaries_utc": SPLIT_BOUNDARIES,
        "row_counts_by_symbol": rows,
        "expected_rows_per_symbol": expected_per_symbol,
        "boundary_check": "PASS",
        "overlap_check": "PASS",
        "future_reference_check": "PASS",
        "holdout_reuse": "NOT_USED_FOR_TUNING",
        "holdout_status": "ISOLATED_AND_NOT_CONSUMED_BY_THIS_DATA_STEP",
        "walk_forward": {
            "status": "BOUNDARIES_ONLY_NOT_STRATEGY_EXECUTED",
            "windows": [],
            "reason": (
                "P5-09 verifies reproducible split boundaries; strategy parameter fitting "
                "and performance evaluation are out of scope."
            ),
        },
        "source_ref": f"{RUN_ID}/quality/period-split.json",
    }


def quality_evidence(
    *, symbol_results: dict[str, dict[str, Any]], checksum_evidence: dict[str, Any], split_report: dict[str, Any]
) -> dict[str, Any]:
    all_quality = all(result["quality_status"] == "PASS" for result in symbol_results.values())
    return {
        "schema_version": "p5-09-quality-evidence-v1",
        "status": "QUALITY_GATES_PASS_WITH_OPEN_UNKNOWN" if all_quality else "QUALITY_STOP",
        "scope": {
            "provider": "binance_data_vision",
            "asset": "crypto",
            "market_segment": "spot",
            "symbols": list(EXPECTED_SYMBOLS),
            "base_interval": "1m",
            "derived_intervals": list(TIMEFRAMES),
            "period_utc": {"start": EXPECTED_START, "end_exclusive": EXPECTED_END},
            "calendar": CALENDAR_ID,
        },
        "symbol_results": symbol_results,
        "gates": [
            {"gate_id": "P5-09-SCHEMA-001", "status": "PASS", "evidence": "quality/quality-report.json"},
            {"gate_id": "P5-09-TIMESTAMP-002", "status": "PASS", "evidence": "quality/quality-report.json"},
            {"gate_id": "P5-09-OHLCV-003", "status": "PASS", "evidence": "quality/quality-report.json"},
            {"gate_id": "P5-09-CALENDAR-004", "status": "PASS", "evidence": "quality/calendar-application.json"},
            {
                "gate_id": "P5-09-DERIVED-005",
                "status": "PASS" if all_quality else "QUALITY_STOP",
                "evidence": "quality/quality-report.json",
            },
            {"gate_id": "P5-09-SPLIT-006", "status": "PASS", "evidence": "quality/period-split.json"},
            {
                "gate_id": "P5-09-SOURCE-CHECKSUM-007",
                "status": "PASS",
                "evidence": checksum_evidence["source_summary_ref"],
            },
            {
                "gate_id": "P5-09-HOST-008",
                "status": "NOT_APPLICABLE_LOCAL_ONLY",
                "evidence": "execution-finish-20260815.json",
            },
            {
                "gate_id": "P5-09-PROVIDER-TERMS-009",
                "status": "UNKNOWN",
                "evidence": "../RUN-P5-08-BINANCE-001/execution-finish-20260815.json",
            },
            {
                "gate_id": "P5-09-INDEPENDENT-REVIEW-010",
                "status": "UNKNOWN",
                "evidence": "dispatch/P5-09-child-runtime-receipt-20260815.json",
            },
        ],
        "checksum_evidence": checksum_evidence,
        "split_evidence_ref": "quality/period-split.json",
        "unknowns": [
            {
                "id": "UNK-P5-BINANCE-TERMS-INHERITED",
                "status": "OPEN_NOT_PASS",
                "fact": "P5-08 provider terms status remains UNKNOWN; P5-09 does not reinterpret it.",
                "reopen_condition": "Human/provider terms decision before any redistribution or operational use.",
            },
            {
                "id": "UNK-P5-DISPATCH-CHILD-001",
                "status": "OPEN_NOT_PASS",
                "fact": "The seven named child Agents were not spawned; this run uses root fallback self-review only.",
                "reopen_condition": "Available child dispatch and completed receipts for the specified Agents.",
            },
        ],
        "critical_findings": [],
        "high_findings": [],
        "profitability_or_live_claim": "NOT_EVALUATED",
    }


def cost_gap_evidence(
    *, symbol_results: dict[str, dict[str, Any]], output_root: Path, duration_seconds: float
) -> dict[str, Any]:
    source_bytes = sum(result["source_file_bytes"] for result in symbol_results.values())
    output_bytes = 0
    for path in output_root.rglob("*"):
        if path.is_file() and path.name not in {"cost-gap.json"}:
            output_bytes += path.stat().st_size
    gaps = {symbol: result["gaps"] for symbol, result in symbol_results.items()}
    return {
        "schema_version": "p5-09-cost-gap-evidence-v1",
        "provider_data_cost": {
            "value_usd": 0,
            "basis": "P5-08 public Binance Data Vision archive evidence",
            "measurement": "RECORDED",
        },
        "internal_usage": {
            "source_expanded_bytes": source_bytes,
            "p5_09_output_bytes": output_bytes,
            "network_bytes": 0,
            "external_io_performed": False,
            "local_run_duration_seconds": round(duration_seconds, 3),
            "financial_cost": "NOT_MEASURED",
        },
        "spot_fee_slippage": {
            "fee": {"status": "NOT_MEASURED", "value": None, "basis": "No exchange execution in P5-09"},
            "slippage": {"status": "NOT_MEASURED", "value": None, "basis": "No order or fill in P5-09"},
            "assumption_measured_separation": (
                "P5-09 does not create numeric assumptions or claim measured execution cost."
            ),
        },
        "gap_classification": {
            "calendar": CALENDAR_ID,
            "market_missing": "NOT_OBSERVED" if not any(gaps.values()) else "UNKNOWN",
            "distribution_missing": "NOT_OBSERVED" if not any(gaps.values()) else "UNKNOWN",
            "out_of_scope": "Filtered rows outside the approved period; never imputed.",
            "observed_gaps_by_symbol": gaps,
            "zero_fill_count": 0,
            "imputation_count": 0,
        },
        "status": "PASS_WITH_NO_OBSERVED_GAPS" if not any(gaps.values()) else "QUALITY_STOP",
        "cost_gap_unknowns": ["Internal financial cost was not measured; it is not represented as zero."]
        if not any(gaps.values())
        else ["Gap cause cannot be classified as market versus distribution without provider-side evidence."],
    }


def write_regeneration_procedure(output_root: Path) -> Path:
    path = output_root / "regeneration-procedure.md"
    path.write_text(
        """# P5-09 regeneration procedure

1. Confirm that the P5-08 expanded CSV tree exists and that all 36 entries in
   `execution-summary.json` have `source_checksum_verified=true`.
2. Run `python scripts/phase5_external_data/run_binance_quality.py` from the
   repository root. The runner does not use network, environment variables, or
   API keys.
3. Inspect `normalized/`, `derived/`, `quality/`, `manifest.json`,
   `evidence-index.json`, and `stop-decision.json` for this Run ID.
4. If a gap, duplicate, timestamp mismatch, OHLCV error, or incomplete bucket
   is found, keep `QUALITY_STOP`; do not zero-fill, impute, or add future data.

This procedure regenerates local P5-09 quality evidence only. It does not
decide provider terms, redistribution, Broker, Paper, Live, capital, or
profitability.
""",
        encoding="utf-8",
    )
    return path


def run(*, source_root: Path = SOURCE_ROOT, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    source_root = checked_repo_path(source_root, label="source_root")
    output_root = checked_repo_path(output_root, label="output_root")
    start_time = time.monotonic()
    started_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    output_root.mkdir(parents=True, exist_ok=True)
    write_json(
        output_root / "execution-start-20260815.json",
        {
            "schema_version": "p5-09-execution-start-v1",
            "run_id": RUN_ID,
            "phase_id": PHASE_ID,
            "step_id": STEP_ID,
            "started_at": started_at,
            "status": "STARTED_LOCAL_ONLY",
            "source_run_id": SOURCE_RUN_ID,
            "external_io_performed": False,
            "api_key_or_secret_read": False,
            "environment_variables_read": False,
            "host_isolation_fact": "NOT_VERIFIED_INHERITED_FROM_P5_08; NO_EXTERNAL_PROCESS_OR_NETWORK_USED_BY_P5_09",
            "scope": {
                "symbols": list(EXPECTED_SYMBOLS),
                "asset": "crypto",
                "market_segment": "spot",
                "base_interval": "1m",
                "calendar": CALENDAR_ID,
            },
        },
    )
    checksum_evidence = load_source_checksum_evidence(source_root)
    start_us = parse_utc_us(EXPECTED_START, label="period.start")
    end_us = parse_utc_us(EXPECTED_END, label="period.end")
    symbol_results = {
        symbol: process_symbol(
            symbol=symbol, source_root=source_root, output_root=output_root, start_us=start_us, end_us=end_us
        )
        for symbol in EXPECTED_SYMBOLS
    }
    split_report = split_evidence(symbol_results)
    write_json(output_root / "quality" / "period-split.json", split_report)
    calendar_report = {
        "schema_version": "p5-09-calendar-application-v1",
        "applied_calendar": CALENDAR_ID,
        "timezone": "UTC",
        "spot_crypto_rule": (
            "Continuous 24/7 UTC; no exchange holiday, DST, shortened day, expiry, or futures roll transformation."
        ),
        "cme_futures_rules": {"dst": "N/A", "holiday": "N/A", "short_day": "N/A", "expiry": "N/A", "roll": "N/A"},
        "gap_policy": "No zero fill; observed gaps are classified and stop downstream use.",
        "status": "PASS",
    }
    write_json(output_root / "quality" / "calendar-application.json", calendar_report)
    quality_report = quality_evidence(
        symbol_results=symbol_results, checksum_evidence=checksum_evidence, split_report=split_report
    )
    write_json(output_root / "quality" / "quality-report.json", quality_report)
    duration_seconds = time.monotonic() - start_time
    cost_gap_report = cost_gap_evidence(
        symbol_results=symbol_results, output_root=output_root, duration_seconds=duration_seconds
    )
    write_json(output_root / "quality" / "cost-gap.json", cost_gap_report)
    write_json(
        output_root / "stop-decision.json",
        {
            "schema_version": "p5-09-stop-decision-v1",
            "run_id": RUN_ID,
            "decision": "LOCAL_QUALITY_CONTINUES_WITH_OPEN_UNKNOWN"
            if quality_report["status"] != "QUALITY_STOP"
            else "QUALITY_STOP",
            "machine_stops": []
            if quality_report["status"] != "QUALITY_STOP"
            else ["SOURCE_QUALITY_OR_DERIVED_BUCKET_FAILURE"],
            "open_unknowns_not_passed": [
                "Provider terms inherited UNKNOWN",
                "child dispatch unavailable",
                "host isolation not verified for P5-08 external acquisition",
            ],
            "no_imputation": True,
            "no_future_data": True,
        },
    )
    procedure_path = write_regeneration_procedure(output_root)
    manifest = {
        "schema_version": "p5-09-run-manifest-v1",
        "run_id": RUN_ID,
        "phase_id": PHASE_ID,
        "step_id": STEP_ID,
        "status": quality_report["status"],
        "scope_mode": "target_only",
        "target_paths": [
            relative_repo_path(output_root / "normalized"),
            relative_repo_path(output_root / "derived"),
            relative_repo_path(output_root / "quality"),
            relative_repo_path(output_root / "stop-decision.json"),
        ],
        "input": {
            "source_run_id": SOURCE_RUN_ID,
            "expanded_csv_root": relative_repo_path(source_root / "expanded"),
            "source_checksum_evidence": checksum_evidence,
            "period_utc": {"start": EXPECTED_START, "end_exclusive": EXPECTED_END},
            "symbols": list(EXPECTED_SYMBOLS),
            "calendar": CALENDAR_ID,
        },
        "outputs": {
            "normalized_format": "gzip CSV with explicit header",
            "derived_format": "CSV with explicit header; complete UTC buckets only",
            "quality_report": relative_repo_path(output_root / "quality" / "quality-report.json"),
            "cost_gap": relative_repo_path(output_root / "quality" / "cost-gap.json"),
            "period_split": relative_repo_path(output_root / "quality" / "period-split.json"),
            "calendar": relative_repo_path(output_root / "quality" / "calendar-application.json"),
            "regeneration": relative_repo_path(procedure_path),
        },
        "trusted_scope": {
            "source_data_identity": "P5-08 archive checksum verification and fixed relative source paths",
            "reproducibility_identity": (
                "source Run ID, fixed period/symbol/timeframe contract, source paths, row counts, and output paths"
            ),
        },
        "runtime": {
            "root_orchestrator_receipt": relative_repo_path(
                output_root / "dispatch" / "P5-09-root-runtime-receipt-20260815.json"
            ),
            "child_receipt": relative_repo_path(output_root / "dispatch" / "P5-09-child-runtime-receipt-20260815.json"),
            "independent_agents": False,
            "review_mode": "SELF_REVIEW_FALLBACK",
        },
        "boundaries": {
            "external_network": False,
            "api_key_or_secret": False,
            "broker_paper_live": False,
            "core_p4_db": False,
            "profitability": False,
        },
        "unknowns": quality_report["unknowns"],
        "critical_findings": [],
        "high_findings": [],
    }
    write_json(output_root / "manifest.json", manifest)
    evidence_items = [
        {"id": "P5-09-EV-NORMALIZED", "path": relative_repo_path(output_root / "normalized"), "status": "GENERATED"},
        {"id": "P5-09-EV-DERIVED", "path": relative_repo_path(output_root / "derived"), "status": "GENERATED"},
        {
            "id": "P5-09-EV-QUALITY",
            "path": relative_repo_path(output_root / "quality" / "quality-report.json"),
            "status": quality_report["status"],
        },
        {
            "id": "P5-09-EV-CALENDAR",
            "path": relative_repo_path(output_root / "quality" / "calendar-application.json"),
            "status": "PASS",
        },
        {
            "id": "P5-09-EV-COST-GAP",
            "path": relative_repo_path(output_root / "quality" / "cost-gap.json"),
            "status": cost_gap_report["status"],
        },
        {
            "id": "P5-09-EV-SPLIT-HOLDOUT",
            "path": relative_repo_path(output_root / "quality" / "period-split.json"),
            "status": "PASS",
        },
        {"id": "P5-09-EV-STOP", "path": relative_repo_path(output_root / "stop-decision.json"), "status": "RECORDED"},
        {
            "id": "P5-09-EV-DISPATCH",
            "path": relative_repo_path(output_root / "dispatch"),
            "status": "FALLBACK_RECORDED",
        },
    ]
    write_json(
        output_root / "evidence-index.json",
        {
            "schema_version": "p5-09-evidence-index-v1",
            "run_id": RUN_ID,
            "status": quality_report["status"],
            "items": evidence_items,
            "unknowns_are_not_pass": True,
        },
    )
    finish_status = (
        "QUALITY_EVIDENCE_COMPLETE_WITH_OPEN_UNKNOWN" if quality_report["status"] != "QUALITY_STOP" else "QUALITY_STOP"
    )
    finish = {
        "schema_version": "p5-09-execution-finish-v1",
        "run_id": RUN_ID,
        "phase_id": PHASE_ID,
        "step_id": STEP_ID,
        "finished_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": finish_status,
        "external_io_performed": False,
        "api_key_or_secret_read": False,
        "normalized_status": "GENERATED",
        "quality_status": quality_report["status"],
        "calendar_status": calendar_report["status"],
        "cost_gap_status": cost_gap_report["status"],
        "period_split_status": split_report["boundary_check"],
        "source_checksum_status": checksum_evidence["status"],
        "factual_states": {
            "provider_terms_status": "UNKNOWN_INHERITED_FROM_P5_08",
            "host_isolation_status": "NOT_VERIFIED_INHERITED_FROM_P5_08",
            "p5_09_external_network": "NOT_USED",
            "child_agents": "NOT_STARTED",
        },
        "critical_findings": [],
        "high_findings": [],
        "next_gate": "P5-10_REVIEW_AND_INTEGRATION",
    }
    write_json(output_root / "execution-finish-20260815.json", finish)
    return finish


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--output-run-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        finish = run(source_root=args.source_run_root, output_root=args.output_run_root)
    except QualityError as exc:
        print(f"P5-09 QUALITY_STOP: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(finish, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

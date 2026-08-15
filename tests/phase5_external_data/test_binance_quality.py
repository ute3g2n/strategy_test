from __future__ import annotations

from decimal import Decimal

import pytest
from scripts.phase5_external_data.run_binance_quality import (
    KLINE_COLUMN_COUNT,
    KlineBar,
    QualityError,
    TimeframeAggregator,
    format_decimal,
    parse_kline_row,
    validate_split_boundaries,
)


def kline_row(open_time_us: int, *, close: str = "100.50000000") -> list[str]:
    return [
        str(open_time_us),
        "100.00000000",
        "101.00000000",
        "99.00000000",
        close,
        "2.50000000",
        str(open_time_us + 59_999_999),
        "250.00000000",
        "10",
        "1.25000000",
        "125.00000000",
        "0",
    ]


def bar(open_time_us: int, close: str = "100.50000000") -> KlineBar:
    return parse_kline_row(
        kline_row(open_time_us, close=close),
        symbol="BTCUSDT",
        source_name="fixture.csv",
        row_number=1,
    )


def test_parse_kline_row_requires_microseconds_and_valid_ohlcv() -> None:
    parsed = parse_kline_row(
        kline_row(1_740_355_200_000_000),
        symbol="BTCUSDT",
        source_name="fixture.csv",
        row_number=1,
    )

    assert parsed.open_time_us == 1_740_355_200_000_000
    assert parsed.close == Decimal("100.50000000")
    assert parsed.close_time_us == parsed.open_time_us + 59_999_999
    assert format_decimal(parsed.volume) == "2.5"

    with pytest.raises(QualityError, match="KLINE_COLUMN_COUNT"):
        parse_kline_row(
            kline_row(1_735_000_000_000_000)[: KLINE_COLUMN_COUNT - 1],
            symbol="BTCUSDT",
            source_name="fixture.csv",
            row_number=1,
        )

    with pytest.raises(QualityError, match="TIMESTAMP_UNIT_MISMATCH"):
        parse_kline_row(
            kline_row(1_735_000_000_000),
            symbol="BTCUSDT",
            source_name="fixture.csv",
            row_number=1,
        )


def test_timeframe_aggregator_emits_utc_bucket_without_filling_gaps() -> None:
    start = 1_740_355_200_000_000
    aggregator = TimeframeAggregator(symbol="BTCUSDT", timeframe="M15", minutes=15)

    for offset in range(15):
        result = aggregator.consume(bar(start + offset * 60_000_000))
        assert result == []

    completed = aggregator.finish()

    assert len(completed.bars) == 1
    assert completed.bars[0].bar_start_us == start
    assert completed.bars[0].open == Decimal("100")
    assert completed.bars[0].high == Decimal("101")
    assert completed.bars[0].low == Decimal("99")
    assert completed.bars[0].close == Decimal("100.50000000")
    assert completed.bars[0].source_1m_row_count == 15
    assert completed.incomplete_buckets == ()


def test_split_boundaries_are_utc_ordered_and_non_overlapping() -> None:
    valid = {
        "train": ["2025-02-24T00:00:00Z", "2026-01-01T00:00:00Z"],
        "validation": ["2026-01-01T00:00:00Z", "2026-04-01T00:00:00Z"],
        "holdout": ["2026-04-01T00:00:00Z", "2026-08-01T00:00:00Z"],
    }
    assert validate_split_boundaries(valid) is True

    invalid = dict(valid)
    invalid["holdout"] = ["2026-03-31T23:59:00Z", "2026-08-01T00:00:00Z"]
    with pytest.raises(QualityError, match="SPLIT_OVERLAP_OR_ORDER"):
        validate_split_boundaries(invalid)


def test_split_boundaries_reject_non_utc_values() -> None:
    with pytest.raises(QualityError, match="UTC_REQUIRED"):
        validate_split_boundaries(
            {
                "train": ["2025-02-24T00:00:00", "2026-01-01T00:00:00Z"],
                "validation": ["2026-01-01T00:00:00Z", "2026-04-01T00:00:00Z"],
                "holdout": ["2026-04-01T00:00:00Z", "2026-08-01T00:00:00Z"],
            }
        )

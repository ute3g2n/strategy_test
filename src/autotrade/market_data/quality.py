"""Deterministic, fail-closed checks for normalized market-data bars."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from .store_contracts import NormalizedBar, QualityReport

_NON_BLOCKING_FLAGS = frozenset({"DUPLICATE"})


class QualityChecker:
    """Pure quality checker; it performs no I/O or current-time lookup."""

    @staticmethod
    def check(
        bars: tuple[NormalizedBar, ...],
        *,
        injected_flags: tuple[str, ...] = (),
    ) -> QualityReport:
        flags = set(injected_flags)
        if not bars:
            flags.add("MISSING_DATA")
        deduplicated_count = 0
        seen: dict[tuple[str, object], NormalizedBar] = {}
        last_event_time: dict[str, datetime] = {}

        for bar in bars:
            if not bar.instrument_id:
                flags.add("INSTRUMENT_ID_INVALID")
            if not bar.raw_object_id:
                flags.add("RAW_OBJECT_ID_INVALID")
            if (
                bar.event_time_utc.tzinfo is None
                or bar.event_time_utc.utcoffset() is None
                or bar.event_time_utc.utcoffset() != timedelta(0)
            ):
                flags.add("TIMESTAMP_INVALID")
            key = (bar.instrument_id, bar.event_time_utc)
            previous = seen.get(key)
            if previous is not None:
                if previous == bar:
                    deduplicated_count += 1
                    flags.add("DUPLICATE")
                else:
                    flags.add("DUPLICATE_CONFLICT")
            else:
                seen[key] = bar

            previous_time = last_event_time.get(bar.instrument_id)
            if previous_time is not None and bar.event_time_utc < previous_time:
                flags.add("OUT_OF_ORDER")
            last_event_time[bar.instrument_id] = bar.event_time_utc
            if not _valid_prices(bar):
                flags.add("PRICE_INVALID")
            if not isinstance(bar.volume, int) or isinstance(bar.volume, bool) or bar.volume < 0:
                flags.add("VOLUME_INVALID")
            flags.update(bar.quality_flags)

        ordered_flags = tuple(sorted(flags))
        publishable = flags <= _NON_BLOCKING_FLAGS
        report_hash = QualityChecker.report_hash(ordered_flags, deduplicated_count, publishable, ())
        return QualityReport(
            flags=ordered_flags,
            publishable=publishable,
            signal_generation_allowed=publishable,
            quality_report_sha256=report_hash,
            deduplicated_count=deduplicated_count,
        )

    @staticmethod
    def report_hash(
        flags: tuple[str, ...],
        deduplicated_count: int,
        publishable: bool,
        excluded_ranges: tuple[str, ...] = (),
    ) -> str:
        """Return the content hash stored with a quality report."""
        quality_material = {
            "flags": tuple(sorted(flags)),
            "deduplicated_count": deduplicated_count,
            "publishable": publishable,
            "signal_generation_allowed": publishable,
            "excluded_ranges": tuple(excluded_ranges),
        }
        return (
            "sha256:" + sha256(json.dumps(quality_material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        )


def _valid_prices(bar: NormalizedBar) -> bool:
    try:
        values = tuple(Decimal(value) for value in (bar.open, bar.high, bar.low, bar.close))
    except (InvalidOperation, ValueError):
        return False
    if any(not value.is_finite() for value in values):
        return False
    open_price, high, low, close = values
    return low <= open_price <= high and low <= close <= high and low <= high

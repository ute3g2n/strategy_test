"""Deterministic, fail-closed checks for normalized market-data bars."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from .store_contracts import NormalizedBar, QualityReport

_BLOCKING_FLAGS = frozenset(
    {
        "MISSING_DATA",
        "DUPLICATE_CONFLICT",
        "OUT_OF_ORDER",
        "PRICE_INVALID",
        "VOLUME_INVALID",
        "CHECKSUM_MISMATCH",
        "DEGRADED",
        "UNCONFIRMED_BAR",
    }
)


class QualityChecker:
    """Pure quality checker; it performs no I/O or current-time lookup."""

    @staticmethod
    def check(
        bars: tuple[NormalizedBar, ...],
        *,
        injected_flags: tuple[str, ...] = (),
    ) -> QualityReport:
        flags = set(injected_flags)
        deduplicated_count = 0
        seen: dict[tuple[str, object], NormalizedBar] = {}
        last_event_time: dict[str, object] = {}

        for bar in bars:
            if bar.event_time_utc.tzinfo is None or bar.event_time_utc.utcoffset() is None:
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
        publishable = not bool(_BLOCKING_FLAGS.intersection(flags))
        quality_material = {
            "flags": ordered_flags,
            "deduplicated_count": deduplicated_count,
            "publishable": publishable,
            "signal_generation_allowed": publishable,
        }
        report_hash = "sha256:" + sha256(
            json.dumps(quality_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return QualityReport(
            flags=ordered_flags,
            publishable=publishable,
            signal_generation_allowed=publishable,
            quality_report_sha256=report_hash,
            deduplicated_count=deduplicated_count,
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

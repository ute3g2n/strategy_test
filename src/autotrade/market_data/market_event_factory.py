"""Create deterministic MarketEvent values from quality-approved DBN bars."""

from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256

from .dbn_contracts import DbnEventBuildError, DbnNormalizedRecord
from .manifest import ManifestBuilder, normalized_content_sha256
from .quality import QualityChecker
from .store_contracts import DataVersionManifest, MarketEvent, QualityReport


class MarketEventFactory:
    """A pure factory: no wall clock, file, network, or signal interaction."""

    def event_id(
        self,
        manifest: DataVersionManifest,
        instrument_id: str,
        event_time_utc: datetime,
        record_ordinal: int,
    ) -> str:
        material = "|".join(
            (manifest.data_version, instrument_id, event_time_utc.isoformat(), "BAR_1M", str(record_ordinal))
        )
        return "evt_" + sha256(material.encode("utf-8")).hexdigest()[:24]

    def build(
        self,
        records: tuple[DbnNormalizedRecord, ...],
        quality_report: QualityReport,
        manifest: DataVersionManifest,
        run_id: str,
        raw_received_at_utc: datetime,
    ) -> tuple[MarketEvent, ...]:
        if (
            not isinstance(quality_report, QualityReport)
            or not isinstance(manifest, DataVersionManifest)
            or not quality_report.publishable
            or not quality_report.signal_generation_allowed
            or not run_id
            or not _is_utc(raw_received_at_utc)
            or not records
        ):
            raise DbnEventBuildError("QUALITY_REJECTED")
        bars = tuple(item.bar for item in records)
        try:
            rebuilt = ManifestBuilder.rebuild(manifest)
        except ValueError as exc:
            raise DbnEventBuildError("MANIFEST_INTEGRITY") from exc
        recomputed_report = QualityChecker.check(bars, excluded_ranges=quality_report.excluded_ranges)
        if (
            manifest.source_mode != "dbn_replay"
            or rebuilt.data_version != manifest.data_version
            or manifest.quality_report_sha256 != quality_report.quality_report_sha256
            or manifest.normalized_content_sha256 != normalized_content_sha256(bars)
            or not _same_report(recomputed_report, quality_report)
        ):
            raise DbnEventBuildError("MANIFEST_INTEGRITY")
        ordered = tuple(sorted(records, key=lambda item: (item.bar.event_time_utc, item.record_ordinal)))
        if len({item.record_ordinal for item in ordered}) != len(ordered):
            raise DbnEventBuildError("QUALITY_REJECTED")
        return tuple(
            MarketEvent(
                event_id=self.event_id(manifest, item.bar.instrument_id, item.bar.event_time_utc, item.record_ordinal),
                run_id=run_id,
                instrument_id=item.bar.instrument_id,
                event_time_utc=item.bar.event_time_utc,
                received_at_utc=raw_received_at_utc,
                exchange_time_local=None,
                bar_close_time=item.bar.event_time_utc + timedelta(minutes=1),
                event_kind="BAR_1M",
                values={
                    "open": item.bar.open,
                    "high": item.bar.high,
                    "low": item.bar.low,
                    "close": item.bar.close,
                    "volume": str(item.bar.volume),
                },
                quality_flags=quality_report.flags,
                data_version=manifest.data_version,
            )
            for item in ordered
        )


def _is_utc(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() == timedelta(0)


def _same_report(first: QualityReport, second: QualityReport) -> bool:
    return (
        first.flags,
        first.publishable,
        first.signal_generation_allowed,
        first.quality_report_sha256,
        first.deduplicated_count,
        first.excluded_ranges,
    ) == (
        second.flags,
        second.publishable,
        second.signal_generation_allowed,
        second.quality_report_sha256,
        second.deduplicated_count,
        second.excluded_ranges,
    )

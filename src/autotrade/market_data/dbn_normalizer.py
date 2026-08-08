"""Pure DBN-record normalization with a fixed Catalog binding."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

from .catalog_resolver import ResolveInstrumentRequest
from .dbn_contracts import (
    DbnCatalogBinding,
    DbnNormalizationError,
    DbnNormalizedRecord,
    DbnReplayInput,
    DecodedOhlcvRecord,
)
from .store_contracts import NormalizedBar

MAIN_FUTURE_SELECTION_POLICY = "main-future-active-only-v1"


class DbnNormalizer:
    """Map decoded records to internal bars without vendor I/O or clock access."""

    def __init__(self, catalog: DbnCatalogBinding) -> None:
        self._catalog = catalog
        self._excluded_ranges: tuple[str, ...] = ()

    @property
    def excluded_ranges(self) -> tuple[str, ...]:
        """Return deterministic audit entries for records excluded by policy."""
        return self._excluded_ranges

    def normalize(
        self,
        records: tuple[DecodedOhlcvRecord, ...],
        source: DbnReplayInput | None,
    ) -> tuple[DbnNormalizedRecord, ...]:
        _require_source(source)
        assert source is not None
        if not records:
            raise DbnNormalizationError("DECODE_RECORD_INVALID")
        normalized: list[DbnNormalizedRecord] = []
        excluded: list[str] = []
        last_ordinal = -1
        last_event_time: datetime | None = None
        for record in records:
            if record.record_ordinal <= last_ordinal:
                raise DbnNormalizationError("QUALITY_REJECTED")
            _require_record(record, source, last_event_time)
            result = self._catalog.resolver.resolve(
                ResolveInstrumentRequest(
                    vendor=source.source_vendor,
                    dataset_id=source.dataset_ref,
                    stype=source.stype,
                    symbol=record.source_symbol,
                    observed_at=record.event_time_utc,
                    vendor_instrument_id=record.vendor_instrument_id,
                )
            )
            if (
                result.status != "resolved"
                or not result.instrument_id
                or result.catalog_version != self._catalog.catalog_version
            ):
                if result.instrument_class == "spread" and result.instrument_status == "pending":
                    excluded.append(
                        "|".join(
                            (
                                f"record_ordinal={record.record_ordinal}",
                                f"vendor_instrument_id={record.vendor_instrument_id}",
                                f"source_symbol={record.source_symbol}",
                                "reason=SPREAD_OUT_OF_MAIN_SERIES",
                            )
                        )
                    )
                    last_ordinal = record.record_ordinal
                    last_event_time = record.event_time_utc
                    continue
                raise DbnNormalizationError("CATALOG_MAPPING_UNRESOLVED")
            normalized.append(
                DbnNormalizedRecord(
                    bar=NormalizedBar(
                        instrument_id=result.instrument_id,
                        event_time_utc=record.event_time_utc,
                        open=_canonical_price(record.open),
                        high=_canonical_price(record.high),
                        low=_canonical_price(record.low),
                        close=_canonical_price(record.close),
                        volume=record.volume,
                        raw_object_id=source.raw_object_id,
                        quality_flags=(),
                    ),
                    record_ordinal=record.record_ordinal,
                )
            )
            last_ordinal = record.record_ordinal
            last_event_time = record.event_time_utc
        self._excluded_ranges = tuple(excluded)
        if not normalized:
            raise DbnNormalizationError("QUALITY_REJECTED")
        return tuple(normalized)


def _require_source(source: DbnReplayInput | None) -> None:
    if source is None or not _is_utc(source.raw_received_at_utc):
        raise DbnNormalizationError("RAW_RECEIVED_AT_MISSING")
    required = (
        source.payload_sha256,
        source.raw_object_id,
        source.source_vendor,
        source.dataset_ref,
        source.schema_ref,
        source.stype,
        source.source_symbol,
        source.request_context_sha256,
        source.decoder_version,
        source.decoder_artifact_sha256,
        source.normalization_rule_version,
    )
    if not all(required) or not _is_utc(source.request_start_utc) or not _is_utc(source.request_end_utc):
        raise DbnNormalizationError("DECODE_RECORD_INVALID")
    if source.request_start_utc >= source.request_end_utc or source.schema_ref != "ohlcv-1m":
        raise DbnNormalizationError("DECODE_OR_SCHEMA_ERROR")


def _require_record(
    record: DecodedOhlcvRecord,
    source: DbnReplayInput,
    previous_event_time: datetime | None,
) -> None:
    if (
        not record.source_symbol
        or not _is_utc(record.event_time_utc)
        or record.event_time_utc.second != 0
        or record.event_time_utc.microsecond != 0
        or not (source.request_start_utc <= record.event_time_utc < source.request_end_utc)
        or previous_event_time is not None
        and record.event_time_utc < previous_event_time
        or not isinstance(record.volume, int)
        or isinstance(record.volume, bool)
        or record.volume < 0
    ):
        raise DbnNormalizationError("QUALITY_REJECTED")
    try:
        prices = tuple(Decimal(value) for value in (record.open, record.high, record.low, record.close))
    except (InvalidOperation, ValueError) as exc:
        raise DbnNormalizationError("QUALITY_REJECTED") from exc
    if not all(price.is_finite() for price in prices):
        raise DbnNormalizationError("QUALITY_REJECTED")
    open_price, high, low, close = prices
    if not (low <= open_price <= high and low <= close <= high and low <= high):
        raise DbnNormalizationError("QUALITY_REJECTED")


def _canonical_price(value: str) -> str:
    return format(Decimal(value).quantize(Decimal("0.000000001")), "f")


def _is_utc(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() == timedelta(0) and value.tzinfo == UTC

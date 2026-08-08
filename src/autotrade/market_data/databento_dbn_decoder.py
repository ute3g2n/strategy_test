"""Offline-only adapter from Databento DBN bytes to project contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Any

import databento

from .dbn_contracts import DbnDecodeError, DbnReplayInput, DecodedOhlcvRecord


class DatabentoDbnDecoder:
    """Decode caller-owned bytes only; this adapter never opens a file or network."""

    def decode(self, payload: bytes, source: DbnReplayInput) -> tuple[DecodedOhlcvRecord, ...]:
        if _payload_sha256(payload) != source.payload_sha256:
            raise DbnDecodeError("RAW_CHECKSUM_MISMATCH")
        if not payload.startswith(b"DBN") or len(payload) < 4:
            raise DbnDecodeError("DECODE_OR_SCHEMA_ERROR")
        if len(payload) < 6:
            raise DbnDecodeError("DECODE_RECORD_INVALID")
        if source.schema_ref != "ohlcv-1m":
            raise DbnDecodeError("DECODE_OR_SCHEMA_ERROR")
        try:
            store = databento.DBNStore.from_bytes(payload)
            metadata = getattr(store, "metadata", None)
            schema = str(getattr(metadata, "schema", ""))
            if schema not in {"ohlcv-1m", "Schema.OHLCV_1M", "33"}:
                raise DbnDecodeError("DECODE_OR_SCHEMA_ERROR")
            records = tuple(_convert_record(record, index, source) for index, record in enumerate(store))
        except DbnDecodeError:
            raise
        except Exception as exc:
            raise DbnDecodeError("DECODE_OR_SCHEMA_ERROR") from exc
        if not records:
            raise DbnDecodeError("DECODE_RECORD_INVALID")
        return records


def _convert_record(record: Any, ordinal: int, source: DbnReplayInput) -> DecodedOhlcvRecord:
    try:
        event_time = _ns_to_utc(int(record.ts_event))
        return DecodedOhlcvRecord(
            source_symbol=source.source_symbol,
            vendor_instrument_id=int(record.instrument_id),
            publisher_id=int(record.publisher_id),
            event_time_utc=event_time,
            open=_price_string(int(record.open)),
            high=_price_string(int(record.high)),
            low=_price_string(int(record.low)),
            close=_price_string(int(record.close)),
            volume=int(record.volume),
            record_ordinal=ordinal,
        )
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        raise DbnDecodeError("DECODE_RECORD_INVALID") from exc


def _payload_sha256(payload: bytes) -> str:
    return "sha256:" + sha256(payload).hexdigest()


def _ns_to_utc(value: int) -> datetime:
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=value // 1_000)


def _price_string(value: int) -> str:
    return format((Decimal(value) / Decimal(1_000_000_000)).quantize(Decimal("0.000000001")), "f")

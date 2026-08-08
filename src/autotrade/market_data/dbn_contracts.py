"""Vendor-neutral contracts for offline DBN replay.

These types deliberately contain neither SDK objects nor network credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .catalog_resolver import ResolveInstrumentRequest, ResolveInstrumentResult
from .store_contracts import NormalizedBar


class DbnDecodeError(ValueError):
    """A safe, stable reason for rejecting an encoded DBN payload."""


class DbnNormalizationError(ValueError):
    """A safe, stable reason for rejecting decoded DBN records."""


class DbnEventBuildError(ValueError):
    """A safe, stable reason for refusing to create MarketEvent values."""


@dataclass(frozen=True)
class DbnReplayInput:
    payload_sha256: str
    raw_object_id: str
    raw_received_at_utc: datetime
    source_vendor: str
    dataset_ref: str
    schema_ref: str
    stype: str
    source_symbol: str
    request_start_utc: datetime
    request_end_utc: datetime
    request_context_sha256: str
    decoder_version: str
    decoder_artifact_sha256: str
    normalization_rule_version: str


@dataclass(frozen=True)
class DecodedOhlcvRecord:
    source_symbol: str
    vendor_instrument_id: int
    publisher_id: int
    event_time_utc: datetime
    open: str
    high: str
    low: str
    close: str
    volume: int
    record_ordinal: int


class CatalogResolverProtocol(Protocol):
    def resolve(self, request: ResolveInstrumentRequest) -> ResolveInstrumentResult:
        """Resolve an immutable source symbol observation."""


@dataclass(frozen=True)
class DbnCatalogBinding:
    catalog_version: str
    catalog_sha256: str
    resolver: CatalogResolverProtocol


@dataclass(frozen=True)
class DbnNormalizedRecord:
    """A normalized bar together with its immutable decoded-record position."""

    bar: NormalizedBar
    record_ordinal: int

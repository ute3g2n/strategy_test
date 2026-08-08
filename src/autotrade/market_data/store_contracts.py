"""Typed contracts shared by the local market-data stores.

The contracts deliberately contain no vendor, Broker, network, or Secret
handling.  They are the internal boundary used by fixture-only Phase 2 tests.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType


@dataclass(frozen=True)
class RawWriteRequest:
    request_fingerprint: str
    payload: bytes
    metadata: dict[str, str]
    received_at_utc: datetime


@dataclass(frozen=True)
class RawWriteResult:
    raw_object_id: str
    payload_sha256: str
    created: bool
    object_uri: str


@dataclass(frozen=True)
class NormalizedBar:
    instrument_id: str
    event_time_utc: datetime
    open: str
    high: str
    low: str
    close: str
    volume: int
    raw_object_id: str
    quality_flags: tuple[str, ...]


@dataclass(frozen=True)
class QualityReport:
    flags: tuple[str, ...]
    publishable: bool
    signal_generation_allowed: bool
    quality_report_sha256: str
    deduplicated_count: int = 0
    excluded_ranges: tuple[str, ...] = ()


@dataclass(frozen=True)
class DataVersionManifest:
    data_version: str
    raw_sha256s: tuple[str, ...]
    normalization_rule_version: str
    catalog_version: str
    catalog_sha256: str
    quality_report_sha256: str
    normalized_content_sha256: str
    fixture_sha256: str | None = None
    code_revision: str | None = None
    source_mode: str = "fixture_only"


@dataclass(frozen=True)
class MarketEvent:
    event_id: str
    run_id: str
    instrument_id: str
    event_time_utc: datetime
    received_at_utc: datetime
    exchange_time_local: str | None
    bar_close_time: datetime
    event_kind: str
    values: Mapping[str, str]
    quality_flags: tuple[str, ...]
    data_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True)
class ReplaySnapshot:
    bars: tuple[NormalizedBar, ...]
    manifest: DataVersionManifest

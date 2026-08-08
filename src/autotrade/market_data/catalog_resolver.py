"""P2-D07 fixed-snapshot Instrument Catalog resolver.

This module is intentionally pure: it loads no files, reads no environment
variables, and makes no network, Broker, or vendor calls.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol

ResolutionStatus = Literal["resolved", "pending", "ambiguous", "not_found", "unknown"]


@dataclass(frozen=True)
class ResolveInstrumentRequest:
    """A symbol observation supplied by a fixed caller-owned snapshot."""

    vendor: str
    dataset_id: str
    stype: str
    symbol: str
    observed_at: datetime
    vendor_instrument_id: int | None = None


@dataclass(frozen=True)
class ResolveInstrumentResult:
    """A resolution result; only ``resolved`` carries an instrument ID."""

    status: ResolutionStatus
    instrument_id: str | None
    mapping_id: str | None
    catalog_version: str
    reason: str | None
    instrument_class: str | None = None
    instrument_status: str | None = None


@dataclass(frozen=True)
class _Mapping:
    mapping_id: str
    vendor: str
    dataset_id: str
    stype: str
    symbol: str
    valid_from: datetime
    valid_to: datetime | None
    instrument_id: str
    instrument_status: str
    tick_size: str | None
    vendor_instrument_id: int | None
    instrument_class: str | None = None


class CatalogAudit(Protocol):
    """In-memory audit boundary; implementations must not perform external I/O here."""

    def record(self, request: ResolveInstrumentRequest, mapping_id: str, catalog_version: str) -> bool:
        """Record the resolution fact, returning false when it cannot be retained."""


class InMemoryCatalogAudit:
    """Default audit sink for fixture-only tests; it does not write to disk."""

    def record(self, request: ResolveInstrumentRequest, mapping_id: str, catalog_version: str) -> bool:
        del request, mapping_id, catalog_version
        return True


class CatalogResolver:
    """Resolve only one active, fully specified mapping from an immutable fixture."""

    def __init__(self, catalog_version: str, mappings: Sequence[_Mapping], audit: CatalogAudit) -> None:
        self._catalog_version = catalog_version
        self._mappings = tuple(mappings)
        self._audit = audit

    @classmethod
    def from_fixture(cls, fixture: Mapping[str, object], audit: CatalogAudit | None = None) -> CatalogResolver:
        """Build a resolver from a caller-provided fixed fixture, without I/O."""
        catalog_version = fixture.get("catalog_version")
        raw_mappings = fixture.get("mappings")
        if not isinstance(catalog_version, str) or not catalog_version or not isinstance(raw_mappings, list):
            raise ValueError("invalid fixed catalog fixture")
        return cls(
            catalog_version,
            tuple(_mapping_from_fixture(item) for item in raw_mappings),
            audit or InMemoryCatalogAudit(),
        )

    def resolve(self, request: ResolveInstrumentRequest) -> ResolveInstrumentResult:
        """Return an ID only for exactly one active mapping valid at the observed UTC time."""
        if request.observed_at.tzinfo is None or request.observed_at.utcoffset() != UTC.utcoffset(request.observed_at):
            return ResolveInstrumentResult("unknown", None, None, self._catalog_version, "OBSERVED_AT_NOT_UTC")
        candidates = tuple(
            mapping
            for mapping in self._mappings
            if mapping.vendor == request.vendor
            and mapping.dataset_id == request.dataset_id
            and mapping.stype == request.stype
            and mapping.symbol == request.symbol
            and (request.vendor_instrument_id is None or mapping.vendor_instrument_id == request.vendor_instrument_id)
            and mapping.valid_from <= request.observed_at
            and (mapping.valid_to is None or request.observed_at < mapping.valid_to)
        )
        if len(candidates) == 0:
            return ResolveInstrumentResult("not_found", None, None, self._catalog_version, "MAPPING_NOT_UNIQUE")
        if len(candidates) != 1:
            return ResolveInstrumentResult("ambiguous", None, None, self._catalog_version, "MAPPING_NOT_UNIQUE")
        candidate = candidates[0]
        if candidate.instrument_status != "active" or candidate.tick_size is None:
            return ResolveInstrumentResult(
                "unknown",
                None,
                candidate.mapping_id,
                self._catalog_version,
                "REQUIRED_ATTRIBUTE_UNKNOWN",
                candidate.instrument_class,
                candidate.instrument_status,
            )
        if not self._audit.record(request, candidate.mapping_id, self._catalog_version):
            return ResolveInstrumentResult(
                "unknown", None, candidate.mapping_id, self._catalog_version, "CATALOG_AUDIT_FAILED"
            )
        return ResolveInstrumentResult(
            "resolved",
            candidate.instrument_id,
            candidate.mapping_id,
            self._catalog_version,
            None,
            candidate.instrument_class,
            candidate.instrument_status,
        )


def _mapping_from_fixture(raw: object) -> _Mapping:
    if not isinstance(raw, Mapping):
        raise ValueError("invalid fixed catalog mapping")
    required = (
        "mapping_id",
        "vendor",
        "dataset_id",
        "stype",
        "symbol",
        "valid_from",
        "instrument_id",
        "instrument_status",
    )
    values = {key: _required_string(raw, key) for key in required}
    raw_valid_to = raw.get("valid_to")
    if raw_valid_to is not None and not isinstance(raw_valid_to, str):
        raise ValueError("invalid fixed catalog mapping")
    tick_size = raw.get("tick_size")
    if tick_size is not None and (not isinstance(tick_size, str) or not _is_positive_decimal(tick_size)):
        raise ValueError("invalid fixed catalog mapping")
    vendor_instrument_id = raw.get("vendor_instrument_id")
    if vendor_instrument_id is not None and (
        isinstance(vendor_instrument_id, bool) or not isinstance(vendor_instrument_id, int) or vendor_instrument_id <= 0
    ):
        raise ValueError("invalid fixed catalog mapping")
    valid_from = _utc_datetime(values["valid_from"])
    valid_to = _utc_datetime(raw_valid_to) if raw_valid_to is not None else None
    if valid_to is not None and valid_from >= valid_to:
        raise ValueError("invalid fixed catalog mapping")
    return _Mapping(
        mapping_id=values["mapping_id"],
        vendor=values["vendor"],
        dataset_id=values["dataset_id"],
        stype=values["stype"],
        symbol=values["symbol"],
        valid_from=valid_from,
        valid_to=valid_to,
        instrument_id=values["instrument_id"],
        instrument_status=values["instrument_status"],
        tick_size=tick_size,
        vendor_instrument_id=vendor_instrument_id,
        instrument_class=_optional_string(raw, "instrument_class"),
    )


def _utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("invalid fixed catalog mapping")
    return parsed


def _required_string(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError("invalid fixed catalog mapping")
    return value


def _optional_string(raw: Mapping[str, object], key: str) -> str | None:
    value = raw.get(key)
    if value is not None and (not isinstance(value, str) or not value):
        raise ValueError("invalid fixed catalog mapping")
    return value


def _is_positive_decimal(value: str) -> bool:
    try:
        parsed = Decimal(value)
        return parsed.is_finite() and parsed > 0
    except InvalidOperation:
        return False

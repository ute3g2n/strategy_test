"""P2-D07 IC-F02: fixed-fixture Instrument Catalog resolution tests."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from autotrade.market_data.catalog_resolver import CatalogAudit, CatalogResolver, ResolveInstrumentRequest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "market_data" / "catalog_resolver_fixture.json"


def resolver() -> CatalogResolver:
    return CatalogResolver.from_fixture(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def request(symbol: str, observed_at: str = "2026-06-15T12:00:00+00:00") -> ResolveInstrumentRequest:
    return ResolveInstrumentRequest(
        "fixture_vendor", "fixture_dataset", "raw_symbol", symbol, datetime.fromisoformat(observed_at)
    )


def test_resolves_a_unique_active_mapping_from_fixed_fixture() -> None:
    result = resolver().resolve(request("FIX-2026M"))

    assert (result.status, result.instrument_id, result.mapping_id, result.catalog_version) == (
        "resolved",
        "fixture-instrument-001",
        "map-fixture-001",
        "fixture-catalog-v1",
    )


def test_does_not_guess_when_no_mapping_is_valid_at_observed_time() -> None:
    result = resolver().resolve(request("FIX-2026M", "2026-07-01T00:00:00+00:00"))

    assert (result.status, result.instrument_id, result.reason) == ("not_found", None, "MAPPING_NOT_UNIQUE")


def test_stops_when_required_instrument_attributes_are_unknown() -> None:
    result = resolver().resolve(request("PENDING-2026M"))

    assert (result.status, result.instrument_id, result.reason) == ("unknown", None, "REQUIRED_ATTRIBUTE_UNKNOWN")


def test_does_not_choose_between_multiple_valid_mappings() -> None:
    result = resolver().resolve(request("AMB-2026M"))

    assert (result.status, result.instrument_id, result.reason) == ("ambiguous", None, "MAPPING_NOT_UNIQUE")


def test_rejects_a_naive_observed_time_instead_of_using_current_time() -> None:
    naive = ResolveInstrumentRequest(
        "fixture_vendor", "fixture_dataset", "raw_symbol", "FIX-2026M", datetime(2026, 6, 15, 12)
    )

    result = resolver().resolve(naive)

    assert (result.status, result.instrument_id, result.reason) == ("unknown", None, "OBSERVED_AT_NOT_UTC")


def test_resolves_an_open_ended_mapping_without_using_current_time() -> None:
    result = resolver().resolve(request("OPEN-2026M", "2030-01-01T00:00:00+00:00"))

    assert result.status == "resolved"


def test_rejects_a_non_utc_or_non_positive_fixture_mapping() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["mappings"][0]["valid_from"] = "2026-06-01T00:00:00+09:00"
    fixture["mappings"][0]["tick_size"] = "0"

    with pytest.raises(ValueError, match="invalid fixed catalog mapping"):
        CatalogResolver.from_fixture(fixture)


def test_rejects_a_non_finite_tick_size_in_the_fixed_fixture() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["mappings"][0]["tick_size"] = "Infinity"

    with pytest.raises(ValueError, match="invalid fixed catalog mapping"):
        CatalogResolver.from_fixture(fixture)


def test_stops_when_in_memory_catalog_audit_rejects_a_resolution() -> None:
    class RejectingAudit(CatalogAudit):
        def record(self, request: ResolveInstrumentRequest, mapping_id: str, catalog_version: str) -> bool:
            del request, mapping_id, catalog_version
            return False

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    result = CatalogResolver.from_fixture(fixture, audit=RejectingAudit()).resolve(request("FIX-2026M"))

    assert (result.status, result.instrument_id, result.reason) == ("unknown", None, "CATALOG_AUDIT_FAILED")

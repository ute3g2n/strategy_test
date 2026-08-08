from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from autotrade.market_data.catalog_resolver import CatalogResolver, ResolveInstrumentRequest


def test_dbn_catalog_snapshot_binds_external_ids_and_rejects_spread() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "market_data" / "dbn_catalog_mcl_20260615.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    resolver = CatalogResolver.from_fixture(fixture)
    observed_at = datetime(2026, 6, 15, 12, tzinfo=UTC)

    expected = {
        42026511: ("resolved", "instrument-mclq6"),
        42025624: ("resolved", "instrument-mclu6"),
        42460441: ("unknown", None),
        42026750: ("resolved", "instrument-mcln6"),
    }
    for vendor_instrument_id, (status, instrument_id) in expected.items():
        result = resolver.resolve(
            ResolveInstrumentRequest(
                vendor="databento",
                dataset_id="GLBX.MDP3",
                stype="raw_symbol",
                symbol={
                    42026511: "MCLQ6",
                    42025624: "MCLU6",
                    42460441: "MCLN6-MCLQ6",
                    42026750: "MCLN6",
                }[vendor_instrument_id],
                observed_at=observed_at,
                vendor_instrument_id=vendor_instrument_id,
            )
        )
        assert (result.status, result.instrument_id) == (status, instrument_id)
        if vendor_instrument_id == 42460441:
            assert (result.instrument_class, result.instrument_status) == ("spread", "pending")
        elif vendor_instrument_id in {42026511, 42025624, 42026750}:
            assert (result.instrument_class, result.instrument_status) == ("future", "active")

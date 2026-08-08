"""P2-07 implementation tests for immutable local stores and event types."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from autotrade.market_data.manifest import ManifestBuilder
from autotrade.market_data.normalized_store import LocalNormalizedStore
from autotrade.market_data.quality import QualityChecker
from autotrade.market_data.raw_store import LocalRawStore
from autotrade.market_data.store_contracts import (
    MarketEvent,
    NormalizedBar,
    RawWriteRequest,
)


def raw_request(metadata: dict[str, str] | None = None) -> RawWriteRequest:
    return RawWriteRequest(
        request_fingerprint="fixture-request-001",
        payload=b"fixed-raw-payload",
        metadata=metadata or {"dataset": "fixture_dataset", "schema": "ohlcv-1m"},
        received_at_utc=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
    )


def normalized_bar(close: str = "70.10") -> NormalizedBar:
    return NormalizedBar(
        instrument_id="fixture-instrument-001",
        event_time_utc=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        open="70.00",
        high="70.25",
        low="69.75",
        close=close,
        volume=10,
        raw_object_id="raw-fixture-001",
        quality_flags=(),
    )


def manifest(report_hash: str = "sha256:quality-fixed"):
    return ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report_hash,
    )


def test_raw_store_is_idempotent_and_never_overwrites_completed_payload(tmp_path: Path) -> None:
    store = LocalRawStore(tmp_path)
    first = store.put_if_absent(raw_request())
    second = store.put_if_absent(raw_request())

    assert first.created is True
    assert second.created is False
    assert second.raw_object_id == first.raw_object_id
    assert second.payload_sha256 == first.payload_sha256

    payload_path = tmp_path / "raw" / first.raw_object_id / "payload.bin"
    payload_path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="RAW_CHECKSUM_MISMATCH"):
        store.put_if_absent(raw_request())


def test_raw_store_rejects_secret_like_metadata_and_naive_time(tmp_path: Path) -> None:
    store = LocalRawStore(tmp_path)
    with pytest.raises(ValueError, match="SECRET_METADATA_REJECTED"):
        store.put_if_absent(raw_request({"api_key": "must-not-be-stored"}))

    naive = raw_request()
    naive = RawWriteRequest(naive.request_fingerprint, naive.payload, naive.metadata, datetime(2026, 6, 15, 12))
    with pytest.raises(ValueError, match="RECEIVED_AT_NOT_UTC"):
        store.put_if_absent(naive)


def test_normalized_store_rejects_bad_quality_and_same_version_conflict(tmp_path: Path) -> None:
    store = LocalNormalizedStore(tmp_path)
    bad_report = QualityChecker.check((normalized_bar(),), injected_flags=("MISSING_DATA",))
    with pytest.raises(ValueError, match="QUALITY_REJECTED"):
        store.write_if_absent((normalized_bar(),), manifest(bad_report.quality_report_sha256), bad_report)

    report = QualityChecker.check((normalized_bar(),))
    good_manifest = manifest(report.quality_report_sha256)
    store.write_if_absent((normalized_bar(),), good_manifest, report)
    with pytest.raises(ValueError, match="DATA_VERSION_CONFLICT"):
        store.write_if_absent((normalized_bar("70.20"),), good_manifest, report)


def test_market_event_values_are_read_only_and_keep_data_version() -> None:
    event = MarketEvent(
        event_id="event-001",
        run_id="run-001",
        instrument_id="fixture-instrument-001",
        event_time_utc=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        received_at_utc=datetime(2026, 6, 15, 12, 0, 1, tzinfo=UTC),
        exchange_time_local="2026-06-15T21:00:00+09:00",
        bar_close_time=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        event_kind="BAR_1M",
        values={"close": "70.10"},
        quality_flags=(),
        data_version="dv_fixture_v1",
    )

    assert event.data_version == "dv_fixture_v1"
    with pytest.raises(TypeError):
        event.values["close"] = "70.20"  # type: ignore[index]

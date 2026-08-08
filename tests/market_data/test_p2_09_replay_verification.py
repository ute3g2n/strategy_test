"""P2-09 verification of the fixed Data Quality / Replay contract."""

from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from autotrade.market_data.manifest import ManifestBuilder
from autotrade.market_data.quality import QualityChecker
from autotrade.market_data.store_contracts import MarketEvent, NormalizedBar

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "market_data" / "data_quality_replay_fixture.json"
FIXTURE_SHA256 = "a30055c3dfc71834801d298f57c4f758e602cf6fcec057762c15a0c8c27f1b79"


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _bars() -> tuple[NormalizedBar, ...]:
    rows = _fixture()["bars"]
    assert isinstance(rows, list)
    return tuple(
        NormalizedBar(
            instrument_id=row["instrument_id"],
            event_time_utc=datetime.fromisoformat(row["event_time_utc"]),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
            raw_object_id=row["raw_object_id"],
            quality_flags=tuple(row["quality_flags"]),
        )
        for row in rows
    )


def _manifest() -> tuple[object, object]:
    bars = _bars()
    report = QualityChecker.check(bars)
    manifest = ManifestBuilder.build(
        raw_sha256s=("sha256:" + sha256(b"fixed-raw-payload").hexdigest(),),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
        fixture_sha256="sha256:" + FIXTURE_SHA256,
        code_revision="fixture-code-revision",
        source_mode="fixture_only",
    )
    return manifest, report


def _events(data_version: str) -> tuple[MarketEvent, ...]:
    return tuple(
        MarketEvent(
            event_id=f"event-{index}",
            run_id="RUN-P2-RPL-001",
            instrument_id=bar.instrument_id,
            event_time_utc=bar.event_time_utc,
            received_at_utc=bar.event_time_utc,
            exchange_time_local=None,
            bar_close_time=bar.event_time_utc,
            event_kind="BAR_1M",
            values={"open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close, "volume": str(bar.volume)},
            quality_flags=bar.quality_flags,
            data_version=data_version,
        )
        for index, bar in enumerate(_bars())
    )


def test_fixture_quality_matrix_is_fail_closed() -> None:
    data = _fixture()
    cases = data["cases"]
    assert isinstance(cases, dict)
    for case in cases.values():
        assert isinstance(case, dict)
        flags = tuple(case["quality_flags"])
        report = QualityChecker.check(_bars(), injected_flags=flags)
        assert report.publishable is case["publishable"]
        assert report.signal_generation_allowed is case["publishable"]

    unknown_report = QualityChecker.check(_bars(), injected_flags=("UNKNOWN_QUALITY",))
    assert unknown_report.publishable is False
    assert unknown_report.signal_generation_allowed is False


def test_fixture_replay_manifest_and_market_events_are_deterministic() -> None:
    first_manifest, first_report = _manifest()
    second_manifest, second_report = _manifest()

    assert first_manifest == second_manifest
    assert first_report == second_report
    assert first_manifest.data_version == "dv_ed27a1e51b4a39bef629"
    assert (
        first_report.quality_report_sha256 == "sha256:39de9d12fc61df12cec6c8a4eafb3f1a8cf40772955ae05f94afd3e8f5cccc9b"
    )
    first_events = _events(first_manifest.data_version)
    second_events = _events(second_manifest.data_version)
    assert first_events == second_events
    assert all(event.data_version == first_manifest.data_version for event in first_events)


def test_conditional_universe_cannot_mix_into_main_fixture() -> None:
    contract = _fixture()["replay_contract"]
    assert isinstance(contract, dict)
    assert set(contract["conditional_universe"]).isdisjoint(contract["main_universe"])

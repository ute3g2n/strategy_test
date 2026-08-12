"""P5-06 fixed-fixture Data contract and fail-closed quality tests."""

from __future__ import annotations

import json
import socket
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from autotrade.market_data.manifest import ManifestBuilder, normalized_content_sha256
from autotrade.market_data.normalized_store import LocalNormalizedStore
from autotrade.market_data.quality import QualityChecker
from autotrade.market_data.store_contracts import NormalizedBar

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "market_data" / "data_quality_replay_fixture.json"
FIXTURE_SHA256 = "c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99"
CALENDAR_HASH = "sha256:calendar-fixed"


def fixture_bars() -> tuple[NormalizedBar, ...]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    rows = fixture["bars"]
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


def quality_manifest(bars: tuple[NormalizedBar, ...]):
    report = QualityChecker.check(bars)
    return report, ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=normalized_content_sha256(bars),
        fixture_sha256=f"sha256:{FIXTURE_SHA256}",
        code_revision="p5-local-fixed",
    )


def test_p5_fixed_fixture_contract_is_read_only_and_complete() -> None:
    assert sha256(FIXTURE_PATH.read_bytes()).hexdigest() == FIXTURE_SHA256
    assert fixture_bars()


@pytest.mark.parametrize(
    "bars",
    [
        (),
        fixture_bars() + (fixture_bars()[0],),
        (fixture_bars()[1], fixture_bars()[0]),
    ],
)
def test_p5_missing_duplicate_and_out_of_order_are_fail_closed(bars: tuple[NormalizedBar, ...]) -> None:
    report = QualityChecker.check(bars)

    assert report.publishable is False
    assert report.signal_generation_allowed is False


def test_p5_calendar_mismatch_and_future_look_ahead_are_fail_closed() -> None:
    bars = fixture_bars()
    calendar_mismatch = QualityChecker.check(
        bars,
        calendar_hash=CALENDAR_HASH,
        expected_calendar_hash="sha256:calendar-other",
    )
    future = QualityChecker.check(
        (replace(bars[0], event_time_utc=datetime(2026, 6, 15, 12, 1, tzinfo=UTC)),),
        as_of_utc=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        calendar_hash=CALENDAR_HASH,
        expected_calendar_hash=CALENDAR_HASH,
    )

    assert "CALENDAR_MISMATCH" in calendar_mismatch.flags
    assert calendar_mismatch.publishable is False
    assert "FUTURE_DATA" in future.flags
    assert future.signal_generation_allowed is False


def test_p5_hash_mismatch_rejects_replay_and_replay_is_deterministic(tmp_path: Path) -> None:
    bars = fixture_bars()
    report, manifest = quality_manifest(bars)
    store = LocalNormalizedStore(tmp_path)
    store.write_if_absent(bars, manifest, report)
    assert store.read_replay_snapshot(manifest.data_version).bars == bars

    snapshot_path = tmp_path / "normalized" / f"{manifest.data_version}.json"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    payload["manifest"]["quality_report_sha256"] = "sha256:tampered"
    snapshot_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(manifest.data_version)


def test_p5_quality_contract_performs_no_external_io(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("external I/O is forbidden")

    monkeypatch.setattr(socket, "create_connection", blocked_network)
    report = QualityChecker.check(
        fixture_bars(),
        as_of_utc=datetime(2026, 6, 15, 12, 1, tzinfo=UTC),
        calendar_hash=CALENDAR_HASH,
        expected_calendar_hash=CALENDAR_HASH,
    )

    assert report.publishable is True

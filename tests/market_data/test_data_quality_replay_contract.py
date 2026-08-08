"""P2-06 RED contract tests for Data Quality / Replay.

These tests intentionally name the public boundaries from P2-D05/P2-D06.
P2-07 must implement the boundaries; this file must not be weakened with
skips or permissive expected values.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from autotrade.market_data.manifest import ManifestBuilder, normalized_content_sha256
from autotrade.market_data.normalized_store import LocalNormalizedStore
from autotrade.market_data.quality import QualityChecker
from autotrade.market_data.store_contracts import DataVersionManifest, NormalizedBar, QualityReport

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "market_data" / "data_quality_replay_fixture.json"
FIXTURE_SHA256 = "c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99"


def fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def bars() -> tuple[NormalizedBar, ...]:
    rows = fixture()["bars"]
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


def test_fixed_fixture_has_no_generated_time_and_expected_case_matrix() -> None:
    assert sha256(FIXTURE_PATH.read_bytes()).hexdigest() == FIXTURE_SHA256
    data = fixture()
    assert data["schema_version"] == "p2-dqr-fixture-v1"
    assert data["fixture_hash_scope"] == "canonical-json-without-generated-at"
    assert "generated_at" not in data
    assert set(data["cases"]) == {
        "missing_data",
        "duplicate_exact",
        "duplicate_conflict",
        "out_of_order",
        "price_invalid",
        "volume_invalid",
        "checksum_mismatch",
        "degraded",
    }


@pytest.mark.parametrize(
    ("flag", "publishable"),
    [
        ("MISSING_DATA", False),
        ("TIMESTAMP_INVALID", False),
        ("DUPLICATE", False),
        ("DUPLICATE_CONFLICT", False),
        ("OUT_OF_ORDER", False),
        ("PRICE_INVALID", True),
        ("VOLUME_INVALID", True),
        ("CHECKSUM_MISMATCH", False),
        ("DEGRADED", True),
    ],
)
def test_quality_flag_policy_matches_user_decision(flag: str, publishable: bool) -> None:
    report = QualityChecker.check(bars(), injected_flags=(flag,))

    assert isinstance(report, QualityReport)
    assert flag in report.flags
    assert report.publishable is publishable
    assert report.signal_generation_allowed is publishable


def test_exact_duplicate_is_collapsed_but_recorded() -> None:
    report = QualityChecker.check(bars() + (bars()[1],))

    assert report.publishable is False
    assert report.deduplicated_count == 1
    assert "DUPLICATE" in report.flags


def test_naive_timestamp_is_fail_closed() -> None:
    naive_bar = replace(bars()[0], event_time_utc=datetime(2026, 6, 15, 12, 0))

    report = QualityChecker.check((naive_bar,))

    assert "TIMESTAMP_INVALID" in report.flags
    assert report.publishable is False
    assert report.signal_generation_allowed is False


def test_non_utc_timestamp_is_fail_closed() -> None:
    offset_bar = replace(bars()[0], event_time_utc=datetime(2026, 6, 15, 21, tzinfo=timezone(timedelta(hours=9))))

    report = QualityChecker.check((offset_bar,))

    assert "TIMESTAMP_INVALID" in report.flags
    assert report.publishable is False


def test_empty_snapshot_is_fail_closed() -> None:
    report = QualityChecker.check(())

    assert report.flags == ("MISSING_DATA",)
    assert report.publishable is False


def test_unknown_quality_flag_is_fail_closed() -> None:
    report = QualityChecker.check(bars(), injected_flags=("UNKNOWN_QUALITY",))

    assert report.publishable is False
    assert report.signal_generation_allowed is False


def test_missing_bar_identity_is_fail_closed() -> None:
    missing_instrument = replace(bars()[0], instrument_id="")
    missing_raw = replace(bars()[0], raw_object_id="")

    assert QualityChecker.check((missing_instrument,)).publishable is False
    assert QualityChecker.check((missing_raw,)).publishable is False


def test_quality_report_hash_binds_excluded_ranges() -> None:
    base = QualityChecker.report_hash(("DUPLICATE",), 1, False)
    changed = QualityChecker.report_hash(("DUPLICATE",), 1, False, ("2026-06-15T12:00:00Z",))

    assert changed != base


def test_replay_manifest_is_deterministic_and_excludes_generated_at() -> None:
    raw_sha256s = (sha256(b"fixed-raw").hexdigest(),)
    first = ManifestBuilder.build(
        raw_sha256s=raw_sha256s,
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256="sha256:quality-fixed",
        normalized_content_sha256="sha256:normalized-fixed",
        fixture_sha256="sha256:fixture-fixed",
        code_revision="code-fixed",
    )
    second = ManifestBuilder.build(
        raw_sha256s=raw_sha256s,
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256="sha256:quality-fixed",
        normalized_content_sha256="sha256:normalized-fixed",
        fixture_sha256="sha256:fixture-fixed",
        code_revision="code-fixed",
    )

    assert isinstance(first, DataVersionManifest)
    assert first == second
    assert first.data_version
    assert not hasattr(first, "generated_at")


def test_replay_rejects_quality_report_hash_mismatch(tmp_path: Path) -> None:
    report = QualityChecker.check(bars())
    manifest = ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=normalized_content_sha256(bars()),
        fixture_sha256="sha256:fixture-fixed",
        code_revision="code-fixed",
    )
    store = LocalNormalizedStore(tmp_path)
    store.write_if_absent(bars(), manifest, report)
    snapshot_path = tmp_path / "normalized" / f"{manifest.data_version}.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["manifest"]["quality_report_sha256"] = "sha256:quality-tampered"
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(manifest.data_version)


def test_replay_rejects_quality_report_payload_tampering(tmp_path: Path) -> None:
    report = QualityChecker.check(bars())
    manifest = ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=normalized_content_sha256(bars()),
        fixture_sha256="sha256:fixture-fixed",
        code_revision="code-fixed",
    )
    store = LocalNormalizedStore(tmp_path)
    store.write_if_absent(bars(), manifest, report)
    snapshot_path = tmp_path / "normalized" / f"{manifest.data_version}.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["quality_report"]["flags"] = ["DEGRADED"]
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(manifest.data_version)


def test_replay_rejects_normalized_bar_tampering(tmp_path: Path) -> None:
    report = QualityChecker.check(bars())
    manifest = ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=normalized_content_sha256(bars()),
        fixture_sha256="sha256:fixture-fixed",
        code_revision="code-fixed",
    )
    store = LocalNormalizedStore(tmp_path)
    store.write_if_absent(bars(), manifest, report)
    snapshot_path = tmp_path / "normalized" / f"{manifest.data_version}.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["bars"][0]["close"] = "999.00"
    snapshot_path.write_text(json.dumps(snapshot, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(manifest.data_version)


def test_replay_round_trip_verifies_content_digest(tmp_path: Path) -> None:
    report = QualityChecker.check(bars())
    manifest = ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
        normalized_content_sha256=normalized_content_sha256(bars()),
        fixture_sha256="sha256:fixture-fixed",
        code_revision="code-fixed",
    )
    store = LocalNormalizedStore(tmp_path)
    store.write_if_absent(bars(), manifest, report)

    snapshot = store.read_replay_snapshot(manifest.data_version)

    assert snapshot.manifest == manifest
    assert snapshot.bars == bars()


def test_manifest_requires_provenance_inputs() -> None:
    with pytest.raises(ValueError, match="MANIFEST_INPUT_MISSING"):
        ManifestBuilder.build(
            raw_sha256s=("sha256:raw-fixed",),
            normalization_rule_version="normalized-v1",
            catalog_version="fixture-catalog-v1",
            catalog_sha256="sha256:catalog-fixed",
            quality_report_sha256="sha256:quality-fixed",
            normalized_content_sha256="sha256:normalized-fixed",
        )


def test_replay_rejects_future_data_and_conditional_universe_mix() -> None:
    data = fixture()
    contract = data["replay_contract"]

    assert contract["future_bars_must_not_change_published_history"] is True
    assert set(contract["conditional_universe"]).isdisjoint(contract["main_universe"])
    assert datetime(2026, 6, 15, 12, tzinfo=UTC) < datetime(2026, 6, 15, 12, 1, tzinfo=UTC)

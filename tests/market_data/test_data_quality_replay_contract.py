"""P2-06 RED contract tests for Data Quality / Replay.

These tests intentionally name the public boundaries from P2-D05/P2-D06.
P2-07 must implement the boundaries; this file must not be weakened with
skips or permissive expected values.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from autotrade.market_data.manifest import ManifestBuilder
from autotrade.market_data.normalized_store import LocalNormalizedStore
from autotrade.market_data.quality import QualityChecker
from autotrade.market_data.store_contracts import DataVersionManifest, NormalizedBar, QualityReport

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "market_data" / "data_quality_replay_fixture.json"


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
        ("DUPLICATE_CONFLICT", False),
        ("OUT_OF_ORDER", False),
        ("PRICE_INVALID", False),
        ("VOLUME_INVALID", False),
        ("CHECKSUM_MISMATCH", False),
        ("DEGRADED", False),
    ],
)
def test_fail_closed_quality_flags_never_publish_a_data_version(flag: str, publishable: bool) -> None:
    report = QualityChecker.check(bars(), injected_flags=(flag,))

    assert isinstance(report, QualityReport)
    assert flag in report.flags
    assert report.publishable is publishable
    assert report.signal_generation_allowed is False


def test_exact_duplicate_is_collapsed_but_recorded() -> None:
    report = QualityChecker.check(bars() + (bars()[1],))

    assert report.publishable is True
    assert report.deduplicated_count == 1
    assert "DUPLICATE" in report.flags


def test_replay_manifest_is_deterministic_and_excludes_generated_at() -> None:
    raw_sha256s = (sha256(b"fixed-raw").hexdigest(),)
    first = ManifestBuilder.build(
        raw_sha256s=raw_sha256s,
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256="sha256:quality-fixed",
    )
    second = ManifestBuilder.build(
        raw_sha256s=raw_sha256s,
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256="sha256:quality-fixed",
    )

    assert isinstance(first, DataVersionManifest)
    assert first == second
    assert first.data_version
    assert not hasattr(first, "generated_at")


def test_replay_rejects_quality_report_hash_mismatch(tmp_path: Path) -> None:
    report = QualityReport(
        flags=(),
        publishable=True,
        signal_generation_allowed=True,
        quality_report_sha256="sha256:quality-fixed",
    )
    manifest = ManifestBuilder.build(
        raw_sha256s=("sha256:raw-fixed",),
        normalization_rule_version="normalized-v1",
        catalog_version="fixture-catalog-v1",
        catalog_sha256="sha256:catalog-fixed",
        quality_report_sha256=report.quality_report_sha256,
    )
    store = LocalNormalizedStore(tmp_path)
    store.write_if_absent(bars(), manifest, report)
    tampered = replace(manifest, quality_report_sha256="sha256:quality-tampered")

    with pytest.raises(ValueError, match="MANIFEST_INTEGRITY"):
        store.read_replay_snapshot(tampered.data_version)


def test_replay_rejects_future_data_and_conditional_universe_mix() -> None:
    data = fixture()
    contract = data["replay_contract"]

    assert contract["future_bars_must_not_change_published_history"] is True
    assert set(contract["conditional_universe"]).isdisjoint(contract["main_universe"])
    assert datetime(2026, 6, 15, 12, tzinfo=UTC) < datetime(2026, 6, 15, 12, 1, tzinfo=UTC)

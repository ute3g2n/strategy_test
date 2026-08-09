"""GREEN integrity contracts for P3-05 Backtest fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
MANIFEST_PATH = ROOT / "fixtures" / "phase3" / "run_p3_gold_fixture_manifest.json"


def _fixture_manifest() -> dict[str, object]:
    value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.mark.parametrize(
    "fixture_name",
    [
        "calendar_us_futures_v1.json",
        "backtest_replay_v1.json",
        "bias_manifest_v1.json",
        "performance_synthetic_v1.json",
    ],
)
def test_phase3_backtest_fixture_is_declared_and_hash_pinned(fixture_name: str) -> None:
    """Every small P3 Backtest fixture has an immutable parent-manifest digest."""
    manifest = _fixture_manifest()
    children = manifest["children"]
    assert isinstance(children, list)
    child = next(item for item in children if item["path"].endswith(fixture_name))
    path = ROOT.parent / child["path"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == child["sha256"]


def test_performance_fixture_keeps_phase3_limits_as_data() -> None:
    fixture = json.loads((ROOT / "fixtures" / "phase3" / "performance_synthetic_v1.json").read_text(encoding="utf-8"))
    assert len(fixture["markets"]) == 5
    assert fixture["calendar_years"] == [2024, 2025]
    assert fixture["limits"] == {"elapsed_minutes": 30, "peak_rss_gib": 8}

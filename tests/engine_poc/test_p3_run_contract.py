"""P3-09 execution and adapter contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.quality_gate.p3_poc_runner import (
    RunContractError,
    build_lean_output_from_observed,
    validate_observed_bars,
    validate_p3_09_run_manifest,
)

ROOT = Path(__file__).parents[2]
FIXTURE_PATH = ROOT / "tests/fixtures/phase3/m30_backtest_v2.json"
EXPECTED_PATH = ROOT / "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/core-reference.json"
RUN_MANIFEST_PATH = ROOT / "tests/evidence/phase3/RUN-P3-POC-001/run-manifest.json"


def _observed_bars() -> list[dict[str, str]]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [
        {
            "event_id": event_id,
            "event_time_utc": bar["open_time_utc"],
            "bar_close_time_utc": bar["close_time_utc"],
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
            "volume": bar["volume"],
        }
        for event_id, bar in zip(fixture["source_event_ids"], fixture["direct_m1_bars"], strict=True)
    ]


def test_fixed_run_manifest_binds_approval_and_all_hashes() -> None:
    manifest = json.loads(RUN_MANIFEST_PATH.read_text(encoding="utf-8"))

    validated = validate_p3_09_run_manifest(manifest, ROOT)

    assert validated["run_id"] == "RUN-P3-POC-001"
    assert validated["execution"]["network_mode"] == "none"
    assert validated["authorization"]["execution_allowed"] is True


def test_observed_bars_are_ordered_and_complete() -> None:
    observed = _observed_bars()

    validate_observed_bars(observed)

    invalid = copy.deepcopy(observed)
    invalid[1], invalid[2] = invalid[2], invalid[1]
    with pytest.raises(RunContractError, match="ordered"):
        validate_observed_bars(invalid)


def test_lean_adapter_replays_only_observed_bars_and_matches_core_reference() -> None:
    output, projection = build_lean_output_from_observed(_observed_bars(), ROOT)
    expected: dict[str, Any] = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))

    assert output["status"] == "PASS"
    assert output["hashes"] == expected["hashes"]
    assert output["sequence"] == expected["lean_projection"]["sequence"]
    assert projection["observed_event_count"] == 30
    assert projection["derived_bars"]


def test_observed_bar_mutation_cannot_be_normalized_into_a_pass() -> None:
    observed = _observed_bars()
    observed[0]["close"] = "999.00"

    with pytest.raises(RunContractError, match="fixture"):
        build_lean_output_from_observed(observed, ROOT)

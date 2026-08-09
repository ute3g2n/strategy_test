"""GREEN integrity contracts for immutable P3-05R M30 fixture material."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

STRATEGY_FIXTURE = Path(__file__).parents[1] / "fixtures" / "strategy" / "m30_strategy_v2.json"
BACKTEST_FIXTURE = Path(__file__).parents[1] / "fixtures" / "phase3" / "m30_backtest_v2.json"
BACKTEST_CONTRACT_FIXTURE = Path(__file__).parents[1] / "fixtures" / "phase3" / "m30_backtest_contract_cases_v2.json"
PARENT_MANIFEST = Path(__file__).parents[1] / "fixtures" / "phase3" / "run_p3_m30_fixture_manifest_v2.json"
V1_STRATEGY_FIXTURE = Path(__file__).parents[1] / "fixtures" / "strategy" / "turtle_golden_v1.json"
STRATEGY_FIXTURE_SHA256 = "116799b5fe7b0c6b96c2eae0a5e3988473a28b865f7da44e0982a1927b7379b1"
BACKTEST_FIXTURE_SHA256 = "7282ea7bda1c6701cffc2e8e1949b2b38e036b107b99d2857b1508afe51f6e08"
BACKTEST_CONTRACT_FIXTURE_SHA256 = "a3fda8506aeba088405bcb3436aaa14957f990427f2e3dd9c0f1c8188fba63db"
PARENT_MANIFEST_SHA256 = "224d6c54fe0fdbf039bc5819140e9d12aa23e27e55ece5de22a5f4800b2b985b"
V1_STRATEGY_FIXTURE_SHA256 = "571ac25dbd5f2786cde2aa5cb25f66232bdb4a4ab5e3fc3c6ff5f3e09e37a1f4"
V1_SEMANTIC_HASH = "sha256:31c704a6b5b99eafaaf397c65a023b7fc52634593c6cd21244173f5ec3c9c41f"


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_m30_v2_fixtures_are_hash_pinned_and_complete() -> None:
    strategy = _read_object(STRATEGY_FIXTURE)
    backtest = _read_object(BACKTEST_FIXTURE)
    contracts = _read_object(BACKTEST_CONTRACT_FIXTURE)
    manifest = _read_object(PARENT_MANIFEST)

    assert hashlib.sha256(STRATEGY_FIXTURE.read_bytes()).hexdigest() == STRATEGY_FIXTURE_SHA256
    assert hashlib.sha256(BACKTEST_FIXTURE.read_bytes()).hexdigest() == BACKTEST_FIXTURE_SHA256
    assert hashlib.sha256(BACKTEST_CONTRACT_FIXTURE.read_bytes()).hexdigest() == BACKTEST_CONTRACT_FIXTURE_SHA256
    assert hashlib.sha256(PARENT_MANIFEST.read_bytes()).hexdigest() == PARENT_MANIFEST_SHA256
    assert strategy["schema_version"] == "p3-m30-strategy-fixture-v2"
    assert backtest["schema_version"] == "p3-m30-backtest-fixture-v2"
    assert contracts["schema_version"] == "p3-m30-backtest-contract-cases-v2"
    assert (
        strategy["fixture_status"] == backtest["fixture_status"] == contracts["fixture_status"] == "PROPOSED_FOR_H3_1R"
    )
    assert set(strategy["cases"]) == {f"GT-TUR-{number:03d}" for number in range(36, 41)}
    assert set(contracts["cases"]) == {f"BT-{number:03d}" for number in range(38, 43)}
    assert manifest["run_id"] == "RUN-P3-M30-001"
    assert manifest["fixture_status"] == "PROPOSED_FOR_H3_1R"
    assert [child["sha256"] for child in manifest["children"]] == [
        STRATEGY_FIXTURE_SHA256,
        BACKTEST_FIXTURE_SHA256,
        BACKTEST_CONTRACT_FIXTURE_SHA256,
    ]

    v1 = _read_object(V1_STRATEGY_FIXTURE)
    assert hashlib.sha256(V1_STRATEGY_FIXTURE.read_bytes()).hexdigest() == V1_STRATEGY_FIXTURE_SHA256
    v1_semantic_payload = {
        "candidate_decisions": v1["candidate_decisions"],
        "binding": v1["binding"],
        "enabled_timeframes": ["M15", "H1", "H4", "D1"],
    }
    v1_semantic_hash = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(v1_semantic_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    assert v1_semantic_hash == V1_SEMANTIC_HASH
    assert strategy["cases"]["GT-TUR-036"]["input"]["v1_fixture_sha256"] == f"sha256:{V1_STRATEGY_FIXTURE_SHA256}"
    assert strategy["cases"]["GT-TUR-036"]["input"]["v1_semantic_hash"] == V1_SEMANTIC_HASH
    assert strategy["cases"]["GT-TUR-036"]["expected"]["v1"]["semantic_hash"] == V1_SEMANTIC_HASH
    assert contracts["cases"]["BT-042"]["input"]["v1_fixture_sha256"] == f"sha256:{V1_STRATEGY_FIXTURE_SHA256}"
    assert contracts["cases"]["BT-042"]["expected"]["semantic_hashes"] == [V1_SEMANTIC_HASH, V1_SEMANTIC_HASH]


def test_m30_normal_fixture_has_exactly_thirty_direct_closed_m1_bars_from_the_session_anchor() -> None:
    fixture = _read_object(BACKTEST_FIXTURE)
    anchor = fixture["session_anchor"]
    bars = fixture["direct_m1_bars"]
    expected = fixture["expected_normal_m30"]
    assert isinstance(anchor, dict)
    assert isinstance(bars, list)
    assert isinstance(expected, dict)
    assert len(bars) == 30
    assert expected["source_bar_kind"] == "BAR_1M"
    assert expected["source_bar_count"] == len(bars)
    source_event_ids = fixture["source_event_ids"]
    assert isinstance(source_event_ids, list)
    assert source_event_ids == [f"evt-m1-{index:03d}" for index in range(30)]
    assert fixture["source_event_ids_sha256"] == (
        "sha256:f3a02f9b1ed01ceabeefa8ecc479fa5ccebf34afef34acc6494d3fe21669207e"
    )

    anchor_time = datetime.fromisoformat(str(anchor["m30_open_utc"]).replace("Z", "+00:00"))
    assert anchor_time.tzinfo is UTC
    for index, bar in enumerate(bars):
        assert isinstance(bar, dict)
        open_time = datetime.fromisoformat(str(bar["open_time_utc"]).replace("Z", "+00:00"))
        close_time = datetime.fromisoformat(str(bar["close_time_utc"]).replace("Z", "+00:00"))
        assert open_time == anchor_time + timedelta(minutes=index)
        assert close_time == open_time + timedelta(minutes=1)
        assert bar["is_closed"] is True
        assert "M15" not in bar


def test_m30_red_contracts_keep_the_answer_key_out_of_production_calls() -> None:
    for path in (
        Path(__file__).with_name("test_turtle_m30_red_contract.py"),
        Path(__file__).parents[1] / "backtest" / "test_backtest_m30_red_contract.py",
    ):
        source = path.read_text(encoding="utf-8")
        assert "operation(input_value)" in source or "operation(_input_for_case(case_id))" in source
        assert "operation(case" not in source
        assert "operation(expected" not in source

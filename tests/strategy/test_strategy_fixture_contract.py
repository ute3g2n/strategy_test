"""Fixed P3-05 fixture contracts that are already GREEN without Strategy code.

The business-rule tests are intentionally kept in the separate RED file.  This
file proves that their input material is deterministic and that P3-06 must
continue to consume the existing Phase 2 MarketEvent contract unchanged.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path

from autotrade.market_data.store_contracts import MarketEvent

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "strategy"
PROJECT_ROOT = Path(__file__).parents[2]
PARENT_MANIFEST = PROJECT_ROOT / "tests" / "fixtures" / "phase3" / "run_p3_gold_fixture_manifest.json"
TRUSTED_SCOPES = PROJECT_ROOT / "scripts" / "quality_gate" / "trusted_scopes.json"
TURTLE_FIXTURE = FIXTURE_ROOT / "turtle_golden_v1.json"
MULTI_TIMEFRAME_FIXTURE = FIXTURE_ROOT / "multi_timeframe_v1.json"
TURTLE_FIXTURE_SHA256 = "571ac25dbd5f2786cde2aa5cb25f66232bdb4a4ab5e3fc3c6ff5f3e09e37a1f4"
MULTI_TIMEFRAME_FIXTURE_SHA256 = "17af6ef83ce770b275499967a28590726a3085bde0400ab7ef5498b8eb47abde"


def _read_fixture(path: Path) -> dict[str, object]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_turtle_fixture_is_complete_and_has_a_fixed_hash() -> None:
    fixture = _read_fixture(TURTLE_FIXTURE)

    assert sha256(TURTLE_FIXTURE.read_bytes()).hexdigest() == TURTLE_FIXTURE_SHA256
    assert fixture["schema_version"] == "p3-turtle-golden-v1"
    assert fixture["fixture_hash_scope"] == "utf-8-json-bytes-without-generated-at"
    assert fixture["fixture_status"] == "PROPOSED_FOR_H3_1"
    assert "generated_at" not in fixture
    cases = fixture["cases"]
    assert isinstance(cases, dict)
    assert set(cases) == {f"GT-TUR-{number:03d}" for number in range(1, 36)}
    assert all(isinstance(case, dict) and "input" in case and "expected" in case for case in cases.values())


def test_parent_manifest_binds_the_complete_fixture_set_and_trusted_scope() -> None:
    """RED tests may run directly only after every child is hash-bound to the parent."""
    parent = _read_fixture(PARENT_MANIFEST)
    trusted = _read_fixture(TRUSTED_SCOPES)
    scopes = trusted["scopes"]
    assert isinstance(scopes, dict)
    scope = scopes["RUN-P3-GOLD-001"]
    assert isinstance(scope, dict)
    expected_paths = {
        "tests/fixtures/strategy/turtle_golden_v1.json",
        "tests/fixtures/strategy/multi_timeframe_v1.json",
        "tests/fixtures/phase3/calendar_us_futures_v1.json",
        "tests/fixtures/phase3/backtest_replay_v1.json",
        "tests/fixtures/phase3/backtest_contract_cases_v1.json",
        "tests/fixtures/phase3/bias_manifest_v1.json",
        "tests/fixtures/phase3/performance_synthetic_v1.json",
    }
    children = parent["children"]
    assert isinstance(children, list)
    child_paths = {child["path"] for child in children}
    assert child_paths == expected_paths
    assert len(children) == len(child_paths)
    for child in children:
        path = PROJECT_ROOT / child["path"]
        assert sha256(path.read_bytes()).hexdigest() == child["sha256"]
    parent_hash = sha256(PARENT_MANIFEST.read_bytes()).hexdigest()
    fixture = scope["fixture"]
    assert isinstance(fixture, dict)
    assert fixture["checksum"] == f"sha256:{parent_hash}"


def test_red_contracts_do_not_pass_the_answer_key_to_production_operations() -> None:
    """Keep the expected answer in the test, preventing fixture-echo implementations."""
    for relative_path in (
        PROJECT_ROOT / "tests" / "strategy" / "test_turtle_golden_red_contract.py",
        PROJECT_ROOT / "tests" / "strategy" / "test_strategy_input_boundary_red.py",
        PROJECT_ROOT / "tests" / "backtest" / "test_backtest_red_contract.py",
    ):
        source = relative_path.read_text(encoding="utf-8")
        assert "evaluate_golden_case" not in source
        assert "evaluate_fixture_case" not in source
        assert "operation(case" not in source
        assert "case=rejected_case" not in source
        assert "case=simultaneous_close," not in source
    assert "operation(input_value)" in (
        PROJECT_ROOT / "tests" / "strategy" / "test_turtle_golden_red_contract.py"
    ).read_text(encoding="utf-8")
    assert "operation(input_value)" in (
        PROJECT_ROOT / "tests" / "backtest" / "test_backtest_red_contract.py"
    ).read_text(encoding="utf-8")


def test_multitimeframe_fixture_is_fixed_and_uses_utc_ordering() -> None:
    fixture = _read_fixture(MULTI_TIMEFRAME_FIXTURE)

    assert sha256(MULTI_TIMEFRAME_FIXTURE.read_bytes()).hexdigest() == MULTI_TIMEFRAME_FIXTURE_SHA256
    assert fixture["schema_version"] == "p3-multitimeframe-fixture-v1"
    assert fixture["fixture_hash_scope"] == "utf-8-json-bytes-without-generated-at"
    assert "generated_at" not in fixture
    simultaneous_close = fixture["simultaneous_close"]
    assert isinstance(simultaneous_close, dict)
    expected = simultaneous_close["expected"]
    assert isinstance(expected, dict)
    assert expected["normalized_order"] == ["M15", "H1", "H4", "D1"]
    assert expected["strategy_calls"] == 1


def test_existing_market_event_contract_is_immutable_and_utc_based() -> None:
    event_time = datetime(2026, 3, 10, 20, 0, tzinfo=UTC)
    event = MarketEvent(
        event_id="evt-p3-green-001",
        run_id="run-p3-green-001",
        instrument_id="fixture-instrument-001",
        event_time_utc=event_time,
        received_at_utc=event_time,
        exchange_time_local=None,
        bar_close_time=event_time + timedelta(minutes=1),
        event_kind="BAR_1M",
        values={"open": "100.00", "high": "101.00", "low": "99.00", "close": "100.50", "volume": "10"},
        quality_flags=(),
        data_version="dv_p3_fixture_001",
    )

    assert event.event_time_utc.tzinfo is UTC
    assert event.bar_close_time == event.event_time_utc + timedelta(minutes=1)
    assert dict(event.values)["close"] == "100.50"

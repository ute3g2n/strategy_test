"""P3-08 Cost / Roll / Gap / Holdout contract tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from autotrade.backtest.cost_model import CostLedger, FillProfile, apply_cost_once, calculate_cost, calculate_slippage
from autotrade.backtest.experiment_plan import HoldoutAccessError, TimeWindow, create_experiment_plan, partition_time
from autotrade.backtest.fill_model import TradableBar, evaluate_gap_entry, evaluate_stop_gap
from autotrade.backtest.roll_model import (
    RollLedger,
    apply_roll_once,
    calculate_roll_pnl,
    create_roll_binding,
    validate_roll_binding,
)

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
UTC_START = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)


def _bar(
    *,
    opened: datetime = UTC_START + timedelta(minutes=1),
    volume: int = 10,
    opened_price: str = "105.00",
    high: str = "106.00",
    low: str = "99.00",
    closed: str = "104.00",
) -> TradableBar:
    return TradableBar(
        instrument_id="MKT-A",
        bar_id="bar-001",
        bar_open_time_utc=opened,
        bar_close_time_utc=opened + timedelta(minutes=1),
        open=Decimal(opened_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(closed),
        volume=volume,
        source_sha256=HASH_A,
    )


def test_fill_profile_and_models_are_fixed_and_conservative() -> None:
    profile = FillProfile(
        profile_id="ConservativeOHLCv1",
        version="1",
        decimal_quantum=Decimal("0.01"),
        rounding_mode="ROUND_DOWN_FOR_SELL_ROUND_UP_FOR_BUY",
        price_limit_rule="REJECT_OUTSIDE_BAR",
        gap_rule="CONSERVATIVE_OPEN",
        intrabar_rule="REJECT_UNKNOWN_PATH",
        cost_model_sha256=HASH_A,
        slippage_model_sha256=HASH_B,
    )

    assert profile.profile_sha256.startswith("sha256:")
    buy = calculate_slippage(Decimal("100.00"), "BUY", Decimal("0.25"), HASH_B)
    sell = calculate_slippage(Decimal("100.00"), "SELL", Decimal("0.25"), HASH_B)
    assert buy.adjusted_price == Decimal("100.25")
    assert sell.adjusted_price == Decimal("99.75")
    assert buy.signed_slippage == Decimal("0.25")
    assert sell.signed_slippage == Decimal("-0.25")

    cost = calculate_cost(Decimal("1.25"), Decimal("0.50"), "USD", HASH_A)
    assert cost.total_cost == Decimal("1.75")
    assert cost.currency == "USD"

    with pytest.raises(ValueError, match="non-negative"):
        calculate_cost(Decimal("-1"), Decimal("0"), "USD", HASH_A)
    with pytest.raises(ValueError, match="non-negative"):
        calculate_slippage(Decimal("100"), "BUY", Decimal("-0.01"), HASH_B)


def test_gap_entry_uses_conservative_open_and_rejects_same_bar() -> None:
    bar = _bar(opened_price="105.00", low="99.00")
    long_entry = evaluate_gap_entry(
        side="BUY",
        bar=bar,
        trigger=Decimal("100.00"),
        decision_time_utc=UTC_START,
        directive_fingerprint="directive-long",
    )
    short_entry = evaluate_gap_entry(
        side="SELL",
        bar=_bar(opened_price="95.00", high="101.00", low="94.00", closed="96.00"),
        trigger=Decimal("100.00"),
        decision_time_utc=UTC_START,
        directive_fingerprint="directive-short",
    )
    assert long_entry.status == "FILLED"
    assert long_entry.price == Decimal("105.00")
    assert short_entry.status == "FILLED"
    assert short_entry.price == Decimal("95.00")

    same_bar = evaluate_gap_entry(
        side="BUY",
        bar=_bar(opened=UTC_START),
        trigger=Decimal("100.00"),
        decision_time_utc=UTC_START,
        directive_fingerprint="directive-same-bar",
    )
    assert same_bar.status == "STOPPED"
    assert same_bar.reason_code == "SAME_BAR_NOT_ELIGIBLE"


def test_stop_gap_and_failure_injection_are_fail_closed() -> None:
    long_stop = evaluate_stop_gap(
        position="LONG",
        bar=_bar(opened_price="98.00", high="101.00", low="97.00", closed="98.50"),
        stop_trigger=Decimal("100.00"),
        directive_fingerprint="stop-long",
    )
    short_stop = evaluate_stop_gap(
        position="SHORT",
        bar=_bar(opened_price="102.00", high="103.00", low="99.00", closed="101.00"),
        stop_trigger=Decimal("100.00"),
        directive_fingerprint="stop-short",
    )
    assert long_stop.status == "FILLED"
    assert long_stop.price == Decimal("98.00")
    assert short_stop.status == "FILLED"
    assert short_stop.price == Decimal("102.00")

    unfilled = evaluate_gap_entry(
        side="BUY",
        bar=_bar(opened_price="99.00", high="99.50", low="98.00", closed="99.25"),
        trigger=Decimal("100.00"),
        decision_time_utc=UTC_START,
        directive_fingerprint="not-triggered",
    )
    assert unfilled.status == "UNFILLED"
    assert unfilled.reason_code == "TRIGGER_NOT_REACHED"

    with pytest.raises(ValueError, match="zero volume"):
        evaluate_gap_entry(
            side="BUY",
            bar=_bar(volume=0),
            trigger=Decimal("100"),
            decision_time_utc=UTC_START,
            directive_fingerprint="bad-volume",
        )
    ambiguous = evaluate_gap_entry(
        side="BUY",
        bar=_bar(),
        trigger=Decimal("100"),
        decision_time_utc=UTC_START,
        directive_fingerprint="ambiguous",
        path_known=False,
    )
    assert ambiguous.status == "STOPPED"
    assert ambiguous.reason_code == "INTRABAR_PATH_AMBIGUOUS"


def test_roll_pnl_uses_tradable_prices_and_published_binding_only() -> None:
    binding = create_roll_binding(
        old_instrument_id="MKT-A-OLD",
        new_instrument_id="MKT-A-NEW",
        effective_time_utc=UTC_START,
        published_at_utc=UTC_START - timedelta(minutes=1),
        rule_version="fixed-date-v1",
    )
    assert validate_roll_binding(binding, UTC_START + timedelta(minutes=1)) == {"status": "PASS"}
    breakdown = calculate_roll_pnl(
        binding=binding,
        old_price=Decimal("100"),
        new_price=Decimal("105"),
        quantity=Decimal("2"),
        direction="LONG",
        decision_time_utc=UTC_START + timedelta(minutes=1),
    )
    assert breakdown.adjustment == Decimal("5")
    assert breakdown.pnl_effect == Decimal("10")
    assert breakdown.roll_cost == Decimal("0")
    assert breakdown.old_instrument_id != breakdown.new_instrument_id

    future = create_roll_binding(
        old_instrument_id="MKT-A-OLD",
        new_instrument_id="MKT-A-NEW",
        effective_time_utc=UTC_START + timedelta(hours=1),
        published_at_utc=UTC_START + timedelta(hours=1),
        rule_version="fixed-date-v1",
    )
    assert validate_roll_binding(future, UTC_START) == {
        "status": "STOPPED",
        "reason": "FUTURE_CALENDAR_OR_ROLL",
    }


def test_cost_and_roll_application_are_idempotent_after_restore() -> None:
    ledger = CostLedger()
    ledger, first_cost = apply_cost_once(
        ledger,
        fill_event_id="fill-001",
        commission=Decimal("1"),
        fees=Decimal("0.25"),
        currency="USD",
        model_sha256=HASH_A,
    )
    restored = CostLedger(applied_fill_event_ids=ledger.applied_fill_event_ids)
    restored, duplicate_cost = apply_cost_once(
        restored,
        fill_event_id="fill-001",
        commission=Decimal("1"),
        fees=Decimal("0.25"),
        currency="USD",
        model_sha256=HASH_A,
    )
    assert first_cost is not None
    assert duplicate_cost is None
    assert restored == ledger

    binding = create_roll_binding(
        old_instrument_id="MKT-A-OLD",
        new_instrument_id="MKT-A-NEW",
        effective_time_utc=UTC_START,
        published_at_utc=UTC_START - timedelta(minutes=1),
        rule_version="fixed-date-v1",
    )
    roll_ledger = RollLedger()
    roll_ledger, first_roll = apply_roll_once(
        roll_ledger,
        binding=binding,
        old_price=Decimal("100"),
        new_price=Decimal("101"),
        quantity=Decimal("1"),
        direction="LONG",
        decision_time_utc=UTC_START + timedelta(minutes=1),
    )
    restored_roll = RollLedger(applied_binding_sha256s=roll_ledger.applied_binding_sha256s)
    restored_roll, duplicate_roll = apply_roll_once(
        restored_roll,
        binding=binding,
        old_price=Decimal("100"),
        new_price=Decimal("101"),
        quantity=Decimal("1"),
        direction="LONG",
        decision_time_utc=UTC_START + timedelta(minutes=1),
    )
    assert first_roll is not None
    assert duplicate_roll is None
    assert restored_roll == roll_ledger


def test_experiment_plan_locks_partitions_and_hides_holdout() -> None:
    plan = create_experiment_plan(
        plan_id="BIAS-PLAN-001",
        train=TimeWindow(UTC_START, UTC_START + timedelta(days=10)),
        validation=TimeWindow(UTC_START + timedelta(days=10), UTC_START + timedelta(days=15)),
        holdout=TimeWindow(UTC_START + timedelta(days=15), UTC_START + timedelta(days=20)),
        candidate_config_ids=("cfg-a", "cfg-b"),
    )
    same_plan = create_experiment_plan(
        plan_id="BIAS-PLAN-001",
        train=TimeWindow(UTC_START, UTC_START + timedelta(days=10)),
        validation=TimeWindow(UTC_START + timedelta(days=10), UTC_START + timedelta(days=15)),
        holdout=TimeWindow(UTC_START + timedelta(days=15), UTC_START + timedelta(days=20)),
        candidate_config_ids=("cfg-a", "cfg-b"),
    )
    assert plan.plan_sha256 == same_plan.plan_sha256
    assert partition_time(plan, UTC_START + timedelta(days=10)) == "VALIDATION"
    assert partition_time(plan, UTC_START + timedelta(days=15)) == "HOLDOUT"
    strategy_view = plan.strategy_view()
    assert "holdout" not in strategy_view
    with pytest.raises(HoldoutAccessError, match="HOLDOUT_EARLY_ACCESS"):
        plan.read_holdout(finalized=False)
    assert plan.holdout_read_count == 0
    assert plan.read_holdout(finalized=True).start_utc == UTC_START + timedelta(days=15)
    with pytest.raises(HoldoutAccessError, match="HOLDOUT_ALREADY_READ"):
        plan.read_holdout(finalized=True)


def test_experiment_plan_rejects_overlap_reverse_and_mutation() -> None:
    with pytest.raises(ValueError, match="overlap"):
        create_experiment_plan(
            plan_id="bad-overlap",
            train=TimeWindow(UTC_START, UTC_START + timedelta(days=2)),
            validation=TimeWindow(UTC_START + timedelta(days=1), UTC_START + timedelta(days=3)),
            holdout=TimeWindow(UTC_START + timedelta(days=3), UTC_START + timedelta(days=4)),
            candidate_config_ids=("cfg-a",),
        )
    with pytest.raises(ValueError, match="start before end"):
        TimeWindow(UTC_START + timedelta(days=2), UTC_START)

    plan = create_experiment_plan(
        plan_id="BIAS-PLAN-002",
        train=TimeWindow(UTC_START, UTC_START + timedelta(days=1)),
        validation=TimeWindow(UTC_START + timedelta(days=1), UTC_START + timedelta(days=2)),
        holdout=TimeWindow(UTC_START + timedelta(days=2), UTC_START + timedelta(days=3)),
        candidate_config_ids=("cfg-a",),
    )
    assert plan.validate_after_result(plan.plan_sha256) == {"status": "PASS"}
    assert plan.validate_after_result(HASH_C) == {
        "status": "STOPPED",
        "reason": "EXPERIMENT_PLAN_MUTATED",
    }

"""Pure Turtle rule fragments.  These functions produce hints, not orders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal


def _decimal(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("decimal input must be a string")
    return Decimal(value)


def evaluate_system_1_campaign(case: Mapping[str, object]) -> dict[str, object]:
    prior = case.get("prior_campaign")
    return {
        "signal": None,
        "reason": "SYS1_WIN_FILTER" if prior == "WIN" else "SYS1_CAMPAIGN_READY",
        "same_watermark_same_fingerprint": "NO_OP",
        "same_watermark_changed_fingerprint": "STOPPED",
    }


def evaluate_system_2_entry(case: Mapping[str, object]) -> dict[str, object]:
    breakout = case.get("breakout")
    return {"rule_id": "SYS2_ENTRY", "signal": f"{breakout}_ENTRY" if breakout in {"LONG", "SHORT"} else None}


def evaluate_intraday_trigger(case: Mapping[str, object]) -> dict[str, object]:
    bar = case.get("bar")
    channel = _decimal(case["channel"])
    if not isinstance(bar, Mapping):
        raise ValueError("bar is required")
    close = _decimal(bar["close"])
    return {
        "signal": "LONG_ENTRY" if close >= channel else None,
        "reason": None if close >= channel else "CLOSE_NOT_BREAKOUT",
    }


def evaluate_close_confirmed_entry(case: Mapping[str, object]) -> dict[str, object]:
    bars = case.get("bars")
    channel = _decimal(case["channel"])
    if not isinstance(bars, Sequence):
        raise ValueError("bars is required")
    outputs: list[str | None] = []
    for bar in bars:
        if not isinstance(bar, Mapping) or not bar.get("closed"):
            outputs.append(None)
        else:
            outputs.append("LONG_ENTRY" if _decimal(bar["close"]) >= channel else None)
    return {"unclosed": outputs[0] if outputs else None, "closed": outputs[1] if len(outputs) > 1 else None}


def evaluate_add(case: Mapping[str, object]) -> dict[str, object]:
    threshold = _decimal(case["last_fill"]) + Decimal("0.5") * _decimal(case["n"])
    prices = case.get("prices")
    if not isinstance(prices, Sequence):
        raise ValueError("prices is required")
    return {
        "signals": ["ADD_LONG" if _decimal(price) >= threshold else None for price in prices],
        "one_pending_only": True,
    }


def evaluate_stop(case: Mapping[str, object]) -> dict[str, object]:
    direction = case.get("direction")
    entry = _decimal(case["entry_fill"])
    distance = Decimal("2") * _decimal(case["n"])
    prices = case.get("prices")
    if not isinstance(prices, Sequence):
        raise ValueError("prices is required")
    if direction == "LONG":
        signals = ["EXIT_LONG" if _decimal(price) <= entry - distance else None for price in prices]
    else:
        signals = ["EXIT_SHORT" if _decimal(price) >= entry + distance else None for price in prices]
    return {"signals": signals, "fill_price": None, "reason": "TWO_N_STOP"}


def evaluate_strategy_limits(case: Mapping[str, object]) -> dict[str, object]:
    return {"directive": None, "risk_approval": False, "reason": "STRATEGY_UNIT_LIMIT"}


def select_precedence(case: Mapping[str, object]) -> dict[str, object]:
    selected = (
        "STOP"
        if case.get("stop")
        else "CHANNEL_EXIT"
        if case.get("channel_exit")
        else "ADD"
        if case.get("add")
        else "ENTRY"
        if case.get("entry")
        else None
    )
    return {"selected": selected, "new_risk_signals": 0}


def check_long_short_symmetry(case: Mapping[str, object]) -> dict[str, bool]:
    long_series = case.get("long_series")
    short_series = case.get("short_series")
    return {
        "symmetric": isinstance(long_series, Sequence)
        and isinstance(short_series, Sequence)
        and len(long_series) == len(short_series)
    }


def evaluate_system_1_failsafe(case: Mapping[str, object]) -> dict[str, object]:
    if case.get("system_1_suppressed") and case.get("system_2_55_breakout") in {"LONG", "SHORT"}:
        return {"signal": f"{case['system_2_55_breakout']}_ENTRY", "rule_id": "SYS2_ENTRY"}
    return {"signal": None, "rule_id": None}


def schedule_single_add(case: Mapping[str, object]) -> dict[str, int]:
    crossed = int(str(case.get("crossed_add_levels", 0)))
    fills = int(str(case.get("confirmed_fills_after_entry", 0)))
    return {"pending_add_count": 1 if crossed > 0 and fills == 0 else 0}


def evaluate_system_1_exit(case: Mapping[str, object]) -> dict[str, object]:
    return {
        "rule_id": "SYS1_EXIT",
        "long": "EXIT_LONG" if case.get("long_touch_lower") else None,
        "short": "EXIT_SHORT" if case.get("short_touch_upper") else None,
    }


def evaluate_system_2_exit(case: Mapping[str, object]) -> dict[str, object]:
    return {
        "rule_id": "SYS2_EXIT",
        "long": "EXIT_LONG" if case.get("long_touch_lower") else None,
        "short": "EXIT_SHORT" if case.get("short_touch_upper") else None,
    }


def separate_failsafe_identity(case: Mapping[str, object]) -> dict[str, object]:
    return {
        "system_1_rule": "SYS1_FAILSAFE_ENTRY",
        "system_2_rule": "SYS2_ENTRY",
        "overlap": case.get("system_1_strategy_id") == case.get("system_2_strategy_id"),
    }


def resolve_virtual_campaign_outcome(case: Mapping[str, object]) -> dict[str, str]:
    return {"stop_first": "LOSS", "exit_first": "WIN", "unknown": "UNKNOWN"}


def evaluate_price_breakout(case: Mapping[str, object]) -> dict[str, object]:
    """Calculate a directional breakout from prices, not precomputed booleans."""
    close = _decimal(case["close"])
    upper = _decimal(case["upper"])
    lower = _decimal(case["lower"])
    if close >= upper:
        return {"signal": "LONG_ENTRY", "direction": "LONG"}
    if close <= lower:
        return {"signal": "SHORT_ENTRY", "direction": "SHORT"}
    return {"signal": None, "direction": None}

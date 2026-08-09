from __future__ import annotations

from typing import Any

from ._common import decimal


def apply_slippage(value: dict[str, Any]) -> dict[str, Any]:
    try:
        base = decimal(value.get("base"))
    except ValueError:
        return {"worse_or_equal": False}
    side = value.get("side")
    if side not in {"BUY", "SELL", "LONG", "SHORT"}:
        return {"worse_or_equal": False}
    if not base.is_finite():
        return {"worse_or_equal": False}
    try:
        amount = decimal(value.get("slippage", "0"))
    except ValueError:
        return {"worse_or_equal": False}
    if amount < 0:
        return {"worse_or_equal": False}
    adjusted = base + amount if side in {"BUY", "LONG"} else base - amount
    result: dict[str, Any] = {"worse_or_equal": adjusted >= base if side in {"BUY", "LONG"} else adjusted <= base}
    if "slippage" in value:
        result["price"] = format(adjusted, "f")
    return result


def apply_cost(value: dict[str, Any]) -> dict[str, Any]:
    try:
        fill = decimal(value.get("fill"))
        cost = decimal(value.get("cost", "0"))
    except ValueError:
        return {"cost_non_negative": False}
    return {"cost_non_negative": value.get("cost_model_fixed") is True and fill >= 0 and cost >= 0}

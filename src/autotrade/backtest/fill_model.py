from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_UP
from typing import Any

from ._common import decimal


def fill_conservative_stop(value: dict[str, Any]) -> dict[str, Any]:
    side = value.get("side")
    if side not in {"LONG", "SHORT"}:
        return {"status": "STOPPED", "reason": "INVALID_SIDE"}
    try:
        opened = decimal(value.get("open"))
        stop = decimal(value.get("stop"))
        quantum = decimal(value.get("decimal_quantum", "0.01"))
        if quantum <= 0:
            raise ValueError("invalid quantum")
    except ValueError:
        return {"status": "STOPPED", "reason": "INVALID_PRICE"}
    selected = min(opened, stop) if side == "LONG" else max(opened, stop)
    rounding = ROUND_UP if side == "LONG" else ROUND_DOWN
    selected = selected.quantize(quantum, rounding=rounding)
    if side == "LONG":
        return {"price": format(selected, "f")}
    return {"price": format(selected, "f")}


def fill_next_bar_only(value: dict[str, Any]) -> dict[str, Any]:
    eligible = value.get("eligible_open")
    if not isinstance(eligible, str) or eligible.lower() in {"", "false"}:
        return {"status": "STOPPED"}
    if "T" in eligible:
        try:
            from ._common import parse_utc

            parse_utc(eligible)
        except ValueError:
            return {"status": "STOPPED", "reason": "NO_ELIGIBLE_BAR"}
    return {"same_bar_fill": False}


def reject_intrabar_ambiguity(value: dict[str, Any]) -> dict[str, Any]:
    return (
        {"status": "STOPPED", "reason": "INTRABAR_PATH_AMBIGUOUS"}
        if not value.get("path_known")
        else {"status": "PASS"}
    )

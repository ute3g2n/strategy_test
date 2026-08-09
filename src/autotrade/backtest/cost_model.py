from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ._common import decimal
from .contracts import canonical_hash


def _require_hash(value: str, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 71
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise ValueError(f"{name} must be a sha256 hash")
    return value


def _require_side(value: str) -> str:
    if value in {"BUY", "LONG"}:
        return "BUY"
    if value in {"SELL", "SHORT"}:
        return "SELL"
    raise ValueError("side must be BUY/SELL or LONG/SHORT")


@dataclass(frozen=True)
class FillProfile:
    """Immutable, conservative fill/cost rule binding."""

    profile_id: str
    version: str
    decimal_quantum: Decimal
    rounding_mode: str
    price_limit_rule: str
    gap_rule: str
    intrabar_rule: str
    cost_model_sha256: str
    slippage_model_sha256: str

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value for value in (self.profile_id, self.version)):
            raise ValueError("profile identity is required")
        if not isinstance(self.decimal_quantum, Decimal):
            raise ValueError("decimal_quantum must be positive")
        try:
            quantum = decimal(self.decimal_quantum)
        except ValueError as error:
            raise ValueError("decimal_quantum must be positive") from error
        if not quantum.is_finite() or quantum <= 0:
            raise ValueError("decimal_quantum must be positive")
        if any(
            not isinstance(value, str) or not value
            for value in (self.rounding_mode, self.price_limit_rule, self.gap_rule, self.intrabar_rule)
        ):
            raise ValueError("fill rules must be fixed")
        _require_hash(self.cost_model_sha256, name="cost_model_sha256")
        _require_hash(self.slippage_model_sha256, name="slippage_model_sha256")

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "decimal_quantum": self.decimal_quantum,
            "rounding_mode": self.rounding_mode,
            "price_limit_rule": self.price_limit_rule,
            "gap_rule": self.gap_rule,
            "intrabar_rule": self.intrabar_rule,
            "cost_model_sha256": self.cost_model_sha256,
            "slippage_model_sha256": self.slippage_model_sha256,
        }

    @property
    def profile_sha256(self) -> str:
        return canonical_hash(self.as_dict())


@dataclass(frozen=True)
class SlippageDecision:
    base_price: Decimal
    adjusted_price: Decimal
    signed_slippage: Decimal
    model_sha256: str
    reason_code: str


@dataclass(frozen=True)
class CostBreakdown:
    commission: Decimal
    fees: Decimal
    total_cost: Decimal
    currency: str
    model_sha256: str


@dataclass(frozen=True)
class CostLedger:
    """Consumed fill IDs make cost application idempotent across restore."""

    applied_fill_event_ids: tuple[str, ...] = ()


def calculate_slippage(
    base_price: Decimal,
    side: str,
    amount: Decimal,
    model_sha256: str,
    *,
    reason_code: str = "SLIPPAGE_APPLIED",
) -> SlippageDecision:
    base = decimal(base_price)
    slippage = decimal(amount)
    if slippage < 0:
        raise ValueError("slippage must be non-negative")
    model = _require_hash(model_sha256, name="model_sha256")
    normalized_side = _require_side(side)
    adjusted = base + slippage if normalized_side == "BUY" else base - slippage
    signed = adjusted - base
    return SlippageDecision(base, adjusted, signed, model, reason_code)


def calculate_cost(
    commission: Decimal,
    fees: Decimal,
    currency: str,
    model_sha256: str,
) -> CostBreakdown:
    commission_value = decimal(commission)
    fees_value = decimal(fees)
    if commission_value < 0 or fees_value < 0:
        raise ValueError("commission and fees must be non-negative")
    if not isinstance(currency, str) or not currency:
        raise ValueError("currency is required")
    model = _require_hash(model_sha256, name="model_sha256")
    return CostBreakdown(commission_value, fees_value, commission_value + fees_value, currency, model)


def apply_cost_once(
    ledger: CostLedger,
    *,
    fill_event_id: str,
    commission: Decimal,
    fees: Decimal,
    currency: str,
    model_sha256: str,
) -> tuple[CostLedger, CostBreakdown | None]:
    if not isinstance(fill_event_id, str) or not fill_event_id:
        raise ValueError("fill_event_id is required")
    if fill_event_id in ledger.applied_fill_event_ids:
        return ledger, None
    breakdown = calculate_cost(commission, fees, currency, model_sha256)
    return CostLedger(ledger.applied_fill_event_ids + (fill_event_id,)), breakdown


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

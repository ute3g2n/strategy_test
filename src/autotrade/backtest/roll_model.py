from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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


def _require_utc(value: datetime, *, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{name} must be UTC")


@dataclass(frozen=True)
class RollBinding:
    old_instrument_id: str
    new_instrument_id: str
    effective_time_utc: datetime
    published_at_utc: datetime
    rule_version: str
    binding_sha256: str

    def payload(self) -> dict[str, Any]:
        return {
            "old_instrument_id": self.old_instrument_id,
            "new_instrument_id": self.new_instrument_id,
            "effective_time_utc": self.effective_time_utc,
            "published_at_utc": self.published_at_utc,
            "rule_version": self.rule_version,
        }


@dataclass(frozen=True)
class RollBreakdown:
    old_instrument_id: str
    new_instrument_id: str
    effective_time_utc: datetime
    old_price: Decimal
    new_price: Decimal
    adjustment: Decimal
    roll_cost: Decimal
    pnl_effect: Decimal
    binding_sha256: str


@dataclass(frozen=True)
class RollLedger:
    """Consumed binding hashes make roll application idempotent across restore."""

    applied_binding_sha256s: tuple[str, ...] = ()


def create_roll_binding(
    *,
    old_instrument_id: str,
    new_instrument_id: str,
    effective_time_utc: datetime,
    published_at_utc: datetime,
    rule_version: str,
) -> RollBinding:
    if not old_instrument_id or not new_instrument_id or old_instrument_id == new_instrument_id:
        raise ValueError("roll instruments must be distinct")
    if not rule_version:
        raise ValueError("roll rule version is required")
    _require_utc(effective_time_utc, name="effective_time_utc")
    _require_utc(published_at_utc, name="published_at_utc")
    payload = {
        "old_instrument_id": old_instrument_id,
        "new_instrument_id": new_instrument_id,
        "effective_time_utc": effective_time_utc,
        "published_at_utc": published_at_utc,
        "rule_version": rule_version,
    }
    return RollBinding(
        old_instrument_id,
        new_instrument_id,
        effective_time_utc,
        published_at_utc,
        rule_version,
        canonical_hash(payload),
    )


def validate_roll_binding(binding: RollBinding, decision_time_utc: datetime) -> dict[str, str]:
    try:
        _require_utc(decision_time_utc, name="decision_time_utc")
        _require_utc(binding.effective_time_utc, name="effective_time_utc")
        _require_utc(binding.published_at_utc, name="published_at_utc")
        _require_hash(binding.binding_sha256, name="binding_sha256")
        if canonical_hash(binding.payload()) != binding.binding_sha256:
            raise ValueError("binding hash mismatch")
        if binding.published_at_utc > decision_time_utc or binding.effective_time_utc > decision_time_utc:
            return {"status": "STOPPED", "reason": "FUTURE_CALENDAR_OR_ROLL"}
        if binding.old_instrument_id == binding.new_instrument_id:
            raise ValueError("roll instruments are not distinct")
    except (TypeError, ValueError):
        return {"status": "STOPPED", "reason": "FUTURE_CALENDAR_OR_ROLL"}
    return {"status": "PASS"}


def calculate_roll_pnl(
    *,
    binding: RollBinding,
    old_price: Decimal,
    new_price: Decimal,
    quantity: Decimal,
    direction: str,
    decision_time_utc: datetime,
) -> RollBreakdown:
    validation = validate_roll_binding(binding, decision_time_utc)
    if validation["status"] != "PASS":
        raise ValueError(validation["reason"])
    old_value = decimal(old_price)
    new_value = decimal(new_price)
    units = decimal(quantity)
    if units <= 0:
        raise ValueError("quantity must be positive")
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("direction must be LONG or SHORT")
    adjustment = new_value - old_value
    pnl_effect = adjustment * units if direction == "LONG" else -adjustment * units
    roll_cost = max(-pnl_effect, Decimal("0"))
    return RollBreakdown(
        binding.old_instrument_id,
        binding.new_instrument_id,
        binding.effective_time_utc,
        old_value,
        new_value,
        adjustment,
        roll_cost,
        pnl_effect,
        binding.binding_sha256,
    )


def apply_roll_once(
    ledger: RollLedger,
    *,
    binding: RollBinding,
    old_price: Decimal,
    new_price: Decimal,
    quantity: Decimal,
    direction: str,
    decision_time_utc: datetime,
) -> tuple[RollLedger, RollBreakdown | None]:
    if binding.binding_sha256 in ledger.applied_binding_sha256s:
        return ledger, None
    breakdown = calculate_roll_pnl(
        binding=binding,
        old_price=old_price,
        new_price=new_price,
        quantity=quantity,
        direction=direction,
        decision_time_utc=decision_time_utc,
    )
    return RollLedger(ledger.applied_binding_sha256s + (binding.binding_sha256,)), breakdown


def apply_roll(value: dict[str, Any]) -> dict[str, Any]:
    return (
        {"status": "PASS"}
        if value.get("catalog_resolved") and value.get("published_before_decision")
        else {"status": "STOPPED"}
    )


def reject_roll_conflict(value: dict[str, Any]) -> dict[str, Any]:
    conflict = value.get("roll_and_stop_same_bar")
    if not isinstance(conflict, bool):
        return {"status": "STOPPED", "reason": "ROLL_CONFLICT_UNKNOWN"}
    return {"status": "STOPPED"} if conflict else {"status": "PASS"}

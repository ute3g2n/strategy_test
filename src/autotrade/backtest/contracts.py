"""Vendor-neutral contracts and deterministic serialization utilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class BacktestFailure:
    """A stable fail-closed reason (not an exception carrying data)."""

    reason: str
    detail: str | None = None

    def as_dict(self) -> dict[str, str]:
        result = {"reason": self.reason}
        if self.detail:
            result["detail"] = self.detail
        return result


def canonical_json(value: Any) -> bytes:
    """Encode JSON in the canonical form used for result fingerprints."""

    def encode(item: Any) -> str:
        if isinstance(item, Decimal):
            if not item.is_finite():
                raise ValueError("canonical decimal must be finite")
            return format(item, "f")
        if isinstance(item, datetime):
            if item.tzinfo is None or item.utcoffset() != UTC.utcoffset(item):
                raise ValueError("canonical time must be UTC")
            return item.astimezone(UTC).isoformat().replace("+00:00", "Z")
        raise TypeError(f"unsupported canonical value: {type(item).__name__}")

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=encode,
        allow_nan=False,
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def parse_utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("UTC timestamp string required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed.astimezone(UTC)


def decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("finite decimal string required") from error
    else:
        raise ValueError("finite decimal string required")
    if not parsed.is_finite():
        raise ValueError("finite decimal string required")
    return parsed

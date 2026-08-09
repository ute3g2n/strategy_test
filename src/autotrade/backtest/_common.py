from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def canonical(value: Any) -> str:
    def encode(item: Any) -> str:
        if isinstance(item, Decimal):
            if not item.is_finite():
                raise ValueError("canonical decimal must be finite")
            return format(item, "f")
        if isinstance(item, datetime):
            parsed = parse_utc(item.isoformat())
            return parsed.isoformat().replace("+00:00", "Z")
        raise TypeError(f"unsupported canonical value: {type(item).__name__}")

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=encode,
        allow_nan=False,
    )


def sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def parse_utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("UTC時刻がありません")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("UTC時刻ではありません")
    return parsed.astimezone(UTC)


def decimal(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("数値が不正です") from error
    if not result.is_finite():
        raise ValueError("有限値ではありません")
    return result

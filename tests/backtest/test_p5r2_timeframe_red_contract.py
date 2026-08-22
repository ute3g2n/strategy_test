"""P5R2 RED contracts for strategy timeframe and source-data quality."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest

from autotrade.application import preflight as preflight_module

ALLOWED_STRATEGY_TIMEFRAMES = ("15m", "30m", "1h", "4h", "1d")


def _require_contract(module: ModuleType, name: str, requirement: str) -> Callable[..., object]:
    operation = getattr(module, name, None)
    assert callable(operation), f"{requirement} RED: 未実装契約 {module.__name__}.{name}"
    return operation


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _closed_bar(open_time: str, *, closed: bool = True, provenance: object | None = "fixture") -> dict[str, object]:
    return {
        "open_time_utc": open_time,
        "close_time_utc": "2026-08-20T00:15:00Z",
        "open": "100.00",
        "high": "101.00",
        "low": "99.00",
        "close": "100.50",
        "volume": 10,
        "is_closed": closed,
        "provenance": provenance,
    }


def _run_input(
    *,
    strategy_timeframe: str = "15m",
    requested_range: dict[str, str] | None = None,
    bars: tuple[dict[str, object], ...] = (),
    data_quality: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "strategy_timeframe": strategy_timeframe,
        "requested_range": requested_range or {"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:00:00Z"},
        "data_version": "fixture-only-p5r2-v1",
        "bars": bars,
        "data_quality": data_quality or {},
    }


@pytest.mark.parametrize("timeframe", ALLOWED_STRATEGY_TIMEFRAMES)
def test_strategy_timeframe_accepts_only_the_five_new_selection_values(timeframe: str) -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-001",
    )

    result = operation(_run_input(strategy_timeframe=timeframe))

    assert _field(result, "decision") in {"PASS", "WARNING"}


@pytest.mark.parametrize("legacy_timeframe", ("1m", "M30"), ids=("source-1m", "legacy-m30"))
def test_strategy_timeframe_rejects_source_and_legacy_values(legacy_timeframe: str) -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-001",
    )

    result = operation(_run_input(strategy_timeframe=legacy_timeframe))

    assert _field(result, "decision") == "REJECT"
    assert "STRATEGY_TIMEFRAME_INVALID" in (_field(result, "reason_codes") or ())


def test_preflight_exposes_effective_end_after_the_last_closed_bar() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )

    result = operation(
        _run_input(
            requested_range={"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:00:00Z"},
            bars=(
                _closed_bar("2026-08-20T00:00:00Z"),
                _closed_bar("2026-08-20T00:15:00Z", closed=False),
            ),
        )
    )

    effective_range = _field(result, "effective_range")
    assert effective_range is not None
    assert "2026-08-20T00:00:00Z" in str(effective_range)


@pytest.mark.parametrize(
    "invalid_input",
    (
        pytest.param(
            _run_input(requested_range={"start": "2026-08-20T00:00:00+09:00", "end": "2026-08-20T01:00:00+09:00"}),
            id="non-utc-boundary",
        ),
        pytest.param(
            _run_input(bars=(_closed_bar("2026-08-20T00:00:00Z", closed=False),)),
            id="unclosed-bar",
        ),
        pytest.param(
            _run_input(
                bars=(
                    _closed_bar("2026-08-20T00:00:00Z", closed=False),
                    _closed_bar("2026-08-20T00:15:00Z", closed=False),
                )
            ),
            id="whole-period-unconfirmed",
        ),
    ),
)
def test_preflight_rejects_non_utc_or_unconfirmed_periods(invalid_input: dict[str, object]) -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )

    result = operation(invalid_input)

    assert _field(result, "decision") == "REJECT"
    assert _field(result, "reason_codes")


def test_single_internal_gap_is_usable_with_prior_close_warning_and_provenance() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-003",
    )

    result = operation(
        _run_input(
            data_quality={
                "missing_bars": [
                    {
                        "position": "internal",
                        "count": 1,
                        "repair": "PRIOR_CLOSE_OHLC_VOLUME_ZERO",
                        "ohlcv": {"open": "100.50", "high": "100.50", "low": "100.50", "close": "100.50", "volume": 0},
                        "provenance": {"source": "prior_close", "warning": "SINGLE_INTERNAL_GAP"},
                    }
                ]
            }
        )
    )

    assert _field(result, "decision") == "WARNING"
    assert _field(result, "quality_state") == "USABLE_WITH_WARNING"
    assert _field(result, "provenance")
    assert "SINGLE_INTERNAL_GAP" in str(_field(result, "reason_codes"))


@pytest.mark.parametrize(
    "invalid_quality",
    (
        pytest.param({"missing_bars": [{"position": "start", "count": 1}]}, id="endpoint-start"),
        pytest.param({"missing_bars": [{"position": "end", "count": 1}]}, id="endpoint-end"),
        pytest.param({"missing_bars": [{"position": "internal", "count": 2}]}, id="two-or-more"),
        pytest.param({"future_value": True}, id="future-value"),
        pytest.param({"reversed_order": True}, id="reversed-order"),
        pytest.param({"missing_bars": [{"position": "internal", "count": 1, "provenance": None}]}, id="no-provenance"),
    ),
)
def test_timeframe_quality_rejects_non_h1_gap_repairs(invalid_quality: dict[str, object]) -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-003",
    )

    result = operation(_run_input(data_quality=invalid_quality))

    assert _field(result, "decision") == "REJECT"
    assert _field(result, "reason_codes")

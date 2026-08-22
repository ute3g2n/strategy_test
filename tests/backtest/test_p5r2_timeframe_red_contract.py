"""P5R2 RED contracts for strategy timeframe and source-data quality."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from types import ModuleType

import pytest

from autotrade.application import preflight as preflight_module

ALLOWED_STRATEGY_TIMEFRAMES = ("15m", "30m", "1h", "4h", "1d")
TIMEFRAME_DELTAS = {
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}
DEFAULT_BAR_PROVENANCE = {"source_mode": "fixture_only", "dataset_id": "fixture-p5r2-v1", "record_id": "bar-0001"}


def _require_contract(module: ModuleType, name: str, requirement: str) -> Callable[..., object]:
    operation = getattr(module, name, None)
    assert callable(operation), f"{requirement} RED: 未実装契約 {module.__name__}.{name}"
    return operation


def _field(value: object, name: str) -> object:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def _codes(value: object) -> tuple[object, ...]:
    codes = _field(value, "reason_codes")
    return tuple(codes) if isinstance(codes, (list, tuple)) else ()


def _closed_bar(
    open_time: str,
    *,
    timeframe: str = "15m",
    closed: object = True,
    provenance: object = DEFAULT_BAR_PROVENANCE,
    close_time: str | None = None,
) -> dict[str, object]:
    opened = datetime.fromisoformat(open_time.replace("Z", "+00:00"))
    closed_at = opened + TIMEFRAME_DELTAS[timeframe]
    return {
        "open_time_utc": open_time,
        "close_time_utc": close_time or closed_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "open": "100.00",
        "high": "101.00",
        "low": "99.00",
        "close": "100.50",
        "volume": 10,
        "is_closed": closed,
        "timeframe": timeframe,
        "provenance": dict(provenance) if isinstance(provenance, dict) else provenance,
    }


def _run_input(
    *,
    strategy_timeframe: str = "15m",
    requested_range: dict[str, str] | None = None,
    bars: tuple[dict[str, object], ...] | None = None,
    data_quality: dict[str, object] | None = None,
) -> dict[str, object]:
    start = datetime(2026, 8, 20, tzinfo=UTC)
    fixture_timeframe = strategy_timeframe if strategy_timeframe in TIMEFRAME_DELTAS else "15m"
    default_end = start + TIMEFRAME_DELTAS[fixture_timeframe] * 2
    quality: dict[str, object] = {"quality_state": "USABLE"}
    if data_quality is not None:
        quality.update(data_quality)
    return {
        "symbol": "BTCUSDT",
        "strategy_timeframe": strategy_timeframe,
        "source_timeframe": "1m",
        "requested_range": requested_range
        or {"start": "2026-08-20T00:00:00Z", "end": default_end.isoformat().replace("+00:00", "Z")},
        "data_version": "fixture-only-p5r2-v1",
        "data_identity": {
            "source_mode": "fixture_only",
            "dataset_id": "fixture-p5r2-v1",
            "record_id": "dataset-p5r2-v1",
            "data_version": "fixture-only-p5r2-v1",
        },
        "bars": bars if bars is not None else (_closed_bar("2026-08-20T00:00:00Z", timeframe=fixture_timeframe),),
        "data_quality": quality,
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
    assert "STRATEGY_TIMEFRAME_INVALID" in _codes(result)


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
    assert _field(result, "decision") == "WARNING"
    assert _field(result, "quality_state") == "USABLE_WITH_WARNING"
    assert "2026-08-20T00:15:00Z" in str(effective_range)
    assert "PARTIAL_BAR_EXCLUDED" in _codes(result)


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


def test_preflight_rejects_unresolved_all_period_default() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )
    input_value = _run_input()
    input_value["default_range"] = True

    result = operation(input_value)

    assert _field(result, "decision") == "REJECT"
    assert "DEFAULT_RANGE_UNRESOLVED" in _codes(result)


@pytest.mark.parametrize(
    "requested_range",
    (
        {"start": "2026-08-20T00:05:00Z", "end": "2026-08-20T01:00:00Z"},
        {"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:05:00Z"},
    ),
)
def test_preflight_rejects_non_anchor_range_boundaries(requested_range: dict[str, str]) -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )

    result = operation(_run_input(requested_range=requested_range))

    assert _field(result, "decision") == "REJECT"
    assert "UTC_ANCHOR_INVALID" in _codes(result)


def test_preflight_rejects_empty_closed_data() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )

    result = operation(_run_input(bars=()))

    assert _field(result, "decision") == "REJECT"
    assert "DATA_EMPTY" in _codes(result)


def test_preflight_rejects_an_internal_unclosed_bar() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )

    result = operation(
        _run_input(
            bars=(
                _closed_bar("2026-08-20T00:00:00Z", closed=False),
                _closed_bar("2026-08-20T00:15:00Z"),
            )
        )
    )

    assert _field(result, "decision") == "REJECT"
    assert "UNCONFIRMED_BAR" in _codes(result)


@pytest.mark.parametrize(
    "mutation,reason",
    (
        pytest.param(
            lambda value: value["data_quality"].clear(),
            "DATA_QUALITY_REJECTED",
            id="quality-state-missing",
        ),
        pytest.param(
            lambda value: value["data_quality"].update({"quality_state": "UNKNOWN"}),
            "DATA_QUALITY_REJECTED",
            id="quality-state-unknown",
        ),
        pytest.param(lambda value: value.pop("source_timeframe"), "SOURCE_TIMEFRAME_INVALID", id="source-missing"),
        pytest.param(lambda value: value.update({"legacy": "false"}), "INPUT_SCHEMA_INVALID", id="legacy-type"),
    ),
)
def test_preflight_rejects_unknown_or_untyped_input(mutation: Callable[[dict[str, object]], None], reason: str) -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )
    input_value = _run_input()
    mutation(input_value)

    result = operation(input_value)

    assert _field(result, "decision") == "REJECT"
    assert reason in _codes(result)


def test_preflight_rejects_future_close_and_wrong_bar_cadence() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )
    future = operation(
        _run_input(
            strategy_timeframe="1h",
            requested_range={"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:00:00Z"},
            bars=(_closed_bar("2026-08-20T01:00:00Z", timeframe="1h"),),
        )
    )
    wrong_cadence = operation(
        _run_input(
            strategy_timeframe="1h",
            bars=(_closed_bar("2026-08-20T00:00:00Z", timeframe="15m"),),
        )
    )

    assert _field(future, "decision") == "REJECT"
    assert "FUTURE_VALUE" in _codes(future)
    assert _field(wrong_cadence, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(wrong_cadence)


def test_prior_close_cannot_use_a_bar_after_the_gap() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-003",
    )
    result = operation(
        _run_input(
            requested_range={"start": "2026-08-20T00:00:00Z", "end": "2026-08-20T01:00:00Z"},
            bars=(
                _closed_bar("2026-08-20T00:00:00Z"),
                _closed_bar("2026-08-20T00:15:00Z"),
                _closed_bar("2026-08-20T00:30:00Z"),
            ),
            data_quality={
                "quality_state": "USABLE_WITH_WARNING",
                "missing_bars": [
                    {
                        "position": "internal",
                        "count": 1,
                        "gap_open_time_utc": "2026-08-20T00:15:00Z",
                        "repair": "PRIOR_CLOSE_OHLC_VOLUME_ZERO",
                        "ohlcv": {
                            "open": "100.50",
                            "high": "100.50",
                            "low": "100.50",
                            "close": "100.50",
                            "volume": 0,
                        },
                        "provenance": {
                            "source": "prior_close",
                            "warning": "SINGLE_INTERNAL_GAP",
                            "source_dataset_id": "fixture-p5r2-v1",
                            "reference_close_time_utc": "2026-08-20T00:45:00Z",
                        },
                    }
                ],
            },
        )
    )

    assert _field(result, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(result)


def test_preflight_binds_bar_provenance_and_rejects_unknown_fields() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-002",
    )
    mismatched = _run_input()
    assert isinstance(mismatched["bars"], tuple)
    mismatched["bars"][0]["provenance"] = {
        "source_mode": "fixture_only",
        "dataset_id": "other-dataset-v1",
        "record_id": "bar-0001",
    }
    unknown = _run_input()
    unknown["unexpected"] = "reject-me"

    mismatched_result = operation(mismatched)
    unknown_result = operation(unknown)

    assert _field(mismatched_result, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(mismatched_result)
    assert _field(unknown_result, "decision") == "REJECT"
    assert "INPUT_SCHEMA_INVALID" in _codes(unknown_result)


def test_preflight_rejects_warning_state_without_warning_evidence() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-003",
    )
    result = operation(_run_input(data_quality={"quality_state": "USABLE_WITH_WARNING"}))

    assert _field(result, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(result)


def test_preflight_rejects_missing_ohlcv_and_secret_provenance() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-003",
    )
    missing_ohlcv = _run_input()
    assert isinstance(missing_ohlcv["bars"], tuple)
    missing_ohlcv["bars"][0].pop("open")
    secret_provenance = operation(
        _run_input(
            data_quality={
                "quality_state": "USABLE_WITH_WARNING",
                "missing_bars": [
                    {
                        "position": "internal",
                        "count": 1,
                        "gap_open_time_utc": "2026-08-20T00:15:00Z",
                        "repair": "PRIOR_CLOSE_OHLC_VOLUME_ZERO",
                        "ohlcv": {
                            "open": "100.50",
                            "high": "100.50",
                            "low": "100.50",
                            "close": "100.50",
                            "volume": 0,
                        },
                        "provenance": {
                            "source": "prior_close",
                            "warning": "SINGLE_INTERNAL_GAP",
                            "source_dataset_id": "fixture-p5r2-v1",
                            "reference_close_time_utc": "2026-08-20T00:15:00Z",
                            "api_key": "should-not-echo",
                        },
                    }
                ],
            }
        )
    )

    missing_result = operation(missing_ohlcv)

    assert _field(missing_result, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(missing_result)
    assert _field(secret_provenance, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(secret_provenance)


def test_prior_close_must_match_observed_bar() -> None:
    operation = _require_contract(
        preflight_module,
        "preflight_run_input",
        "P5R2-CREQ-TF-003",
    )
    result = operation(
        _run_input(
            data_quality={
                "quality_state": "USABLE_WITH_WARNING",
                "previous_closed_close": "999.99",
                "missing_bars": [
                    {
                        "position": "internal",
                        "count": 1,
                        "gap_open_time_utc": "2026-08-20T00:15:00Z",
                        "repair": "PRIOR_CLOSE_OHLC_VOLUME_ZERO",
                        "ohlcv": {
                            "open": "100.50",
                            "high": "100.50",
                            "low": "100.50",
                            "close": "100.50",
                            "volume": 0,
                        },
                        "provenance": {
                            "source": "prior_close",
                            "warning": "SINGLE_INTERNAL_GAP",
                            "source_dataset_id": "fixture-p5r2-v1",
                            "reference_close_time_utc": "2026-08-20T00:15:00Z",
                        },
                    }
                ],
            }
        )
    )

    assert _field(result, "decision") == "REJECT"
    assert "DATA_QUALITY_REJECTED" in _codes(result)


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
                        "gap_open_time_utc": "2026-08-20T00:15:00Z",
                        "repair": "PRIOR_CLOSE_OHLC_VOLUME_ZERO",
                        "ohlcv": {"open": "100.50", "high": "100.50", "low": "100.50", "close": "100.50", "volume": 0},
                        "provenance": {
                            "source": "prior_close",
                            "warning": "SINGLE_INTERNAL_GAP",
                            "source_dataset_id": "fixture-p5r2-v1",
                            "reference_close_time_utc": "2026-08-20T00:15:00Z",
                        },
                    }
                ],
                "quality_state": "USABLE_WITH_WARNING",
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

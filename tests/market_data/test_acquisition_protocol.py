"""P2-08 dry-run protocol tests; no external gateway is permitted."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from autotrade.market_data.acquisition_protocol import (
    FixtureGateway,
    HistoricalRequest,
    ProtocolError,
    build_request_plan,
    classify_failure,
    main,
    validate_environment_names,
    validate_request,
)

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "market_data" / "data_quality_replay_fixture.json"


def request(source_mode: str = "fixture") -> HistoricalRequest:
    return HistoricalRequest(
        request_id="p2-08-fixture-001",
        dataset_ref="fixture://p2-dqr",
        schema_ref="ohlcv-1m",
        symbols=("MCL", "M6A"),
        start_utc=datetime(2026, 6, 15, 12, tzinfo=UTC),
        end_utc=datetime(2026, 6, 15, 12, 1, tzinfo=UTC),
        source_mode=source_mode,  # type: ignore[arg-type]
    )


def test_fixture_gateway_reads_only_fixed_payload_and_checks_hash() -> None:
    gateway = FixtureGateway(FIXTURE_PATH, expected_sha256=sha256(FIXTURE_PATH.read_bytes()).hexdigest())

    payload = gateway.fetch(request())

    assert payload.condition == "available"
    assert payload.payload == FIXTURE_PATH.read_bytes()
    assert payload.metadata["provider"] == "fixture"
    assert payload.metadata["fixture_sha256"].startswith("sha256:")
    assert "api_key" not in payload.metadata


def test_external_request_is_rejected_before_any_gateway_call() -> None:
    with pytest.raises(ProtocolError, match="H2_2_NOT_APPROVED"):
        validate_request(request("external"), h2_2_approved=False)


def test_request_plan_is_deterministic_and_disallows_external_io() -> None:
    fixture_hash = "sha256:" + sha256(FIXTURE_PATH.read_bytes()).hexdigest()

    first = build_request_plan(request(), "tests/fixtures/market_data/data_quality_replay_fixture.json", fixture_hash)
    second = build_request_plan(request(), "tests/fixtures/market_data/data_quality_replay_fixture.json", fixture_hash)

    assert first == second
    assert first["mode"] == "dry_run"
    assert first["external_io_allowed"] is False
    assert "generated_at" not in first


@pytest.mark.parametrize(
    ("status_code", "reason_code", "state"),
    [
        (401, "AUTHENTICATION_FAILED", "UNHEALTHY"),
        (403, "ENTITLEMENT_DENIED", "UNKNOWN"),
        (429, "RATE_LIMITED", "DEGRADED"),
        (206, "SYMBOL_PARTIAL", "UNKNOWN"),
        (404, "SYMBOL_NOT_FOUND", "UNKNOWN"),
    ],
)
def test_failure_classification_is_fail_closed(status_code: int, reason_code: str, state: str) -> None:
    event = classify_failure(request(), status_code=status_code)

    assert event.reason_code == reason_code
    assert event.state == state
    assert event.observed_at_utc == request().start_utc
    assert event.event_id.startswith("health-")


@pytest.mark.parametrize(("condition", "state"), [("degraded", "DEGRADED"), ("pending", "UNKNOWN"), ("missing", "UNKNOWN")])
def test_dataset_condition_becomes_health_event(condition: str, state: str) -> None:
    event = classify_failure(request(), condition=condition)

    assert event.reason_code == "DATASET_DEGRADED"
    assert event.state == state


def test_environment_validation_never_accepts_secret_names() -> None:
    validate_environment_names({"AUTOTRADE_H2_2_APPROVED": "0"})

    with pytest.raises(ProtocolError, match="SECRET_ENVIRONMENT_REJECTED"):
        validate_environment_names({"DATABENTO_API_KEY": "should-not-be-read"})


def test_cli_writes_a_fixture_only_request_plan(tmp_path: Path) -> None:
    output = tmp_path / "request-plan.json"
    exit_code = main(
        [
            "--request-id",
            "p2-08-cli-001",
            "--dataset-ref",
            "fixture://p2-dqr",
            "--schema-ref",
            "ohlcv-1m",
            "--symbol",
            "MCL",
            "--start-utc",
            "2026-06-15T12:00:00+00:00",
            "--end-utc",
            "2026-06-15T12:01:00+00:00",
            "--fixture-path",
            str(FIXTURE_PATH),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    plan = json.loads(output.read_text(encoding="utf-8"))
    assert plan["request"]["source_mode"] == "fixture"
    assert plan["external_io_allowed"] is False

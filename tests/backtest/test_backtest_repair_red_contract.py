"""P3-07R-01 hostile RED contracts for the typed Backtest execution path.

These tests deliberately keep the oracle in test code.  They do not read
expected values from the fixture under test, and they never modify the frozen
Phase 3 fixtures.
"""

from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "phase3"
PARENT_MANIFEST = FIXTURE_ROOT / "run_p3_backtest_fixture_manifest_v1.json"

# Independent oracle: this is intentionally duplicated from the approved
# manifest so a test cannot pass merely by echoing the manifest's own values.
EXPECTED_CHILDREN = {
    "tests/fixtures/phase3/run_p3_gold_fixture_manifest.json": (
        "19eff1a99d407570e73fac74d3e0e00bbaf72c3c4278e6f046dcc6723adcc314"
    ),
    "tests/fixtures/phase3/run_p3_m30_fixture_manifest_v3.json": (
        "8674ac9f2b932acc4a6bca5a3d2037b9202cc7f61df71f7e5249c758f51bd79d"
    ),
    "tests/fixtures/phase3/backtest_contract_cases_v1.json": (
        "55861db761a9d2272f235486e6ada5c4354ec2a155ba949b5f7fafc6d5df7299"
    ),
    "tests/fixtures/phase3/m30_backtest_contract_cases_v2.json": (
        "a3fda8506aeba088405bcb3436aaa14957f990427f2e3dd9c0f1c8188fba63db"
    ),
    "tests/fixtures/phase3/m30_backtest_v2.json": ("7282ea7bda1c6701cffc2e8e1949b2b38e036b107b99d2857b1508afe51f6e08"),
    "tests/fixtures/phase3/calendar_us_futures_v1.json": (
        "986e87fec5abd90fdbf81f485737d099131b54fb1cd1326bd7399d22aa05bdc6"
    ),
    "tests/fixtures/phase3/backtest_replay_v1.json": (
        "af8419125afbb22ba0754664aba989b95b2817072d83eef0f87f8268bd9c408d"
    ),
    "tests/fixtures/phase3/bias_manifest_v1.json": ("1d61e25f2fe2b29538788afb890c48caa0f852346d077816a3c34d140be8dd24"),
    "tests/fixtures/phase3/performance_synthetic_v1.json": (
        "1000e99f8d3b75a464e5fbdc79111a58f3ed926e84b795c2df28e53c9b1aa731"
    ),
    "tests/fixtures/phase3/run_p3_strategy_fixture_manifest_v3.json": (
        "4a410f7ac15837ebb9d899daecd56f0c6e45c3795d7f8db067daef80359531e0"
    ),
}

DTO_NAMES = (
    "ReplayInput",
    "ReplayOrderKey",
    "DataGateDecision",
    "ExperimentManifest",
    "BacktestRunRequest",
    "BacktestRunResult",
    "BacktestSnapshot",
    "ResultRow",
    "CommitMarker",
    "EngineIdentity",
    "EngineRunRequest",
    "EngineRunResult",
    "OfflineEvidence",
    "PerformanceEvidence",
)


def _operation(module_name: str, operation_name: str):
    module = importlib.import_module(module_name)
    operation = getattr(module, operation_name, None)
    assert callable(operation), f"{module_name}.{operation_name} is required"
    return operation


def _bar(
    event_id: str,
    *,
    instrument_id: str = "MKT-A",
    event_time: str = "2026-08-09T00:00:00Z",
    bar_close_time: str = "2026-08-09T00:01:00Z",
    close: str = "101.00",
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "run_id": "RUN-P3-BT-REPAIR-001",
        "instrument_id": instrument_id,
        "event_time": event_time,
        "bar_close_time": bar_close_time,
        "event_kind": "BAR_1M",
        "values": {"open": "100.00", "high": "101.00", "low": "99.00", "close": close, "volume": "1"},
        "quality_flags": [],
        "data_version": "dv-approved",
    }


@pytest.mark.parametrize("name", DTO_NAMES)
def test_repair_dtos_are_explicit_immutable_contracts(name: str) -> None:
    module = importlib.import_module("autotrade.backtest.contracts")
    dto = getattr(module, name, None)
    assert dto is not None, f"contracts.{name} is required"
    assert is_dataclass(dto), f"contracts.{name} must be an immutable dataclass"
    assert getattr(dto.__dataclass_params__, "frozen", False), f"contracts.{name} must be frozen"
    assert fields(dto), f"contracts.{name} must declare fields"


def test_engine_adapter_is_protocol_with_typed_methods() -> None:
    module = importlib.import_module("autotrade.backtest.contracts")
    adapter = getattr(module, "EngineAdapter", None)
    assert adapter is not None, "contracts.EngineAdapter is required"
    assert getattr(adapter, "__is_protocol__", False), "EngineAdapter must be a Protocol"
    for method_name in ("validate_identity", "run", "normalize_failure"):
        assert callable(getattr(adapter, method_name, None)), f"EngineAdapter.{method_name} is required"


def test_backtest_runner_is_the_single_typed_entrypoint() -> None:
    module = importlib.import_module("autotrade.backtest.simulator")
    runner = getattr(module, "BacktestRunner", None)
    assert runner is not None, "simulator.BacktestRunner is required"
    run = getattr(runner, "run", None)
    assert callable(run), "BacktestRunner.run is required"
    signature = inspect.signature(run)
    assert len(signature.parameters) == 2, "run must accept self and one BacktestRunRequest"
    assert signature.return_annotation is not bool, "run must return BacktestRunResult, never a caller bool"


def test_parent_manifest_matches_independent_child_oracle() -> None:
    manifest = json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))
    actual = {child["path"]: child["sha256"] for child in manifest["children"]}
    assert actual == EXPECTED_CHILDREN


def test_manifest_rejects_unknown_and_incomplete_values() -> None:
    validate = _operation("autotrade.backtest.experiment_manifest", "validate_manifest")
    minimal = {
        "timeframe_rule_version": "tf-v3",
        "calendar_sha256": "sha256:" + "a" * 64,
        "ordering_rule_version": "order-v2",
        "engine_identity_sha256": "sha256:" + "b" * 64,
        "adapter_artifact_sha256": "sha256:" + "c" * 64,
        "strategy_code_revision": "rev-approved",
    }
    result = validate({**minimal, "unknown_field": "must-stop"})
    assert result == {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}
    assert validate(minimal)["status"] == "STOPPED"


def test_canonical_json_rejects_finite_float() -> None:
    canonical_json = _operation("autotrade.backtest.contracts", "canonical_json")
    with pytest.raises((TypeError, ValueError)):
        canonical_json({"price": 1.25})


def test_replay_requires_explicit_data_and_quality_binding() -> None:
    normalize = _operation("autotrade.backtest.replay_order", "normalize_replay")
    event = _bar("evt-missing-binding")
    event.pop("data_version")
    result = normalize({"events": [event], "replay_cutoff_utc": "2026-08-09T00:02:00Z"})
    assert result == {"status": "STOPPED", "reason": "DATA_GATE_BLOCKED"}


def test_replay_rejects_future_event_against_fixed_cutoff() -> None:
    normalize = _operation("autotrade.backtest.replay_order", "normalize_replay")
    event = _bar(
        "evt-future",
        event_time="2026-08-10T00:00:00Z",
        bar_close_time="2026-08-10T00:01:00Z",
    )
    result = normalize({"events": [event], "replay_cutoff_utc": "2026-08-09T00:02:00Z"})
    assert result == {"status": "STOPPED", "reason": "FUTURE_EVENT_REJECTED"}


def test_replay_rejects_same_instrument_minute_payload_conflict() -> None:
    normalize = _operation("autotrade.backtest.replay_order", "normalize_replay")
    first = _bar("evt-a", close="101.00")
    second = _bar("evt-b", close="102.00")
    result = normalize({"events": [first, second]})
    assert result == {"status": "STOPPED", "reason": "DUPLICATE_1M_CONFLICT"}


def test_m30_does_not_accept_caller_supplied_calendar_predicate() -> None:
    aggregate = _operation("autotrade.backtest.timeframe_aggregator", "aggregate_m30")
    result = aggregate({"calendar_rejections": {"dst": True}})
    assert result == {"status": "STOPPED", "reason": "CALENDAR_BOUNDARY_INVALID"}


def test_pending_directive_cannot_fill_on_a_different_instrument() -> None:
    schedule = _operation("autotrade.backtest.simulator", "schedule_next_bar")
    result = schedule(
        {
            "directive_time": "2026-08-09T00:00:00Z",
            "bar_open": "2026-08-09T00:01:00Z",
            "directive_instrument_id": "MKT-A",
            "bar_instrument_id": "MKT-B",
        }
    )
    assert result == {"filled": False, "reason": "NO_ELIGIBLE_BAR"}


def test_snapshot_without_full_binding_is_stopped() -> None:
    snapshot = _operation("autotrade.backtest.snapshot", "snapshot_aggregator")
    result = snapshot({"interrupt_after_event": 7})
    assert result == {"status": "STOPPED", "reason": "RECOVERY_RECONCILIATION_FAILED"}


def test_result_path_guard_requires_observed_root_and_run_identity() -> None:
    reject_path = _operation("autotrade.backtest.result_store", "reject_bad_result_path")
    result = reject_path({"path_outside_e_root": False})
    assert result == {"status": "STOPPED", "reason": "RESULT_NOT_PUBLISHED"}


def test_engine_identity_requires_all_pinned_fields() -> None:
    validate_identity = _operation("autotrade.backtest.engine_adapter", "validate_engine_identity")
    result = validate_identity({"engine": "ENGINE_NOT_USED"})
    assert result == {"status": "STOPPED", "reason": "ENGINE_IDENTITY_UNPINNED"}


def test_fake_adapter_requires_typed_request_and_core_reference_hash() -> None:
    run_fake = _operation("autotrade.backtest.engine_adapter", "run_fake_engine_adapter")
    result = run_fake({"sdk_imports": 0})
    assert result["status"] == "STOPPED"


def test_offline_evidence_cannot_pass_from_zero_attempt_boolean() -> None:
    reject_offline = _operation("autotrade.backtest.engine_adapter", "reject_offline_violation")
    result = reject_offline({"outbound_attempt": False})
    assert result == {"status": "STOPPED", "reason": "OFFLINE_PREFLIGHT_UNPROVEN"}


def test_offline_replay_requires_observed_hashes_and_dependency_scan() -> None:
    verify = _operation("autotrade.backtest.simulator", "verify_offline_replay")
    result = verify({"network_attempts": 0, "same_manifest_twice": True})
    assert result == {"status": "STOPPED", "reason": "OFFLINE_PREFLIGHT_UNPROVEN"}


def test_performance_evidence_rejects_shape_only_hashes() -> None:
    record = _operation("autotrade.backtest.performance_recorder", "record")
    result = record(
        {
            "elapsed_ms": 1,
            "peak_rss_bytes": 1,
            "event_count": 1,
            "input_sha256": "sha256:fake",
            "result_sha256": "sha256:fake",
        }
    )
    assert result == {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}


def test_performance_measurement_without_observation_is_not_passable() -> None:
    measure = _operation("autotrade.backtest.simulator", "measure_performance")
    result = measure({"elapsed_limit_minutes": 30, "rss_limit_gib": 8})
    assert result == {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}


def test_legacy_replay_predicate_cannot_certify_a_run() -> None:
    replay = _operation("autotrade.backtest.simulator", "run_full_replay")
    result = replay({"same_manifest_twice": True})
    assert result == {"status": "STOPPED", "reason": "TYPED_RUN_REQUIRED"}


def test_result_row_contract_has_no_secret_or_vendor_identity_surface() -> None:
    module = importlib.import_module("autotrade.backtest.contracts")
    result_row = getattr(module, "ResultRow", None)
    assert result_row is not None, "contracts.ResultRow is required"
    names = {field.name.lower() for field in fields(result_row)}
    assert not any(token in name for name in names for token in ("secret", "api_key", "broker_order_id", "engine_id"))

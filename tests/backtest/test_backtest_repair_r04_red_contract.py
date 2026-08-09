"""P3-07R-04 RED contracts for the SDK-less engine boundary and evidence."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from autotrade.backtest.contracts import (
    EngineFailure,
    EngineIdentity,
    EngineRunRequest,
    EngineRunResult,
    ExperimentManifest,
)


def _identity() -> EngineIdentity:
    return EngineIdentity(
        engine_kind="ENGINE_NOT_USED",
        engine_version="ENGINE_NOT_USED",
        distribution_source="ENGINE_NOT_USED",
        artifact_sha256_or_oci_digest="ENGINE_NOT_USED",
        adapter_name="ENGINE_NOT_USED",
        adapter_version="ENGINE_NOT_USED",
        adapter_artifact_sha256="ENGINE_NOT_USED",
        runtime_kind="ENGINE_NOT_USED",
        runtime_version="ENGINE_NOT_USED",
        execution_mode="ENGINE_NOT_USED",
    )


def _request() -> EngineRunRequest:
    identity = _identity()
    manifest = ExperimentManifest(
        run_id="RUN-P3-BT-REPAIR-004",
        input_sha256="sha256:" + "1" * 64,
        strategy_config_sha256="sha256:" + "2" * 64,
        engine_identity=identity,
    )
    return EngineRunRequest(
        manifest=manifest,
        input_sha256=manifest.input_sha256,
        core_reference_sha256="sha256:" + "3" * 64,
        strategy_config_sha256=manifest.strategy_config_sha256,
        engine_identity=identity,
        run_id=manifest.run_id,
    )


def _result(*, result_sha256: str = "sha256:" + "6" * 64) -> EngineRunResult:
    return EngineRunResult(
        status="PASS",
        signal_sha256="sha256:" + "1" * 64,
        directive_sha256="sha256:" + "2" * 64,
        fill_sha256="sha256:" + "3" * 64,
        state_sha256="sha256:" + "4" * 64,
        result_sha256=result_sha256,
        engine_trace_sha256="sha256:" + "5" * 64,
        parity_status="NOT_COMPARED",
    )


def test_engine_failure_is_a_frozen_public_failure_dto() -> None:
    assert dataclasses.is_dataclass(EngineFailure)
    assert getattr(EngineFailure.__dataclass_params__, "frozen", False)
    failure = EngineFailure(reason="ENGINE_PARITY_MISMATCH", detail="result hash differs")
    assert failure.as_dict()["reason"] == "ENGINE_PARITY_MISMATCH"


def test_fake_adapter_compares_core_reference_without_running_strategy_twice() -> None:
    from autotrade.backtest.engine_adapter import FakeEngineAdapter

    adapter = FakeEngineAdapter(reference_result=_result())
    result = adapter.run(_request())
    assert result.status == "PASS"
    assert result.parity_status == "MATCH"
    assert result.result_sha256 == _result().result_sha256


def test_fake_adapter_rejects_ordered_result_parity_difference() -> None:
    from autotrade.backtest.engine_adapter import FakeEngineAdapter

    result = FakeEngineAdapter(
        reference_result=_result(),
        candidate_result=_result(result_sha256="sha256:" + "7" * 64),
    ).run(_request())
    assert result.status == "STOPPED"
    assert result.parity_status == "MISMATCH"
    assert result.failure is not None
    assert result.failure.reason == "ENGINE_PARITY_MISMATCH"


def test_typed_identity_rejects_partial_unknown_and_non_string_values() -> None:
    from autotrade.backtest.engine_adapter import validate_typed_engine_identity

    identity = dataclasses.asdict(_identity())
    for invalid in (
        {**identity, "engine_kind": "lean:latest"},
        {key: value for key, value in identity.items() if key != "runtime_version"},
        {**identity, "runtime_version": None},
    ):
        result = validate_typed_engine_identity(invalid, _request().manifest)
        assert result is not None
        assert result.reason == "ENGINE_IDENTITY_UNPINNED"


def test_offline_evidence_hashes_observed_files_and_rejects_self_attestation(tmp_path: Path) -> None:
    from autotrade.backtest.offline_evidence import collect_offline_evidence, validate_offline_evidence

    input_path = tmp_path / "input.json"
    result_path = tmp_path / "result.json"
    dependency_path = tmp_path / "dependency.txt"
    input_path.write_text('{"event":"input"}', encoding="utf-8")
    result_path.write_text('{"result":"committed"}', encoding="utf-8")
    dependency_path.write_text("local dependency", encoding="utf-8")
    evidence = collect_offline_evidence(
        input_root=tmp_path,
        input_paths=[input_path],
        output_paths=[result_path],
        dependency_paths=[dependency_path],
        scan_paths=[tmp_path],
        observation_id="OBS-R04-001",
    )
    assert validate_offline_evidence(evidence)["status"] == "PASS"
    assert validate_offline_evidence({**evidence, "outbound_attempts": 0})["status"] == "PASS"
    assert validate_offline_evidence({**evidence, "outbound_attempts": 1}) == {
        "status": "STOPPED",
        "reason": "OFFLINE_POLICY_VIOLATION",
    }


def test_offline_evidence_rejects_external_root_and_unknown_fields(tmp_path: Path) -> None:
    from autotrade.backtest.offline_evidence import validate_offline_evidence

    evidence: dict[str, Any] = {
        "schema_version": "p3-offline-evidence-v1",
        "allowed_input_root": str(tmp_path),
        "input_sha256s": ("sha256:" + "1" * 64,),
        "output_sha256s": ("sha256:" + "2" * 64,),
        "dependency_sha256s": ("sha256:" + "3" * 64,),
        "forbidden_import_count": 0,
        "secret_scan_count": 0,
        "outbound_attempts": 0,
        "broker_cloud_url_count": 0,
        "observation_id": "OBS-R04-002",
    }
    assert validate_offline_evidence({**evidence, "unknown": True})["reason"] == "OFFLINE_PREFLIGHT_UNPROVEN"
    assert validate_offline_evidence({**evidence, "allowed_input_root": "E:\\external"})["reason"] == (
        "OFFLINE_PREFLIGHT_UNPROVEN"
    )


def test_offline_scans_forbidden_dependency_secret_and_broker_url(tmp_path: Path) -> None:
    from autotrade.backtest.offline_evidence import collect_offline_evidence, validate_offline_evidence

    input_path = tmp_path / "input.json"
    result_path = tmp_path / "result.json"
    dependency_path = tmp_path / "dependency.txt"
    hostile_source = tmp_path / "hostile.py"
    input_path.write_text("input", encoding="utf-8")
    result_path.write_text("result", encoding="utf-8")
    dependency_path.write_text("dependency", encoding="utf-8")
    hostile_source.write_text(
        "import broker.client\nAPI_KEY = 'must never be observed as evidence'\nURL = 'https://broker.example'\n",
        encoding="utf-8",
    )
    evidence = collect_offline_evidence(
        input_root=tmp_path,
        input_paths=[input_path],
        output_paths=[result_path],
        dependency_paths=[dependency_path],
        scan_paths=[hostile_source],
        observation_id="OBS-R04-HOSTILE",
    )
    assert validate_offline_evidence(evidence) == {"status": "STOPPED", "reason": "OFFLINE_POLICY_VIOLATION"}


def test_performance_generator_and_two_real_measurements_are_deterministic() -> None:
    from autotrade.backtest.performance_recorder import measure_performance_run
    from autotrade.backtest.simulator import generate_performance_input

    fixture = json.loads(
        (Path(__file__).parents[1] / "fixtures" / "phase3" / "performance_synthetic_v1.json").read_text(
            encoding="utf-8"
        )
    )
    first_input = generate_performance_input({"fixture": fixture})
    second_input = generate_performance_input({"fixture": fixture})
    assert first_input["input_sha256"] == second_input["input_sha256"]
    assert len(first_input["derived_bar_sha256s"]) == 5
    evidence = measure_performance_run(first_input, lambda payload: {"rows": payload["events"]})
    assert evidence["status"] == "PASS"
    assert evidence["first_result_sha256"] == evidence["second_result_sha256"]
    assert evidence["measurement_observed"] is True


def test_performance_evidence_rejects_missing_measurement_host_and_shape_only_hash() -> None:
    from autotrade.backtest.performance_recorder import validate_performance_evidence

    assert validate_performance_evidence({})["reason"] == "PERFORMANCE_EVIDENCE_UNPROVEN"
    evidence = {
        "generator_version": "synthetic-1m-v1",
        "schema_version": "p3-performance-evidence-v1",
        "seed": 20260809,
        "input_sha256": "sha256:" + "1" * 64,
        "derived_bar_sha256s": ("sha256:" + "2" * 64,),
        "manifest_sha256": "sha256:" + "3" * 64,
        "host_cpu": "unknown",
        "host_ram_bytes": 1,
        "host_os": "unknown",
        "python_version": "unknown",
        "measurement_tool": "unknown",
        "measurement_tool_version": "unknown",
        "measurement_unit": "ms/bytes",
        "elapsed_ms": 1,
        "peak_rss_bytes": 1,
        "first_result_sha256": "sha256:" + "0" * 64,
        "second_result_sha256": "sha256:" + "0" * 64,
        "observation_id": "OBS-R04-003",
        "measurement_observed": False,
        "host_observed": False,
    }
    assert validate_performance_evidence(evidence)["status"] == "STOPPED"


def test_r04_quality_scope_is_registered_without_changing_p2_scope() -> None:
    scopes = json.loads(Path("scripts/quality_gate/trusted_scopes.json").read_text(encoding="utf-8"))["scopes"]
    scope = scopes.get("RUN-P3-BT-REPAIR-004")
    assert scope is not None
    assert scope["network_isolation_required"] is True
    assert "tests/backtest" in scope["target_paths"]
    assert "RUN-P2-DBN-001" in scopes

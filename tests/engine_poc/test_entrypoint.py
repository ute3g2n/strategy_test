"""P3-08R-02 tests for the dedicated P3-09 preparation boundary."""

from __future__ import annotations

import ast
import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from engine_poc.entrypoint import (
    ContractError,
    build_lean_config,
    canonical_hash,
    load_input_contract,
    prepare_entry,
    sha256_file,
    validate_execution_manifest,
    validate_lean_output,
)

ROOT = Path(__file__).parents[2]
CONTRACT_PATH = ROOT / "tests/evidence/phase3/RUN-P3-POC-READY-001/input-contract.json"


def _contract() -> dict[str, Any]:
    return load_input_contract(CONTRACT_PATH, ROOT)[0]


def _valid_manifest() -> dict[str, Any]:
    contract = _contract()
    fixture = contract["approved_fixture_set"]
    assert isinstance(fixture, dict)
    children = fixture["children"]
    assert isinstance(children, list)
    engine = contract["p3_08a_recheck"]["engine_identity"]
    assert isinstance(engine, dict)
    artifact_values = contract["p3_08a_recheck"]["artifact_recomputed"]
    assert isinstance(artifact_values, list)
    artifact_map = {item["name"]: item for item in artifact_values}
    payload: dict[str, object] = {
        "schema_version": "p3-poc-execution-manifest/v1",
        "run_id": "RUN-P3-POC-001",
        "phase_id": "phase3",
        "step_id": "P3-09",
        "preparation_run_id": "RUN-P3-POC-READY-001",
        "input_contract_sha256": sha256_file(CONTRACT_PATH),
        "fixture_manifest_sha256": fixture["parent_manifest"]["sha256"],
        "fixture_child_sha256s": [item["sha256"] for item in children],
        "code_revision": contract["repository_recheck"]["head"],
        "engine": {
            "image_index_digest": engine["image_index_digest"],
            "linux_amd64_digest": engine["linux_amd64_digest"],
            "image_tar_sha256": artifact_map["image_tar"]["sha256"],
            "license_sha256": artifact_map["license"]["sha256"],
            "source_commit": engine["source_commit"],
            "entrypoint": ["dotnet", "QuantConnect.Lean.Launcher.dll"],
        },
        "execution": {
            "input_root": "tests/fixtures/phase3",
            "readonly_inputs": True,
            "write_roots": ["tests/evidence/phase3/RUN-P3-POC-001"],
            "network_mode": "none",
            "data_provider": "Local",
            "automatic_data_download": False,
            "cloud": "NOT_USED",
            "broker": "NOT_USED",
            "secret": "NOT_USED",
        },
        "adapter": {
            "name": "LeanLocalAdapter",
            "version": "p3-lean-adapter-v1",
            "artifact_sha256": "sha256:" + "1" * 64,
        },
        "expected": {
            "core_reference_path": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/core-reference.json",
            "core_reference_sha256": "sha256:" + "2" * 64,
            "lean_output_schema_path": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/lean-output-schema.json",
            "lean_output_schema_sha256": "sha256:" + "3" * 64,
            "parity_map_path": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/parity-map.json",
            "parity_map_sha256": "sha256:" + "4" * 64,
        },
        "performance": {
            "fixture_path": "tests/fixtures/phase3/performance_synthetic_v1.json",
            "fixture_sha256": "sha256:1000e99f8d3b75a464e5fbdc79111a58f3ed926e84b795c2df28e53c9b1aa731",
            "elapsed_minutes": 30,
            "peak_rss_gib": 8,
        },
    }
    payload["manifest_sha256"] = canonical_hash(payload)
    return payload


def _valid_output() -> dict[str, Any]:
    zero_hash = "sha256:" + "0" * 64
    return {
        "schema_version": "p3-lean-output/v1",
        "run_id": "RUN-P3-POC-001",
        "status": "PASS",
        "sequence": [
            {
                "sequence_no": 0,
                "logical_time_utc": "2026-01-05T23:00:00Z",
                "row_kind": "CORE_PARITY_RESULT",
                "payload_sha256": zero_hash,
                "manifest_sha256": zero_hash,
            }
        ],
        "hashes": {
            "signal_sha256": zero_hash,
            "directive_sha256": zero_hash,
            "fill_sha256": zero_hash,
            "state_sha256": zero_hash,
            "result_sha256": zero_hash,
            "trace_sha256": zero_hash,
        },
        "failure": None,
    }


def test_prepare_validates_contract_without_starting_engine() -> None:
    result = prepare_entry(ROOT, CONTRACT_PATH)

    assert result["status"] in {"CONTRACT_READY", "READY_TO_REHEARSE"}
    assert result["engine_started"] is False
    assert result["p3_09_start_allowed"] is False
    assert result["manifest"]["status"] in {"NOT_YET_FIXED", "VALIDATED"}
    assert result["network"]["observed"] is False


def test_prepare_rejects_fixture_hash_tampering(tmp_path: Path) -> None:
    value = _contract()
    fixture = value["approved_fixture_set"]
    assert isinstance(fixture, dict)
    children = fixture["children"]
    assert isinstance(children, list)
    children[0]["sha256"] = "sha256:" + "f" * 64
    tampered = tmp_path / "input-contract.json"
    tampered.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ContractError, match="fixture hash"):
        load_input_contract(tampered, ROOT)


def test_prepare_rejects_p3_09_execution_scope_enabled(tmp_path: Path) -> None:
    value = _contract()
    value["p3_09_fire_control_recheck"]["execution_allowed"] = True
    tampered = tmp_path / "input-contract.json"
    tampered.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ContractError, match="execution_allowed"):
        load_input_contract(tampered, ROOT)


def test_manifest_accepts_fixed_engine_and_fixture_bindings() -> None:
    manifest = _valid_manifest()
    validate_execution_manifest(manifest, _contract(), ROOT)
    config = build_lean_config(manifest)

    assert config["network_mode"] == "none"
    assert config["data_provider"] == "Local"
    assert config["automatic_data_download"] is False
    assert config["launch_allowed"] is False


def test_manifest_allows_preparation_revision_to_be_distinct_from_contract_snapshot() -> None:
    manifest = _valid_manifest()
    manifest["source_contract_head"] = manifest["code_revision"]
    manifest["code_revision"] = "a" * 40
    manifest["manifest_sha256"] = canonical_hash(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )

    validate_execution_manifest(manifest, _contract(), ROOT)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["engine"].pop("linux_amd64_digest"),
        lambda value: value["engine"].update({"image_index_digest": "sha256:" + "a" * 64}),
        lambda value: value["fixture_child_sha256s"].__setitem__(0, "sha256:" + "b" * 64),
        lambda value: value["execution"].update({"network_mode": "nat"}),
        lambda value: value.__setitem__("manifest_sha256", "sha256:" + "c" * 64),
    ],
)
def test_manifest_tampering_is_fail_closed(mutation: Callable[[dict[str, Any]], object]) -> None:
    manifest = _valid_manifest()
    mutation(manifest)

    with pytest.raises(ContractError):
        validate_execution_manifest(manifest, _contract(), ROOT)


def test_output_schema_accepts_only_vendor_neutral_fields() -> None:
    validate_lean_output(_valid_output())

    invalid = _valid_output()
    invalid["engine_order_id"] = "vendor-id"
    with pytest.raises(ContractError, match="forbidden output field"):
        validate_lean_output(invalid)


def test_output_schema_rejects_non_utc_or_non_contiguous_sequence() -> None:
    invalid = _valid_output()
    invalid["sequence"][0]["logical_time_utc"] = "2026-01-05T23:00:00+09:00"
    with pytest.raises(ContractError, match="UTC"):
        validate_lean_output(invalid)

    invalid = _valid_output()
    invalid["sequence"][0]["sequence_no"] = 2
    with pytest.raises(ContractError, match="sequence"):
        validate_lean_output(invalid)


def test_prepare_entry_does_not_mutate_input_contract() -> None:
    value = _contract()
    before = copy.deepcopy(value)
    prepare_entry(ROOT, CONTRACT_PATH)
    assert value == before


def test_prepare_rejects_non_fixed_contract_path(tmp_path: Path) -> None:
    alternate = tmp_path / "input-contract.json"
    alternate.write_text(CONTRACT_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(ContractError, match="fixed repository path"):
        prepare_entry(ROOT, alternate)


def test_engine_poc_code_has_no_vendor_imports() -> None:
    forbidden = {"quantconnect", "lean", "nautilus", "databento", "broker"}
    for path in (ROOT / "tests/engine_poc").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0].lower())
        assert not imports & forbidden, (path, imports & forbidden)

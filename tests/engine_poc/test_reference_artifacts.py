"""P3-08R-03 expected-output and Manifest integrity contracts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from engine_poc.entrypoint import canonical_hash, validate_execution_manifest

ROOT = Path(__file__).parents[2]
EVIDENCE_ROOT = ROOT / "tests/evidence/phase3/RUN-P3-POC-READY-001"
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ACCEPTANCE_IDS = [f"P3-AC-{index:02d}" for index in range(1, 9)]


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_core_reference_has_two_matching_runs_and_all_acceptance_ids() -> None:
    reference = _read(EVIDENCE_ROOT / "expected/core-reference.json")
    assert reference["schema_version"] == "p3-core-reference/v1"
    assert reference["determinism"]["core_execution_count"] == 2
    assert reference["determinism"]["matching"] is True
    assert reference["determinism"]["first_result_sha256"] == reference["determinism"]["second_result_sha256"]
    assert set(reference["p3_ac"]) == set(ACCEPTANCE_IDS)
    for requirement_id in ACCEPTANCE_IDS:
        values = reference["p3_ac"][requirement_id]
        hashes = [value for key, value in values.items() if key.endswith("_sha256")]
        assert hashes
        assert all(isinstance(value, str) and HASH_PATTERN.fullmatch(value) for value in hashes)


def test_parity_map_assigns_every_requirement_without_creating_engine_output() -> None:
    parity = _read(EVIDENCE_ROOT / "expected/parity-map.json")
    assert parity["engine_execution_status"] == "NOT_EXECUTED_P3-09"
    assert parity["lean_measurements_are_not_expected_values"] is True
    assert parity["unassigned_requirement_count"] == 0
    assert set(parity["requirements"]) == set(ACCEPTANCE_IDS)
    for value in parity["requirements"].values():
        assert value["lean_output"]["status"] == "NOT_CREATED_P3-09"
        assert value["parity_decision"]["status"] == "PENDING_P3-09"


def test_manifest_expected_hashes_and_canonical_hash_are_fixed() -> None:
    manifest = _read(EVIDENCE_ROOT / "run-manifest.json")
    expected = manifest["expected"]
    assert expected["core_reference_sha256"] == _sha256(EVIDENCE_ROOT / "expected/core-reference.json")
    assert expected["lean_output_schema_sha256"] == _sha256(EVIDENCE_ROOT / "expected/lean-output-schema.json")
    assert expected["parity_map_sha256"] == _sha256(EVIDENCE_ROOT / "expected/parity-map.json")
    assert manifest["manifest_sha256"] == canonical_hash(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    assert manifest["execution"]["network_mode"] == "none"
    assert manifest["execution"]["readonly_inputs"] is True
    assert manifest["execution"]["automatic_data_download"] is False
    assert manifest["execution_fire_control"]["p3_09_execution_allowed"] is False


def test_manifest_passes_the_dedicated_entrypoint_validator() -> None:
    contract = _read(EVIDENCE_ROOT / "input-contract.json")
    manifest = _read(EVIDENCE_ROOT / "run-manifest.json")
    validate_execution_manifest(
        manifest,
        contract,
        ROOT,
        contract_path=EVIDENCE_ROOT / "input-contract.json",
        require_expected_files=True,
    )

"""P3-09専用の準備入口。

このモジュールはLEANを起動しない。固定入力、将来のExecution Manifest、
出力境界、禁止された外部経路を検証し、P3-09本Runへ渡せる準備計画だけを
machine-readable形式で返す。
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from autotrade.backtest.contracts import canonical_hash as _core_canonical_hash

CONTRACT_RELATIVE_PATH = Path("tests/evidence/phase3/RUN-P3-POC-READY-001/input-contract.json")
MANIFEST_RELATIVE_PATH = Path("tests/evidence/phase3/RUN-P3-POC-READY-001/run-manifest.json")
OUTPUT_SCHEMA_RELATIVE_PATH = Path("tests/evidence/phase3/RUN-P3-POC-READY-001/expected/lean-output-schema.json")
POC_RUN_ID = "RUN-P3-POC-001"
PREPARATION_RUN_ID = "RUN-P3-POC-READY-001"
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+ KEY-----"),
    re.compile(r"(?:api[_-]?key|authorization|bearer)\s*[:=]", re.IGNORECASE),
)
OUTPUT_TOP_LEVEL_FIELDS = {"schema_version", "run_id", "status", "sequence", "hashes", "failure"}
OUTPUT_HASH_FIELDS = {
    "signal_sha256",
    "directive_sha256",
    "fill_sha256",
    "state_sha256",
    "result_sha256",
    "trace_sha256",
}
OUTPUT_SEQUENCE_FIELDS = {
    "sequence_no",
    "logical_time_utc",
    "row_kind",
    "payload_sha256",
    "manifest_sha256",
}


class ContractError(ValueError):
    """入力、Manifest、出力契約の違反を表す安全停止エラー。"""


def canonical_hash(value: Any) -> str:
    """Coreと同じcanonical JSON規則でhashする。"""

    return _core_canonical_hash(value)


def sha256_file(path: Path) -> str:
    """ファイルを読み取り専用でhashする。"""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{label} must be an object")
    return value


def _require_string(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise ContractError(f"{label} must be a non-empty string")
    return value


def _require_sha256(value: object, label: str) -> str:
    text = _require_string(value, label)
    if not SHA256_PATTERN.fullmatch(text):
        raise ContractError(f"{label} must be a lowercase sha256 hash")
    return text


def _reject_forbidden_values(value: object, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_forbidden_values(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_forbidden_values(child, f"{path}[{index}]")
        return
    if isinstance(value, str) and any(pattern.search(value) for pattern in FORBIDDEN_VALUE_PATTERNS):
        raise ContractError(f"forbidden URL or secret-like value at {path}")


def _safe_relative_path(value: object, label: str) -> Path:
    text = _require_string(value, label).replace("\\", "/")
    candidate = Path(text)
    if candidate.is_absolute() or ":" in text.split("/", 1)[0]:
        raise ContractError(f"{label} must be repository-relative")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ContractError(f"{label} contains unsafe path components")
    return candidate


def _repo_file(repo_root: Path, relative: object, label: str) -> Path:
    candidate = _safe_relative_path(relative, label)
    raw_path = repo_root / candidate
    if raw_path.is_symlink():
        raise ContractError(f"{label} must not be a symlink")
    resolved = raw_path.resolve()
    root = repo_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ContractError(f"{label} escapes repository root")
    if resolved.is_symlink():
        raise ContractError(f"{label} must not be a symlink")
    if not resolved.is_file():
        raise ContractError(f"{label} does not exist: {candidate.as_posix()}")
    return resolved


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read JSON: {path}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def _validate_input_contract(contract: Mapping[str, Any], repo_root: Path) -> None:
    _reject_forbidden_values(contract)
    if contract.get("schema_version") != "p3-08r-input-contract/v1":
        raise ContractError("input contract schema_version is not fixed")
    if contract.get("run_id") != PREPARATION_RUN_ID or contract.get("step_id") != "P3-08R-01":
        raise ContractError("input contract run binding is invalid")
    repository = _require_mapping(contract.get("repository_recheck"), "repository_recheck")
    head = _require_string(repository.get("head"), "repository_recheck.head")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ContractError("repository_recheck.head must be a full lowercase commit")
    if repository.get("worktree") != "CLEAN" or repository.get("fixture_files_modified") is not False:
        raise ContractError("source worktree or fixture modification is not clean")

    p3_08a = _require_mapping(contract.get("p3_08a_recheck"), "p3_08a_recheck")
    if p3_08a.get("final_status") != "PASS" or p3_08a.get("human_gate") != "APPROVED":
        raise ContractError("P3-08A is not approved PASS")
    engine = _require_mapping(p3_08a.get("engine_identity"), "p3_08a_recheck.engine_identity")
    for field in ("image_index_digest", "linux_amd64_digest"):
        _require_sha256(engine.get(field), f"p3_08a_recheck.engine_identity.{field}")
    artifacts = p3_08a.get("artifact_recomputed")
    if not isinstance(artifacts, list) or not artifacts:
        raise ContractError("P3-08A artifact recheck is missing")
    for index, artifact in enumerate(artifacts):
        item = _require_mapping(artifact, f"p3_08a_recheck.artifact_recomputed[{index}]")
        _require_sha256(item.get("sha256"), f"P3-08A artifact hash {index}")
        if item.get("match") is not True:
            raise ContractError(f"P3-08A artifact hash {index} did not match")

    fixture_set = _require_mapping(contract.get("approved_fixture_set"), "approved_fixture_set")
    parent = _require_mapping(fixture_set.get("parent_manifest"), "approved_fixture_set.parent_manifest")
    parent_path = _repo_file(repo_root, parent.get("path"), "parent fixture path")
    if sha256_file(parent_path) != _require_sha256(parent.get("sha256"), "parent fixture hash"):
        raise ContractError("parent fixture hash mismatch")
    children = fixture_set.get("children")
    if not isinstance(children, list) or not children:
        raise ContractError("approved fixture children are missing")
    for index, child in enumerate(children):
        item = _require_mapping(child, f"approved_fixture_set.children[{index}]")
        child_path = _repo_file(repo_root, item.get("path"), f"fixture child path {index}")
        expected = _require_sha256(item.get("sha256"), f"fixture child hash {index}")
        if sha256_file(child_path) != expected:
            raise ContractError(f"fixture hash mismatch: {child_path.as_posix()}")
    if fixture_set.get("all_recomputed_hashes_match_manifest") is not True:
        raise ContractError("fixture recheck is not marked as matching")
    if fixture_set.get("approved_values_changed") is not False:
        raise ContractError("approved fixture values are marked changed")

    fire_control = _require_mapping(contract.get("p3_09_fire_control_recheck"), "p3_09_fire_control_recheck")
    if fire_control.get("execution_allowed") is not False:
        raise ContractError("P3-09 execution_allowed must remain false during preparation")
    unknowns = fire_control.get("unknowns")
    if not isinstance(unknowns, list) or not unknowns:
        raise ContractError("P3-09 fire-control unknown must remain explicit")
    assignments = contract.get("follow_up_assignments")
    if not isinstance(assignments, list):
        raise ContractError("follow-up assignments are missing")
    assignment_ids = {item.get("id") for item in assignments if isinstance(item, Mapping)}
    required_ids = {"P3-08R-02", "P3-08R-03", "P3-08R-04", "P3-08R-05"}
    if not required_ids.issubset(assignment_ids):
        raise ContractError("P3-08R follow-up assignment is incomplete")


def load_input_contract(path: Path, repo_root: Path) -> tuple[dict[str, Any], str]:
    """Load and validate the P3-08R-01 contract without modifying it."""

    contract = _read_json(path)
    _validate_input_contract(contract, repo_root.resolve())
    return contract, sha256_file(path)


def _validate_relative_roots(value: object, label: str, repo_root: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{label} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value):
        relative = _safe_relative_path(item, f"{label}[{index}]")
        resolved = (repo_root / relative).resolve()
        if repo_root.resolve() not in resolved.parents:
            raise ContractError(f"{label}[{index}] escapes repository root")
        result.append(relative.as_posix())
    return result


def _validate_expected_binding(expected: Mapping[str, Any], repo_root: Path, require_files: bool) -> None:
    required = (
        ("core_reference_path", "core_reference_sha256"),
        ("lean_output_schema_path", "lean_output_schema_sha256"),
        ("parity_map_path", "parity_map_sha256"),
    )
    for path_key, hash_key in required:
        path = _safe_relative_path(expected.get(path_key), f"expected.{path_key}")
        digest = _require_sha256(expected.get(hash_key), f"expected.{hash_key}")
        if require_files:
            actual = sha256_file(_repo_file(repo_root, path, f"expected.{path_key}"))
            if actual != digest:
                raise ContractError(f"expected artifact hash mismatch: {path.as_posix()}")


def validate_execution_manifest(
    manifest: Mapping[str, Any],
    contract: Mapping[str, Any],
    repo_root: Path,
    *,
    contract_path: Path | None = None,
    require_expected_files: bool = False,
) -> None:
    """Validate the dedicated P3-09 Manifest and all fixed bindings."""

    _reject_forbidden_values(manifest)
    if manifest.get("schema_version") != "p3-poc-execution-manifest/v1":
        raise ContractError("P3-09 Manifest schema_version is invalid")
    for field, expected in (
        ("run_id", POC_RUN_ID),
        ("phase_id", "phase3"),
        ("step_id", "P3-09"),
        ("preparation_run_id", PREPARATION_RUN_ID),
    ):
        if manifest.get(field) != expected:
            raise ContractError(f"Manifest {field} binding is invalid")
    if contract_path is None:
        contract_path = repo_root / CONTRACT_RELATIVE_PATH
    if _require_sha256(manifest.get("input_contract_sha256"), "input_contract_sha256") != sha256_file(contract_path):
        raise ContractError("input contract hash mismatch")

    fixture_contract = _require_mapping(contract.get("approved_fixture_set"), "approved_fixture_set")
    parent = _require_mapping(fixture_contract.get("parent_manifest"), "parent_manifest")
    if manifest.get("fixture_manifest_sha256") != _require_sha256(parent.get("sha256"), "parent fixture hash"):
        raise ContractError("Manifest parent fixture binding mismatch")
    children = fixture_contract.get("children")
    manifest_children = manifest.get("fixture_child_sha256s")
    expected_children = [item.get("sha256") for item in children] if isinstance(children, list) else []
    if manifest_children != expected_children:
        raise ContractError("Manifest child fixture binding mismatch")
    if not isinstance(manifest_children, list) or any(
        not SHA256_PATTERN.fullmatch(str(item)) for item in manifest_children
    ):
        raise ContractError("Manifest child fixture hash is invalid")
    if manifest.get("code_revision") != contract["repository_recheck"]["head"]:
        raise ContractError("Manifest code revision mismatch")

    p3_08a = _require_mapping(contract.get("p3_08a_recheck"), "p3_08a_recheck")
    contract_engine = _require_mapping(p3_08a.get("engine_identity"), "P3-08A engine identity")
    manifest_engine = _require_mapping(manifest.get("engine"), "Manifest engine")
    for field in ("image_index_digest", "linux_amd64_digest"):
        if manifest_engine.get(field) != contract_engine.get(field):
            raise ContractError(f"Manifest engine {field} mismatch")
        _require_sha256(manifest_engine.get(field), f"Manifest engine {field}")
    artifact_map = {
        item.get("name"): item for item in p3_08a.get("artifact_recomputed", []) if isinstance(item, Mapping)
    }
    for manifest_field, artifact_name in (
        ("image_tar_sha256", "image_tar"),
        ("license_sha256", "license"),
    ):
        artifact_expected = artifact_map.get(artifact_name, {}).get("sha256")
        if manifest_engine.get(manifest_field) != artifact_expected:
            raise ContractError(f"Manifest engine {manifest_field} mismatch")
        _require_sha256(manifest_engine.get(manifest_field), f"Manifest engine {manifest_field}")
    _require_string(manifest_engine.get("source_commit"), "Manifest engine source_commit")
    entrypoint = manifest_engine.get("entrypoint")
    if entrypoint != ["dotnet", "QuantConnect.Lean.Launcher.dll"]:
        raise ContractError("Manifest LEAN entrypoint is not fixed")

    execution = _require_mapping(manifest.get("execution"), "Manifest execution")
    exact_execution = {
        "input_root": "tests/fixtures/phase3",
        "readonly_inputs": True,
        "network_mode": "none",
        "data_provider": "Local",
        "automatic_data_download": False,
        "cloud": "NOT_USED",
        "broker": "NOT_USED",
        "secret": "NOT_USED",
    }
    for field, execution_expected in exact_execution.items():
        if execution.get(field) != execution_expected:
            raise ContractError(f"Manifest execution.{field} is not fail-closed")
    _validate_relative_roots(execution.get("write_roots"), "execution.write_roots", repo_root)

    adapter = _require_mapping(manifest.get("adapter"), "Manifest adapter")
    _require_string(adapter.get("name"), "adapter.name")
    _require_string(adapter.get("version"), "adapter.version")
    _require_sha256(adapter.get("artifact_sha256"), "adapter.artifact_sha256")
    expected_binding = _require_mapping(manifest.get("expected"), "Manifest expected")
    _validate_expected_binding(expected_binding, repo_root, require_expected_files)

    performance = _require_mapping(manifest.get("performance"), "Manifest performance")
    perf_fixture = _require_mapping(fixture_contract.get("performance"), "approved performance fixture")
    if performance.get("fixture_path") != perf_fixture.get("path"):
        raise ContractError("Manifest performance fixture path mismatch")
    if performance.get("fixture_sha256") != perf_fixture.get("sha256"):
        raise ContractError("Manifest performance fixture hash mismatch")
    if performance.get("elapsed_minutes") != 30 or performance.get("peak_rss_gib") != 8:
        raise ContractError("Manifest performance limits are not fixed")

    manifest_hash = _require_sha256(manifest.get("manifest_sha256"), "manifest_sha256")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if canonical_hash(payload) != manifest_hash:
        raise ContractError("Manifest canonical hash mismatch")


def build_lean_config(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Build deterministic Local/network-none config data without launching LEAN."""

    engine = _require_mapping(manifest.get("engine"), "Manifest engine")
    expected = _require_mapping(manifest.get("expected"), "Manifest expected")
    return {
        "schema_version": "p3-lean-project-config/v1",
        "run_id": POC_RUN_ID,
        "network_mode": "none",
        "data_provider": "Local",
        "automatic_data_download": False,
        "input_root": "tests/fixtures/phase3",
        "write_roots": ["/tmp", "/results"],
        "engine_digest": engine["linux_amd64_digest"],
        "expected_output_schema_sha256": expected["lean_output_schema_sha256"],
        "core_reference_sha256": expected["core_reference_sha256"],
        "launch_allowed": False,
    }


def _validate_utc_timestamp(value: object, label: str) -> None:
    text = _require_string(value, label)
    if not UTC_PATTERN.fullmatch(text):
        raise ContractError(f"{label} must be UTC and end with Z")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError(f"{label} is not a valid UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ContractError(f"{label} must be UTC")


def validate_lean_output(output: Mapping[str, Any]) -> None:
    """Validate the vendor-neutral machine-readable LEAN output boundary."""

    _reject_forbidden_values(output)
    extra = set(output) - OUTPUT_TOP_LEVEL_FIELDS
    if extra:
        raise ContractError(f"forbidden output field: {sorted(extra)[0]}")
    if set(output) != OUTPUT_TOP_LEVEL_FIELDS:
        raise ContractError("LEAN output required fields are incomplete")
    if output.get("schema_version") != "p3-lean-output/v1" or output.get("run_id") != POC_RUN_ID:
        raise ContractError("LEAN output run binding is invalid")
    status = output.get("status")
    if status not in {"PASS", "STOPPED"}:
        raise ContractError("LEAN output status is invalid")

    hashes = _require_mapping(output.get("hashes"), "LEAN output hashes")
    if set(hashes) != OUTPUT_HASH_FIELDS:
        raise ContractError("LEAN output hash fields are incomplete or unknown")
    for field in OUTPUT_HASH_FIELDS:
        _require_sha256(hashes.get(field), f"LEAN output hashes.{field}")

    sequence = output.get("sequence")
    if not isinstance(sequence, list):
        raise ContractError("LEAN output sequence must be a list")
    if status == "PASS" and not sequence:
        raise ContractError("PASS output cannot have an empty sequence")
    for expected_no, item in enumerate(sequence):
        row = _require_mapping(item, f"LEAN output sequence[{expected_no}]")
        if set(row) != OUTPUT_SEQUENCE_FIELDS:
            raise ContractError("LEAN output sequence contains unknown or missing fields")
        if row.get("sequence_no") != expected_no:
            raise ContractError("LEAN output sequence numbers are not contiguous")
        _validate_utc_timestamp(row.get("logical_time_utc"), "LEAN output logical_time_utc")
        _require_string(row.get("row_kind"), "LEAN output row_kind")
        _require_sha256(row.get("payload_sha256"), "LEAN output payload_sha256")
        _require_sha256(row.get("manifest_sha256"), "LEAN output manifest_sha256")

    failure = output.get("failure")
    if status == "PASS" and failure is not None:
        raise ContractError("PASS output cannot contain failure")
    if status == "STOPPED":
        failure_mapping = _require_mapping(failure, "STOPPED output failure")
        _require_string(failure_mapping.get("reason"), "STOPPED output failure.reason")


def _entry_plan(contract: Mapping[str, Any]) -> dict[str, Any]:
    fixture_set = _require_mapping(contract["approved_fixture_set"], "approved_fixture_set")
    children = fixture_set["children"]
    assert isinstance(children, list)
    p3_08a = _require_mapping(contract["p3_08a_recheck"], "p3_08a_recheck")
    engine = _require_mapping(p3_08a["engine_identity"], "engine identity")
    return {
        "schema_version": "p3-poc-entry-plan/v1",
        "run_id": POC_RUN_ID,
        "input": {
            "root": "tests/fixtures/phase3",
            "readonly": True,
            "paths": [item["path"] for item in children],
        },
        "project": {
            "template_root": "tests/engine_poc/lean_project",
            "config_schema": "tests/engine_poc/lean_project/config.schema.json",
            "data_provider": "Local",
        },
        "engine": {
            "image_index_digest": engine["image_index_digest"],
            "linux_amd64_digest": engine["linux_amd64_digest"],
            "entrypoint": ["dotnet", "QuantConnect.Lean.Launcher.dll"],
        },
        "execution_boundary": {
            "network_mode": "none",
            "write_roots": ["/tmp", "/results"],
            "cloud": "NOT_USED",
            "broker": "NOT_USED",
            "secret": "NOT_USED",
            "automatic_data_download": False,
        },
        "launch": {
            "mode": "prepare_only",
            "engine_started": False,
            "launch_allowed": False,
        },
    }


def prepare_entry(repo_root: Path, contract_path: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Validate the preparation contract and return a no-launch entry plan."""

    repo_root = repo_root.resolve()
    if contract_path.resolve() != (repo_root / CONTRACT_RELATIVE_PATH).resolve():
        raise ContractError("P3-08R input contract path is not the fixed repository path")
    contract, contract_sha256 = load_input_contract(contract_path, repo_root)
    plan = _entry_plan(contract)
    if manifest_path is None:
        manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    elif manifest_path.resolve() != (repo_root / MANIFEST_RELATIVE_PATH).resolve():
        raise ContractError("P3-09 Manifest path is not the fixed repository path")

    manifest_status = "NOT_YET_FIXED"
    manifest_result: dict[str, Any] = {
        "path": manifest_path.as_posix(),
        "status": manifest_status,
    }
    status = "CONTRACT_READY"
    if manifest_path.exists():
        manifest = _read_json(manifest_path)
        validate_execution_manifest(
            manifest,
            contract,
            repo_root,
            contract_path=contract_path,
            require_expected_files=True,
        )
        manifest_status = "VALIDATED"
        manifest_result = {"path": manifest_path.as_posix(), "status": manifest_status}
        status = "READY_TO_REHEARSE"

    return {
        "schema_version": "p3-poc-prepare-result/v1",
        "run_id": PREPARATION_RUN_ID,
        "mode": "prepare",
        "status": status,
        "contract_sha256": contract_sha256,
        "manifest": manifest_result,
        "entry_plan": plan,
        "network": {"required_mode": "none", "observed": False},
        "engine_started": False,
        "p3_09_start_allowed": False,
        "next_step": "P3-08R-03" if manifest_status == "NOT_YET_FIXED" else "P3-08R-04",
    }

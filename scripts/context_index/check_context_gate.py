from __future__ import annotations

# Step 02 user authority: the document-management platform's management,
# reference, evidence, stale, allowlist, and retry hash checks are force-
# skipped. This gate performs only nonhash path, scope, schema, Secret,
# UTF-8, size, state, and Human Gate checks. Protected safety/data/
# reproducibility hashes are owned by their respective runtimes and are not
# processed here.
import argparse
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .build_code_manifest import discover_code_paths
from .common import (
    ContextIndexError,
    PolicyViolation,
    discover_managed_paths,
    load_policy,
    normalize_relative_path,
    scan_secret_content,
    scan_secret_path,
)

GATE_SCHEMA_VERSION = "ctxmap-gate-report-v0.2-nonhash"
SNAPSHOT_SCHEMA_VERSION = "ctxmap-worktree-snapshot-v0.2-metadata"
DEFAULT_H1_RECEIPT = "plan/context_index/CTXMAP-H1_approval.json"
MANAGEMENT_HASH_POLICY_ENV = "CTXMAP_MANAGEMENT_HASH_POLICY"
DEFAULT_MANAGEMENT_HASH_POLICY = "disabled"

GENERATED_MANIFEST_PATHS = frozenset(
    {
        "context/artifact_manifest.json",
        "context/manifest_state.json",
        "context/code_manifest.json",
        "context/relation_graph.json",
    }
)
GENERATED_PREFIXES = (
    "plan/context_index/runtime/",
    "plan/context_index/receipts/",
)
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class GateError(ContextIndexError):
    """Raised for a safe, non-content-bearing gate failure."""


@dataclass(frozen=True)
class GitChange:
    """Compatibility shape for callers that only need a path/status pair."""

    status: str
    relative_path: str
    before_path: str | None = None


def is_generated_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    return normalized in GENERATED_MANIFEST_PATHS or normalized.startswith(GENERATED_PREFIXES)


def _safe_json_read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError("JSON_INPUT_INVALID") from exc
    if not isinstance(value, dict):
        raise GateError("JSON_ROOT_INVALID")
    return value


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _inside_root(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    candidate = path if path.is_absolute() else resolved_root / path
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise GateError("OUTPUT_OUTSIDE_REPOSITORY")
    return resolved


def _repo_input_file(root: Path, path: Path) -> Path:
    if path.is_absolute():
        raise GateError("INPUT_PATH_ABSOLUTE")
    try:
        resolved = _inside_root(root, path)
        relative = resolved.relative_to(root.resolve()).as_posix()
    except (GateError, ValueError) as exc:
        raise GateError("INPUT_PATH_OUTSIDE_REPOSITORY") from exc
    if not relative or relative == "." or not resolved.is_file():
        raise GateError("INPUT_PATH_MISSING")
    _assert_no_reparse(root, relative)
    return resolved


def _assert_no_reparse(root: Path, relative_path: str) -> None:
    current = root.resolve()
    for part in relative_path.split("/"):
        current = current / part
        try:
            if current.is_symlink():
                raise GateError("SYMLINK_PATH")
            attributes = getattr(os.stat(current, follow_symlinks=False), "st_file_attributes", 0)
            if attributes & 0x400:
                raise GateError("REPARSE_POINT_PATH")
        except FileNotFoundError:
            return
        except OSError as exc:
            raise GateError("PATH_STAT_FAILED") from exc


def _gate_target(root: Path, relative_path: str) -> Path:
    try:
        normalized = normalize_relative_path(relative_path)
    except PolicyViolation as exc:
        raise GateError(str(exc)) from exc
    _assert_no_reparse(root, normalized)
    return _inside_root(root, Path(*normalized.split("/")))


def _safe_path(value: str) -> str:
    try:
        return normalize_relative_path(value)
    except PolicyViolation as exc:
        raise GateError(str(exc)) from exc


def _read_changed_list(root: Path, path: Path) -> list[str]:
    control = _repo_input_file(root, path)
    try:
        lines = control.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise GateError("CHANGED_LIST_INVALID") from exc
    return [line.strip() for line in lines if line.strip()]


def _metadata_for_path(root: Path, relative_path: str, policy: dict[str, Any]) -> dict[str, Any]:
    normalized = _safe_path(relative_path)
    if scan_secret_path(normalized, policy):
        raise GateError("SECRET_PATH")
    target = _gate_target(root, normalized)
    result: dict[str, Any] = {"relative_path": normalized, "exists": target.exists()}
    if not target.exists():
        return result
    if not target.is_file():
        raise GateError("TARGET_NOT_FILE")
    try:
        data = target.read_bytes()
        stat = target.stat()
    except OSError as exc:
        raise GateError("FILE_READ_FAILED") from exc
    max_bytes = int(policy.get("max_file_bytes", 0))
    if max_bytes <= 0 or len(data) > max_bytes:
        raise GateError("FILE_SIZE_LIMIT")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError("UTF8_REQUIRED") from exc
    if scan_secret_content(text, policy):
        raise GateError("SECRET_CONTENT")
    result.update({"size": len(data), "mtime_ns": int(stat.st_mtime_ns)})
    return result


def capture_worktree_snapshot(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    """Return path/size/mtime metadata only; no content digest is produced."""

    paths = sorted(set(discover_managed_paths(root, policy)) | set(discover_code_paths(root, policy)))
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "verification": "path_size_mtime_only",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "paths": {path: _metadata_for_path(root, path, policy) for path in paths if not is_generated_path(path)},
    }


def require_h1_approval(root: Path, receipt: Path) -> None:
    receipt_path = _inside_root(root, receipt) if receipt.is_absolute() else _repo_input_file(root, receipt)
    value = _safe_json_read(receipt_path)
    if value.get("status") != "APPROVED":
        raise GateError("H1_NOT_APPROVED")


def _base_report(
    *, status: str, reason_code: str, requested_paths: list[str], target_paths: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "status": status,
        "reason_code": reason_code,
        "verification": "non_hash_path_schema_secret_state",
        "requested_paths": sorted(set(requested_paths)),
        "allowed_paths": sorted(set(target_paths)),
        "protected_hash_checks": "NOT_APPLICABLE_TO_DOCUMENT_GATE",
        "management_hash_checks": "SKIPPED_BY_USER_AUTHORITY",
    }


def run_gate(
    root: Path,
    policy_path: Path | str,
    manifest_path: Path | str | None = None,
    state_path: Path | str | None = None,
    code_manifest_path: Path | str | None = None,
    relation_graph_path: Path | str | None = None,
    *,
    changed: list[str] | None = None,
    changed_list: Path | None = None,
    baseline_snapshot: Path | None = None,
    a07_responses: Path | None = None,
    require_h1: bool = False,
    h1_receipt: Path | None = None,
    management_hash_policy: str = DEFAULT_MANAGEMENT_HASH_POLICY,
) -> dict[str, Any]:
    del manifest_path, state_path, code_manifest_path, relation_graph_path, baseline_snapshot, a07_responses
    if management_hash_policy != DEFAULT_MANAGEMENT_HASH_POLICY:
        raise GateError("LEGACY_MANAGEMENT_HASH_POLICY_RETIRED")
    repository = root.resolve()
    policy = load_policy(_inside_root(repository, Path(policy_path)))
    if require_h1:
        require_h1_approval(repository, h1_receipt or Path(DEFAULT_H1_RECEIPT))
    requested = list(changed or [])
    if changed_list is not None:
        requested.extend(_read_changed_list(repository, changed_list))
    safe_paths: list[str] = []
    details: list[dict[str, Any]] = []
    for path in requested:
        normalized = _safe_path(path)
        if is_generated_path(normalized):
            continue
        details.append(_metadata_for_path(repository, normalized, policy))
        safe_paths.append(normalized)
    report = _base_report(
        status="PASS",
        reason_code="NON_HASH_GATE_PASS",
        requested_paths=requested,
        target_paths=safe_paths,
    )
    report["targets"] = details
    report["human_gate"] = "APPROVED" if require_h1 else "NOT_REQUIRED"
    return report


def approved_paths_from_report(report_path: Path, root: Path, expected_legacy_value: str | None = None) -> list[str]:
    """Compatibility helper returning a nonhash path allowlist."""

    del root, expected_legacy_value
    report = _safe_json_read(report_path)
    if report.get("status") != "PASS":
        raise GateError("GATE_NOT_PASS")
    paths = report.get("allowed_paths", [])
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise GateError("GATE_ALLOWED_PATHS_INVALID")
    return sorted(set(paths))


def verify_index_matches_report(
    report_path: Path, root: Path, expected_legacy_value: str | None = None
) -> None:
    """Compatibility helper performing only path/safety revalidation."""

    del expected_legacy_value
    paths = approved_paths_from_report(report_path, root)
    policy = load_policy(_inside_root(root, Path("context/context_policy.json")))
    for path in paths:
        _metadata_for_path(root, path, policy)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nonhash local context safety gate.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("context/context_policy.json"))
    parser.add_argument("--manifest", type=Path, default=Path("context/artifact_manifest.json"))
    parser.add_argument("--state", type=Path, default=Path("context/manifest_state.json"))
    parser.add_argument("--code-manifest", type=Path, default=Path("context/code_manifest.json"))
    parser.add_argument("--relation-graph", type=Path, default=Path("context/relation_graph.json"))
    parser.add_argument("--report", type=Path, default=Path("plan/context_index/runtime/context_gate_report.json"))
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--changed-list", type=Path)
    parser.add_argument("--baseline-snapshot", type=Path)
    parser.add_argument("--a07-responses", type=Path)
    parser.add_argument("--snapshot-output", type=Path)
    parser.add_argument("--require-h1", action="store_true")
    parser.add_argument("--h1-receipt", type=Path, default=Path(DEFAULT_H1_RECEIPT))
    parser.add_argument(
        "--management-hash-policy",
        choices=("disabled",),
        default=os.environ.get(MANAGEMENT_HASH_POLICY_ENV, DEFAULT_MANAGEMENT_HASH_POLICY),
        help="Retained as a disabled-only migration compatibility option.",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report_path = _inside_root(root, args.report)
    try:
        if args.snapshot_output:
            policy = load_policy(_inside_root(root, args.policy))
            _write_json_atomic(_inside_root(root, args.snapshot_output), capture_worktree_snapshot(root, policy))
        report = run_gate(
            root,
            args.policy,
            args.manifest,
            args.state,
            args.code_manifest,
            args.relation_graph,
            changed=args.changed,
            changed_list=args.changed_list,
            baseline_snapshot=args.baseline_snapshot,
            a07_responses=args.a07_responses,
            require_h1=args.require_h1,
            h1_receipt=args.h1_receipt,
            management_hash_policy=args.management_hash_policy,
        )
    except (ContextIndexError, PolicyViolation, OSError, UnicodeError, json.JSONDecodeError) as exc:
        report = _base_report(
            status="BLOCKED",
            reason_code=str(exc) or "GATE_FAILED",
            requested_paths=args.changed,
            target_paths=[],
        )
        report["pending"] = {"reason_code": report["reason_code"]}
    try:
        _write_json_atomic(report_path, report)
    except OSError:
        print("GATE_REPORT_WRITE_FAILED")
        return 1
    output = {
        "status": report["status"],
        "reason_code": report["reason_code"],
        "management_hash_policy": "disabled",
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

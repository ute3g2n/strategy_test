from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .build_code_manifest import build_code_manifest, validate_code_manifest
from .build_relation_graph import build_relation_graph
from .common import (
    ContextIndexError,
    PolicyViolation,
    discover_managed_paths,
    is_managed_document,
    load_policy,
    normalize_relative_path,
    scan_secret_content,
    scan_secret_path,
    sha256_bytes,
)
from .run_context_maintenance import A07DispatchError, maintain_document
from .validate_context_index import validate_manifest

GATE_SCHEMA_VERSION = "ctxmap-gate-report-v0.1"
SNAPSHOT_SCHEMA_VERSION = "ctxmap-worktree-snapshot-v0.1"
DEFAULT_H1_RECEIPT = "plan/context_index/CTXMAP-H1_approval.json"
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

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


class GateError(ContextIndexError):
    """Raised for a safe, non-content-bearing gate failure."""


@dataclass(frozen=True)
class GitChange:
    status: str
    relative_path: str
    before_path: str | None = None


def is_generated_path(relative_path: str) -> bool:
    """Return whether a path is an index/runtime output that must not retrigger itself."""

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
    normalized = _safe_path(relative_path)
    _assert_no_reparse(root, normalized)
    candidate = (root.resolve() / Path(*normalized.split("/"))).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise GateError("PATH_OUTSIDE_REPOSITORY")
    return candidate


def _safe_path(value: str) -> str:
    try:
        return normalize_relative_path(value)
    except PolicyViolation as exc:
        raise GateError(str(exc)) from exc


def _git_status(root: Path) -> list[GitChange]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GateError("GIT_STATUS_UNAVAILABLE") from exc
    raw = result.stdout.decode("utf-8", errors="strict")
    tokens = [item for item in raw.split("\0") if item]
    changes: list[GitChange] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if len(token) < 4:
            raise GateError("GIT_STATUS_INVALID")
        status = token[:2]
        path = _safe_path(token[3:])
        before_path: str | None = None
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise GateError("GIT_STATUS_INVALID")
            before_path = _safe_path(tokens[index + 1])
            index += 1
        changes.append(GitChange(status, path, before_path))
        index += 1
    return changes


def _file_hash(root: Path, relative_path: str) -> str | None:
    target = _gate_target(root, relative_path)
    try:
        return sha256_bytes(target.read_bytes()) if target.is_file() else None
    except (OSError, ValueError) as exc:
        raise GateError("FILE_READ_FAILED") from exc


def capture_worktree_snapshot(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    """Capture hashes only; no document or source body is stored."""

    paths = set(discover_managed_paths(root.resolve(), policy))
    from .build_code_manifest import discover_code_paths

    paths.update(discover_code_paths(root.resolve(), policy))
    entries: dict[str, dict[str, Any]] = {}
    for path in sorted(paths):
        if is_generated_path(path):
            continue
        digest = _file_hash(root, path)
        entries[path] = {"exists": digest is not None, "sha256": digest}
    return {"schema_version": SNAPSHOT_SCHEMA_VERSION, "paths": entries}


def _load_snapshot(path: Path) -> dict[str, Any]:
    value = _safe_json_read(path)
    if value.get("schema_version") != SNAPSHOT_SCHEMA_VERSION or not isinstance(value.get("paths"), dict):
        raise GateError("SNAPSHOT_SCHEMA_INVALID")
    return value


def _snapshot_changed_paths(root: Path, policy: dict[str, Any], baseline: dict[str, Any]) -> set[str]:
    current = capture_worktree_snapshot(root, policy).get("paths", {})
    old = baseline.get("paths", {})
    paths = set(current) | set(old)
    changed: set[str] = set()
    for path in paths:
        if current.get(path) != old.get(path):
            changed.add(path)
    return changed


def _read_changed_list(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise GateError("CHANGED_LIST_INVALID") from exc
    result: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        normalized = _safe_path(line.strip())
        if normalized not in result:
            result.append(normalized)
    return result


def _selected_changes(
    root: Path,
    policy: dict[str, Any],
    explicit: list[str],
    changed_list: Path | None,
    baseline_snapshot: Path | None,
) -> tuple[list[GitChange], list[str]]:
    try:
        status_changes = _git_status(root)
    except GateError as exc:
        if explicit or changed_list:
            status_changes = []
        else:
            raise exc
    by_path = {item.relative_path: item for item in status_changes}
    if explicit or changed_list:
        requested = [_safe_path(item) for item in explicit]
        if changed_list:
            requested.extend(_read_changed_list(changed_list))
        requested = list(dict.fromkeys(requested))
    elif baseline_snapshot:
        requested = sorted(_snapshot_changed_paths(root, policy, _load_snapshot(baseline_snapshot)))
    else:
        requested = [item.relative_path for item in status_changes]
    selected: list[GitChange] = []
    for path in requested:
        selected.append(by_path.get(path, GitChange("??", path)))
    return selected, requested


def _validate_h1_receipt(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "H1_RECEIPT_MISSING"
    try:
        value = _safe_json_read(path)
    except GateError as exc:
        return False, str(exc)
    if value.get("gate_id") != "CTXMAP-H1":
        return False, "H1_RECEIPT_INVALID"
    if value.get("status") != "APPROVED":
        return False, "H1_NOT_APPROVED"
    if value.get("approval_text") != "CTXMAP-H1を承認します":
        return False, "H1_APPROVAL_TEXT_INVALID"
    return True, "H1_APPROVED"


def require_h1_approval(root: Path, receipt: Path) -> None:
    receipt_path = _inside_root(root, receipt)
    allowed, reason = _validate_h1_receipt(receipt_path)
    if not allowed:
        raise GateError(reason)


def _load_a07_responses(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    value = _safe_json_read(path)
    raw = value.get("responses", value)
    if not isinstance(raw, dict):
        raise GateError("A07_RESPONSES_INVALID")
    result: dict[str, dict[str, Any]] = {}
    for key, item in raw.items():
        normalized = _safe_path(str(key))
        if not isinstance(item, dict):
            raise GateError("A07_RESPONSES_INVALID")
        result[normalized] = copy.deepcopy(item)
    return result


def _safe_read_target(root: Path, relative_path: str, policy: dict[str, Any]) -> bytes:
    normalized = _safe_path(relative_path)
    if scan_secret_path(normalized, policy):
        raise GateError("SECRET_PATH")
    target = _gate_target(root, normalized)
    try:
        data = target.read_bytes()
    except (OSError, ValueError) as exc:
        raise GateError("FILE_READ_FAILED") from exc
    limit = int(policy.get("max_file_bytes", 0))
    source_limit = int(policy.get("source_max_file_bytes", limit))
    if len(data) > (source_limit if normalized not in GENERATED_MANIFEST_PATHS else limit):
        raise GateError("FILE_SIZE_LIMIT")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError("UTF8_REQUIRED") from exc
    if scan_secret_content(text, policy):
        raise GateError("SECRET_CONTENT")
    return data


def _request_id(relative_path: str) -> str:
    digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:16]
    return f"ctx-gate-{digest}"


def _receipt_path(root: Path, request_id: str) -> Path:
    return _inside_root(root, Path("plan/context_index/receipts") / f"{request_id}.json")


def _graph_valid(graph: Any) -> bool:
    return (
        isinstance(graph, dict)
        and graph.get("schema_version") == "ctxmap-relation-graph-v0.1"
        and isinstance(graph.get("nodes"), list)
        and isinstance(graph.get("edges"), list)
        and isinstance(graph.get("diagnostics"), list)
    )


def _validate_all(
    root: Path,
    policy: dict[str, Any],
    document_manifest: dict[str, Any],
    state: dict[str, Any] | None,
    code_manifest: dict[str, Any],
    relation_graph: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    document_report = validate_manifest(document_manifest, root, policy, state=state)
    code_report = validate_code_manifest(code_manifest, root, policy)
    graph_ok = _graph_valid(relation_graph)
    details = {
        "document_manifest": {"valid": document_report.valid, "counts": document_report.counts},
        "code_manifest": {"valid": code_report.valid, "status": code_report.status, "counts": code_report.counts},
        "relation_graph": {
            "valid": graph_ok,
            "node_count": len(relation_graph.get("nodes", [])) if isinstance(relation_graph, dict) else 0,
            "edge_count": len(relation_graph.get("edges", [])) if isinstance(relation_graph, dict) else 0,
        },
    }
    return document_report.valid and code_report.valid and graph_ok, details


def _base_report(
    *, status: str, reason_code: str, requested_paths: list[str], target_paths: list[str]
) -> dict[str, Any]:
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "status": status,
        "reason_code": reason_code,
        "requested_paths": requested_paths,
        "target_paths": target_paths,
        "ignored_paths": [],
        "generated_paths": [],
        "document_actions": [],
        "source_manifest_updated": False,
        "document_manifest_updated": False,
        "relation_graph_updated": False,
        "allowed_paths": [],
        "receipts": [],
        "pending": None,
        "validator": None,
    }


def approved_paths_from_report(report_path: Path, root: Path) -> list[str]:
    """Load a PASS report and return only normalized, repository-relative paths."""

    report = _safe_json_read(report_path)
    if report.get("schema_version") != GATE_SCHEMA_VERSION or report.get("status") != "PASS":
        raise GateError("GATE_REPORT_NOT_APPROVED")
    paths = report.get("allowed_paths")
    if not isinstance(paths, list) or not paths:
        raise GateError("GATE_ALLOWLIST_EMPTY")
    result: list[str] = []
    for value in paths:
        if not isinstance(value, str):
            raise GateError("GATE_ALLOWLIST_INVALID")
        normalized = _safe_path(value)
        if normalized not in result:
            _gate_target(root, normalized)
            result.append(normalized)
    return result


def run_gate(
    root: Path,
    policy_path: Path,
    manifest_path: Path,
    state_path: Path,
    code_manifest_path: Path,
    relation_graph_path: Path,
    *,
    changed: list[str] | None = None,
    changed_list: Path | None = None,
    baseline_snapshot: Path | None = None,
    a07_responses: Path | None = None,
    require_h1: bool = False,
    h1_receipt: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    policy = load_policy(_inside_root(root, policy_path))
    if require_h1:
        require_h1_approval(root, h1_receipt or Path(DEFAULT_H1_RECEIPT))
    selected, requested = _selected_changes(
        root, policy, changed or [], changed_list, baseline_snapshot
    )
    report = _base_report(status="PASS", reason_code="NO_TARGET_CHANGES", requested_paths=requested, target_paths=[])
    document_paths: list[str] = []
    source_paths: list[str] = []
    generated_paths: list[str] = []
    ignored_paths: list[str] = []
    for item in selected:
        path = item.relative_path
        if is_generated_path(path):
            generated_paths.append(path)
            continue
        try:
            is_doc = is_managed_document(path, policy)
            from .build_code_manifest import is_managed_code_path

            is_source = is_managed_code_path(path, policy)
        except (PolicyViolation, ValueError) as exc:
            is_doc = False
            is_source = False
            ignored_paths.append(path)
            if changed or changed_list:
                report["status"] = "BLOCKED"
                report["reason_code"] = str(exc) or "OUT_OF_SCOPE"
                report["target_paths"] = requested
                report["ignored_paths"] = sorted(set(ignored_paths))
                return report
            continue
        if is_doc:
            document_paths.append(path)
        elif is_source:
            source_paths.append(path)
        else:
            ignored_paths.append(path)
            if changed or changed_list:
                report["status"] = "BLOCKED"
                report["reason_code"] = "OUT_OF_SCOPE_TARGET"
                report["target_paths"] = requested
                report["ignored_paths"] = sorted(set(ignored_paths))
                return report
    target_paths = sorted(set(document_paths + source_paths + generated_paths))
    report["target_paths"] = target_paths
    report["ignored_paths"] = sorted(set(ignored_paths))
    report["generated_paths"] = sorted(set(generated_paths))

    document_manifest = _safe_json_read(_inside_root(root, manifest_path))
    state = _safe_json_read(_inside_root(root, state_path)) if _inside_root(root, state_path).exists() else None
    code_manifest = _safe_json_read(_inside_root(root, code_manifest_path))
    relation_graph = _safe_json_read(_inside_root(root, relation_graph_path))
    original_document = copy.deepcopy(document_manifest)
    original_state = copy.deepcopy(state)
    original_code = copy.deepcopy(code_manifest)
    original_graph = copy.deepcopy(relation_graph)
    receipt_records: list[tuple[Path, dict[str, Any]]] = []
    response_map = _load_a07_responses(a07_responses)

    if any(item.status[0] in {"D", "R", "C"} or item.status[1] in {"D", "R", "C"} for item in selected):
        report["status"] = "BLOCKED"
        report["reason_code"] = "RENAME_OR_DELETE_REQUIRES_RECONCILIATION"
        report["pending"] = {"reason_code": report["reason_code"], "paths": target_paths}
        return report
    active_manifest_paths = {
        str(item.get("relative_path"))
        for item in document_manifest.get("artifacts", [])
        if isinstance(item, dict) and item.get("status") == "active"
    }
    missing_manifest_paths = sorted(
        path for path in active_manifest_paths if _file_hash(root, path) is None
    )
    if missing_manifest_paths:
        report["status"] = "BLOCKED"
        report["reason_code"] = "RENAME_OR_DELETE_REQUIRES_RECONCILIATION"
        report["pending"] = {"reason_code": report["reason_code"], "paths": missing_manifest_paths}
        return report

    def dispatcher(payload: dict[str, Any]) -> dict[str, Any]:
        path = str(payload.get("relative_path", ""))
        decision = response_map.get(path)
        if decision is None:
            raise A07DispatchError("RUNTIME_DISPATCH_FALLBACK_REQUIRED")
        return decision

    observed_at = "2026-08-14T00:00:00Z"
    for path in sorted(document_paths):
        _safe_read_target(root, path, policy)
        result = maintain_document(
            root,
            path,
            policy,
            document_manifest,
            dispatcher=dispatcher,
            request_id=_request_id(path),
            observed_at=observed_at,
            state=state,
        )
        if result.status != "PASS":
            receipt = result.receipt
            receipt_path = _receipt_path(root, _request_id(path))
            _write_json_atomic(receipt_path, receipt)
            reason = str(receipt.get("reason_code", "MAINTENANCE_FAILED"))
            if reason == "RUNTIME_DISPATCH_FALLBACK_REQUIRED":
                reason = "A07_RUNTIME_UNAVAILABLE"
            report["status"] = "BLOCKED"
            report["reason_code"] = reason
            report["pending"] = {
                "reason_code": reason,
                "paths": [path],
                "receipt_path": receipt_path.relative_to(root).as_posix(),
            }
            return report
        document_manifest = result.manifest
        state = result.state
        receipt_path = _receipt_path(root, _request_id(path))
        receipt_records.append((receipt_path, result.receipt))
        report["document_actions"].append({"path": path, "action": result.action, "status": result.status})

    if source_paths:
        code_manifest = build_code_manifest(
            root, policy, observed_at=observed_at, existing_manifest=code_manifest
        )
        report["source_manifest_updated"] = code_manifest != original_code
    if document_paths:
        report["document_manifest_updated"] = document_manifest != original_document or state != original_state
    if document_paths or source_paths:
        relation_graph = build_relation_graph(code_manifest, document_manifest)
        report["relation_graph_updated"] = relation_graph != original_graph

    valid, validator = _validate_all(root, policy, document_manifest, state, code_manifest, relation_graph)
    report["validator"] = validator
    if not valid:
        report["status"] = "BLOCKED"
        report["reason_code"] = "VALIDATOR_FAILED"
        report["pending"] = {"reason_code": "VALIDATOR_FAILED", "paths": target_paths}
        return report

    for receipt_path, receipt in receipt_records:
        _write_json_atomic(receipt_path, receipt)
    if document_paths:
        _write_json_atomic(_inside_root(root, manifest_path), document_manifest)
        if state is not None:
            _write_json_atomic(_inside_root(root, state_path), state)
    if source_paths:
        _write_json_atomic(_inside_root(root, code_manifest_path), code_manifest)
    if document_paths or source_paths:
        _write_json_atomic(_inside_root(root, relation_graph_path), relation_graph)

    allowed = set(target_paths)
    if document_paths:
        allowed.update({"context/artifact_manifest.json", "context/manifest_state.json", "context/relation_graph.json"})
    if source_paths:
        allowed.update({"context/code_manifest.json", "context/relation_graph.json"})
    allowed.update(path.relative_to(root).as_posix() for path, _ in receipt_records)
    report["allowed_paths"] = sorted(allowed)
    report["status"] = "PASS"
    report["reason_code"] = "GATE_PASS"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed CTXMAP commit gate.")
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
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report_path = _inside_root(root, args.report)
    try:
        policy = load_policy(_inside_root(root, args.policy))
        if args.snapshot_output:
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
    print(json.dumps({"status": report["status"], "reason_code": report["reason_code"]}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

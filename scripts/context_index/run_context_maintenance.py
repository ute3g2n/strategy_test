from __future__ import annotations

# Step 02 user authority: document-management hashes, manifest fingerprints,
# stale checks, mismatch retries, and A07 hash contracts are force-skipped.
# Maintenance keeps metadata manifests and nonhash safety checks only.
import argparse
import copy
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .build_context_index import build_record
from .common import (
    GENERATOR_VERSION,
    SCHEMA_VERSION,
    ContextIndexError,
    PolicyViolation,
    assert_safe_document,
    is_managed_document,
    load_policy,
    normalize_relative_path,
)
from .validate_context_index import validate_manifest

MAINTENANCE_SCHEMA_VERSION = "ctxmap-maintenance-receipt-v0.2-nonhash"
A07_MODEL = "gpt-5.6-luna"
A07_REASONING_EFFORT = "low"
MANAGEMENT_HASH_POLICY_ENV = "CTXMAP_MANAGEMENT_HASH_POLICY"
DEFAULT_MANAGEMENT_HASH_POLICY = "disabled"
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SAFE_TIMESTAMP_RE = re.compile(r"^[0-9T:Z+._-]{1,64}$")


class MaintenanceError(ContextIndexError):
    """Raised for safe, non-content-bearing maintenance errors."""


class A07DispatchError(MaintenanceError):
    """Compatibility error; active maintenance no longer dispatches A07."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class A07OutputError(MaintenanceError):
    """Compatibility error for retired A07 output contracts."""


@dataclass(frozen=True)
class MaintenanceResult:
    status: str
    action: str
    manifest: dict[str, Any]
    receipt: dict[str, Any]
    state: dict[str, Any] | None = None


Dispatcher = Callable[[dict[str, Any]], Mapping[str, Any]]


def _empty_manifest() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "generator_version": GENERATOR_VERSION, "artifacts": []}


def _clone(value: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(value))


def _safe_request_id(value: str) -> str:
    if not isinstance(value, str) or not _SAFE_IDENTIFIER_RE.fullmatch(value):
        raise MaintenanceError("REQUEST_ID_INVALID")
    return value


def _safe_timestamp(value: str | None) -> str:
    if value and _SAFE_TIMESTAMP_RE.fullmatch(value):
        return value
    return "UNSPECIFIED"


def _artifact_by_path(manifest: Mapping[str, Any], relative_path: str) -> dict[str, Any] | None:
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        raise MaintenanceError("MANIFEST_SCHEMA_INVALID")
    matches = [
        record for record in records if isinstance(record, dict) and record.get("relative_path") == relative_path
    ]
    if len(matches) > 1:
        raise MaintenanceError("MANIFEST_DUPLICATE_PATH")
    return matches[0] if matches else None


def _validate_manifest_input(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise MaintenanceError("MANIFEST_SCHEMA_INVALID")
    if not isinstance(manifest.get("generator_version"), str) or not isinstance(manifest.get("artifacts"), list):
        raise MaintenanceError("MANIFEST_SCHEMA_INVALID")


def _structural_diff(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any],
    *,
    major_change: bool,
    change_kind: str,
) -> dict[str, Any]:
    return {
        "change_kind": change_kind,
        "major_change": major_change,
        "before_headings": before.get("headings", []) if before else [],
        "after_headings": after.get("headings", []),
        "before_trace_ids": before.get("trace_ids", []) if before else [],
        "after_trace_ids": after.get("trace_ids", []),
        "before_local_links": before.get("local_links", []) if before else [],
        "after_local_links": after.get("local_links", []),
    }


def _is_major_change(before: Mapping[str, Any], after: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    before_size = int(before.get("byte_size", 0))
    after_size = int(after.get("byte_size", 0))
    denominator = max(before_size, after_size, 1)
    if abs(after_size - before_size) / denominator > float(policy.get("major_change_ratio", 0.20)):
        return True
    return any(before.get(field) != after.get(field) for field in ("headings", "trace_ids", "local_links"))


def _replace_record(manifest: Mapping[str, Any], record: Mapping[str, Any]) -> dict[str, Any]:
    result = _clone(manifest)
    result["artifacts"] = [
        _clone(item)
        for item in result["artifacts"]
        if isinstance(item, dict) and item.get("relative_path") != record.get("relative_path")
    ]
    result["artifacts"].append(_clone(record))
    result["artifacts"].sort(key=lambda item: str(item.get("relative_path", "")))
    return result


def _replace_path_record(manifest: Mapping[str, Any], old_path: str, record: Mapping[str, Any]) -> dict[str, Any]:
    result = _clone(manifest)
    result["artifacts"] = [
        _clone(item)
        for item in result["artifacts"]
        if not (isinstance(item, dict) and item.get("relative_path") in {old_path, record.get("relative_path")})
    ]
    result["artifacts"].append(_clone(record))
    result["artifacts"].sort(key=lambda item: str(item.get("relative_path", "")))
    return result


def _update_state(
    state: Mapping[str, Any] | None,
    record: Mapping[str, Any],
    observed_at: str,
    delta_kind: str,
) -> dict[str, Any]:
    result = (
        _clone(state)
        if state
        else {"schema_version": SCHEMA_VERSION, "generator_version": GENERATOR_VERSION, "states": []}
    )
    if not isinstance(result.get("states"), list):
        raise MaintenanceError("STATE_SCHEMA_INVALID")
    result["states"] = [
        _clone(item)
        for item in result["states"]
        if not (isinstance(item, dict) and item.get("subject_id") == record.get("artifact_id"))
    ]
    item = {
        "subject_id": record.get("artifact_id"),
        "subject_type": "artifact",
        "state": record.get("status"),
        "last_processed_at": observed_at,
        "generator_version": record.get("generator_version", GENERATOR_VERSION),
        "schema_version": SCHEMA_VERSION,
        "delta_kind": delta_kind,
    }
    result["states"].append(item)
    result["states"].sort(key=lambda value: str(value.get("subject_id", "")))
    return result


def _safe_dispatch_info(
    *,
    attempts: int,
    status: str,
    reason_code: str | None = None,
    decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    del decision
    result: dict[str, Any] = {
        "backend": "not_run",
        "agent_name": "AutoTrade_A07_ContextManifestMaintainer_v0_1",
        "model": A07_MODEL,
        "reasoning_effort": A07_REASONING_EFFORT,
        "status": status,
        "attempts": attempts,
        "independent": False,
        "review_mode": "NOT_APPLICABLE_METADATA_ONLY",
    }
    if reason_code:
        result["reason_code"] = reason_code
    return result


def _base_receipt(
    *,
    request_id: str,
    relative_path: str | None,
    action: str,
    status: str,
    observed_at: str | None,
    reason_code: str,
) -> dict[str, Any]:
    return {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "request_id": request_id,
        "relative_path": relative_path,
        "action": action,
        "status": status,
        "reason_code": reason_code,
        "recorded_at": _safe_timestamp(observed_at),
        "verification": "metadata_schema_path_link_secret_state",
        "management_hash_checks": "SKIPPED_BY_USER_AUTHORITY",
        "protected_hash_checks": "NOT_APPLICABLE_TO_DOCUMENT_MANAGEMENT",
        "dispatch": _safe_dispatch_info(attempts=0, status="NOT_RUN"),
    }


def _blocked(
    manifest: Mapping[str, Any],
    *,
    request_id: str,
    relative_path: str | None,
    observed_at: str | None,
    reason_code: str,
    state: Mapping[str, Any] | None = None,
    dispatch: Mapping[str, Any] | None = None,
) -> MaintenanceResult:
    receipt = _base_receipt(
        request_id=request_id,
        relative_path=relative_path,
        action="blocked",
        status="BLOCKED",
        observed_at=observed_at,
        reason_code=reason_code,
    )
    if dispatch:
        receipt["dispatch"] = _clone(dispatch)
    return MaintenanceResult("BLOCKED", "blocked", _clone(manifest), receipt, _clone(state) if state else None)


def _finalize(
    manifest: Mapping[str, Any], root: Path, policy: Mapping[str, Any], *, state: Mapping[str, Any] | None
) -> None:
    report = validate_manifest(manifest, root, policy, state=state)
    if not report.valid:
        raise MaintenanceError("NON_HASH_VALIDATION_FAILED")


def maintain_document(
    root: Path,
    changed_path: str,
    policy: Mapping[str, Any] | Path | str,
    manifest: Mapping[str, Any],
    *,
    dispatcher: Dispatcher | None,
    request_id: str = "ctx-maintenance",
    observed_at: str | None = None,
    state: Mapping[str, Any] | None = None,
    history: Sequence[Mapping[str, Any]] | None = None,
    max_attempts: int = 1,
    validate_manifest_result: bool = True,
) -> MaintenanceResult:
    del dispatcher, history, max_attempts
    safe_request = request_id if isinstance(request_id, str) else "REDACTED"
    normalized: str | None = None
    try:
        safe_request = _safe_request_id(request_id)
        loaded_policy = load_policy(policy)
        _validate_manifest_input(manifest)
        normalized = normalize_relative_path(changed_path)
        if not is_managed_document(normalized, loaded_policy):
            raise MaintenanceError("OUT_OF_SCOPE")
        existing = _artifact_by_path(manifest, normalized)
        assert_safe_document(root.resolve(), normalized, loaded_policy)
        timestamp = _safe_timestamp(observed_at)
        candidate = build_record(root.resolve(), normalized, loaded_policy, timestamp, existing)
        if existing is None:
            action = "record_add"
            reason_code = "METADATA_RECORD_ADDED"
            delta_kind = "added"
            major_change = True
        else:
            major_change = _is_major_change(existing, candidate, loaded_policy)
            changed_fields = tuple(
                field
                for field in (
                    "title",
                    "headings",
                    "trace_ids",
                    "local_links",
                    "summary",
                    "purpose",
                    "line_count",
                    "byte_size",
                )
                if existing.get(field) != candidate.get(field)
            )
            action = "record_update" if changed_fields else "metadata_unchanged"
            reason_code = "METADATA_RECORD_UPDATED" if changed_fields else "METADATA_UNCHANGED"
            delta_kind = "modified_major" if major_change else "modified_minor"
        updated_state = _update_state(state, candidate, timestamp, delta_kind)
        updated_manifest = _replace_record(manifest, candidate)
        if validate_manifest_result:
            _finalize(updated_manifest, root.resolve(), loaded_policy, state=updated_state)
        receipt = _base_receipt(
            request_id=safe_request,
            relative_path=normalized,
            action=action,
            status="PASS",
            observed_at=observed_at,
            reason_code=reason_code,
        )
        receipt["change"] = _structural_diff(existing, candidate, major_change=major_change, change_kind=delta_kind)
        receipt["dispatch"] = _safe_dispatch_info(attempts=0, status="NOT_RUN")
        return MaintenanceResult("PASS", action, updated_manifest, receipt, updated_state)
    except (MaintenanceError, PolicyViolation, OSError) as exc:
        return _blocked(
            manifest,
            request_id=safe_request,
            relative_path=normalized,
            observed_at=observed_at,
            reason_code=str(exc) or "MAINTENANCE_FAILED",
            state=state,
        )


def process_delta(
    root: Path,
    policy: Mapping[str, Any] | Path | str,
    manifest: Mapping[str, Any],
    delta: Mapping[str, Any],
    *,
    request_id: str = "ctx-delta",
    observed_at: str | None = None,
    state: Mapping[str, Any] | None = None,
) -> MaintenanceResult:
    safe_request = (
        request_id if isinstance(request_id, str) and _SAFE_IDENTIFIER_RE.fullmatch(request_id) else "REDACTED"
    )
    try:
        loaded_policy = load_policy(policy)
        _validate_manifest_input(manifest)
        kind = delta.get("change_kind")
        if kind not in {"renamed", "deleted"}:
            raise MaintenanceError("DELTA_KIND_INVALID")
        if kind == "renamed":
            old_path = normalize_relative_path(str(delta.get("before_path", "")))
            new_path = normalize_relative_path(str(delta.get("after_path", "")))
            existing = _artifact_by_path(manifest, old_path)
            if existing is None or _artifact_by_path(manifest, new_path) is not None:
                raise MaintenanceError("RENAME_STATE_INVALID")
            record = build_record(root.resolve(), new_path, loaded_policy, _safe_timestamp(observed_at), existing)
            updated_state = _update_state(state, record, _safe_timestamp(observed_at), "renamed")
            updated_manifest = _replace_path_record(manifest, old_path, record)
            _finalize(updated_manifest, root.resolve(), loaded_policy, state=updated_state)
            receipt = _base_receipt(
                request_id=safe_request,
                relative_path=new_path,
                action="renamed",
                status="PASS",
                observed_at=observed_at,
                reason_code="RENAME_METADATA_UPDATED",
            )
            receipt["before_path"] = old_path
            return MaintenanceResult("PASS", "renamed", updated_manifest, receipt, updated_state)
        old_path = normalize_relative_path(str(delta.get("before_path", "")))
        existing = _artifact_by_path(manifest, old_path)
        if existing is None:
            raise MaintenanceError("DELETE_STATE_INVALID")
        deleted = _clone(existing)
        deleted.pop("source_hash", None)
        deleted.update(
            {
                "status": "deleted",
                "deleted_at": _safe_timestamp(observed_at),
                "last_known_path": old_path,
                "updated_at": _safe_timestamp(observed_at),
            }
        )
        updated_state = _update_state(state, deleted, _safe_timestamp(observed_at), "deleted")
        updated_manifest = _replace_record(manifest, deleted)
        _finalize(updated_manifest, root.resolve(), loaded_policy, state=updated_state)
        receipt = _base_receipt(
            request_id=safe_request,
            relative_path=old_path,
            action="deleted",
            status="PASS",
            observed_at=observed_at,
            reason_code="DELETE_METADATA_UPDATED",
        )
        return MaintenanceResult("PASS", "deleted", updated_manifest, receipt, updated_state)
    except (MaintenanceError, PolicyViolation, OSError) as exc:
        return _blocked(
            manifest,
            request_id=safe_request,
            relative_path=None,
            observed_at=observed_at,
            reason_code=str(exc) or "DELTA_FAILED",
            state=state,
        )


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
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
            handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MaintenanceError("JSON_INPUT_INVALID") from exc
    if not isinstance(value, dict):
        raise MaintenanceError("JSON_ROOT_INVALID")
    return value


def _output_inside_root(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise MaintenanceError("OUTPUT_OUTSIDE_REPOSITORY")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one metadata-only document context maintenance event.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--state-output", type=Path)
    parser.add_argument("--changed")
    parser.add_argument("--delta-json", type=Path)
    parser.add_argument("--request-id", default="ctx-maintenance")
    parser.add_argument("--observed-at")
    parser.add_argument("--max-attempts", type=int, default=1, help="Accepted for compatibility; retries are retired.")
    parser.add_argument(
        "--management-hash-policy",
        choices=("disabled",),
        default=os.environ.get(MANAGEMENT_HASH_POLICY_ENV, DEFAULT_MANAGEMENT_HASH_POLICY),
        help="Retained as a disabled-only migration compatibility option.",
    )
    args = parser.parse_args(argv)
    if bool(args.changed) == bool(args.delta_json):
        print("CHANGED_OR_DELTA_REQUIRED")
        return 1
    root = args.root.resolve()
    try:
        manifest_path = _output_inside_root(root, args.manifest)
        output_path = _output_inside_root(root, args.output)
        receipt_path = _output_inside_root(root, args.receipt_output)
        state_path = _output_inside_root(root, args.state) if args.state else None
        state_output = _output_inside_root(root, args.state_output) if args.state_output else None
        manifest = _load_json(manifest_path) if manifest_path.exists() else _empty_manifest()
        state = _load_json(state_path) if state_path and state_path.exists() else None
        if args.delta_json:
            result = process_delta(
                root,
                args.policy,
                manifest,
                _load_json(_output_inside_root(root, args.delta_json)),
                request_id=args.request_id,
                observed_at=args.observed_at,
                state=state,
            )
        else:
            result = maintain_document(
                root,
                args.changed,
                args.policy,
                manifest,
                dispatcher=None,
                request_id=args.request_id,
                observed_at=args.observed_at,
                state=state,
                max_attempts=args.max_attempts,
            )
        _write_json_atomic(receipt_path, result.receipt)
        if result.status == "PASS":
            _write_json_atomic(output_path, result.manifest)
            if state_output and result.state is not None:
                _write_json_atomic(state_output, result.state)
        print(
            json.dumps(
                {"status": result.status, "action": result.action, "verification": "metadata_only"},
                ensure_ascii=False,
            )
        )
        return 0 if result.status == "PASS" else 1
    except (MaintenanceError, OSError) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

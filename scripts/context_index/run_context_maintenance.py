from __future__ import annotations

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
    sha256_bytes,
)
from .validate_context_index import validate_manifest

MAINTENANCE_SCHEMA_VERSION = "ctxmap-maintenance-receipt-v0.1"
A07_ACTIONS = {"record_add", "record_update", "metadata_unchanged", "blocked"}
A07_MODEL = "gpt-5.6-luna"
A07_REASONING_EFFORT = "low"
_A07_REQUIRED_KEYS = {
    "artifact_id",
    "action",
    "summary",
    "purpose",
    "triggers",
    "headings",
    "relations",
    "confidence",
    "reason",
    "source_hash",
    "receipt",
}
_SAFE_RECEIPT_KEYS = {
    "agent_id",
    "model",
    "reasoning_effort",
    "status",
    "run_id",
    "backend",
    "review_mode",
    "independent",
}
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SAFE_TIMESTAMP_RE = re.compile(r"^[0-9T:Z+._-]{1,64}$")
_HASH_RE = re.compile(r"^[a-f0-9]{64}$")


class MaintenanceError(ContextIndexError):
    """Raised for a safe, non-content-bearing maintenance error."""


class A07DispatchError(MaintenanceError):
    """Raised when the A07 runtime cannot produce a decision."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class A07OutputError(MaintenanceError):
    """Raised when an A07 response violates its strict output contract."""


@dataclass(frozen=True)
class MaintenanceResult:
    status: str
    action: str
    manifest: dict[str, Any]
    receipt: dict[str, Any]
    state: dict[str, Any] | None = None


Dispatcher = Callable[[dict[str, Any]], Mapping[str, Any]]


def _empty_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "artifacts": [],
    }


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
        record
        for record in records
        if isinstance(record, dict) and record.get("relative_path") == relative_path
    ]
    if len(matches) > 1:
        raise MaintenanceError("MANIFEST_DUPLICATE_PATH")
    return matches[0] if matches else None


def _validate_manifest_input(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise MaintenanceError("MANIFEST_SCHEMA_INVALID")
    if not isinstance(manifest.get("generator_version"), str):
        raise MaintenanceError("MANIFEST_SCHEMA_INVALID")
    if not isinstance(manifest.get("artifacts"), list):
        raise MaintenanceError("MANIFEST_SCHEMA_INVALID")


def _safe_existing_record(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    allowed = (
        "artifact_id",
        "kind",
        "status",
        "relative_path",
        "source_hash",
        "schema_version",
        "generator_version",
        "title",
        "headings",
        "trace_ids",
        "local_links",
        "summary",
        "purpose",
        "triggers",
        "relation_ids",
        "line_count",
        "byte_size",
    )
    result = {key: copy.deepcopy(record[key]) for key in allowed if key in record}
    for key in ("title", "summary", "purpose"):
        if isinstance(result.get(key), str):
            result[key] = result[key][:2000]
    return result


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


def _input_hash(payload: Mapping[str, Any]) -> str:
    serializable = {key: value for key, value in payload.items() if key != "input_hash"}
    raw = json.dumps(serializable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def _is_major_change(before: Mapping[str, Any], after: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    before_size = int(before.get("byte_size", 0))
    after_size = int(after.get("byte_size", 0))
    denominator = max(before_size, after_size, 1)
    if abs(after_size - before_size) / denominator > float(policy.get("major_change_ratio", 0.20)):
        return True
    return any(before.get(field) != after.get(field) for field in ("headings", "trace_ids", "local_links"))


def _minor_record(
    before: Mapping[str, Any], after: Mapping[str, Any], observed_at: str
) -> dict[str, Any]:
    record = _clone(before)
    for key in ("source_hash", "updated_at", "line_count", "byte_size", "status"):
        record[key] = after[key] if key != "updated_at" else observed_at
    record["status"] = "active"
    return record


def _merge_a07_decision(
    candidate: Mapping[str, Any], decision: Mapping[str, Any], observed_at: str
) -> dict[str, Any]:
    record = _clone(candidate)
    record.update(
        {
            "summary": decision["summary"],
            "purpose": decision["purpose"],
            "triggers": copy.deepcopy(decision["triggers"]),
            "headings": copy.deepcopy(decision["headings"]),
            "relation_ids": copy.deepcopy(decision["relations"]),
            "updated_at": observed_at,
            "status": "active",
        }
    )
    return record


def _replace_record(manifest: Mapping[str, Any], record: Mapping[str, Any]) -> dict[str, Any]:
    result = _clone(manifest)
    artifacts = [
        _clone(item)
        for item in result["artifacts"]
        if isinstance(item, dict) and item.get("relative_path") != record.get("relative_path")
    ]
    artifacts.append(_clone(record))
    artifacts.sort(key=lambda item: str(item.get("relative_path", "")))
    result["artifacts"] = artifacts
    return result


def _replace_path_record(
    manifest: Mapping[str, Any], old_path: str, record: Mapping[str, Any]
) -> dict[str, Any]:
    result = _clone(manifest)
    artifacts = [
        _clone(item)
        for item in result["artifacts"]
        if isinstance(item, dict) and item.get("relative_path") not in {old_path, record.get("relative_path")}
    ]
    artifacts.append(_clone(record))
    artifacts.sort(key=lambda item: str(item.get("relative_path", "")))
    result["artifacts"] = artifacts
    return result


def _update_state(
    state: Mapping[str, Any] | None,
    record: Mapping[str, Any],
    observed_at: str,
    delta_kind: str,
) -> dict[str, Any] | None:
    if state is None:
        return None
    if state.get("schema_version") != SCHEMA_VERSION or not isinstance(state.get("states"), list):
        raise MaintenanceError("STATE_SCHEMA_INVALID")
    result = _clone(state)
    states = [
        _clone(item)
        for item in result["states"]
        if isinstance(item, dict) and item.get("subject_id") != record.get("artifact_id")
    ]
    states.append(
        {
            "subject_id": record["artifact_id"],
            "subject_type": "artifact",
            "source_hash": record["source_hash"],
            "state": record["status"],
            "last_processed_at": observed_at,
            "generator_version": record["generator_version"],
            "schema_version": SCHEMA_VERSION,
            "delta_kind": delta_kind,
        }
    )
    states.sort(key=lambda item: str(item.get("subject_id", "")))
    result["states"] = states
    return result


def _sanitize_a07_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, Any] = {}
    for key in sorted(_SAFE_RECEIPT_KEYS):
        item = value.get(key)
        if isinstance(item, bool):
            result[key] = item
        elif isinstance(item, str) and len(item) <= 200 and _SAFE_IDENTIFIER_RE.fullmatch(item):
            result[key] = item
    return result


def _base_receipt(
    *,
    request_id: str,
    relative_path: str | None,
    source_hash: str | None,
    action: str,
    status: str,
    observed_at: str | None,
    reason_code: str,
) -> dict[str, Any]:
    return {
        "schema_version": MAINTENANCE_SCHEMA_VERSION,
        "request_id": request_id if _SAFE_IDENTIFIER_RE.fullmatch(request_id) else "REDACTED",
        "relative_path": relative_path,
        "source_hash": source_hash if source_hash and _HASH_RE.fullmatch(source_hash) else None,
        "action": action,
        "status": status,
        "reason_code": reason_code,
        "recorded_at": _safe_timestamp(observed_at),
    }


def _blocked(
    manifest: Mapping[str, Any],
    *,
    request_id: str,
    relative_path: str | None,
    source_hash: str | None,
    observed_at: str | None,
    reason_code: str,
    dispatch: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
) -> MaintenanceResult:
    receipt = _base_receipt(
        request_id=request_id,
        relative_path=relative_path,
        source_hash=source_hash,
        action="blocked",
        status="BLOCKED",
        observed_at=observed_at,
        reason_code=reason_code,
    )
    if dispatch is not None:
        receipt["dispatch"] = dict(dispatch)
    return MaintenanceResult("BLOCKED", "blocked", _clone(manifest), receipt, _clone(state) if state else None)


def _validate_a07_decision(
    decision: Any,
    *,
    expected_artifact_id: str,
    expected_hash: str,
    required_action: str,
    min_confidence: float,
) -> dict[str, Any]:
    if not isinstance(decision, dict) or set(decision) != _A07_REQUIRED_KEYS:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if decision.get("artifact_id") != expected_artifact_id:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if decision.get("action") not in A07_ACTIONS or decision["action"] != required_action:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if decision.get("source_hash") != expected_hash:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not isinstance(decision.get("summary"), str) or len(decision["summary"]) > 2000:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not isinstance(decision.get("purpose"), str) or len(decision["purpose"]) > 2000:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not isinstance(decision.get("reason"), str) or not decision["reason"] or len(decision["reason"]) > 1000:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not isinstance(decision.get("triggers"), list) or len(decision["triggers"]) > 100:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not isinstance(decision.get("headings"), list) or len(decision["headings"]) > 1000:
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not isinstance(decision.get("relations"), list) or len(decision["relations"]) > 100:
        raise A07OutputError("A07_OUTPUT_INVALID")
    confidence = decision.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise A07OutputError("A07_OUTPUT_INVALID")
    if not 0.0 <= float(confidence) <= 1.0 or float(confidence) < min_confidence:
        raise A07OutputError("A07_CONFIDENCE_INSUFFICIENT")
    if not isinstance(decision.get("receipt"), Mapping):
        raise A07OutputError("A07_OUTPUT_INVALID")
    return decision


def _safe_dispatch_info(
    *,
    attempts: int,
    status: str,
    decision: Mapping[str, Any] | None = None,
    reason_code: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "backend": "multi_agent_v1",
        "agent_name": "AutoTrade_A07_ContextManifestMaintainer_v0_1",
        "model": A07_MODEL,
        "reasoning_effort": A07_REASONING_EFFORT,
        "status": status,
        "attempts": attempts,
        "agent_id": "N/A",
        "independent": False,
        "review_mode": "SELF_REVIEW_FALLBACK",
    }
    if reason_code:
        value["reason_code"] = reason_code
    if decision is not None:
        value.update(_sanitize_a07_receipt(decision.get("receipt")))
    return value


def _finalize(
    manifest: Mapping[str, Any],
    root: Path,
    policy: Mapping[str, Any],
    *,
    state: Mapping[str, Any] | None,
) -> None:
    report = validate_manifest(manifest, root, policy, state=state)
    if not report.valid:
        raise MaintenanceError("VALIDATOR_FAILED")


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
) -> MaintenanceResult:
    safe_request = request_id if isinstance(request_id, str) else "REDACTED"
    try:
        safe_request = _safe_request_id(request_id)
        loaded_policy = load_policy(policy)
        _validate_manifest_input(manifest)
        if max_attempts < 1 or max_attempts > 3:
            raise MaintenanceError("ATTEMPT_LIMIT_INVALID")
        normalized = normalize_relative_path(changed_path)
        if not loaded_policy or not normalized:
            raise MaintenanceError("PATH_INVALID")
        if not is_managed_document(normalized, loaded_policy):
            raise MaintenanceError("OUT_OF_SCOPE")
        existing = _artifact_by_path(manifest, normalized)
        target, data, text = assert_safe_document(root.resolve(), normalized, loaded_policy)
        del target
        candidate = build_record(
            root.resolve(), normalized, loaded_policy, _safe_timestamp(observed_at), existing
        )
        source_hash = candidate["source_hash"]
        for item in history or []:
            if item.get("request_id") != safe_request:
                continue
            if item.get("source_hash") == source_hash and existing is not None:
                receipt = _base_receipt(
                    request_id=safe_request,
                    relative_path=normalized,
                    source_hash=source_hash,
                    action="idempotent_replay",
                    status="PASS",
                    observed_at=observed_at,
                    reason_code="IDEMPOTENT_REPLAY",
                )
                receipt["dispatch"] = {"status": "NOT_REQUIRED", "attempts": 0}
                return MaintenanceResult(
                    "PASS",
                    "idempotent_replay",
                    _clone(manifest),
                    receipt,
                    _clone(state) if state else None,
                )
            return _blocked(
                manifest,
                request_id=safe_request,
                relative_path=normalized,
                source_hash=source_hash,
                observed_at=observed_at,
                reason_code="REPLAY_CONFLICT",
                state=state,
            )

        if existing is None:
            major_change = True
            change_kind = "added"
        else:
            major_change = _is_major_change(existing, candidate, loaded_policy)
            change_kind = "modified_major" if major_change else "modified_minor"
        if existing is not None and not major_change:
            updated = _minor_record(existing, candidate, _safe_timestamp(observed_at))
            updated_state = _update_state(state, updated, _safe_timestamp(observed_at), "modified_minor")
            updated_manifest = _replace_record(manifest, updated)
            _finalize(updated_manifest, root.resolve(), loaded_policy, state=updated_state)
            receipt = _base_receipt(
                request_id=safe_request,
                relative_path=normalized,
                source_hash=source_hash,
                action="metadata_unchanged",
                status="PASS",
                observed_at=observed_at,
                reason_code="SMALL_CHANGE_DETERMINISTIC_UPDATE",
            )
            receipt["dispatch"] = {"status": "NOT_REQUIRED", "attempts": 0}
            return MaintenanceResult("PASS", "metadata_unchanged", updated_manifest, receipt, updated_state)

        if dispatcher is None:
            raise A07DispatchError("RUNTIME_DISPATCH_FALLBACK_REQUIRED")
        structural_diff = _structural_diff(
            existing,
            candidate,
            major_change=major_change,
            change_kind=change_kind,
        )
        payload: dict[str, Any] = {
            "relative_path": normalized,
            "kind": "managed_document",
            "source_hash": source_hash,
            "structural_diff": structural_diff,
            "existing_record": _safe_existing_record(existing),
            "safe_excerpt": text[:18000],
            "request_id": safe_request,
            "schema_version": SCHEMA_VERSION,
            "generator_version": str(loaded_policy.get("generator_version", GENERATOR_VERSION)),
        }
        payload["input_hash"] = _input_hash(payload)
        expected_action = "record_add" if existing is None else None
        last_dispatch = _safe_dispatch_info(attempts=0, status="NOT_STARTED")
        for attempt in range(1, max_attempts + 1):
            try:
                raw_decision = dispatcher(payload)
            except A07DispatchError as exc:
                last_dispatch = _safe_dispatch_info(
                    attempts=attempt,
                    status="FAILED",
                    reason_code=exc.reason_code,
                )
                if attempt < max_attempts:
                    continue
                raise
            except Exception as exc:
                del exc
                raise A07DispatchError("A07_DISPATCH_FAILED") from None
            last_dispatch = _safe_dispatch_info(attempts=attempt, status="RESPONSE_RECEIVED")
            required_action = (
                expected_action or str(raw_decision.get("action"))
                if isinstance(raw_decision, Mapping)
                else ""
            )
            if existing is not None and required_action not in {"record_update", "metadata_unchanged"}:
                raise A07OutputError("A07_OUTPUT_INVALID")
            decision = _validate_a07_decision(
                raw_decision,
                expected_artifact_id=candidate["artifact_id"],
                expected_hash=source_hash,
                required_action=required_action,
                min_confidence=float(loaded_policy.get("a07_min_confidence", 0.70)),
            )
            last_dispatch = _safe_dispatch_info(
                attempts=attempt,
                status="COMPLETED",
                decision=decision,
            )
            if decision["action"] == "metadata_unchanged":
                updated = _minor_record(existing or candidate, candidate, _safe_timestamp(observed_at))
            else:
                updated = _merge_a07_decision(candidate, decision, _safe_timestamp(observed_at))
            updated_state = _update_state(state, updated, _safe_timestamp(observed_at), decision["action"])
            updated_manifest = _replace_record(manifest, updated)
            _finalize(updated_manifest, root.resolve(), loaded_policy, state=updated_state)
            receipt = _base_receipt(
                request_id=safe_request,
                relative_path=normalized,
                source_hash=source_hash,
                action=decision["action"],
                status="PASS",
                observed_at=observed_at,
                reason_code="A07_DECISION_ACCEPTED",
            )
            receipt["dispatch"] = last_dispatch
            return MaintenanceResult("PASS", decision["action"], updated_manifest, receipt, updated_state)
        raise A07DispatchError("A07_DISPATCH_FAILED")
    except A07OutputError as exc:
        return _blocked(
            manifest,
            request_id=safe_request,
            relative_path=locals().get("normalized"),
            source_hash=locals().get("source_hash"),
            observed_at=observed_at,
            reason_code=str(exc),
            dispatch=locals().get("last_dispatch"),
            state=state,
        )
    except A07DispatchError as exc:
        dispatch = locals().get("last_dispatch") or _safe_dispatch_info(
            attempts=0,
            status="NOT_STARTED",
            reason_code=exc.reason_code,
        )
        dispatch["reason_code"] = exc.reason_code
        return _blocked(
            manifest,
            request_id=safe_request,
            relative_path=locals().get("normalized"),
            source_hash=locals().get("source_hash"),
            observed_at=observed_at,
            reason_code=exc.reason_code,
            dispatch=dispatch,
            state=state,
        )
    except (MaintenanceError, PolicyViolation, OSError) as exc:
        error_text = str(exc)
        code = "MAINTENANCE_FAILED"
        for candidate_code in (
            "REQUEST_ID_INVALID",
            "MANIFEST_SCHEMA_INVALID",
            "MANIFEST_DUPLICATE_PATH",
            "ATTEMPT_LIMIT_INVALID",
            "PATH_INVALID",
            "PATH_ABSOLUTE",
            "PATH_UNC",
            "PATH_TRAVERSAL",
            "OUT_OF_SCOPE",
            "SECRET_PATH",
            "SECRET_CONTENT",
            "FILE_SIZE_LIMIT",
            "UTF8_REQUIRED",
            "FILE_READ_FAILED",
            "STATE_SCHEMA_INVALID",
            "VALIDATOR_FAILED",
        ):
            if candidate_code in error_text:
                code = candidate_code
                break
        return _blocked(
            manifest,
            request_id=safe_request,
            relative_path=locals().get("normalized"),
            source_hash=locals().get("source_hash"),
            observed_at=observed_at,
            reason_code=code,
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
        request_id
        if isinstance(request_id, str) and _SAFE_IDENTIFIER_RE.fullmatch(request_id)
        else "REDACTED"
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
                source_hash=record["source_hash"],
                action="renamed",
                status="PASS",
                observed_at=observed_at,
                reason_code="RENAME_STATE_UPDATED",
            )
            receipt["before_path"] = old_path
            receipt["dispatch"] = {"status": "NOT_REQUIRED", "attempts": 0}
            return MaintenanceResult("PASS", "renamed", updated_manifest, receipt, updated_state)
        old_path = normalize_relative_path(str(delta.get("before_path", "")))
        existing = _artifact_by_path(manifest, old_path)
        if existing is None:
            raise MaintenanceError("DELETE_STATE_INVALID")
        deleted = _clone(existing)
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
            source_hash=deleted["source_hash"],
            action="deleted",
            status="PASS",
            observed_at=observed_at,
            reason_code="DELETE_STATE_UPDATED",
        )
        receipt["dispatch"] = {"status": "NOT_REQUIRED", "attempts": 0}
        return MaintenanceResult("PASS", "deleted", updated_manifest, receipt, updated_state)
    except (MaintenanceError, PolicyViolation, OSError) as exc:
        code = str(exc) if str(exc) else "DELTA_FAILED"
        return _blocked(
            manifest,
            request_id=safe_request,
            relative_path=None,
            source_hash=None,
            observed_at=observed_at,
            reason_code=code,
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
    parser = argparse.ArgumentParser(description="Run one fail-closed document context maintenance event.")
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
    parser.add_argument("--max-attempts", type=int, default=1)
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
            delta = _load_json(_output_inside_root(root, args.delta_json))
            result = process_delta(
                root,
                args.policy,
                manifest,
                delta,
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
        print(json.dumps({"status": result.status, "action": result.action}, ensure_ascii=False))
        return 0 if result.status == "PASS" else 1
    except MaintenanceError as exc:
        print(str(exc))
        return 1
    except OSError:
        print("MAINTENANCE_COMMAND_FAILED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

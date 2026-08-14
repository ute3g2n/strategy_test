from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import (
    SCHEMA_VERSION,
    ContextIndexError,
    PolicyViolation,
    assert_safe_document,
    discover_managed_paths,
    is_managed_document,
    load_policy,
    normalize_relative_path,
    sha256_bytes,
)


class ManifestInputError(ContextIndexError):
    """Raised when a manifest file cannot be parsed safely."""


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    errors: list[dict[str, str]]
    counts: dict[str, int]


_REQUIRED_RECORD_KEYS = {
    "artifact_id",
    "kind",
    "status",
    "relative_path",
    "source_hash",
    "schema_version",
    "generator_version",
    "first_seen_at",
    "updated_at",
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
}
_OPTIONAL_RECORD_KEYS = {"deleted_at", "last_known_path"}
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_ID_RE = re.compile(r"^art-[0-9a-f-]{36}$")


def load_manifest_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestInputError("MANIFEST_INPUT_INVALID") from exc
    if not isinstance(value, dict):
        raise ManifestInputError("MANIFEST_ROOT_INVALID")
    return value


def _error(errors: list[dict[str, str]], code: str, relative_path: str | None = None) -> None:
    item = {"code": code}
    if relative_path:
        item["relative_path"] = relative_path
    errors.append(item)


def _validate_record_shape(record: Any, errors: list[dict[str, str]]) -> bool:
    if not isinstance(record, dict):
        _error(errors, "SCHEMA_INVALID")
        return False
    keys = set(record)
    if not _REQUIRED_RECORD_KEYS.issubset(keys) or not keys.issubset(_REQUIRED_RECORD_KEYS | _OPTIONAL_RECORD_KEYS):
        _error(errors, "SCHEMA_INVALID")
        return False
    if not isinstance(record.get("artifact_id"), str) or not _ID_RE.fullmatch(record["artifact_id"]):
        _error(errors, "SCHEMA_INVALID")
    if record.get("kind") != "managed_document" or record.get("schema_version") != SCHEMA_VERSION:
        _error(errors, "SCHEMA_INVALID")
    if record.get("status") not in {"active", "deleted", "partial", "blocked", "pending"}:
        _error(errors, "SCHEMA_INVALID")
    if not isinstance(record.get("relative_path"), str):
        _error(errors, "SCHEMA_INVALID")
    if not isinstance(record.get("source_hash"), str) or not _SHA256_RE.fullmatch(record["source_hash"]):
        _error(errors, "SCHEMA_INVALID")
    if not isinstance(record.get("headings"), list) or not isinstance(record.get("trace_ids"), list):
        _error(errors, "SCHEMA_INVALID")
    if not isinstance(record.get("local_links"), list) or not isinstance(record.get("line_count"), int):
        _error(errors, "SCHEMA_INVALID")
    if not isinstance(record.get("byte_size"), int) or record.get("byte_size", -1) < 0:
        _error(errors, "SCHEMA_INVALID")
    return True


def _validate_state(
    state: Mapping[str, Any] | None,
    records: list[dict[str, Any]],
    errors: list[dict[str, str]],
) -> None:
    if state is None:
        return
    if state.get("schema_version") != SCHEMA_VERSION or not isinstance(state.get("states"), list):
        _error(errors, "STATE_SCHEMA_INVALID")
        return
    state_by_id = {
        item.get("subject_id"): item
        for item in state["states"]
        if isinstance(item, dict) and isinstance(item.get("subject_id"), str)
    }
    for record in records:
        item = state_by_id.get(record.get("artifact_id"))
        if (
            not item
            or item.get("source_hash") != record.get("source_hash")
            or item.get("state") != record.get("status")
        ):
            _error(errors, "STATE_STALE", record.get("relative_path"))


def validate_manifest(
    manifest: Mapping[str, Any],
    root: Path,
    policy: Mapping[str, Any] | Path | str,
    *,
    state: Mapping[str, Any] | None = None,
) -> ValidationReport:
    errors: list[dict[str, str]] = []
    try:
        loaded_policy = load_policy(policy)
    except PolicyViolation as exc:
        return ValidationReport(False, [{"code": str(exc)}], {})
    if not isinstance(manifest, Mapping):
        _error(errors, "SCHEMA_INVALID")
        return ValidationReport(False, errors, {})
    if manifest.get("schema_version") != SCHEMA_VERSION or not isinstance(manifest.get("generator_version"), str):
        _error(errors, "SCHEMA_INVALID")
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        _error(errors, "SCHEMA_INVALID")
        return ValidationReport(False, errors, {})
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    valid_records: list[dict[str, Any]] = []
    for record in records:
        if not _validate_record_shape(record, errors):
            continue
        relative_path = record["relative_path"]
        try:
            normalized = normalize_relative_path(relative_path)
        except PolicyViolation:
            _error(errors, "PATH_INVALID", relative_path if isinstance(relative_path, str) else None)
            continue
        if normalized in seen_paths or record["artifact_id"] in seen_ids:
            _error(errors, "DUPLICATE_ID_OR_PATH", normalized)
        seen_paths.add(normalized)
        seen_ids.add(record["artifact_id"])
        valid_records.append(record)
        if not is_managed_document(normalized, loaded_policy):
            _error(errors, "OUT_OF_SCOPE", normalized)
            continue
        if record.get("status") != "active":
            continue
        try:
            _, data, _ = assert_safe_document(root, normalized, loaded_policy)
        except PolicyViolation as exc:
            _error(errors, str(exc), normalized)
            continue
        if sha256_bytes(data) != record["source_hash"]:
            _error(errors, "STALE_HASH", normalized)
        if len(data) != record.get("byte_size"):
            _error(errors, "SIZE_MISMATCH", normalized)
    try:
        discovered = set(discover_managed_paths(root, loaded_policy))
    except PolicyViolation as exc:
        _error(errors, str(exc))
        discovered = set()
    registered_active = {record["relative_path"] for record in valid_records if record.get("status") == "active"}
    for relative_path in sorted(discovered - registered_active):
        _error(errors, "UNREGISTERED_DOCUMENT", relative_path)
    _validate_state(state, valid_records, errors)
    counts: dict[str, int] = {}
    for record in valid_records:
        status = str(record.get("status", "invalid"))
        counts[status] = counts.get(status, 0) + 1
    return ValidationReport(not errors, errors, counts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a CTXMAP document manifest.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest_file(args.manifest)
        state = load_manifest_file(args.state) if args.state else None
    except ManifestInputError as exc:
        print(str(exc))
        return 1
    report = validate_manifest(manifest, args.root, args.policy, state=state)
    print(json.dumps({"valid": report.valid, "errors": report.errors, "counts": report.counts}, ensure_ascii=False))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Fail-closed, append-only persistence for Phase 3 Backtest runs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

from .contracts import BacktestSnapshot, CommitInput, ResultRow, canonical_hash, canonical_json
from .experiment_manifest import (
    canonical_manifest_bytes,
    manifest_mapping,
    validate_manifest_integrity,
)

DEFAULT_RESULT_ROOT = Path(r"E:\strategy_test_data\phase3\backtests\runs")
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")

_MANIFEST_FILE = "experiment-manifest.json"
_RESULT_FILE = "result.jsonl"
_AUDIT_FILE = "audit.jsonl"
_SNAPSHOT_FILE = "snapshot.json"
_MARKER_FILE = "commit-marker.json"
_ALLOWED_ROW_FIELDS = frozenset(
    {
        "schema_version",
        "row_id",
        "run_id",
        "sequence_no",
        "event_id",
        "instrument_id",
        "logical_time_utc",
        "decision_time_utc",
        "row_kind",
        "batch_id",
        "directive_fingerprint",
        "fill_event_id",
        "payload",
        "payload_sha256",
        "warning_flags",
        "manifest_sha256",
        "content_sha256",
    }
)
_FORBIDDEN_TOKENS = ("secret", "api_key", "token", "password", "broker", "engine", "sdk")


def _stopped(reason: str, detail: str | None = None) -> dict[str, str]:
    result = {"status": "STOPPED", "reason": reason}
    if detail:
        result["detail"] = detail
    return result


def reject_bad_result_path(input_value: Mapping[str, Any]) -> dict[str, str]:
    """Retain the old predicate, but never infer a safe path from a bool alone."""

    if (
        not isinstance(input_value, Mapping)
        or not isinstance(input_value.get("path_outside_e_root"), bool)
        or not isinstance(input_value.get("root_observed"), bool)
        or not isinstance(input_value.get("run_id"), str)
        or not input_value.get("run_id")
    ):
        return _stopped("RESULT_NOT_PUBLISHED")
    if input_value.get("path_outside_e_root") or not input_value.get("root_observed"):
        return _stopped("RESULT_NOT_PUBLISHED")
    return {"status": "PASS"}


def _has_reparse_point(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.stat(), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    except OSError:
        return True


def _contains_reparse(path: Path) -> bool:
    current = path
    while True:
        if current.exists() and _has_reparse_point(current):
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _is_unc(path: str | Path) -> bool:
    value = str(path)
    return value.startswith("\\\\") or value.startswith("//")


def _safe_root(root: str | Path, *, create: bool) -> Path:
    if _is_unc(root):
        raise ValueError("UNC result roots are not allowed")
    candidate = Path(root)
    if not candidate.is_absolute():
        raise ValueError("result root must be absolute")
    if _contains_reparse(candidate):
        raise ValueError("result root contains a reparse point")
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    resolved = candidate.resolve(strict=False)
    if not resolved.is_dir() or _contains_reparse(resolved):
        raise ValueError("result root must be a regular directory")
    return resolved


def _safe_run_path(root: Path, run_id: str, *, allow_missing: bool) -> Path:
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("invalid run id")
    if any(part in {".", ".."} for part in Path(run_id).parts) or Path(run_id).name != run_id:
        raise ValueError("invalid run id path")
    candidate = root / run_id
    if _contains_reparse(candidate):
        raise ValueError("run path contains a reparse point")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("run path outside result root") from error
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(run_id)
    if resolved.exists() and _has_reparse_point(resolved):
        raise ValueError("reparse run path")
    return resolved


def is_publishable(path: str | Path, root: str | Path) -> bool:
    try:
        base = _safe_root(root, create=False)
        candidate = Path(path)
        if _is_unc(candidate) or not candidate.is_absolute() or _contains_reparse(candidate):
            return False
        resolved = candidate.resolve(strict=False)
        if resolved == base or _has_reparse_point(resolved):
            return False
        resolved.relative_to(base)
        return not (resolved.exists() and not resolved.is_file())
    except (OSError, ValueError):
        return False


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _flush_bytes(path: Path, payload: bytes, *, overwrite: bool = False) -> None:
    """Write one file durably and atomically, refusing accidental replacement."""

    if not path.parent.is_dir() or _has_reparse_point(path.parent):
        raise ValueError("unsafe result parent")
    mode = "wb" if overwrite else "xb"
    with path.open(mode) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError:
        # Windows directory handles do not always support fsync. The file
        # itself has already been flushed; publication still remains atomic.
        pass


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.write")
    if path.exists() or temporary.exists():
        raise FileExistsError("stale write temporary exists")
    try:
        _flush_bytes(temporary, payload)
        if path.exists():
            raise FileExistsError("target appeared during atomic write")
        os.replace(temporary, path)
    except Exception:
        if temporary.exists() and temporary.is_file():
            temporary.unlink()
        raise


def _reject_forbidden(value: Any) -> None:
    if isinstance(value, str):
        if re.search(r"(?i)(api[_-]?key|secret|password|access[_-]?token|bearer)\s*[:=]", value):
            raise ValueError("forbidden result value")
        if re.match(r"(?i)sk-[A-Za-z0-9]", value) or re.search(
            r"(?i)https?://[^\s]+(?:broker|engine|sdk|cloud)", value
        ):
            raise ValueError("forbidden result value")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError("result object keys must be strings")
            lowered = key.lower()
            if any(token in lowered for token in _FORBIDDEN_TOKENS):
                raise ValueError("forbidden result field")
            _reject_forbidden(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _reject_forbidden(child)


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise TypeError("canonical mapping required")


def _row_mapping(value: Any, *, run_id: str, manifest_sha256: str) -> dict[str, Any]:
    if isinstance(value, ResultRow):
        payload = dict(value.payload)
        result = {
            "schema_version": "backtest-result-row/v1",
            "row_id": value.row_id,
            "run_id": run_id,
            "sequence_no": value.sequence_no,
            "event_id": value.event_id,
            "instrument_id": value.instrument_id,
            "logical_time_utc": value.decision_time_utc,
            "row_kind": value.row_kind,
            "payload": payload,
            "payload_sha256": canonical_hash(payload),
            "warning_flags": [],
            "manifest_sha256": value.manifest_sha256,
            "content_sha256": value.content_sha256,
        }
    else:
        result = _as_mapping(value)
        result.setdefault("run_id", run_id)
        if "decision_time_utc" in result and "logical_time_utc" not in result:
            result["logical_time_utc"] = result.pop("decision_time_utc")
        result.setdefault("manifest_sha256", manifest_sha256)
    if set(result) - _ALLOWED_ROW_FIELDS:
        raise ValueError("unknown result row field")
    _reject_forbidden(result)
    if result.get("run_id") != run_id or result.get("manifest_sha256") != manifest_sha256:
        raise ValueError("result row binding mismatch")
    sequence_no = result.get("sequence_no")
    if not isinstance(sequence_no, int) or sequence_no < 0:
        raise ValueError("result sequence must be a non-negative integer")
    if not isinstance(result.get("row_id"), str) or not result["row_id"]:
        raise ValueError("result row id is required")
    if not isinstance(result.get("row_kind"), str) or not result["row_kind"]:
        raise ValueError("result row kind is required")
    if "payload_sha256" in result and result["payload_sha256"] != canonical_hash(result.get("payload")):
        raise ValueError("result payload hash mismatch")
    canonical_json(result)
    return result


def _snapshot_mapping(value: Any, *, run_id: str, manifest_sha256: str) -> dict[str, Any]:
    typed_snapshot = isinstance(value, BacktestSnapshot)
    if isinstance(value, BacktestSnapshot):
        result = asdict(value)
    else:
        result = _as_mapping(value)
    if set(result) - {
        "schema_version",
        "run_id",
        "manifest_sha256",
        "input_sequence_sha256",
        "replay_sha256",
        "aggregator_snapshot_sha256",
        "strategy_snapshot_sha256",
        "simulator_state_sha256",
        "pending_fingerprints",
        "consumed_fingerprints",
        "execution_watermarks",
        "last_committed_event_id",
        "last_event_id",
        "last_batch_sha256",
        "result_offset",
        "result_sha256",
        "commit_marker_sha256",
        "state_payload_sha256",
        "state_payload",
    }:
        raise ValueError("unknown snapshot field")
    required_snapshot_fields = {
        "schema_version",
        "manifest_sha256",
        "input_sequence_sha256",
        "last_committed_event_id",
        "last_batch_sha256",
        "strategy_snapshot_sha256",
        "aggregator_snapshot_sha256",
        "simulator_state_sha256",
        "pending_fingerprints",
        "consumed_fingerprints",
        "result_offset",
        "commit_marker_sha256",
    }
    if not typed_snapshot and not required_snapshot_fields.issubset(result):
        raise ValueError("snapshot binding is incomplete")
    result.setdefault("run_id", run_id)
    if typed_snapshot:
        result.setdefault("input_sequence_sha256", result.get("replay_sha256", manifest_sha256))
        result.setdefault("replay_sha256", result["input_sequence_sha256"])
        result.setdefault("execution_watermarks", {})
        result.setdefault("pending_fingerprints", [])
        result.setdefault("consumed_fingerprints", [])
        result.setdefault("state_payload", {})
    else:
        result.setdefault("state_payload", {})
    expected_state_hash = canonical_hash(result["state_payload"])
    if result.get("state_payload_sha256", expected_state_hash) != expected_state_hash:
        raise ValueError("snapshot state payload hash mismatch")
    result["state_payload_sha256"] = expected_state_hash
    result["manifest_sha256"] = result.get("manifest_sha256", manifest_sha256)
    _reject_forbidden(result)
    if result["manifest_sha256"] != manifest_sha256:
        raise ValueError("snapshot binding mismatch")
    result_offset = result.get("result_offset")
    if not isinstance(result_offset, int) or result_offset < 0:
        raise ValueError("snapshot result offset is invalid")
    canonical_json(result)
    return result


def _marker_mapping(value: Any) -> dict[str, Any]:
    result = _as_mapping(value)
    required = {
        "commit_id",
        "result_offset",
        "last_event_id",
        "last_batch_sha256",
        "snapshot_sha256",
        "audit_tail_sha256",
        "manifest_sha256",
    }
    if not required.issubset(result) or set(result) - required - {"result_sha256", "commit_sha256"}:
        raise ValueError("invalid commit marker fields")
    if not isinstance(result["commit_id"], str) or not result["commit_id"]:
        raise ValueError("commit id is required")
    if not isinstance(result["result_offset"], int) or result["result_offset"] < 0:
        raise ValueError("invalid commit offset")
    _reject_forbidden(result)
    canonical_json(result)
    return result


def _audit_mapping(value: Any, *, run_id: str, manifest_sha256: str, sequence_no: int) -> dict[str, Any]:
    result = _as_mapping(value)
    allowed = {
        "audit_id",
        "run_id",
        "sequence_no",
        "logical_time_utc",
        "severity",
        "code",
        "message_ja",
        "manifest_sha256",
        "subject_hashes",
    }
    if set(result) - allowed:
        raise ValueError("unknown audit field")
    result.setdefault("sequence_no", sequence_no)
    result.setdefault("run_id", run_id)
    result.setdefault("manifest_sha256", manifest_sha256)
    if result.get("run_id") != run_id or result.get("manifest_sha256") != manifest_sha256:
        raise ValueError("audit binding mismatch")
    if not isinstance(result.get("audit_id"), str) or not result["audit_id"]:
        raise ValueError("audit id is required")
    _reject_forbidden(result)
    canonical_json(result)
    return result


@dataclass(frozen=True)
class RunStaging:
    run_id: str
    tmp_path: Path
    manifest_sha256: str


@dataclass(frozen=True)
class CommitMarker:
    """Persisted commit marker; marker bytes are always written last."""

    commit_id: str
    manifest_sha256: str
    result_sha256: str
    snapshot_sha256: str = ""
    result_offset: int = 0
    last_event_id: str | None = None
    last_batch_sha256: str = ""
    audit_tail_sha256: str = ""
    commit_sha256: str = ""


class AtomicResultStore:
    """Immutable run publisher rooted in one regular local directory."""

    def __init__(self, root: str | Path = DEFAULT_RESULT_ROOT) -> None:
        self.root = _safe_root(root, create=True)

    def _revalidate(self) -> None:
        observed = _safe_root(self.root, create=False)
        if observed != self.root:
            raise ValueError("result root changed")

    def create_staging(
        self,
        manifest: Any = None,
        manifest_sha256: str | None = None,
        *,
        run_id: str | None = None,
    ) -> RunStaging:
        """Create staging and durably write the immutable manifest first."""

        self._revalidate()
        if run_id is not None:
            if manifest is not None:
                raise ValueError("manifest and run_id cannot both be supplied")
            manifest = run_id
        if manifest is None:
            raise ValueError("manifest is required")
        if manifest_sha256 is None:
            manifest = manifest_mapping(manifest)
            check = validate_manifest_integrity(manifest)
            if check["status"] != "PASS":
                raise ValueError(check["reason"])
            run_id = manifest["run_id"]
            manifest_sha256 = manifest["manifest_sha256"]
        else:
            if not isinstance(manifest, str):
                raise ValueError("legacy staging requires run_id")
            run_id = manifest
            manifest = {
                "schema_version": "legacy-staging-rejected-v1",
                "run_id": run_id,
                "manifest_sha256": manifest_sha256,
            }
        if not isinstance(manifest_sha256, str) or not HASH_PATTERN.fullmatch(manifest_sha256):
            raise ValueError("invalid manifest hash")
        final = _safe_run_path(self.root, run_id, allow_missing=True)
        tmp = self.root / f".{run_id}.tmp"
        if final.exists() or tmp.exists() or _has_reparse_point(self.root):
            raise FileExistsError("run already exists")
        tmp.mkdir()
        if _has_reparse_point(tmp):
            raise ValueError("staging path is a reparse point")
        manifest_bytes = (
            canonical_manifest_bytes(manifest)
            if manifest.get("schema_version") == "experiment-manifest/v2"
            else canonical_json(manifest)
        )
        _atomic_write(tmp / _MANIFEST_FILE, manifest_bytes)
        return RunStaging(run_id, tmp, manifest_sha256)

    def append_then_commit(self, staging: RunStaging, commit: CommitInput | list[dict[str, Any]]) -> CommitMarker:
        """Write result rows, snapshot, then marker, each with durable bytes."""

        self._revalidate()
        if (
            staging.tmp_path.parent != self.root
            or not staging.tmp_path.is_dir()
            or _has_reparse_point(staging.tmp_path)
        ):
            raise ValueError("staging path outside root")
        if isinstance(commit, list):
            rows = tuple(commit)
            snapshot: dict[str, Any] = {
                "schema_version": "legacy-staging-rejected-v1",
                "run_id": staging.run_id,
                "manifest_sha256": staging.manifest_sha256,
                "input_sequence_sha256": staging.manifest_sha256,
                "last_committed_event_id": None,
                "last_batch_sha256": canonical_hash([]),
                "strategy_snapshot_sha256": canonical_hash({}),
                "aggregator_snapshot_sha256": canonical_hash({}),
                "simulator_state_sha256": canonical_hash({}),
                "pending_fingerprints": [],
                "consumed_fingerprints": [],
                "result_offset": len(rows),
                "commit_marker_sha256": canonical_hash({"run_id": staging.run_id}),
            }
            commit = CommitInput(staging.run_id, rows, snapshot)
        if not isinstance(commit, CommitInput) or commit.commit_id != staging.run_id:
            raise ValueError("invalid commit input")
        if not HASH_PATTERN.fullmatch(staging.manifest_sha256):
            raise ValueError("invalid staging manifest hash")
        manifest_path = staging.tmp_path / _MANIFEST_FILE
        if not manifest_path.is_file() or _has_reparse_point(manifest_path):
            raise ValueError("immutable manifest is missing")
        rows = tuple(
            _row_mapping(row, run_id=staging.run_id, manifest_sha256=staging.manifest_sha256)
            for row in commit.result_rows
        )
        if [row["sequence_no"] for row in rows] != list(range(len(rows))):
            raise ValueError("result sequence is not contiguous")
        if len({row["row_id"] for row in rows}) != len(rows):
            raise ValueError("duplicate result row id")
        result_bytes = b"".join(canonical_json(row) + b"\n" for row in rows)
        result_sha256 = _sha256_bytes(result_bytes)
        _atomic_write(staging.tmp_path / _RESULT_FILE, result_bytes)

        audit_rows = tuple(
            _audit_mapping(item, run_id=staging.run_id, manifest_sha256=staging.manifest_sha256, sequence_no=index)
            for index, item in enumerate(commit.audit_rows)
        )
        audit_bytes = b"".join(canonical_json(row) + b"\n" for row in audit_rows)
        _atomic_write(staging.tmp_path / _AUDIT_FILE, audit_bytes)

        snapshot = _snapshot_mapping(commit.snapshot, run_id=staging.run_id, manifest_sha256=staging.manifest_sha256)
        if snapshot["result_offset"] != len(rows):
            raise ValueError("snapshot/result offset mismatch")
        snapshot_bytes = canonical_json(snapshot)
        snapshot_sha256 = _sha256_bytes(snapshot_bytes)
        _atomic_write(staging.tmp_path / _SNAPSHOT_FILE, snapshot_bytes)

        audit_tail = commit.audit_tail_sha256 or canonical_hash(audit_rows[-1] if audit_rows else {})
        marker_payload = {
            "commit_id": commit.commit_id,
            "result_offset": len(rows),
            "last_event_id": commit.last_event_id or snapshot.get("last_committed_event_id"),
            "last_batch_sha256": commit.last_batch_sha256 or str(snapshot.get("last_batch_sha256", "")),
            "snapshot_sha256": snapshot_sha256,
            "audit_tail_sha256": audit_tail,
            "manifest_sha256": staging.manifest_sha256,
            "result_sha256": result_sha256,
        }
        marker_payload["commit_sha256"] = canonical_hash(
            {key: value for key, value in marker_payload.items() if key != "commit_sha256"}
        )
        last_event_id = marker_payload["last_event_id"]
        last_batch_sha256 = marker_payload["last_batch_sha256"]
        commit_sha256 = marker_payload["commit_sha256"]
        if last_event_id is not None and not isinstance(last_event_id, str):
            raise ValueError("commit marker last event id is invalid")
        if not isinstance(last_batch_sha256, str) or not isinstance(commit_sha256, str):
            raise ValueError("commit marker hash is invalid")
        marker_bytes = canonical_json(marker_payload)
        _atomic_write(staging.tmp_path / _MARKER_FILE, marker_bytes)
        return CommitMarker(
            commit_id=commit.commit_id,
            manifest_sha256=staging.manifest_sha256,
            result_sha256=result_sha256,
            snapshot_sha256=snapshot_sha256,
            result_offset=len(rows),
            last_event_id=last_event_id,
            last_batch_sha256=last_batch_sha256,
            audit_tail_sha256=audit_tail,
            commit_sha256=commit_sha256,
        )

    def _verify_staging(self, staging: RunStaging, marker: CommitMarker) -> dict[str, Any]:
        if staging.tmp_path.parent != self.root or _has_reparse_point(staging.tmp_path):
            raise ValueError("unsafe staging path")
        expected = {
            _MANIFEST_FILE: staging.tmp_path / _MANIFEST_FILE,
            _RESULT_FILE: staging.tmp_path / _RESULT_FILE,
            _AUDIT_FILE: staging.tmp_path / _AUDIT_FILE,
            _SNAPSHOT_FILE: staging.tmp_path / _SNAPSHOT_FILE,
            _MARKER_FILE: staging.tmp_path / _MARKER_FILE,
        }
        if any(not path.is_file() or _has_reparse_point(path) for path in expected.values()):
            raise ValueError("partial commit")
        manifest = json.loads(expected[_MANIFEST_FILE].read_text(encoding="utf-8"))
        if validate_manifest_integrity(manifest)["status"] != "PASS":
            raise ValueError("manifest integrity violation")
        if manifest.get("run_id") != staging.run_id or manifest.get("manifest_sha256") != staging.manifest_sha256:
            raise ValueError("manifest binding mismatch")
        result_bytes = expected[_RESULT_FILE].read_bytes()
        snapshot_bytes = expected[_SNAPSHOT_FILE].read_bytes()
        stored_marker = _marker_mapping(json.loads(expected[_MARKER_FILE].read_text(encoding="utf-8")))
        supplied_marker = _marker_mapping(asdict(marker))
        actual_result_sha = _sha256_bytes(result_bytes)
        actual_snapshot_sha = _sha256_bytes(snapshot_bytes)
        if stored_marker.get("commit_id") != staging.run_id or stored_marker.get("commit_sha256") != canonical_hash(
            {key: value for key, value in stored_marker.items() if key != "commit_sha256"}
        ):
            raise ValueError("commit marker integrity mismatch")
        if (
            stored_marker != supplied_marker
            or stored_marker.get("result_sha256") != actual_result_sha
            or stored_marker.get("snapshot_sha256") != actual_snapshot_sha
        ):
            raise ValueError("commit marker or payload hash mismatch")
        if stored_marker.get("manifest_sha256") != staging.manifest_sha256:
            raise ValueError("commit manifest mismatch")
        rows = [json.loads(line) for line in result_bytes.splitlines() if line]
        for expected_sequence, row in enumerate(rows):
            _row_mapping(row, run_id=staging.run_id, manifest_sha256=staging.manifest_sha256)
            if row.get("sequence_no") != expected_sequence:
                raise ValueError("result sequence mismatch")
        audit_bytes = expected[_AUDIT_FILE].read_bytes()
        audit_rows = [json.loads(line) for line in audit_bytes.splitlines() if line]
        for sequence_no, audit_row in enumerate(audit_rows):
            _audit_mapping(
                audit_row,
                run_id=staging.run_id,
                manifest_sha256=staging.manifest_sha256,
                sequence_no=sequence_no,
            )
        if stored_marker.get("audit_tail_sha256") != canonical_hash(audit_rows[-1] if audit_rows else {}):
            raise ValueError("audit tail mismatch")
        snapshot = _snapshot_mapping(
            json.loads(snapshot_bytes), run_id=staging.run_id, manifest_sha256=staging.manifest_sha256
        )
        if snapshot.get("result_offset") != len(rows) or stored_marker.get("result_offset") != len(rows):
            raise ValueError("result offset mismatch")
        return {"manifest": manifest, "rows": rows, "snapshot": snapshot, "marker": stored_marker}

    def publish(self, staging: RunStaging, marker: CommitMarker) -> Path:
        self._revalidate()
        self._verify_staging(staging, marker)
        self._revalidate()
        destination = _safe_run_path(self.root, staging.run_id, allow_missing=True)
        if destination.exists():
            existing_marker = destination / _MARKER_FILE
            if (
                existing_marker.is_file()
                and existing_marker.read_bytes() == (staging.tmp_path / _MARKER_FILE).read_bytes()
            ):
                return destination
            raise FileExistsError("run already published")
        # Recheck the parent and the destination immediately before the single
        # rename. The marker is the last file in staging, so the directory is
        # either invisible or complete to readers.
        if destination.exists() or _has_reparse_point(self.root):
            raise FileExistsError("run appeared during publication")
        os.replace(staging.tmp_path, destination)
        if _has_reparse_point(destination):
            raise ValueError("published run became a reparse point")
        return destination

    def read_published(self, run_id: str) -> dict[str, Any]:
        try:
            self._revalidate()
            run_path = _safe_run_path(self.root, run_id, allow_missing=False)
            staging = RunStaging(run_id, run_path, "")
            marker_dict = json.loads((run_path / _MARKER_FILE).read_text(encoding="utf-8"))
            marker = CommitMarker(
                commit_id=marker_dict["commit_id"],
                manifest_sha256=marker_dict["manifest_sha256"],
                result_sha256=marker_dict.get("result_sha256", ""),
                snapshot_sha256=marker_dict["snapshot_sha256"],
                result_offset=marker_dict["result_offset"],
                last_event_id=marker_dict.get("last_event_id"),
                last_batch_sha256=marker_dict["last_batch_sha256"],
                audit_tail_sha256=marker_dict["audit_tail_sha256"],
                commit_sha256=marker_dict.get("commit_sha256", ""),
            )
            staging = RunStaging(run_id, run_path, marker.manifest_sha256)
            verified = self._verify_staging(staging, marker)
            return {"status": "PASS", "run_id": run_id, **verified}
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return _stopped("RECOVERY_RECONCILIATION_FAILED", type(error).__name__)

    def recover_published(self, run_id: str, event_ids: Sequence[str] | None = None) -> dict[str, Any]:
        """Verify a committed run and return the exclusive replay watermark."""

        result = self.read_published(run_id)
        if result.get("status") != "PASS":
            return result
        marker = result["marker"]
        if event_ids is not None:
            committed = marker.get("last_event_id")
            if committed is not None and committed in event_ids:
                start = max(index for index, item in enumerate(event_ids) if item == committed) + 1
            else:
                start = 0
            result["replay_start_index"] = start
            result["replayed_event_ids"] = [item for item in list(event_ids)[start:] if item != committed]
        return result

    def publish_backtest_result(self, manifest: Any, run_result: Any) -> dict[str, Any]:
        """Persist one committed typed runner result through the only I/O port."""

        if getattr(run_result, "status", None) != "COMMITTED" or getattr(run_result, "snapshot", None) is None:
            return _stopped("RESULT_NOT_PUBLISHED", "only committed typed results may be published")
        try:
            staging = self.create_staging(manifest)
            result = self.append_then_commit(
                staging,
                CommitInput(
                    commit_id=staging.run_id,
                    result_rows=tuple(run_result.rows),
                    snapshot=run_result.snapshot,
                    last_event_id=run_result.snapshot.last_committed_event_id,
                    last_batch_sha256=run_result.snapshot.last_batch_sha256,
                ),
            )
            destination = self.publish(staging, result)
            return {"status": "PASS", "path": str(destination), "marker": asdict(result)}
        except (OSError, TypeError, ValueError, FileExistsError) as error:
            return _stopped("RESULT_NOT_PUBLISHED", type(error).__name__)

    # Explicit alias used by the runbook and by callers that treat recovery as
    # a read-only verification operation.
    verify_published = read_published

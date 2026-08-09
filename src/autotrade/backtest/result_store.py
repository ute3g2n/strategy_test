"""Safe path and append-only publication helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def reject_bad_result_path(input_value: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(input_value, Mapping) or not isinstance(input_value.get("path_outside_e_root"), bool):
        return {"status": "STOPPED"}
    if input_value.get("path_outside_e_root"):
        return {"status": "STOPPED"}
    return {"status": "PASS"}


def is_publishable(path: str | Path, root: str | Path) -> bool:
    try:
        candidate, base = Path(path).resolve(), Path(root).resolve()
        if candidate == base or not base.is_dir() or (candidate.exists() and not candidate.is_file()):
            return False
        candidate.relative_to(base)
    except (OSError, ValueError):
        return False
    return True


@dataclass(frozen=True)
class RunStaging:
    run_id: str
    tmp_path: Path
    manifest_sha256: str


@dataclass(frozen=True)
class CommitMarker:
    commit_id: str
    manifest_sha256: str
    result_sha256: str


class AtomicResultStore:
    """Append-only local result publisher; an existing run is never overwritten."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_staging(self, run_id: str, manifest_sha256: str) -> RunStaging:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", manifest_sha256
        ):
            raise ValueError("invalid staging binding")
        final = self.root / run_id
        tmp = self.root / f".{run_id}.tmp"
        if final.exists() or tmp.exists():
            raise FileExistsError("run already exists")
        tmp.mkdir()
        return RunStaging(run_id, tmp, manifest_sha256)

    def append_then_commit(self, staging: RunStaging, rows: list[dict[str, Any]]) -> CommitMarker:
        if staging.tmp_path.parent != self.root or not staging.tmp_path.is_dir() or staging.tmp_path.is_symlink():
            raise ValueError("staging path outside root")
        result_path = staging.tmp_path / "result.json"
        marker_path = staging.tmp_path / "commit.json"
        if result_path.exists() or marker_path.exists():
            raise FileExistsError("staging already committed")
        if not isinstance(rows, list) or any(
            not isinstance(row, dict) or any("secret" in str(k).lower() for k in row) for row in rows
        ):
            raise ValueError("invalid result rows")
        payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
        result_sha = "sha256:" + hashlib.sha256(payload).hexdigest()
        result_path.write_bytes(payload)
        marker = CommitMarker(staging.run_id, staging.manifest_sha256, result_sha)
        marker_path.write_text(json.dumps(marker.__dict__, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return marker

    def publish(self, staging: RunStaging, marker: CommitMarker) -> Path:
        marker_path = staging.tmp_path / "commit.json"
        result_path = staging.tmp_path / "result.json"
        if marker.commit_id != staging.run_id or not marker_path.is_file() or not result_path.is_file():
            raise ValueError("commit marker mismatch")
        try:
            stored = json.loads(marker_path.read_text(encoding="utf-8"))
            actual_result_sha = "sha256:" + hashlib.sha256(result_path.read_bytes()).hexdigest()
            if (
                stored != marker.__dict__
                or stored.get("manifest_sha256") != staging.manifest_sha256
                or stored.get("result_sha256") != actual_result_sha
            ):
                raise ValueError("commit marker mismatch")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("commit marker mismatch") from error
        destination = self.root / staging.run_id
        if destination.exists():
            raise FileExistsError("run already published")
        os.replace(staging.tmp_path, destination)
        return destination

"""Evidence reference helpers with relative-path and hash checks."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .contracts import EvidenceReference, canonical_hash, is_sha256


def hash_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def evidence_reference(
    run_id: str, relative_root: str, files: dict[str, str], *, status: str = "RECORDED"
) -> EvidenceReference:
    if not relative_root or Path(relative_root).is_absolute() or ".." in Path(relative_root).parts:
        raise ValueError("EVIDENCE_PATH_INVALID")
    if any(Path(name).is_absolute() or ".." in Path(name).parts for name in files):
        raise ValueError("EVIDENCE_PATH_INVALID")
    if any(not is_sha256(value) for value in files.values()):
        raise ValueError("EVIDENCE_HASH_INVALID")
    bundle_hash = canonical_hash({"root": relative_root, "files": dict(sorted(files.items()))})
    return EvidenceReference(f"evidence-{bundle_hash[7:19]}", run_id, relative_root, bundle_hash, status)  # type: ignore[arg-type]

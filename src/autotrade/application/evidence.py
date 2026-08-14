"""Evidence reference helpers with relative-path and structure checks."""

from __future__ import annotations

from pathlib import Path

from .contracts import EvidenceReference, is_safe_id


def evidence_reference(
    run_id: str, relative_root: str, files: dict[str, str], *, status: str = "RECORDED"
) -> EvidenceReference:
    if not relative_root or Path(relative_root).is_absolute() or ".." in Path(relative_root).parts:
        raise ValueError("EVIDENCE_PATH_INVALID")
    if any(Path(name).is_absolute() or ".." in Path(name).parts for name in files):
        raise ValueError("EVIDENCE_PATH_INVALID")
    if not is_safe_id(run_id):
        raise ValueError("EVIDENCE_RUN_ID_INVALID")
    if status not in {"DESIGNED_NOT_EXECUTED", "RECORDED", "RECONCILIATION_REQUIRED"}:
        raise ValueError("EVIDENCE_STATUS_INVALID")
    # Evidence identity is semantic and stable for the run.  The caller may
    # still carry protected data/replay hashes inside `files`; this helper
    # does not turn the bundle into another management hash.
    del files
    return EvidenceReference(f"evidence-{run_id}", run_id, relative_root, None, status)  # type: ignore[arg-type]

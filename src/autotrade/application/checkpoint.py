"""Checkpoint references; payloads stay in the approved file boundary."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import Sha256, is_sha256


@dataclass(frozen=True)
class CheckpointReference:
    job_id: str
    run_id: str
    sequence_no: int
    relative_ref: str
    checkpoint_sha256: Sha256
    manifest_sha256: Sha256
    commit_marker_sha256: Sha256

    def validate(self) -> None:
        if self.sequence_no < 0 or not self.relative_ref or self.relative_ref.startswith(("/", "\\", "//")):
            raise ValueError("CHECKPOINT_PATH_INVALID")
        if not all(
            is_sha256(value) for value in (self.checkpoint_sha256, self.manifest_sha256, self.commit_marker_sha256)
        ):
            raise ValueError("CHECKPOINT_HASH_INVALID")

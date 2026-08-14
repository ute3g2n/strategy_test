"""Application-side Run Manifest reference, not the Core result body."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import Sha256, is_sha256


@dataclass(frozen=True)
class RunManifest:
    schema_version: str
    run_id: str
    fixture_sha256: Sha256
    core_baseline_sha256: Sha256
    condition_sha256: Sha256
    evidence_root_relative: str
    external_io: bool = False

    def validate(self) -> None:
        if self.external_io:
            raise ValueError("EXTERNAL_IO_FORBIDDEN")
        if not all(
            is_sha256(value) for value in (self.fixture_sha256, self.core_baseline_sha256, self.condition_sha256)
        ):
            raise ValueError("MANIFEST_HASH_INVALID")
        if (
            not self.evidence_root_relative
            or self.evidence_root_relative.startswith(("/", "\\"))
            or ".." in self.evidence_root_relative.split("/")
        ):
            raise ValueError("MANIFEST_PATH_INVALID")

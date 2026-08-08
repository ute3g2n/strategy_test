"""Small immutable local raw store for fixture-only execution."""

from __future__ import annotations

import json
import os
import re
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

from .store_contracts import RawWriteRequest, RawWriteResult

_SECRET_KEY = re.compile(r"(?:secret|api[_-]?key|token|password|account[_-]?id)", re.IGNORECASE)


class LocalRawStore:
    """Persist raw payloads without overwriting a completed object."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def put_if_absent(self, request: RawWriteRequest) -> RawWriteResult:
        if (
            request.received_at_utc.tzinfo is None
            or request.received_at_utc.utcoffset() is None
            or request.received_at_utc.utcoffset() != timedelta(0)
        ):
            raise ValueError("RECEIVED_AT_NOT_UTC")
        if not request.request_fingerprint or not request.payload:
            raise ValueError("RAW_INPUT_MISSING")
        if any(_SECRET_KEY.search(key) for key in request.metadata):
            raise ValueError("SECRET_METADATA_REJECTED")

        payload_sha256 = sha256(request.payload).hexdigest()
        raw_object_id = sha256(f"{request.request_fingerprint}:{payload_sha256}".encode()).hexdigest()
        object_dir = self._root / "raw" / raw_object_id
        payload_path = object_dir / "payload.bin"
        metadata_path = object_dir / "metadata.json"
        if payload_path.exists() or metadata_path.exists():
            if not payload_path.is_file() or sha256(payload_path.read_bytes()).hexdigest() != payload_sha256:
                raise ValueError("RAW_CHECKSUM_MISMATCH")
            return RawWriteResult(raw_object_id, payload_sha256, False, str(object_dir))

        object_dir.mkdir(parents=True, exist_ok=False)
        temporary_payload = object_dir / "payload.bin.tmp"
        temporary_metadata = object_dir / "metadata.json.tmp"
        try:
            temporary_payload.write_bytes(request.payload)
            metadata = {
                "request_fingerprint": request.request_fingerprint,
                "payload_sha256": payload_sha256,
                "received_at_utc": request.received_at_utc.isoformat(),
                "metadata": request.metadata,
            }
            temporary_metadata.write_text(
                json.dumps(metadata, sort_keys=True, separators=(",", ":")), encoding="utf-8"
            )
            os.replace(temporary_payload, payload_path)
            os.replace(temporary_metadata, metadata_path)
        except OSError:
            temporary_payload.unlink(missing_ok=True)
            temporary_metadata.unlink(missing_ok=True)
            if object_dir.exists() and not any(object_dir.iterdir()):
                object_dir.rmdir()
            raise
        return RawWriteResult(raw_object_id, payload_sha256, True, str(object_dir))

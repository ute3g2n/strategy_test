"""CSV job contract; file publication is atomic and relative-only."""

from __future__ import annotations

import csv
import os
from collections.abc import Iterable, Mapping
from io import StringIO
from pathlib import Path

from .contracts import is_sha256


def atomic_csv_output(
    root: Path, relative_path: str, rows: Iterable[Mapping[str, str]], columns: tuple[str, ...]
) -> str:
    if (
        not columns
        or Path(relative_path).is_absolute()
        or ".." in Path(relative_path).parts
        or relative_path.startswith(("\\\\", "//"))
    ):
        raise ValueError("CSV_PATH_INVALID")
    target_root = root.resolve()
    target = (target_root / relative_path).resolve()
    try:
        target.relative_to(target_root)
    except ValueError as error:
        raise ValueError("CSV_PATH_INVALID") from error
    if target.exists():
        raise FileExistsError("CSV_OVERWRITE_FORBIDDEN")
    target.parent.mkdir(parents=True, exist_ok=True)
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(columns), extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: str(row[column]) for column in columns})
    payload = stream.getvalue().encode("utf-8")
    temporary = target.with_name(f".{target.name}.tmp")
    if temporary.exists():
        raise FileExistsError("CSV_STALE_TEMPORARY")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    import hashlib

    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_source_hash(value: str) -> None:
    if not is_sha256(value):
        raise ValueError("CSV_SOURCE_HASH_INVALID")

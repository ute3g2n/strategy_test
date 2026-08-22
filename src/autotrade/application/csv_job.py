"""CSV job contract; file publication is atomic and relative-only."""

from __future__ import annotations

import csv
import os
import tempfile
from collections.abc import Iterable, Mapping
from io import StringIO
from pathlib import Path

_REPARSE_POINT_ATTRIBUTE = 0x0400


def _is_link_or_reparse(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        return path.is_symlink() or bool(attributes & _REPARSE_POINT_ATTRIBUTE)
    except FileNotFoundError:
        return False
    except OSError as error:
        raise ValueError("CSV_PATH_UNSAFE") from error


def _assert_path_chain_safe(path: Path, root: Path) -> None:
    if _is_link_or_reparse(root):
        raise ValueError("CSV_PATH_UNSAFE")
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ValueError("CSV_PATH_INVALID") from error
    current = root
    for part in relative.parts:
        current /= part
        if _is_link_or_reparse(current):
            raise ValueError("CSV_PATH_UNSAFE")


def atomic_csv_output(
    root: Path, relative_path: str, rows: Iterable[Mapping[str, str]], columns: tuple[str, ...]
) -> None:
    if (
        not columns
        or Path(relative_path).is_absolute()
        or ".." in Path(relative_path).parts
        or relative_path.startswith(("\\\\", "//"))
    ):
        raise ValueError("CSV_PATH_INVALID")
    target_root = Path(root)
    target_root.mkdir(parents=True, exist_ok=True)
    _assert_path_chain_safe(target_root, target_root)
    target = target_root / relative_path
    _assert_path_chain_safe(target.parent, target_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_path_chain_safe(target.parent, target_root)
    if target.exists() or _is_link_or_reparse(target):
        raise FileExistsError("CSV_OVERWRITE_FORBIDDEN")
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(columns), extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: str(row[column]) for column in columns})
    payload = stream.getvalue().encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _assert_path_chain_safe(target.parent, target_root)
        if target.exists() or _is_link_or_reparse(target):
            raise FileExistsError("CSV_OVERWRITE_FORBIDDEN")
        os.replace(temporary, target)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink(missing_ok=True)

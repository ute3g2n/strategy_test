"""Application-owned storage locations for the local AutoTrade application.

Runtime data is kept on the dedicated E: data drive.  The application fails
closed when that drive is unavailable instead of silently falling back to the
project directory, the Windows temporary directory, or a phase-specific
directory.
"""

from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath


class StoragePathError(RuntimeError):
    """Raised when an application-owned storage path violates the contract."""


APPLICATION_STORAGE_ROOT = Path(r"E:\strategy_test_data\autotrade")
HISTORICAL_DATA_ROOT = APPLICATION_STORAGE_ROOT / "historical" / "spot" / "klines" / "1m"
BACKTEST_STORAGE_ROOT = APPLICATION_STORAGE_ROOT / "backtest"
BACKTEST_RESULT_ROOT = BACKTEST_STORAGE_ROOT / "results"
BACKTEST_EXPORT_ROOT = BACKTEST_STORAGE_ROOT / "exports"
BACKTEST_CATALOG_ROOT = BACKTEST_STORAGE_ROOT / "catalog"
APPLICATION_LOG_ROOT = APPLICATION_STORAGE_ROOT / "logs"

_FORBIDDEN_COMPONENTS = frozenset({"temp", "tmp"})
_WSL_E_DRIVE_ROOT = Path("/mnt/e")
_REPARSE_POINT_ATTRIBUTE = 0x0400


def filesystem_storage_path(path: Path) -> Path:
    """Map the logical E: storage path to the mounted WSL E: drive.

    Windows remains the production platform and keeps the original Path.  A
    WSL quality gate may exercise the same logical E: boundary through the
    mounted ``/mnt/e`` drive; no project or temporary-directory fallback is
    permitted.
    """

    candidate = Path(path)
    if os.name == "nt":
        return candidate
    logical = PureWindowsPath(str(candidate))
    if logical.drive.upper() != "E:":
        return candidate
    return _WSL_E_DRIVE_ROOT.joinpath(*logical.parts[1:])


def _reject_reparse_components(path: Path, *, purpose: str) -> None:
    """Reject symlink/junction/reparse components before a storage write."""

    current = Path(path.anchor)
    for part in path.parts:
        if part == path.anchor:
            continue
        current /= part
        try:
            exists = current.exists() or current.is_symlink()
            if not exists:
                break
            attributes = getattr(current.lstat(), "st_file_attributes", 0)
            if current.is_symlink() or attributes & _REPARSE_POINT_ATTRIBUTE:
                raise StoragePathError(f"{purpose} contains a symlink or reparse point")
        except FileNotFoundError:
            break
        except OSError as error:
            raise StoragePathError(f"{purpose} path cannot be inspected safely") from error


def _resolved_path(path: Path, *, purpose: str) -> Path:
    """Resolve a path without following an unsafe component silently."""

    _reject_reparse_components(path, purpose=purpose)
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise StoragePathError(f"{purpose} path cannot be resolved safely") from error


def validate_local_storage_path(path: Path, *, purpose: str) -> Path:
    """Validate an explicitly injected local test root without E: fallback."""

    candidate = Path(path)
    if not candidate.is_absolute():
        raise StoragePathError(f"{purpose} must be an absolute local path")
    return _resolved_path(candidate, purpose=purpose)


def validate_storage_path(path: Path, *, purpose: str, create: bool = True) -> Path:
    """Validate and optionally create an application-owned E: path.

    The check is intentionally strict: an unavailable E: drive or an invalid
    path is an explicit startup failure.  There is no C: or Windows temp
    fallback because losing the storage boundary could mix test and runtime
    data.
    """

    candidate = Path(path)
    logical_candidate = PureWindowsPath(str(candidate))
    logical_root = PureWindowsPath(str(APPLICATION_STORAGE_ROOT))
    if not logical_candidate.is_absolute() or logical_candidate.drive.upper() != "E:":
        raise StoragePathError(f"{purpose} must be stored on E:/{candidate}")
    drive_root = Path(candidate.anchor) if os.name == "nt" else _WSL_E_DRIVE_ROOT
    if not drive_root.exists():
        raise StoragePathError("E_DRIVE_UNAVAILABLE")

    if any(part == ".." for part in logical_candidate.parts):
        raise StoragePathError(f"{purpose} contains parent traversal")

    normalized_parts = tuple(part.casefold() for part in logical_candidate.parts)
    if any(part in _FORBIDDEN_COMPONENTS or "phase5r" in part for part in normalized_parts):
        raise StoragePathError(f"{purpose} uses a forbidden temporary or phase-specific path")

    try:
        logical_candidate.relative_to(logical_root)
    except ValueError as error:
        raise StoragePathError(f"{purpose} must be under {APPLICATION_STORAGE_ROOT}") from error

    filesystem_candidate = filesystem_storage_path(candidate)
    filesystem_root = filesystem_storage_path(APPLICATION_STORAGE_ROOT)
    resolved_root = _resolved_path(filesystem_root, purpose=f"{purpose} root")
    resolved_candidate = _resolved_path(filesystem_candidate, purpose=purpose)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as error:
        raise StoragePathError(f"{purpose} must resolve under {APPLICATION_STORAGE_ROOT}") from error

    if create:
        filesystem_candidate.mkdir(parents=True, exist_ok=True)
    return candidate

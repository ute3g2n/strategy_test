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

    normalized_parts = tuple(part.casefold() for part in logical_candidate.parts)
    if any(part in _FORBIDDEN_COMPONENTS or "phase5r" in part for part in normalized_parts):
        raise StoragePathError(f"{purpose} uses a forbidden temporary or phase-specific path")

    try:
        logical_candidate.relative_to(logical_root)
    except ValueError as error:
        raise StoragePathError(f"{purpose} must be under {APPLICATION_STORAGE_ROOT}") from error

    if create:
        filesystem_storage_path(candidate).mkdir(parents=True, exist_ok=True)
    return candidate

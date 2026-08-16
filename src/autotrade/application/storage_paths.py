"""Application-owned storage locations for the local AutoTrade application.

Runtime data is kept on the dedicated E: data drive.  The application fails
closed when that drive is unavailable instead of silently falling back to the
project directory, the Windows temporary directory, or a phase-specific
directory.
"""

from __future__ import annotations

from pathlib import Path


class StoragePathError(RuntimeError):
    """Raised when an application-owned storage path violates the contract."""


APPLICATION_STORAGE_ROOT = Path(r"E:\strategy_test_data\autotrade")
HISTORICAL_DATA_ROOT = APPLICATION_STORAGE_ROOT / "historical" / "spot" / "klines" / "1m"
BACKTEST_STORAGE_ROOT = APPLICATION_STORAGE_ROOT / "backtest"
BACKTEST_RESULT_ROOT = BACKTEST_STORAGE_ROOT / "results"
BACKTEST_EXPORT_ROOT = BACKTEST_STORAGE_ROOT / "exports"
APPLICATION_LOG_ROOT = APPLICATION_STORAGE_ROOT / "logs"

_FORBIDDEN_COMPONENTS = frozenset({"temp", "tmp"})


def validate_storage_path(path: Path, *, purpose: str, create: bool = True) -> Path:
    """Validate and optionally create an application-owned E: path.

    The check is intentionally strict: an unavailable E: drive or an invalid
    path is an explicit startup failure.  There is no C: or Windows temp
    fallback because losing the storage boundary could mix test and runtime
    data.
    """

    candidate = Path(path)
    if not candidate.is_absolute() or candidate.drive.upper() != "E:":
        raise StoragePathError(f"{purpose} must be stored on E:/{candidate}")
    if not Path(candidate.anchor).exists():
        raise StoragePathError("E_DRIVE_UNAVAILABLE")

    normalized_parts = tuple(part.casefold() for part in candidate.parts)
    if any(part in _FORBIDDEN_COMPONENTS or "phase5r" in part for part in normalized_parts):
        raise StoragePathError(f"{purpose} uses a forbidden temporary or phase-specific path")

    try:
        candidate.relative_to(APPLICATION_STORAGE_ROOT)
    except ValueError as error:
        raise StoragePathError(f"{purpose} must be under {APPLICATION_STORAGE_ROOT}") from error

    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    return candidate

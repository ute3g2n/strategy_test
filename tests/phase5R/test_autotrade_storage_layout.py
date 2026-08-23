import os
from pathlib import Path

import pytest

from autotrade.application.storage_paths import (
    APPLICATION_LOG_ROOT,
    APPLICATION_STORAGE_ROOT,
    BACKTEST_EXPORT_ROOT,
    BACKTEST_RESULT_ROOT,
    HISTORICAL_DATA_ROOT,
    StoragePathError,
    filesystem_storage_path,
    validate_local_storage_path,
    validate_storage_path,
)


def test_default_storage_layout_is_on_e_drive_and_application_scoped() -> None:
    paths = (
        APPLICATION_STORAGE_ROOT,
        HISTORICAL_DATA_ROOT,
        BACKTEST_RESULT_ROOT,
        BACKTEST_EXPORT_ROOT,
        APPLICATION_LOG_ROOT,
    )

    for path in paths:
        normalized = str(path).replace("/", "\\").lower()
        if os.name == "nt":
            assert path.drive.upper() == "E:", path
        else:
            filesystem_path = filesystem_storage_path(path)
            assert filesystem_path.as_posix().startswith("/mnt/e/"), filesystem_path
        assert "temp" not in normalized
        assert "autotrade" in normalized


@pytest.mark.parametrize(
    "candidate",
    (
        Path(r"C:\project\strategy_test\runtime"),
        Path(r"E:\strategy_test_data\temp"),
        Path(r"E:\strategy_test_data\unsupported"),
        Path(r"E:\strategy_test_data\autotrade\unsupported"),
    ),
)
def test_storage_path_validation_rejects_c_drive_temp_and_unrecognized_areas(candidate: Path) -> None:
    with pytest.raises(StoragePathError):
        validate_storage_path(candidate, purpose="test")


def test_storage_path_validation_accepts_application_path_without_creating_it() -> None:
    candidate = Path(r"E:\strategy_test_data\autotrade\backtest\results")

    validated = validate_storage_path(candidate, purpose="test", create=False)

    assert validated == candidate


def test_storage_path_validation_rejects_parent_traversal() -> None:
    with pytest.raises(StoragePathError, match="parent traversal"):
        validate_storage_path(
            Path(r"E:\strategy_test_data\autotrade\..\outside"),
            purpose="test",
            create=False,
        )


def test_injected_storage_path_requires_an_absolute_path() -> None:
    with pytest.raises(StoragePathError, match="absolute"):
        validate_local_storage_path(Path("relative-runtime"), purpose="test")

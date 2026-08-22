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
            assert path.parts[:2] == ("E:\\", "strategy_test_data"), path
        assert "temp" not in normalized
        assert "phase5r" not in normalized
        assert "autotrade" in normalized


@pytest.mark.parametrize(
    "candidate",
    (
        Path(r"C:\project\strategy_test\runtime"),
        Path(r"E:\strategy_test_data\temp"),
        Path(r"E:\strategy_test_data\phase5r"),
        Path(r"E:\strategy_test_data\autotrade\backtest\phase5r"),
    ),
)
def test_storage_path_validation_rejects_c_drive_temp_and_phase_names(candidate: Path) -> None:
    with pytest.raises(StoragePathError):
        validate_storage_path(candidate, purpose="test")


def test_storage_path_validation_accepts_application_path_without_creating_it() -> None:
    candidate = Path(r"E:\strategy_test_data\autotrade\backtest\results")

    validated = validate_storage_path(candidate, purpose="test", create=False)

    assert validated == candidate

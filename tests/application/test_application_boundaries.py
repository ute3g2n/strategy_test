"""P4-06 target-scope boundary tests."""

from pathlib import Path

import pytest

from autotrade.application.csv_job import atomic_csv_output
from autotrade.application.quality_contract import is_fail_closed


def test_csv_output_is_relative_and_atomic(tmp_path: Path) -> None:
    digest = atomic_csv_output(tmp_path, "run-1/result.csv", [{"id": "1", "value": "ok"}], ("id", "value"))
    assert digest.startswith("sha256:")
    assert (tmp_path / "run-1/result.csv").read_text(encoding="utf-8") == "id,value\n1,ok\n"


def test_csv_path_escape_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="CSV_PATH_INVALID"):
        atomic_csv_output(tmp_path, "../escape.csv", [], ("id",))


def test_fail_closed_reason_ids_are_not_silent_success() -> None:
    assert is_fail_closed("STALE_REVISION")
    assert is_fail_closed("MANIFEST_MISMATCH")

from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "phase5_external_data" / "run_p5r2_binance_data_vision.py"
SPEC = importlib.util.spec_from_file_location("p5r2_external_runner", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


EVIDENCE_ROOT = ROOT / "tests" / "evidence" / "phase5R2" / "RUN-P5R2-18-EXTERNAL-001"


def _load_configs() -> tuple[dict, dict, dict, dict]:
    return tuple(
        json.loads((EVIDENCE_ROOT / name).read_text(encoding="utf-8"))
        for name in ("request.json", "runner-registration.json", "allowlist.json", "host-isolation.json")
    )  # type: ignore[return-value]


def _raw_row(open_time: int, close_time: int) -> list[str]:
    return [
        str(open_time),
        "1",
        "2",
        "0.5",
        "1.5",
        "10",
        str(close_time),
        "20",
        "3",
        "4",
        "5",
        "0",
    ]


def _zip_csv(path: Path, rows: list[list[str]], *, name: str = "BTCUSDT-1m-2025-02.csv") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        lines: list[str] = []
        for row in rows:
            output = []
            for item in row:
                output.append(item)
            lines.append(",".join(output))
        archive.writestr(name, "\n".join(lines) + "\n")


def test_dry_run_is_blocked_without_host_level_isolation() -> None:
    request, registration, allowlist, isolation = _load_configs()

    report = runner.build_dry_run_report(request, registration, allowlist, isolation)

    assert report["status"] == "BLOCKED"
    assert report["external_io_performed"] is False
    assert report["ready_for_external_io"] is False
    assert "HOST_LEVEL_ISOLATION_NOT_VERIFIED" in report["blocking_reasons"]
    assert report["archive_object_count"] == 4


def test_dry_run_requires_the_bounded_approval_evidence() -> None:
    request, registration, allowlist, isolation = _load_configs()
    request["approval_evidence"] = "tests/evidence/phase5R2/RUN-P5R2-18-EXTERNAL-001/missing-approval.md"

    report = runner.build_dry_run_report(request, registration, allowlist, isolation)

    assert "P5R2_DATA_G1_APPROVAL_EVIDENCE_MISSING" in report["blocking_reasons"]
    assert report["external_io_performed"] is False


def test_request_rejects_a_non_source_interval() -> None:
    request, _, _, _ = _load_configs()
    request["source_interval"] = "30m"

    with pytest.raises(runner.ContractError, match="SOURCE_INTERVAL_SCOPE_MISMATCH"):
        runner.validate_request(request)


def test_allowlist_rejects_another_host() -> None:
    _, _, allowlist, _ = _load_configs()
    allowlist["entries"][0]["host"] = "example.invalid"

    with pytest.raises(runner.ContractError, match="ALLOWLIST_SCOPE_MISMATCH"):
        runner.validate_allowlist(allowlist)


def test_redirect_is_fail_closed() -> None:
    with pytest.raises(runner.ContractError, match="REDIRECT_NOT_ALLOWED"):
        runner._NoRedirect().redirect_request(None, "https://example.invalid", None)


def test_duplicate_timestamp_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "source.zip"
    start_ms = 1_740_355_200_000
    _zip_csv(archive, [_raw_row(start_ms, start_ms + 59_999), _raw_row(start_ms, start_ms + 59_999)])

    with pytest.raises(runner.ContractError, match="CSV_DUPLICATE_TIMESTAMP"):
        runner._normalise_archive(
            archive,
            tmp_path / "normalized.csv.gz",
            symbol="BTCUSDT",
            month="2025-02",
            period_start_us=start_ms * 1000,
            period_end_us=(start_ms + 60_000) * 1000,
        )


def test_gap_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "source.zip"
    start_ms = 1_740_355_200_000
    _zip_csv(
        archive,
        [_raw_row(start_ms, start_ms + 59_999), _raw_row(start_ms + 120_000, start_ms + 179_999)],
    )

    with pytest.raises(runner.ContractError, match="CSV_GAP_DETECTED"):
        runner._normalise_archive(
            archive,
            tmp_path / "normalized.csv.gz",
            symbol="BTCUSDT",
            month="2025-02",
            period_start_us=start_ms * 1000,
            period_end_us=(start_ms + 180_000) * 1000,
        )


def test_existing_normalized_target_is_never_overwritten(tmp_path: Path) -> None:
    archive = tmp_path / "source.zip"
    target = tmp_path / "normalized.csv.gz"
    start_ms = 1_740_355_200_000
    _zip_csv(archive, [_raw_row(start_ms, start_ms + 59_999)])
    target.write_bytes(b"protected-existing-data")

    with pytest.raises(runner.ContractError, match="TARGET_ALREADY_EXISTS"):
        runner._normalise_archive(
            archive,
            target,
            symbol="BTCUSDT",
            month="2025-02",
            period_start_us=start_ms * 1000,
            period_end_us=(start_ms + 60_000) * 1000,
        )

    assert target.read_bytes() == b"protected-existing-data"


def test_execute_is_blocked_before_network_when_host_is_not_verified() -> None:
    request, registration, allowlist, isolation = _load_configs()

    with pytest.raises(runner.ContractError, match="HOST_LEVEL_ISOLATION_NOT_VERIFIED"):
        runner.execute_acquisition(request, registration, allowlist, isolation)

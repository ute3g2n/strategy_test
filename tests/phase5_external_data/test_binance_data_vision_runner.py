from __future__ import annotations

"""Raw source-data hash checks protect reproducibility only; no management hash is tested."""

import json
from pathlib import Path

import pytest

from scripts.phase5_external_data import run_binance_data_vision as runner


EVIDENCE_ROOT = Path("tests/evidence/phase5/RUN-P5-08-BINANCE-001")


def fixed_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    root = Path(__file__).parents[2]
    request = runner.load_json(root / EVIDENCE_ROOT / "request.json")
    registration = runner.load_json(root / EVIDENCE_ROOT / "runner-registration.json")
    allowlist = runner.load_json(root / EVIDENCE_ROOT / "allowlist.json")
    isolation = runner.load_json(root / EVIDENCE_ROOT / "host-isolation.json")
    return request, registration, allowlist, isolation


def test_fixed_request_is_spot_only_and_has_expected_months() -> None:
    request, _registration, _allowlist, _isolation = fixed_inputs()

    months = runner.validate_request(request)

    assert len(months) == 18
    assert months[0] == "2025-02"
    assert months[-1] == "2026-07"
    assert request["symbols"] == ["BTCUSDT", "ETHUSDT"]
    assert request["market_segment"] == "spot"


def test_dry_run_is_local_and_reports_unverified_gates() -> None:
    request, registration, allowlist, isolation = fixed_inputs()

    report = runner.build_dry_run_report(request, registration, allowlist, isolation)

    assert report["status"] == "REGISTERED_NOT_EXECUTED"
    assert report["external_io_performed"] is False
    assert report["api_key_or_secret_read"] is False
    assert report["ready_for_external_io"] is False
    assert "HOST_ISOLATION_NOT_VERIFIED" in report["blocking_reasons"]
    assert "PROVIDER_TERMS_UNKNOWN" in report["blocking_reasons"]


def test_archive_and_checksum_urls_are_exactly_allowlisted() -> None:
    archive = runner.expected_archive_url("BTCUSDT", "2025-02")
    checksum = runner.expected_checksum_url("BTCUSDT", "2025-02")

    runner.validate_provider_url(archive, symbol="BTCUSDT", year_month="2025-02", checksum=False)
    runner.validate_provider_url(checksum, symbol="BTCUSDT", year_month="2025-02", checksum=True)
    with pytest.raises(runner.ContractError, match="URL_ALLOWLIST_MISMATCH"):
        runner.validate_provider_url(
            "https://api.binance.com/api/v3/klines?symbol=BTCUSDT",
            symbol="BTCUSDT",
            year_month="2025-02",
            checksum=False,
        )


def test_execute_requires_verified_isolation_and_confirmed_terms() -> None:
    request, registration, allowlist, isolation = fixed_inputs()

    with pytest.raises(runner.ContractError, match="HOST_ISOLATION_NOT_VERIFIED"):
        runner.execute_acquisition(request, registration, allowlist, isolation)


def test_fixed_json_files_do_not_contain_secret_values() -> None:
    root = Path(__file__).parents[2]
    content = "\n".join(
        (root / EVIDENCE_ROOT / name).read_text(encoding="utf-8")
        for name in ("request.json", "runner-registration.json", "allowlist.json", "host-isolation.json")
    )
    parsed = json.loads((root / EVIDENCE_ROOT / "request.json").read_text(encoding="utf-8"))

    assert parsed["secret_policy"] == {
        "api_key_used": False,
        "secret_used": False,
        "environment_read": False,
        "authorization_header": False,
    }
    assert "DATABENTO_API_KEY" not in content
    assert "secret-value" not in content

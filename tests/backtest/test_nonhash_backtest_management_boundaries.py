"""Step 06 regression tests for Backtest manifest/result management hashes."""

from __future__ import annotations

from tests.backtest.test_backtest_repair_core import _event, _request

from autotrade.backtest.experiment_manifest import manifest_mapping
from autotrade.backtest.runner import BacktestRunner


def test_runner_publishes_protected_state_without_management_result_identity() -> None:
    request = _request((_event(0),))
    payload = manifest_mapping(request.manifest)
    result = BacktestRunner().run(request)

    assert result.status == "COMMITTED"
    assert "manifest_sha256" not in payload
    assert "output_sha256" not in payload
    assert result.result_sha256 is None
    assert result.snapshot is not None
    assert result.snapshot.manifest_sha256 is None
    assert result.snapshot.commit_marker_sha256 is None
    assert result.commit_marker is not None
    assert result.commit_marker.manifest_sha256 is None
    assert result.commit_marker.result_sha256 is None
    assert result.commit_marker.commit_sha256 is None

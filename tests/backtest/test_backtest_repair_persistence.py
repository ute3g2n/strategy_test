"""P3-07R-03 persistence, recovery, and hostile ResultStore contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from autotrade.backtest.contracts import canonical_hash, canonical_json
from autotrade.backtest.experiment_manifest import manifest_mapping, validate_manifest_integrity
from autotrade.backtest.result_store import (
    AtomicResultStore,
    CommitInput,
    is_publishable,
)


def _manifest(run_id: str = "RUN-P3-BT-REPAIR-003") -> dict[str, Any]:
    legacy = {
        "run_id": run_id,
        "schema_version": "p3-backtest-run-v1",
        "raw_input_sha256": "sha256:" + "1" * 64,
        "normalized_input_sha256": "sha256:" + "2" * 64,
        "market_event_sequence_sha256": "sha256:" + "3" * 64,
        "data_version": "dv-p3-repair-003",
        "catalog_version": "catalog-p3-repair-003",
        "catalog_sha256": "sha256:" + "4" * 64,
        "calendar_version": "calendar-p3-repair-003",
        "calendar_sha256": "sha256:" + "5" * 64,
        "timeframe_rule_version": "direct-m1-v2",
        "ordering_rule_version": "m1-m15-m30-h1-h4-d1-v2",
        "strategy_config_sha256": "sha256:" + "6" * 64,
        "code_revision": "p3-07r-03-test",
        "quality_policy_version": "quality-p2-v1",
        "quality_report_sha256": "sha256:" + "7" * 64,
        "split_plan_sha256": "sha256:" + "8" * 64,
        "cost_profile_sha256": "sha256:" + "9" * 64,
        "adapter_version": "ENGINE_NOT_USED",
        "adapter_artifact_sha256": "ENGINE_NOT_USED",
        "engine_identity": {
            "engine_kind": "ENGINE_NOT_USED",
            "engine_version": "ENGINE_NOT_USED",
            "distribution_source": "ENGINE_NOT_USED",
            "artifact_sha256_or_oci_digest": "ENGINE_NOT_USED",
            "adapter_name": "ENGINE_NOT_USED",
            "adapter_version": "ENGINE_NOT_USED",
            "adapter_artifact_sha256": "ENGINE_NOT_USED",
            "runtime_kind": "ENGINE_NOT_USED",
            "runtime_version": "ENGINE_NOT_USED",
            "execution_mode": "ENGINE_NOT_USED",
        },
        "fixture_manifest_sha256": "sha256:" + "a" * 64,
        "child_fixture_sha256s": ("sha256:" + "b" * 64,),
        "input_sha256": "sha256:" + "c" * 64,
        "output_sha256": None,
        "enabled_timeframes": ("M1", "M15", "H1"),
    }
    payload = manifest_mapping(legacy)
    assert validate_manifest_integrity(payload) == {"status": "PASS"}
    return payload


def _rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "backtest-result-row/v1",
            "row_id": f"{manifest['run_id']}:0:SIGNAL",
            "run_id": manifest["run_id"],
            "sequence_no": 0,
            "event_id": "evt-001",
            "instrument_id": "MKT-A",
            "logical_time_utc": "2026-08-09T00:01:00Z",
            "row_kind": "SIGNAL",
            "payload": {"direction": "LONG"},
            "payload_sha256": canonical_hash({"direction": "LONG"}),
            "warning_flags": [],
        }
    ]


def _snapshot(manifest: dict[str, Any], offset: int) -> dict[str, Any]:
    return {
        "schema_version": "backtest-snapshot/v1",
        "run_id": manifest["run_id"],
        "input_sequence_sha256": manifest["input_sequence_sha256"],
        "replay_sha256": manifest["market_event_sequence_sha256"],
        "last_committed_event_id": "evt-001" if offset else None,
        "last_batch_sha256": canonical_hash(["batch-001"]),
        "strategy_snapshot_sha256": canonical_hash({"watermark": "2026-08-09T00:01:00Z"}),
        "aggregator_snapshot_sha256": canonical_hash({"M1": "evt-001"}),
        "simulator_state_sha256": canonical_hash({"pending": [], "consumed": []}),
        "pending_fingerprints": [],
        "consumed_fingerprints": [],
        "execution_watermarks": {"M1": "2026-08-09T00:01:00Z"},
        "result_offset": offset,
        "state_payload": {"pending": [], "consumed": []},
    }


def _commit(manifest: dict[str, Any], rows: list[dict[str, Any]] | None = None) -> CommitInput:
    actual_rows = rows if rows is not None else _rows(manifest)
    return CommitInput(
        commit_id=manifest["run_id"],
        result_rows=actual_rows,
        snapshot=_snapshot(manifest, len(actual_rows)),
        last_event_id="evt-001" if actual_rows else None,
        last_batch_sha256=canonical_hash(["batch-001"]),
    )


def test_canonical_json_rejects_float_nonfinite_set_and_object() -> None:
    for value in ({"price": 1.25}, {"price": float("nan")}, {"values": {"x"}}, {"value": object()}):
        with pytest.raises((TypeError, ValueError)):
            canonical_json(value)


def test_manifest_structure_and_protected_fields_are_validated_without_manifest_hash() -> None:
    manifest = _manifest()
    assert "manifest_sha256" not in manifest
    assert validate_manifest_integrity(manifest) == {"status": "PASS"}
    changed = {**manifest, "unknown": "must-stop"}
    assert validate_manifest_integrity(changed)["status"] == "STOPPED"
    changed = {**manifest, "calendar_sha256": "sha256:" + "d" * 64}
    assert validate_manifest_integrity(changed) == {"status": "PASS"}


def test_result_store_rejects_relative_unc_traversal_and_root_path(tmp_path: Path) -> None:
    store = AtomicResultStore(tmp_path / "runs")
    assert not is_publishable(store.root, store.root)
    assert not is_publishable(store.root / ".." / "outside.txt", store.root)
    assert not is_publishable(Path(r"\\server\share\run"), store.root)
    with pytest.raises(ValueError):
        store.create_staging({**_manifest(), "run_id": "../escape"})


def test_staging_writes_manifest_result_snapshot_marker_and_publishes_atomically(tmp_path: Path) -> None:
    manifest = _manifest()
    store = AtomicResultStore(tmp_path / "runs")
    staging = store.create_staging(manifest=manifest)
    assert (staging.tmp_path / "experiment-manifest.json").is_file()
    marker = store.append_then_commit(staging, _commit(manifest))
    assert sorted(path.name for path in staging.tmp_path.iterdir()) == sorted(
        [
            "experiment-manifest.json",
            "result.jsonl",
            "audit.jsonl",
            "snapshot.json",
            "commit-marker.json",
        ]
    )
    published = store.publish(staging, marker)
    assert published == store.root / manifest["run_id"]
    assert not staging.tmp_path.exists()
    recovered = store.read_published(manifest["run_id"])
    assert recovered["status"] == "PASS"
    assert len(recovered["rows"]) == 1
    assert recovered["marker"]["result_offset"] == 1
    recovered_after_redelivery = store.recover_published(manifest["run_id"], ["evt-001", "evt-001", "evt-002"])
    assert recovered_after_redelivery["replay_start_index"] == 2
    assert recovered_after_redelivery["replayed_event_ids"] == ["evt-002"]


def test_same_run_cannot_be_overwritten_and_tampering_stops_recovery(tmp_path: Path) -> None:
    manifest = _manifest()
    store = AtomicResultStore(tmp_path / "runs")
    staging = store.create_staging(manifest)
    marker = store.append_then_commit(staging, _commit(manifest))
    store.publish(staging, marker)
    with pytest.raises(FileExistsError):
        store.create_staging(manifest)
    marker_path = store.root / manifest["run_id"] / "commit-marker.json"
    marker_path.write_text(marker_path.read_text(encoding="utf-8").replace("evt-001", "evt-tampered"), encoding="utf-8")
    assert store.read_published(manifest["run_id"]) == {
        "status": "STOPPED",
        "reason": "RECOVERY_RECONCILIATION_FAILED",
        "detail": "ValueError",
    }


def test_partial_commit_is_not_publishable(tmp_path: Path) -> None:
    manifest = _manifest()
    store = AtomicResultStore(tmp_path / "runs")
    staging = store.create_staging(manifest)
    marker = store.append_then_commit(staging, _commit(manifest))
    (staging.tmp_path / "snapshot.json").unlink()
    with pytest.raises(ValueError, match="partial commit"):
        store.publish(staging, marker)


def test_result_row_rejects_secret_vendor_and_noncanonical_values(tmp_path: Path) -> None:
    manifest = _manifest()
    store = AtomicResultStore(tmp_path / "runs")
    cases = [
        {**_rows(manifest)[0], "api_key": "redact"},
        {**_rows(manifest)[0], "broker_order_id": "B-1"},
        {**_rows(manifest)[0], "payload": {"price": 1.5}},
    ]
    for index, row in enumerate(cases):
        run_manifest = _manifest(f"RUN-P3-ROW-{index}")
        staging = store.create_staging(manifest=run_manifest)
        with pytest.raises((TypeError, ValueError)):
            store.append_then_commit(staging, _commit(run_manifest, [row]))


def test_typed_runner_result_can_be_published_and_recovered(tmp_path: Path) -> None:
    from tests.backtest.test_backtest_repair_core import _event, _request

    from autotrade.backtest.runner import BacktestRunner

    request = _request((_event(0),))
    payload = manifest_mapping(request.manifest)
    result = BacktestRunner().run(request)
    assert result.status == "COMMITTED"
    published = AtomicResultStore(tmp_path / "runs").publish_backtest_result(payload, result)
    assert published["status"] == "PASS"

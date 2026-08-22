"""Step 06 regression tests for the nonhash management boundary."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tests.application.test_p4_07_execution import HASH, _config

from autotrade.application.api import ProductApplicationApi, build_create_run_command
from autotrade.application.contracts import PreflightReport
from autotrade.application.evidence import evidence_reference
from autotrade.application.persistence import MetadataStore
from autotrade.application.preflight import preflight_run
from autotrade.application.result_view import LocalResultArtifacts, MetricSet


def test_preflight_result_and_artifact_reference_do_not_create_management_hashes(tmp_path: Path) -> None:
    report = preflight_run(_config())
    assert report.status == "PASS"
    assert report.report_sha256 is None

    artifacts = LocalResultArtifacts(tmp_path)
    output = type(
        "Output",
        (),
        {
            "metrics": MetricSet("0", "0", 0, "0", "0", "TEST", "", "", "", None),
            "rows": (),
        },
    )()
    reference = artifacts.publish("run-nonhash", output)
    assert reference.manifest_sha256 is None
    assert reference.result_sha256 is None
    assert reference.commit_marker_sha256 is None
    marker = (tmp_path / "results" / "run-nonhash" / "result.commit.json").read_text(encoding="utf-8")
    assert "sha256" not in marker
    assert artifacts.read(reference)["rows"] == []

    evidence = evidence_reference("run-nonhash", "evidence/run-nonhash", {"core.state.sha256": HASH})
    assert evidence.evidence_id == "evidence-run-nonhash"
    assert evidence.evidence_sha256 is None


def test_new_metadata_rows_leave_management_hash_columns_empty() -> None:
    store = MetadataStore()
    try:
        store.initialize()
        migration = store.connection.execute(
            "SELECT checksum FROM schema_migration WHERE version = ?", ("p4-metadata-v2-nonhash-management",)
        ).fetchone()
        assert migration["checksum"] is None
        api = ProductApplicationApi(store=store)
        report = api.preflight_run(_config()).data
        assert report is not None
        command = build_create_run_command("nonhash-run", _config(), report)
        created = api.create_run(command, report)
        assert created.ok
        run = store.connection.execute("SELECT manifest_sha256 FROM run").fetchone()
        transition = store.connection.execute("SELECT payload_sha256 FROM run_state_transition").fetchone()
        audit = store.connection.execute("SELECT payload_sha256 FROM audit_event").fetchone()
        assert run["manifest_sha256"] is None
        assert transition["payload_sha256"] is None
        assert audit["payload_sha256"] is None
        api.close()
    finally:
        store.close()


def test_run_boundary_recomputes_preflight_and_rejects_forged_pass_report() -> None:
    config = _config()
    invalid_config = replace(config, unit_key=replace(config.unit_key, timeframe="1m"))
    forged_pass = PreflightReport("PASS", ())
    store = MetadataStore()
    try:
        with ProductApplicationApi(store=store) as api:
            response = api.create_run(
                build_create_run_command("forged-p5r2-preflight", invalid_config, forged_pass),
                forged_pass,
            )
            assert response.status_code == 403
            assert response.failure is not None
            assert response.failure.code == "PREFLIGHT_REQUIRED"
            assert api.list_runs().data == ()
            legacy_m30 = replace(config, unit_key=replace(config.unit_key, timeframe="M30"))
            legacy_response = api.create_run(
                build_create_run_command("legacy-m30-run", legacy_m30, forged_pass),
                forged_pass,
            )
            assert legacy_response.status_code == 403
            assert api.list_runs().data == ()
    finally:
        store.close()


def test_canonical_p5r2_run_requires_and_revalidates_strict_input() -> None:
    base = _config()
    config = replace(
        base,
        unit_key=replace(base.unit_key, timeframe="15m"),
        experiment_plan={"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
    )
    strict_input = {
        "symbol": "EURUSD",
        "strategy_timeframe": "15m",
        "source_timeframe": "1m",
        "requested_range": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-01T01:00:00Z"},
        "data_version": "fixture-v1",
        "data_identity": {
            "source_mode": "fixture_only",
            "dataset_id": "fixture-v1",
            "record_id": "dataset-v1",
            "data_version": "fixture-v1",
        },
        "bars": [
            {
                "open_time_utc": "2024-01-01T00:00:00Z",
                "close_time_utc": "2024-01-01T00:15:00Z",
                "open": "100.00",
                "high": "101.00",
                "low": "99.00",
                "close": "100.50",
                "volume": 10,
                "is_closed": True,
                "timeframe": "15m",
                "provenance": {"source_mode": "fixture_only", "dataset_id": "fixture-v1", "record_id": "bar-1"},
            }
        ],
        "data_quality": {"quality_state": "USABLE"},
    }
    forged_pass = PreflightReport("PASS", ())
    store = MetadataStore()
    try:
        with ProductApplicationApi(store=store) as api:
            missing_input = api.create_run(
                build_create_run_command("p5r2-missing-input", config, forged_pass),
                forged_pass,
            )
            accepted = api.create_run(
                build_create_run_command("p5r2-strict-input", config, forged_pass, preflight_input=strict_input),
                forged_pass,
            )
            assert missing_input.status_code == 403
            assert accepted.status_code == 201
    finally:
        store.close()


def test_sweep_revalidates_candidates_before_child_persistence() -> None:
    store = MetadataStore()
    try:
        with ProductApplicationApi(store=store) as api:
            report = api.preflight_run(_config()).data
            assert report is not None
            secret_candidate = api.create_sweep(
                "p5r2-secret-candidate",
                _config(),
                ({"api_key": "should-not-persist"},),
                report,
            )
            nonfinite_candidate = api.create_sweep(
                "p5r2-nonfinite-candidate",
                _config(),
                ({"n": float("nan")},),
                report,
            )
            assert secret_candidate.status_code == 422
            assert secret_candidate.failure is not None
            assert secret_candidate.failure.code == "SWEEP_CANDIDATE_INVALID"
            assert nonfinite_candidate.status_code == 422
            assert nonfinite_candidate.failure is not None
            assert nonfinite_candidate.failure.code == "SWEEP_CANDIDATE_INVALID"
            stored = store.connection.execute("SELECT config_json FROM run").fetchall()
            assert all("should-not-persist" not in row[0] for row in stored)
    finally:
        store.close()

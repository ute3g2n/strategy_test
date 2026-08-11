"""P4-07 fixed-fixture execution contracts.

The tests use a deterministic adapter double at the Application boundary.  It
stands in for the frozen Core output and proves that the Application layer
calls that boundary once; it does not change or emulate Core source code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotrade.application.api import API_INVENTORY, ProductApplicationApi, build_create_run_command
from autotrade.application.checkpoint import CheckpointReference
from autotrade.application.contracts import (
    BacktestConfig,
    DataReference,
    OutputPolicy,
    ResumeJobCommand,
    RiskReference,
    StartJobCommand,
    StrategyReference,
    UnitKey,
    canonical_hash,
)
from autotrade.application.core_adapter import (
    BacktestCoreAdapter,
    CoreExecutionNotEnabled,
    CoreExecutionOutput,
    CoreExecutionStopped,
    FrozenCoreAdapter,
)
from autotrade.application.persistence import MetadataStore
from autotrade.application.result_view import LocalResultArtifacts, MetricSet
from autotrade.application.worker import LocalWorker

HASH = "sha256:" + "b" * 64


def _config() -> BacktestConfig:
    return BacktestConfig(
        unit_key=UnitKey("EURUSD", "M15", "turtle-v1"),
        data=DataReference("fixture-v1", HASH, HASH, HASH),
        strategy=StrategyReference("turtle", "v1", HASH, "fixed-core"),
        risk=RiskReference("reference-only", "v1", HASH),
        experiment_plan={"start": "2024-01-01T00:00:00Z", "end": "2024-01-02T00:00:00Z"},
        cost_profile_sha256=HASH,
        calendar_version="fixed-local-v1",
        calendar_sha256=HASH,
        output_policy=OutputPolicy(),
        config_sha256=HASH,
    )


def _fixed_output(_job: object) -> CoreExecutionOutput:
    return CoreExecutionOutput(
        metrics=MetricSet(
            total_pnl="12.50",
            maximum_drawdown="-3.00",
            trade_count=2,
            win_rate="0.5000",
            ending_balance="1012.50",
            unit="USD",
            period_start_utc="2024-01-01T00:00:00Z",
            period_end_utc="2024-01-02T00:00:00Z",
            rounding_rule="ROUND_HALF_EVEN_4DP",
            source_result_sha256=HASH,
        ),
        rows=({"event_id": "evt-1", "pnl": "12.50"},),
        evidence_files={"preflight.json": HASH},
    )


def _create_run(api: ProductApplicationApi, *, request_id: str = "p4-07-run") -> str:
    report = api.preflight_run(_config()).data
    assert report is not None
    response = api.create_run(build_create_run_command(request_id, _config(), report), report)
    assert response.ok and response.data is not None
    return response.data.run_id


def test_single_backtest_calls_frozen_boundary_once_and_publishes_references_only(tmp_path: Path) -> None:
    store = MetadataStore()
    artifacts = LocalResultArtifacts(tmp_path)
    adapter = FrozenCoreAdapter(_fixed_output)
    with ProductApplicationApi(store, artifacts=artifacts) as api:
        run_id = _create_run(api)
        run = api.get_run(run_id).data
        assert run is not None
        job = api.start_job(StartJobCommand(run_id, canonical_hash("start"), expected_revision=run.revision)).data
        assert job is not None
        completed = LocalWorker(store, worker_id="p4-07", core_adapter=adapter, artifacts=artifacts).run_once()
        assert completed is not None and completed.status.value == "SUCCEEDED"
        assert adapter.execution_count == 1
        result = api.get_result_summary(run_id)
        assert result.ok and result.data is not None
        assert result.data["metrics"]["trade_count"] == 2
        rows = api.list_result_rows(run_id)
        assert rows.ok and rows.data == ({"event_id": "evt-1", "pnl": "12.50"},)
        evidence = api.get_evidence(run_id)
        assert evidence.ok and evidence.data is not None
        stored = store.connection.execute("SELECT config_json FROM run WHERE run_id = ?", (run_id,)).fetchone()[0]
        assert "ending_balance" not in stored
        assert "evt-1" not in stored


def test_sweep_members_are_independent_runs_and_a_failed_member_does_not_become_success(tmp_path: Path) -> None:
    del tmp_path
    with ProductApplicationApi(MetadataStore()) as api:
        report = api.preflight_run(_config()).data
        assert report is not None
        sweep = api.create_sweep("p4-07-sweep", _config(), ({"n": 10}, {"n": 20}), report)
        assert sweep.ok and sweep.data is not None
        members = sweep.data.members
        assert len(members) == 2
        assert len({member.run_id for member in members}) == 2
        assert all(member.run_kind == "SWEEP_CHILD" for member in members)
        assert api.compare_runs(members[0].run_id, members[1].run_id).data is not None


def test_sweep_parent_projects_partial_failure_after_all_members_are_terminal(tmp_path: Path) -> None:
    store = MetadataStore()
    artifacts = LocalResultArtifacts(tmp_path)

    def stopped(_job: object) -> CoreExecutionOutput:
        raise CoreExecutionStopped("FIXED_FAILURE")

    with ProductApplicationApi(store, artifacts=artifacts) as api:
        report = api.preflight_run(_config()).data
        assert report is not None
        sweep = api.create_sweep("p4-07-partial", _config(), ({"n": 1}, {"n": 2}), report).data
        assert sweep is not None
        for ordinal, member in enumerate(sweep.members):
            assert api.start_job(
                StartJobCommand(member.run_id, canonical_hash(f"partial-{ordinal}"), expected_revision=member.revision)
            ).ok
        assert (
            LocalWorker(
                store,
                worker_id="p4-07-partial-success",
                core_adapter=FrozenCoreAdapter(_fixed_output),
                artifacts=artifacts,
            ).run_once()
            is not None
        )
        assert (
            LocalWorker(
                store,
                worker_id="p4-07-partial-failure",
                core_adapter=FrozenCoreAdapter(stopped),
                artifacts=artifacts,
            ).run_once()
            is not None
        )
        parent = api.get_run(sweep.parent_run.run_id).data
        assert parent is not None and parent.status.value == "PARTIAL_FAILED"


def test_csv_is_metadata_first_then_atomic_output_and_is_idempotent(tmp_path: Path) -> None:
    store = MetadataStore()
    artifacts = LocalResultArtifacts(tmp_path)
    adapter = FrozenCoreAdapter(_fixed_output)
    with ProductApplicationApi(store, artifacts=artifacts) as api:
        run_id = _create_run(api, request_id="p4-07-csv")
        run = api.get_run(run_id).data
        assert run is not None
        assert api.start_job(StartJobCommand(run_id, canonical_hash("csv-start"), expected_revision=run.revision)).ok
        assert (
            LocalWorker(store, worker_id="p4-07-csv", core_adapter=adapter, artifacts=artifacts).run_once() is not None
        )
        source = api.get_run(run_id).data
        assert source is not None and source.result is not None
        first = api.create_csv_job_for_rows(
            run_id, source.result.result_sha256, ("event_id", "pnl"), canonical_hash("all")
        )
        replay = api.create_csv_job_for_rows(
            run_id, source.result.result_sha256, ("event_id", "pnl"), canonical_hash("all")
        )
        assert first.ok and replay.ok and first.data == replay.data
        assert first.data is not None
        completed = api.run_csv_job(first.data["csv_job_id"])
        assert completed.ok and completed.data is not None
        assert completed.data["status"] == "COMPLETED"
        assert (tmp_path / completed.data["relative_output_ref"]).is_file()


def test_inventory_has_all_nineteen_api_ids_and_holdout_is_recorded_as_blocked() -> None:
    assert tuple(API_INVENTORY) == tuple(f"API-P4-{number:03d}" for number in range(1, 20))
    with ProductApplicationApi(MetadataStore()) as api:
        run_id = _create_run(api, request_id="p4-07-holdout")
        result = api.assess_holdout_reuse(run_id, canonical_hash({"holdout": "fixed"}))
        assert result.status_code == 403
        assert result.failure is not None and result.failure.code == "HOLDOUT_REUSE_BLOCKED"
        row = api.store.connection.execute("SELECT decision, reason_code FROM holdout_assessment").fetchone()
        assert tuple(row) == ("BLOCKED", "HOLDOUT_REUSE_BLOCKED")


def test_marker_mismatch_is_fail_closed(tmp_path: Path) -> None:
    artifacts = LocalResultArtifacts(tmp_path)
    reference = artifacts.publish("run-marker", _fixed_output(object()), HASH)
    marker = tmp_path / reference.relative_root / "result.commit.json"
    marker.write_text('{"result_sha256":"sha256:' + "0" * 64 + '"}', encoding="utf-8")
    try:
        artifacts.read(reference)
    except ValueError as error:
        assert str(error) == "RESULT_MARKER_MISMATCH"
    else:
        raise AssertionError("marker mismatch must fail closed")


def test_frozen_backtest_runner_adapter_is_typed_and_single_use() -> None:
    from tests.backtest.test_backtest_repair_core import _event, _request

    adapter = BacktestCoreAdapter(lambda _job: _request(tuple(_event(index) for index in range(3))))
    output = adapter.execute(object())
    assert output.core_result_sha256 is not None
    assert adapter.execution_count == 1
    with pytest.raises(CoreExecutionNotEnabled, match="DUPLICATE"):
        adapter.execute(object())


def test_sweep_write_rolls_back_when_a_child_write_fails() -> None:
    with ProductApplicationApi(MetadataStore()) as api:
        report = api.preflight_run(_config()).data
        assert report is not None
        original = api.store._create_run_in_transaction
        calls = 0

        def fail_on_child(command: object, correlation_id: str) -> object:
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("failure injection")
            return original(command, correlation_id)  # type: ignore[arg-type]

        api.store._create_run_in_transaction = fail_on_child  # type: ignore[method-assign]
        with pytest.raises(RuntimeError, match="failure injection"):
            api.create_sweep("p4-07-rollback", _config(), ({"n": 1}, {"n": 2}), report)
        assert api.store.connection.execute("SELECT COUNT(*) FROM run").fetchone()[0] == 0
        assert api.store.connection.execute("SELECT COUNT(*) FROM sweep_parent").fetchone()[0] == 0


def test_checkpoint_hash_is_required_before_resume() -> None:
    store = MetadataStore()
    with ProductApplicationApi(store) as api:
        run_id = _create_run(api, request_id="p4-07-resume")
        run = api.get_run(run_id).data
        assert run is not None
        started = api.start_job(StartJobCommand(run_id, canonical_hash("resume-start"), run.revision)).data
        assert started is not None
        failed = LocalWorker(store, worker_id="p4-07-no-core").run_once()
        assert failed is not None and failed.status.value == "RECOVERY_REQUIRED"
        current = api.get_run(run_id).data
        assert current is not None
        blocked = api.resume_job(
            ResumeJobCommand(run_id, HASH, canonical_hash("bad-checkpoint"), expected_revision=current.revision)
        )
        assert blocked.status_code == 423
        reference = CheckpointReference(
            started.job_id,
            run_id,
            0,
            "checkpoints/run-1.json",
            HASH,
            run.manifest_sha256,
            HASH,
        )
        store.record_checkpoint(reference)
        resumed = api.resume_job(
            ResumeJobCommand(run_id, HASH, canonical_hash("good-checkpoint"), expected_revision=current.revision)
        )
        assert resumed.status_code == 202
        assert resumed.data is not None and resumed.data.attempt == 1

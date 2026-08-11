"""P4-06 RED→GREEN contract tests.

P4-04Dの旧sentinelは、P4-03正式file treeとの不一致を起こしていた
``autotrade.product_application``を参照していた。P4-H1後は、正本である
``autotrade.application``の型・transaction・Fail-closed契約を検証する。
"""

from datetime import UTC, datetime

from autotrade.application import (
    BacktestConfig,
    CancelJobCommand,
    DataReference,
    MetadataStore,
    OutputPolicy,
    ProductApplicationApi,
    RiskReference,
    StartJobCommand,
    StrategyReference,
    UnitKey,
    build_create_run_command,
)
from autotrade.application.config import condition_sha256
from autotrade.application.contracts import canonical_hash
from autotrade.application.run_manifest import RunManifest
from autotrade.application.ui_contract import UI_CONTRACT_VERSION, validate_ui_payload

HASH = "sha256:" + "a" * 64


def make_config() -> BacktestConfig:
    return BacktestConfig(
        unit_key=UnitKey("EURUSD", "M15", "turtle-v1"),
        data=DataReference("fixture-v1", HASH, HASH, HASH),
        strategy=StrategyReference("turtle", "v1", HASH, "local-test"),
        risk=RiskReference("not-materialized", "v1", HASH),
        experiment_plan={"start": "2024-01-01T00:00:00Z", "end": "2024-01-02T00:00:00Z"},
        cost_profile_sha256=HASH,
        calendar_version="fixed-local-v1",
        calendar_sha256=HASH,
        output_policy=OutputPolicy(),
        config_sha256=HASH,
    )


def test_p4_h1_contract_modules_and_manifest_are_green() -> None:
    manifest = RunManifest("p4-v1", "run-1", HASH, HASH, HASH, "evidence")
    manifest.validate()
    assert manifest.manifest_sha256.startswith("sha256:")
    validate_ui_payload({"contract_version": UI_CONTRACT_VERSION, "state": "INITIAL"})


def test_preflight_and_create_run_are_typed_and_idempotent() -> None:
    config = make_config()
    with ProductApplicationApi(MetadataStore()) as api:
        preflight = api.preflight_run(config)
        assert preflight.ok
        command = build_create_run_command("request-1", config, preflight.data)  # type: ignore[arg-type]
        first = api.create_run(command, preflight.data)
        replay = api.create_run(command, preflight.data)
        assert first.status_code == 201
        assert replay.status_code == 201
        assert first.data == replay.data
        assert first.data is not None
        assert first.data.condition_sha256 == condition_sha256(config)


def test_start_cancel_uses_transaction_and_expected_revision() -> None:
    config = make_config()
    with ProductApplicationApi(MetadataStore()) as api:
        preflight = api.preflight_run(config).data
        assert preflight is not None
        run = api.create_run(build_create_run_command("request-2", config, preflight), preflight).data
        assert run is not None
        started = api.start_job(StartJobCommand(run.run_id, HASH, expected_revision=run.revision))
        assert started.status_code == 202
        assert started.data is not None
        cancelled = api.cancel_job(CancelJobCommand(started.data.job_id, canonical_hash("cancel")))
        assert cancelled.ok
        assert cancelled.data is not None
        assert cancelled.data.status.value == "CANCELLED"


def test_invalid_input_fails_closed_without_creating_run() -> None:
    config = make_config()
    invalid = BacktestConfig(
        unit_key=config.unit_key,
        data=config.data,
        strategy=config.strategy,
        risk=RiskReference(
            "real", "v1", HASH, value_materialization="REFERENCE_ONLY", source_mode="FIXED_LOCAL_REFERENCE"
        ),
        experiment_plan=config.experiment_plan,
        cost_profile_sha256=config.cost_profile_sha256,
        calendar_version=config.calendar_version,
        calendar_sha256=config.calendar_sha256,
        output_policy=config.output_policy,
        config_sha256=config.config_sha256,
    )
    with ProductApplicationApi(MetadataStore()) as api:
        response = api.preflight_run(invalid)
        assert response.status_code == 403
        assert response.failure is not None
        assert response.failure.code == "RISK_VALUE_OUT_OF_SCOPE"
        assert api.list_runs().data == ()


def test_metadata_rollback_keeps_parent_and_child_consistent() -> None:
    with MetadataStore() as store:
        store.initialize()
        try:
            with store.transaction():
                store.connection.execute(
                    "INSERT INTO run(run_id, run_kind, status, revision, condition_sha256, manifest_sha256, "
                    "config_json, created_at, updated_at) "
                    "VALUES ('run-rollback', 'SINGLE_BACKTEST', 'DRAFT', 0, ?, ?, '{}', ?, ?)",
                    (HASH, HASH, datetime.now(UTC).isoformat(), datetime.now(UTC).isoformat()),
                )
                raise RuntimeError("failure injection")
        except RuntimeError:
            pass
        assert store.get_run("run-rollback") is None

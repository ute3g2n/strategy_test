"""Canonical in-process P4 API facade.

HTTP paths listed in the design are projections only.  This facade is the
single local contract used by tests and, in P4-08, by a fixed local UI.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Any

from .contracts import (
    ApplicationResponse,
    BacktestConfig,
    CancelJobCommand,
    CreateCsvJobCommand,
    CreateRunCommand,
    GetJobQuery,
    GetRunQuery,
    JobView,
    PageQuery,
    PreflightReport,
    RunView,
    StartJobCommand,
    canonical_hash,
    failure_response,
    utc_now,
)
from .job_service import JobService
from .persistence import MetadataStore, PersistenceConflict
from .preflight import preflight_run
from .run_service import RunService
from .sweep_service import SweepService, SweepView


class ProductApplicationApi:
    """P4 canonical operations with safe response objects."""

    def __init__(self, store: MetadataStore | None = None) -> None:
        self.store = store or MetadataStore()
        self.store.initialize()
        self.runs = RunService(self.store)
        self.jobs = JobService(self.store)
        self.sweeps = SweepService(self.store)

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> ProductApplicationApi:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _correlation() -> str:
        return f"corr-{uuid.uuid4().hex}"

    def get_capability(self, *_: object) -> ApplicationResponse[dict[str, Any]]:
        return ApplicationResponse(
            200,
            {
                "contract_version": "P4-06-CONTRACT-V1",
                "BACKTEST_LOCAL": "SUPPORTED_DESIGN",
                "PAPER": {"status": "UNSUPPORTED", "phase": "P7", "gate": "P7-BROKER-LIVE"},
                "LIVE": {"status": "UNSUPPORTED", "phase": "P7", "gate": "P7-BROKER-LIVE"},
                "RISK_VALUE": {"status": "UNSUPPORTED", "phase": "P6", "gate": "P6-RISK-OMS"},
            },
            correlation_id=self._correlation(),
        )

    def preflight_run(self, config: BacktestConfig | Any) -> ApplicationResponse[PreflightReport]:
        candidate = getattr(config, "config", config)
        if not isinstance(candidate, BacktestConfig):
            return failure_response("TYPED_INPUT_INVALID", "P4-MSG-TYPED_INPUT_INVALID", status_code=422)
        report = preflight_run(candidate)
        return ApplicationResponse(200 if report.status == "PASS" else 403, report, report.failure, self._correlation())

    def create_run(
        self, command: CreateRunCommand, preflight: PreflightReport | None = None
    ) -> ApplicationResponse[RunView]:
        if not isinstance(command, CreateRunCommand):
            return failure_response("TYPED_INPUT_INVALID", "P4-MSG-TYPED_INPUT_INVALID", status_code=422)
        report = preflight or preflight_run(command.config)
        return self.runs.create_run(command, report, correlation_id=self._correlation())

    def create_sweep(
        self,
        client_request_id: str,
        config: BacktestConfig,
        candidates: tuple[dict[str, Any], ...],
        preflight: PreflightReport | None = None,
    ) -> ApplicationResponse[SweepView]:
        report = preflight or preflight_run(config)
        try:
            view = self.sweeps.create_sweep(
                client_request_id, config, candidates, report, correlation_id=self._correlation()
            )
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(code, f"P4-MSG-{code}", status_code=422)
        return ApplicationResponse(201, view, correlation_id=self._correlation())

    def get_run(self, query: GetRunQuery | str) -> ApplicationResponse[RunView]:
        run_id = query.run_id if isinstance(query, GetRunQuery) else query
        view = self.store.get_run(run_id)
        if view is None:
            return failure_response("NOT_FOUND", "P4-MSG-RUN_NOT_FOUND", status_code=404)
        return ApplicationResponse(200, view, correlation_id=self._correlation())

    def list_runs(self, query: PageQuery | None = None) -> ApplicationResponse[tuple[RunView, ...]]:
        page = query or PageQuery()
        if page.limit < 1 or page.limit > 200:
            return failure_response("PAGE_LIMIT_INVALID", "P4-MSG-PAGE_LIMIT_INVALID", status_code=422)
        return ApplicationResponse(
            200, self.store.list_runs(page.limit, page.state), correlation_id=self._correlation()
        )

    def start_job(self, command: StartJobCommand) -> ApplicationResponse[JobView]:
        if not isinstance(command, StartJobCommand):
            return failure_response("TYPED_INPUT_INVALID", "P4-MSG-TYPED_INPUT_INVALID", status_code=422)
        return self.jobs.start_job(command, correlation_id=self._correlation())

    def get_job(self, query: GetJobQuery | str) -> ApplicationResponse[JobView]:
        job_id = query.job_id if isinstance(query, GetJobQuery) else query
        view = self.store.get_job(job_id)
        if view is None:
            return failure_response("NOT_FOUND", "P4-MSG-JOB_NOT_FOUND", status_code=404)
        return ApplicationResponse(200, view, correlation_id=self._correlation())

    def list_jobs(self, query: PageQuery | None = None) -> ApplicationResponse[tuple[JobView, ...]]:
        page = query or PageQuery()
        if page.limit < 1 or page.limit > 200:
            return failure_response("PAGE_LIMIT_INVALID", "P4-MSG-PAGE_LIMIT_INVALID", status_code=422)
        return ApplicationResponse(
            200, self.store.list_jobs(page.limit, page.state), correlation_id=self._correlation()
        )

    def cancel_job(self, command: CancelJobCommand) -> ApplicationResponse[JobView]:
        return self.jobs.cancel_job(command, correlation_id=self._correlation())

    def resume_job(self, *_: object) -> ApplicationResponse[JobView]:
        return failure_response(
            "CHECKPOINT_VERIFICATION_REQUIRED",
            "P4-MSG-CHECKPOINT_VERIFICATION_REQUIRED",
            status_code=423,
            recovery_required=True,
        )

    def get_queue_state(self, query: PageQuery | None = None) -> ApplicationResponse[tuple[JobView, ...]]:
        return self.list_jobs(query)

    def get_result_summary(self, query: GetRunQuery | str) -> ApplicationResponse[dict[str, Any]]:
        run_response = self.get_run(query)
        if not run_response.ok or run_response.data is None:
            return ApplicationResponse(
                run_response.status_code, failure=run_response.failure, correlation_id=run_response.correlation_id
            )
        if run_response.data.result is None:
            return failure_response("RESULT_NOT_COMMITTED", "P4-MSG-RESULT_NOT_COMMITTED", status_code=409)
        return ApplicationResponse(
            200,
            {"run_id": run_response.data.run_id, "result": asdict(run_response.data.result)},
            correlation_id=self._correlation(),
        )

    def list_result_rows(self, *_: object) -> ApplicationResponse[tuple[dict[str, Any], ...]]:
        return failure_response("RESULT_ROWS_NOT_AVAILABLE", "P4-MSG-RESULT_ROWS_NOT_AVAILABLE", status_code=409)

    def compare_runs(self, left_run_id: str, right_run_id: str) -> ApplicationResponse[dict[str, Any]]:
        left = self.store.get_run(left_run_id)
        right = self.store.get_run(right_run_id)
        if left is None or right is None:
            return failure_response("NOT_FOUND", "P4-MSG-RUN_NOT_FOUND", status_code=404)
        comparable = left.condition_sha256 == right.condition_sha256
        return ApplicationResponse(
            200,
            {
                "left_run_id": left.run_id,
                "right_run_id": right.run_id,
                "comparable": comparable,
                "comparison_sha256": canonical_hash(
                    {"left": left_run_id, "right": right_run_id, "comparable": comparable}
                ),
            },
            correlation_id=self._correlation(),
        )

    def create_csv_job(self, command: CreateCsvJobCommand) -> ApplicationResponse[dict[str, Any]]:
        if not isinstance(command, CreateCsvJobCommand):
            return failure_response("TYPED_INPUT_INVALID", "P4-MSG-TYPED_INPUT_INVALID", status_code=422)
        result = self.store.get_run(command.source_run_id)
        if result is None or result.result is None:
            return failure_response("RESULT_NOT_COMMITTED", "P4-MSG-RESULT_NOT_COMMITTED", status_code=409)
        return failure_response(
            "CSV_WORKER_NOT_ENABLED_IN_P4_06", "P4-MSG-CSV_WORKER_NOT_ENABLED", status_code=423, recovery_required=True
        )

    def get_csv_job(self, *_: object) -> ApplicationResponse[dict[str, Any]]:
        return failure_response("CSV_JOB_NOT_AVAILABLE", "P4-MSG-CSV_JOB_NOT_AVAILABLE", status_code=404)

    def get_evidence(self, query: GetRunQuery | str) -> ApplicationResponse[dict[str, Any]]:
        run_response = self.get_run(query)
        if not run_response.ok or run_response.data is None:
            return ApplicationResponse(
                run_response.status_code, failure=run_response.failure, correlation_id=run_response.correlation_id
            )
        evidence = run_response.data.evidence
        if evidence is None:
            return failure_response(
                "EVIDENCE_INCOMPLETE", "P4-MSG-EVIDENCE_INCOMPLETE", status_code=423, recovery_required=True
            )
        return ApplicationResponse(200, asdict(evidence), correlation_id=self._correlation())

    def assess_holdout_reuse(self, run_id: str, holdout_plan_sha256: str) -> ApplicationResponse[dict[str, Any]]:
        del holdout_plan_sha256
        if self.store.get_run(run_id) is None:
            return failure_response("NOT_FOUND", "P4-MSG-RUN_NOT_FOUND", status_code=404)
        return failure_response("HOLDOUT_REUSE_BLOCKED", "P4-MSG-HOLDOUT_REUSE_BLOCKED", status_code=403)


def build_create_run_command(
    client_request_id: str,
    config: BacktestConfig,
    preflight_report: PreflightReport,
    *,
    run_kind: str = "SINGLE_BACKTEST",
) -> CreateRunCommand:
    if run_kind not in {"SINGLE_BACKTEST", "SWEEP_CHILD"}:
        raise ValueError("RUN_KIND_INVALID")
    return CreateRunCommand(client_request_id, run_kind, config, utc_now(), preflight_report.report_sha256)  # type: ignore[arg-type]

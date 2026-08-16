"""Canonical in-process P4 API facade.

HTTP paths listed in the design are projections only.  This facade is the
single local contract used by tests and, in P4-08, by a fixed local UI.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from typing import Any, Literal

from .contracts import (
    ApplicationResponse,
    BacktestConfig,
    CancelJobCommand,
    CreateCsvJobCommand,
    CreateRunCommand,
    FailureView,
    GetJobQuery,
    GetRunQuery,
    JobView,
    PageQuery,
    PreflightReport,
    ResumeJobCommand,
    RunView,
    StartJobCommand,
    failure_response,
    utc_now,
)
from .csv_job import atomic_csv_output
from .job_service import JobService
from .persistence import MetadataStore, PersistenceConflict
from .preflight import preflight_run
from .result_view import LocalResultArtifacts
from .run_service import RunService
from .sweep_service import SweepService, SweepView

API_INVENTORY = tuple(f"API-P4-{number:03d}" for number in range(1, 20))


class ProductApplicationApi:
    """P4 canonical operations with safe response objects."""

    def __init__(self, store: MetadataStore | None = None, *, artifacts: LocalResultArtifacts | None = None) -> None:
        self.store = store or MetadataStore()
        self.store.initialize()
        self.runs = RunService(self.store)
        self.jobs = JobService(self.store)
        self.sweeps = SweepService(self.store)
        self.artifacts = artifacts

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

    def resume_job(self, command: ResumeJobCommand) -> ApplicationResponse[JobView]:
        if not isinstance(command, ResumeJobCommand):
            return failure_response("TYPED_INPUT_INVALID", "P4-MSG-TYPED_INPUT_INVALID", status_code=422)
        try:
            job = self.store.resume_job(command, self._correlation())
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(
                code,
                f"P4-MSG-{code}",
                status_code=423 if code in {"CHECKPOINT_VERIFICATION_REQUIRED", "PROTECTED_INPUT_MISMATCH"} else 409,
                recovery_required=True,
            )
        return ApplicationResponse(202, job, correlation_id=self._correlation())

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
        if self.artifacts is None:
            return failure_response(
                "RESULT_ARTIFACT_READER_NOT_ENABLED", "P4-MSG-RESULT_ARTIFACT_READER_NOT_ENABLED", status_code=423
            )
        try:
            payload = self.artifacts.read(run_response.data.result)
        except (OSError, ValueError) as error:
            del error
            return failure_response(
                "RESULT_RECONCILIATION_REQUIRED",
                "P4-MSG-RESULT_RECONCILIATION_REQUIRED",
                status_code=423,
                recovery_required=True,
            )
        return ApplicationResponse(
            200,
            {
                "run_id": run_response.data.run_id,
                "metrics": payload["metrics"],
                "row_count": len(payload["rows"]),
                "result_reference": asdict(run_response.data.result),
            },
            correlation_id=self._correlation(),
        )

    def list_result_rows(self, query: GetRunQuery | str) -> ApplicationResponse[tuple[dict[str, Any], ...]]:
        run_response = self.get_run(query)
        if not run_response.ok or run_response.data is None:
            return ApplicationResponse(
                run_response.status_code, failure=run_response.failure, correlation_id=run_response.correlation_id
            )
        if run_response.data.result is None:
            return failure_response("RESULT_NOT_COMMITTED", "P4-MSG-RESULT_NOT_COMMITTED", status_code=409)
        if self.artifacts is None:
            return failure_response(
                "RESULT_ARTIFACT_READER_NOT_ENABLED", "P4-MSG-RESULT_ARTIFACT_READER_NOT_ENABLED", status_code=423
            )
        try:
            payload = self.artifacts.read(run_response.data.result)
        except (OSError, ValueError) as error:
            del error
            return failure_response(
                "RESULT_RECONCILIATION_REQUIRED",
                "P4-MSG-RESULT_RECONCILIATION_REQUIRED",
                status_code=423,
                recovery_required=True,
            )
        return ApplicationResponse(200, tuple(payload["rows"]), correlation_id=self._correlation())

    def compare_runs(self, left_run_id: str, right_run_id: str) -> ApplicationResponse[dict[str, Any]]:
        left = self.store.get_run(left_run_id)
        right = self.store.get_run(right_run_id)
        if left is None or right is None:
            return failure_response("NOT_FOUND", "P4-MSG-RUN_NOT_FOUND", status_code=404)
        if self.artifacts is not None:
            for candidate in (left, right):
                if candidate.result is None:
                    continue
                try:
                    self.artifacts.read(candidate.result)
                except (OSError, ValueError) as error:
                    del error
                    return failure_response(
                        "RESULT_RECONCILIATION_REQUIRED",
                        "P4-MSG-RESULT_RECONCILIATION_REQUIRED",
                        status_code=423,
                        recovery_required=True,
                    )
        comparable = left.condition_sha256 == right.condition_sha256
        return ApplicationResponse(
            200,
            {
                "left_run_id": left.run_id,
                "right_run_id": right.run_id,
                "comparable": comparable,
                "result_state": {
                    "left": "COMMITTED" if left.result else "NOT_COMMITTED",
                    "right": "COMMITTED" if right.result else "NOT_COMMITTED",
                },
            },
            correlation_id=self._correlation(),
        )

    def create_csv_job(self, command: CreateCsvJobCommand) -> ApplicationResponse[dict[str, Any]]:
        if not isinstance(command, CreateCsvJobCommand):
            return failure_response("TYPED_INPUT_INVALID", "P4-MSG-TYPED_INPUT_INVALID", status_code=422)
        if self.artifacts is None:
            return failure_response(
                "CSV_WORKER_NOT_ENABLED", "P4-MSG-CSV_WORKER_NOT_ENABLED", status_code=423, recovery_required=True
            )
        if not command.column_set or any(
            not isinstance(column, str) or not column or column.startswith("_") for column in command.column_set
        ):
            return failure_response("CSV_COLUMNS_INVALID", "P4-MSG-CSV_COLUMNS_INVALID", status_code=422)
        try:
            row, replay = self.store.create_csv_job(
                source_run_id=command.source_run_id,
                source_result_sha256=command.source_result_sha256,
                column_set=command.column_set,
                filter_payload_sha256=command.filter_payload_sha256,
                request_key=command.request_key,
                correlation_id=self._correlation(),
            )
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(code, f"P4-MSG-{code}", status_code=409)
        return ApplicationResponse(200 if replay else 202, row, correlation_id=self._correlation())

    def create_csv_job_for_rows(
        self,
        source_run_id: str,
        source_result_sha256: str,
        column_set: tuple[str, ...],
        filter_payload_sha256: str,
    ) -> ApplicationResponse[dict[str, Any]]:
        request_key = ":".join(("csv", source_run_id, ",".join(column_set), filter_payload_sha256))
        return self.create_csv_job(
            CreateCsvJobCommand(
                source_run_id,
                source_result_sha256,
                column_set,
                filter_payload_sha256,
                request_key,
            )
        )

    def get_csv_job(self, csv_job_id: str) -> ApplicationResponse[dict[str, Any]]:
        row = self.store.get_csv_job(csv_job_id)
        if row is None:
            return failure_response("CSV_JOB_NOT_FOUND", "P4-MSG-CSV_JOB_NOT_FOUND", status_code=404)
        if row["status"] == "COMPLETED" and self.artifacts is not None:
            try:
                relative = row["relative_output_ref"]
                path = (self.artifacts.root / relative).resolve()
                path.relative_to(self.artifacts.root)
                if not path.is_file():
                    raise ValueError("CSV_OUTPUT_MISSING")
            except (OSError, TypeError, ValueError) as error:
                code = str(error) if str(error).startswith("CSV_") else "CSV_OUTPUT_MISSING"
                return failure_response(code, f"P4-MSG-{code}", status_code=423, recovery_required=True)
        return ApplicationResponse(200, row, correlation_id=self._correlation())

    def run_csv_job(self, csv_job_id: str) -> ApplicationResponse[dict[str, Any]]:
        if self.artifacts is None:
            return failure_response("CSV_WORKER_NOT_ENABLED", "P4-MSG-CSV_WORKER_NOT_ENABLED", status_code=423)
        row = self.store.get_csv_job(csv_job_id)
        if row is None:
            return failure_response("CSV_JOB_NOT_FOUND", "P4-MSG-CSV_JOB_NOT_FOUND", status_code=404)
        if row["status"] == "COMPLETED":
            return self.get_csv_job(csv_job_id)
        source = self.store.get_run(row["source_run_id"])
        if source is None or source.result is None:
            return failure_response(
                "RESULT_NOT_COMMITTED",
                "P4-MSG-RESULT_NOT_COMMITTED",
                status_code=423,
                recovery_required=True,
            )
        try:
            payload = self.artifacts.read(source.result)
            columns = tuple(json.loads(row["column_set_json"]))
            if not columns or (payload["rows"] and any(column not in payload["rows"][0] for column in columns)):
                raise ValueError("CSV_COLUMNS_INVALID")
            relative_ref = f"csv/{csv_job_id}.csv"
            atomic_csv_output(self.artifacts.root, relative_ref, payload["rows"], columns)
            completed = self.store.complete_csv_job(
                csv_job_id,
                relative_output_ref=relative_ref,
                output_sha256=None,
                correlation_id=self._correlation(),
            )
        except (OSError, ValueError, TypeError, KeyError, PersistenceConflict) as error:
            code = str(error) if str(error) else "CSV_JOB_FAILED"
            if code == "CSV_OVERWRITE_FORBIDDEN":
                existing = self.store.get_csv_job(csv_job_id)
                if existing and existing["status"] == "COMPLETED":
                    return self.get_csv_job(csv_job_id)
            return failure_response(code, f"P4-MSG-{code}", status_code=423, recovery_required=True)
        return ApplicationResponse(200, completed, correlation_id=self._correlation())

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
        if self.artifacts is not None and run_response.data.result is not None:
            try:
                self.artifacts.read(run_response.data.result)
            except (OSError, ValueError) as error:
                del error
                return failure_response(
                    "EVIDENCE_RECONCILIATION_REQUIRED",
                    "P4-MSG-EVIDENCE_RECONCILIATION_REQUIRED",
                    status_code=423,
                    recovery_required=True,
                )
        return ApplicationResponse(200, asdict(evidence), correlation_id=self._correlation())

    def assess_holdout_reuse(self, run_id: str, holdout_plan_sha256: str) -> ApplicationResponse[dict[str, Any]]:
        try:
            assessment = self.store.record_holdout_assessment(
                source_run_id=run_id,
                holdout_plan_sha256=holdout_plan_sha256,
                correlation_id=self._correlation(),
            )
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(code, f"P4-MSG-{code}", status_code=404 if code == "RUN_NOT_FOUND" else 409)
        return ApplicationResponse(
            403,
            assessment,
            failure=FailureView("HOLDOUT_REUSE_BLOCKED", "P4-MSG-HOLDOUT_REUSE_BLOCKED"),
            correlation_id=self._correlation(),
        )


def build_create_run_command(
    client_request_id: str,
    config: BacktestConfig,
    preflight_report: PreflightReport,
    *,
    run_kind: Literal["SINGLE_BACKTEST", "SWEEP_CHILD"] = "SINGLE_BACKTEST",
) -> CreateRunCommand:
    if run_kind not in {"SINGLE_BACKTEST", "SWEEP_CHILD"}:
        raise ValueError("RUN_KIND_INVALID")
    return CreateRunCommand(client_request_id, run_kind, config, utc_now(), None)

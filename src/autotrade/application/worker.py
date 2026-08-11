"""Bounded local worker shell; it does not invent Core results."""

from __future__ import annotations

import uuid

from .contracts import FailureView, JobStatus, JobView
from .core_adapter import CoreAdapter, CoreExecutionNotEnabled, CoreExecutionStopped
from .evidence import evidence_reference
from .local_queue import LocalQueue
from .persistence import MetadataStore, PersistenceConflict
from .result_view import LocalResultArtifacts


class LocalWorker:
    def __init__(
        self,
        store: MetadataStore,
        *,
        worker_id: str,
        core_adapter: CoreAdapter | None = None,
        artifacts: LocalResultArtifacts | None = None,
    ) -> None:
        self.store = store
        self.queue = LocalQueue(store)
        self.worker_id = worker_id
        self.core_adapter = core_adapter
        self.artifacts = artifacts

    def run_once(self) -> JobView | None:
        job = self.queue.claim(self.worker_id)
        if job is None:
            return None
        current = self.store.get_job(job.job_id)
        if current is None:
            return self.store.mark_job_terminal(
                job.job_id,
                JobStatus.RECOVERY_REQUIRED,
                failure=FailureView(
                    "JOB_NOT_FOUND_AFTER_CLAIM",
                    "P4-MSG-JOB_NOT_FOUND_AFTER_CLAIM",
                    recovery_required=True,
                ),
            )
        if current.status == JobStatus.CANCEL_REQUESTED:
            return self.store.mark_job_terminal(
                job.job_id,
                JobStatus.STOPPED,
                failure=FailureView("CANCELLED_BEFORE_CORE", "P4-MSG-CANCELLED_BEFORE_CORE"),
            )
        if self.core_adapter is None or self.artifacts is None:
            failure = FailureView(
                "CORE_EXECUTION_NOT_ENABLED_IN_P4_06", "P4-MSG-CORE_EXECUTION_NOT_ENABLED", recovery_required=True
            )
            return self.store.mark_job_terminal(job.job_id, JobStatus.RECOVERY_REQUIRED, failure=failure)
        try:
            output = self.core_adapter.execute(job)
            run = self.store.get_run(job.run_id)
            if run is None:
                raise PersistenceConflict("RUN_NOT_FOUND")
            reference = self.artifacts.publish(job.run_id, output, run.manifest_sha256)
            evidence = evidence_reference(
                job.run_id,
                f"evidence/{job.run_id}",
                {
                    "result.json": reference.result_sha256,
                    "result.commit.json": reference.commit_marker_sha256,
                    **output.evidence_files,
                },
            )
            return self.store.complete_job_with_result(
                job.job_id,
                reference,
                evidence,
                correlation_id=f"corr-worker-{uuid.uuid4().hex}",
            )
        except CoreExecutionNotEnabled:
            failure = FailureView(
                "CORE_EXECUTION_NOT_ENABLED", "P4-MSG-CORE_EXECUTION_NOT_ENABLED", recovery_required=True
            )
            return self.store.mark_job_terminal(job.job_id, JobStatus.RECOVERY_REQUIRED, failure=failure)
        except CoreExecutionStopped as error:
            failure = FailureView("CORE_RESULT_STOPPED", "P4-MSG-CORE_RESULT_STOPPED", recovery_required=False)
            del error
            return self.store.mark_job_terminal(job.job_id, JobStatus.STOPPED, failure=failure)
        except (OSError, PersistenceConflict, RuntimeError, TypeError, ValueError) as error:
            failure = FailureView("WORKER_EXECUTION_FAILED", "P4-MSG-WORKER_EXECUTION_FAILED", recovery_required=True)
            del error
            return self.store.mark_job_terminal(job.job_id, JobStatus.RECOVERY_REQUIRED, failure=failure)

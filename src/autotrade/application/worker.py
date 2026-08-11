"""Bounded local worker shell; it does not invent Core results."""

from __future__ import annotations

from .contracts import FailureView, JobStatus, JobView
from .core_adapter import CoreAdapter, CoreExecutionNotEnabled
from .local_queue import LocalQueue
from .persistence import MetadataStore, PersistenceConflict


class LocalWorker:
    def __init__(self, store: MetadataStore, *, worker_id: str, core_adapter: CoreAdapter | None = None) -> None:
        self.store = store
        self.queue = LocalQueue(store)
        self.worker_id = worker_id
        self.core_adapter = core_adapter

    def run_once(self) -> JobView | None:
        job = self.queue.claim(self.worker_id)
        if job is None:
            return None
        if self.core_adapter is None:
            failure = FailureView(
                "CORE_EXECUTION_NOT_ENABLED_IN_P4_06", "P4-MSG-CORE_EXECUTION_NOT_ENABLED", recovery_required=True
            )
            return self.store.mark_job_terminal(job.job_id, JobStatus.RECOVERY_REQUIRED, failure=failure)
        try:
            self.core_adapter.execute(job)
        except CoreExecutionNotEnabled:
            failure = FailureView(
                "CORE_EXECUTION_NOT_ENABLED", "P4-MSG-CORE_EXECUTION_NOT_ENABLED", recovery_required=True
            )
            return self.store.mark_job_terminal(job.job_id, JobStatus.RECOVERY_REQUIRED, failure=failure)
        except (PersistenceConflict, RuntimeError) as error:
            failure = FailureView("WORKER_EXECUTION_FAILED", "P4-MSG-WORKER_EXECUTION_FAILED", recovery_required=True)
            del error
            return self.store.mark_job_terminal(job.job_id, JobStatus.RECOVERY_REQUIRED, failure=failure)
        return self.store.mark_job_terminal(job.job_id, JobStatus.SUCCEEDED)

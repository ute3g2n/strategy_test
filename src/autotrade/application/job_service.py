"""Job/queue application operations with explicit expected-revision checks."""

from __future__ import annotations

from .contracts import (
    ApplicationResponse,
    CancelJobCommand,
    JobView,
    StartJobCommand,
    failure_response,
)
from .persistence import MetadataStore, PersistenceConflict


class JobService:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store

    def start_job(self, command: StartJobCommand, *, correlation_id: str) -> ApplicationResponse[JobView]:
        try:
            job, _ = self.store.start_job(command, correlation_id)
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(
                code,
                f"P4-MSG-{code}",
                status_code=409,
                recovery_required=code in {"STALE_REVISION", "QUEUE_RUN_STATE_MISMATCH"},
            )
        return ApplicationResponse(202, job, correlation_id=correlation_id)

    def cancel_job(self, command: CancelJobCommand, *, correlation_id: str) -> ApplicationResponse[JobView]:
        try:
            job = self.store.cancel_job(command, correlation_id)
        except PersistenceConflict as error:
            code = str(error)
            return failure_response(code, f"P4-MSG-{code}", status_code=409, recovery_required=code == "STALE_REVISION")
        return ApplicationResponse(200, job, correlation_id=correlation_id)

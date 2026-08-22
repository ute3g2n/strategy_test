"""Run creation service; the operation is metadata-only until a worker claims a Job."""

from __future__ import annotations

from .config import condition_sha256
from .contracts import ApplicationResponse, CreateRunCommand, PreflightReport, RunView, failure_response
from .persistence import MetadataStore, PersistenceConflict
from .preflight import preflight_run


class RunService:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store

    def create_run(
        self, command: CreateRunCommand, preflight: PreflightReport, *, correlation_id: str
    ) -> ApplicationResponse[RunView]:
        del preflight
        # Recompute at the persistence boundary so a stale or forged report
        # cannot bypass timeframe/UTC validation.
        fresh_preflight = preflight_run(command.config)
        if fresh_preflight.status != "PASS":
            return failure_response("PREFLIGHT_REQUIRED", "P4-MSG-PREFLIGHT_REQUIRED", status_code=403)
        try:
            view, _ = self.store.create_run(command, correlation_id)
        except PersistenceConflict as error:
            code = str(error)
            status = 409 if "FINGERPRINT" in code else 422
            return failure_response(code, f"P4-MSG-{code}", status_code=status)
        return ApplicationResponse(201, view, correlation_id=correlation_id)

    @staticmethod
    def condition_sha256(command: CreateRunCommand) -> str:
        return condition_sha256(command.config)

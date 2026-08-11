"""Run creation service; the operation is metadata-only until a worker claims a Job."""

from __future__ import annotations

from .config import condition_sha256
from .contracts import ApplicationResponse, CreateRunCommand, PreflightReport, RunView, failure_response
from .persistence import MetadataStore, PersistenceConflict


class RunService:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store

    def create_run(
        self, command: CreateRunCommand, preflight: PreflightReport, *, correlation_id: str
    ) -> ApplicationResponse[RunView]:
        if preflight.status != "PASS" or command.preflight_report_sha256 != preflight.report_sha256:
            return failure_response("PREFLIGHT_REQUIRED", "P4-MSG-PREFLIGHT_REQUIRED", status_code=403)
        if command.config.config_sha256 != command.config.config_sha256:
            return failure_response("CONFIG_HASH_MISMATCH", "P4-MSG-CONFIG_HASH_MISMATCH", status_code=422)
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

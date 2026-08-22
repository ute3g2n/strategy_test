"""Run creation service; the operation is metadata-only until a worker claims a Job."""

from __future__ import annotations

import threading
from collections.abc import Mapping

from .config import condition_sha256
from .contracts import ApplicationResponse, CreateRunCommand, PreflightReport, RunView, failure_response
from .persistence import MetadataStore, PersistenceConflict
from .preflight import preflight_run, preflight_run_for_command

_CANCELLABLE_RUN_STATES = frozenset({"QUEUED", "RUNNING"})
_OPERATION_IN_FLIGHT_STATES = frozenset({"STOP_REQUESTED"})
_TERMINAL_RUN_STATES = frozenset(
    {
        "CANCELLED",
        "FAILED",
        "SUCCEEDED",
        "PARTIAL_FAILED",
        "RECOVERY_REQUIRED",
        "LEGACY_RESULT_ONLY",
        "STOPPED",
    }
)


class OperationGuard:
    """Serialize Run operations and restore one durable operation generation."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sequence = 0
        self._runs: dict[str, dict[str, object]] = {}
        self._audits: dict[str, dict[str, object]] = {}
        self._retired_tokens: dict[str, set[str]] = {}

    @staticmethod
    def _text(value: object, default: str = "") -> str:
        return value.strip() if isinstance(value, str) else default

    @staticmethod
    def _revision(value: object, default: int = 0) -> int | None:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value

    def _next_audit(
        self,
        *,
        run_id: str,
        request_id: str,
        operation_token: str,
        status_before: str,
        status_after: str,
        error_code: str | None,
        actor: str,
        origin_screen: str,
        reason: str,
    ) -> tuple[str, dict[str, object]]:
        self._sequence += 1
        audit_id = f"AUDIT-RUN-CANCEL-{self._sequence:06d}"
        audit: dict[str, object] = {
            "audit_id": audit_id,
            "aggregate_kind": "RUN",
            "aggregate_id": run_id,
            "event_type": "RUN_CANCEL_ACCEPTED" if error_code is None else "RUN_CANCEL_REJECTED",
            "request_id": request_id,
            "operation_token": operation_token,
            "actor": actor,
            "origin_screen": origin_screen,
            "reason": reason,
            "status_before": status_before,
            "status_after": status_after,
            "error_code": error_code,
        }
        self._audits[audit_id] = dict(audit)
        return audit_id, audit

    def _result(
        self,
        *,
        run_id: str,
        request_id: str,
        operation_token: str,
        status_before: str,
        status_after: str,
        accepted: bool,
        error_code: str | None,
        audit_id: str,
        audit: Mapping[str, object],
        revision_before: int,
        revision_after: int,
        replayed: bool = False,
    ) -> dict[str, object]:
        return {
            "run_id": run_id,
            "request_id": request_id,
            "operation_token": operation_token,
            "status_before": status_before,
            "status_after": status_after,
            "accepted": accepted,
            "error_code": error_code,
            "audit_id": audit_id,
            "audit": dict(audit),
            "revision_before": revision_before,
            "revision_after": revision_after,
            "replayed": replayed,
        }

    def _invalid_request(self, request: Mapping[str, object] | object, error_code: str) -> dict[str, object]:
        raw_run_id = request.get("run_id") if isinstance(request, Mapping) else None
        raw_request_id = request.get("request_id") if isinstance(request, Mapping) else None
        raw_token = request.get("operation_token") if isinstance(request, Mapping) else None
        run_id = self._text(raw_run_id, "UNKNOWN")
        request_id = self._text(raw_request_id, "UNKNOWN")
        operation_token = self._text(raw_token, "UNKNOWN")
        actor = self._text(request.get("actor"), "UNKNOWN") if isinstance(request, Mapping) else "UNKNOWN"
        origin = self._text(request.get("origin_screen"), "UNKNOWN") if isinstance(request, Mapping) else "UNKNOWN"
        reason = self._text(request.get("reason"), "UNSPECIFIED") if isinstance(request, Mapping) else "UNSPECIFIED"
        audit_id, audit = self._next_audit(
            run_id=run_id,
            request_id=request_id,
            operation_token=operation_token,
            status_before="UNKNOWN",
            status_after="UNKNOWN",
            error_code=error_code,
            actor=actor,
            origin_screen=origin,
            reason=reason,
        )
        return self._result(
            run_id=run_id,
            request_id=request_id,
            operation_token=operation_token,
            status_before="UNKNOWN",
            status_after="UNKNOWN",
            accepted=False,
            error_code=error_code,
            audit_id=audit_id,
            audit=audit,
            revision_before=0,
            revision_after=0,
        )

    def request_run_cancel(
        self,
        request: Mapping[str, object] | object,
        *,
        server_state: str | None = None,
        server_revision: int | None = None,
    ) -> dict[str, object]:
        """Handle one cancel request without allowing a second state change."""

        if not isinstance(request, Mapping):
            with self._lock:
                return self._invalid_request(request, "INVALID_REQUEST")

        if server_state is not None:
            request = dict(request)
            request["current_state"] = server_state
            if server_revision is not None:
                request["current_revision"] = server_revision
                request["expected_revision"] = server_revision

        run_id = self._text(request.get("run_id"))
        operation_token = self._text(request.get("operation_token"))
        request_id = self._text(request.get("request_id"), operation_token)
        current_state = self._text(request.get("current_state", request.get("state", request.get("run_state")))).upper()
        actor = self._text(request.get("actor"), "UNKNOWN")
        origin_screen = self._text(request.get("origin_screen"), "UNKNOWN")
        reason = self._text(request.get("reason"), "UNSPECIFIED")
        current_revision = self._revision(request.get("current_revision", request.get("revision", 0)), default=0)
        expected_revision = (
            self._revision(request.get("expected_revision"), default=0) if "expected_revision" in request else None
        )

        with self._lock:
            if not run_id or not operation_token or not request_id:
                return self._invalid_request(request, "INVALID_REQUEST")
            if (
                current_state not in _CANCELLABLE_RUN_STATES
                and current_state not in _OPERATION_IN_FLIGHT_STATES
                and current_state not in _TERMINAL_RUN_STATES
            ):
                return self._invalid_request(request, "STATE_INVALID")
            if current_revision is None or expected_revision is None and "expected_revision" in request:
                return self._invalid_request(request, "REVISION_INVALID")
            if expected_revision is not None and current_revision != expected_revision:
                audit_id, audit = self._next_audit(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=current_state,
                    error_code="REVISION_CONFLICT",
                    actor=actor,
                    origin_screen=origin_screen,
                    reason=reason,
                )
                return self._result(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=current_state,
                    accepted=False,
                    error_code="REVISION_CONFLICT",
                    audit_id=audit_id,
                    audit=audit,
                    revision_before=current_revision,
                    revision_after=current_revision,
                )

            if operation_token in self._retired_tokens.get(run_id, set()):
                audit_id, audit = self._next_audit(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=current_state,
                    error_code="STALE_OPERATION",
                    actor=actor,
                    origin_screen=origin_screen,
                    reason=reason,
                )
                return self._result(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=current_state,
                    accepted=False,
                    error_code="STALE_OPERATION",
                    audit_id=audit_id,
                    audit=audit,
                    revision_before=current_revision,
                    revision_after=current_revision,
                )

            existing = self._runs.get(run_id)
            if existing is not None:
                stored_audit_id = str(existing["audit_id"])
                stored_audit = self._audits[stored_audit_id]
                stored_token = existing["operation_token"]
                stored_result = existing["result"]
                assert isinstance(stored_token, str)
                assert isinstance(stored_result, Mapping)
                if operation_token == stored_token:
                    stored_revision = existing["revision_after"]
                    assert isinstance(stored_revision, int)
                    stored_status = self._text(stored_result.get("status_after"), "UNKNOWN")
                    stored_error = "ALREADY_CANCELLED" if stored_status == "CANCELLED" else "OPERATION_IN_FLIGHT"
                    replay_result = self._result(
                        run_id=run_id,
                        request_id=request_id,
                        operation_token=operation_token,
                        status_before=stored_status,
                        status_after=stored_status,
                        accepted=False,
                        error_code=stored_error,
                        audit_id=stored_audit_id,
                        audit=stored_audit,
                        revision_before=stored_revision,
                        revision_after=stored_revision,
                        replayed=True,
                    )
                    replay_result["prior_result"] = dict(stored_result)
                    return replay_result
            if (
                current_state in _CANCELLABLE_RUN_STATES or current_state in _OPERATION_IN_FLIGHT_STATES
            ) and existing is not None:
                audit_id = str(existing["audit_id"])
                audit = self._audits[audit_id]
                stored_revision = existing["revision_after"]
                stored_token = existing["operation_token"]
                stored_result = existing["result"]
                assert isinstance(stored_revision, int)
                assert isinstance(stored_token, str)
                assert isinstance(stored_result, Mapping)
                stored_status = self._text(stored_result.get("status_after"), "UNKNOWN")
                stored_error = "ALREADY_CANCELLED" if stored_status == "CANCELLED" else "OPERATION_IN_FLIGHT"
                replay_result = self._result(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=stored_status,
                    status_after=stored_status,
                    accepted=False,
                    error_code=stored_error,
                    audit_id=audit_id,
                    audit=audit,
                    revision_before=stored_revision,
                    revision_after=stored_revision,
                    replayed=operation_token == stored_token,
                )
                # The visible contract rejects a duplicate request, while
                # exposing the persisted first outcome for deterministic
                # client reconciliation. It must never create a new audit
                # or revision.
                replay_result["prior_result"] = dict(stored_result)
                return replay_result

            if current_state in _CANCELLABLE_RUN_STATES:
                requested_status = "CANCELLED" if current_state == "QUEUED" else "STOP_REQUESTED"
                audit_id, audit = self._next_audit(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=requested_status,
                    error_code=None,
                    actor=actor,
                    origin_screen=origin_screen,
                    reason=reason,
                )
                result = self._result(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=requested_status,
                    accepted=True,
                    error_code=None,
                    audit_id=audit_id,
                    audit=audit,
                    revision_before=current_revision,
                    revision_after=current_revision + 1,
                )
                self._runs[run_id] = {
                    "operation_token": operation_token,
                    "audit_id": audit_id,
                    "revision_after": current_revision + 1,
                    "result": dict(result),
                }
                return result

            if current_state in _OPERATION_IN_FLIGHT_STATES:
                audit_id, audit = self._next_audit(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=current_state,
                    error_code="OPERATION_IN_FLIGHT",
                    actor=actor,
                    origin_screen=origin_screen,
                    reason=reason,
                )
                return self._result(
                    run_id=run_id,
                    request_id=request_id,
                    operation_token=operation_token,
                    status_before=current_state,
                    status_after=current_state,
                    accepted=False,
                    error_code="OPERATION_IN_FLIGHT",
                    audit_id=audit_id,
                    audit=audit,
                    revision_before=current_revision,
                    revision_after=current_revision,
                )

            audit_id, audit = self._next_audit(
                run_id=run_id,
                request_id=request_id,
                operation_token=operation_token,
                status_before=current_state,
                status_after=current_state,
                error_code="TERMINAL_STATE",
                actor=actor,
                origin_screen=origin_screen,
                reason=reason,
            )
            return self._result(
                run_id=run_id,
                request_id=request_id,
                operation_token=operation_token,
                status_before=current_state,
                status_after=current_state,
                accepted=False,
                error_code="TERMINAL_STATE",
                audit_id=audit_id,
                audit=audit,
                revision_before=current_revision,
                revision_after=current_revision,
            )

    def audit_log(self, run_id: str | None = None) -> tuple[dict[str, object], ...]:
        with self._lock:
            values = tuple(
                dict(item) for item in self._audits.values() if run_id is None or item["aggregate_id"] == run_id
            )
        return values

    def export_run_operation(self, run_id: str) -> dict[str, object] | None:
        """Return the server-owned operation result for durable Run storage."""

        with self._lock:
            existing = self._runs.get(run_id)
            if existing is None:
                return None
            result = existing.get("result")
            if not isinstance(result, Mapping):
                return None
            return dict(result)

    def restore_run_operation(self, run_id: str, record: Mapping[str, object]) -> None:
        """Hydrate a previously persisted operation without creating an audit."""

        if not run_id or not isinstance(record, Mapping) or record.get("run_id") != run_id:
            raise ValueError("OPERATION_RECORD_INVALID")
        operation_token = record.get("operation_token")
        request_id = record.get("request_id")
        audit_id = record.get("audit_id")
        audit = record.get("audit")
        status_before = record.get("status_before")
        status_after = record.get("status_after")
        revision_before = record.get("revision_before")
        revision_after = record.get("revision_after")
        if (
            not isinstance(operation_token, str)
            or not operation_token
            or not isinstance(request_id, str)
            or not request_id
            or not isinstance(audit_id, str)
            or not audit_id
            or not isinstance(audit, Mapping)
            or record.get("accepted") is not True
            or record.get("replayed") is not False
            or record.get("error_code") is not None
            or status_before not in _CANCELLABLE_RUN_STATES
            or status_after != ("CANCELLED" if status_before == "QUEUED" else "STOP_REQUESTED")
            or not isinstance(revision_before, int)
            or isinstance(revision_before, bool)
            or revision_before < 0
            or not isinstance(revision_after, int)
            or isinstance(revision_after, bool)
            or revision_after != revision_before + 1
            or not audit_id.startswith("AUDIT-RUN-CANCEL-")
            or not audit_id.removeprefix("AUDIT-RUN-CANCEL-").isdigit()
        ):
            raise ValueError("OPERATION_RECORD_INVALID")
        audit_fields = {
            "audit_id": audit_id,
            "aggregate_kind": "RUN",
            "aggregate_id": run_id,
            "event_type": "RUN_CANCEL_ACCEPTED",
            "request_id": request_id,
            "operation_token": operation_token,
            "status_before": status_before,
            "status_after": status_after,
            "error_code": None,
        }
        if any(audit.get(key) != value for key, value in audit_fields.items()):
            raise ValueError("OPERATION_RECORD_INVALID")
        for field in ("actor", "origin_screen", "reason"):
            if not isinstance(audit.get(field), str) or not audit[field]:
                raise ValueError("OPERATION_RECORD_INVALID")
        if any(not isinstance(record.get(field), str) or not record[field] for field in ("run_id",)):
            raise ValueError("OPERATION_RECORD_INVALID")
        with self._lock:
            existing = self._runs.get(run_id)
            if existing is not None:
                current = existing.get("result")
                if isinstance(current, Mapping) and dict(current) == dict(record):
                    return
                raise ValueError("OPERATION_RECORD_CONFLICT")
            existing_audit = self._audits.get(audit_id)
            if existing_audit is not None and existing_audit != dict(audit):
                raise ValueError("OPERATION_RECORD_CONFLICT")
            restored_audit = dict(audit)
            self._audits[audit_id] = restored_audit
            self._runs[run_id] = {
                "operation_token": operation_token,
                "audit_id": audit_id,
                "revision_after": revision_after,
                "result": dict(record),
            }
            prefix = "AUDIT-RUN-CANCEL-"
            suffix = audit_id[len(prefix) :] if audit_id.startswith(prefix) else ""
            if suffix.isdigit():
                self._sequence = max(self._sequence, int(suffix))

    def rollback_run_operation(self, run_id: str, record: Mapping[str, object]) -> None:
        """Remove an accepted operation when its owning Run could not persist."""

        with self._lock:
            existing = self._runs.get(run_id)
            if existing is None or existing.get("result") != dict(record):
                return
            audit_id = existing.get("audit_id")
            self._runs.pop(run_id, None)
            if isinstance(audit_id, str) and not any(
                value.get("audit_id") == audit_id for value in self._runs.values()
            ):
                self._audits.pop(audit_id, None)

    def restore_retired_operation_tokens(self, run_id: str, tokens: object) -> None:
        """Restore operation tokens that must remain stale after a Run resume."""

        if not run_id or not isinstance(tokens, (list, tuple, set)):
            raise ValueError("RETIRED_OPERATION_RECORD_INVALID")
        parsed = {token for token in tokens if isinstance(token, str) and token}
        if len(parsed) != len(tokens):
            raise ValueError("RETIRED_OPERATION_RECORD_INVALID")
        with self._lock:
            self._retired_tokens[run_id] = parsed

    def reset_for_local_test(self) -> None:
        """Reset only this local in-memory guard; no persisted data is touched."""

        with self._lock:
            self._sequence = 0
            self._runs.clear()
            self._audits.clear()
            self._retired_tokens.clear()

    def reset_run(self, run_id: str) -> None:
        """Start a new operation generation for one locally resumed Run."""

        with self._lock:
            existing = self._runs.pop(run_id, None)
            if existing is not None:
                token = existing.get("operation_token")
                if isinstance(token, str) and token:
                    self._retired_tokens.setdefault(run_id, set()).add(token)


_DEFAULT_OPERATION_GUARD = OperationGuard()


def request_run_cancel(request: Mapping[str, object] | object) -> dict[str, object]:
    """Shared module-level cancel entry point used by all three screens."""

    return _DEFAULT_OPERATION_GUARD.request_run_cancel(request)


def reset_run_operation_guard() -> None:
    """Reset the local contract guard for isolated tests only."""

    _DEFAULT_OPERATION_GUARD.reset_for_local_test()


class RunService:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store
        self.operation_guard = OperationGuard()

    def request_run_cancel(
        self,
        request: Mapping[str, object] | object,
        *,
        server_state: str | None = None,
        server_revision: int | None = None,
    ) -> dict[str, object]:
        """Expose the same OperationGuard through an application service."""

        return self.operation_guard.request_run_cancel(
            request,
            server_state=server_state,
            server_revision=server_revision,
        )

    def create_run(
        self, command: CreateRunCommand, preflight: PreflightReport, *, correlation_id: str
    ) -> ApplicationResponse[RunView]:
        del preflight
        # Recompute at the persistence boundary so a stale or forged report
        # cannot bypass timeframe/UTC validation.
        fresh_preflight = preflight_run(command.config)
        if fresh_preflight.status != "PASS":
            return failure_response("PREFLIGHT_REQUIRED", "P4-MSG-PREFLIGHT_REQUIRED", status_code=403)
        if command.config.unit_key.timeframe in {"15m", "30m", "1h", "4h", "1d"}:
            strict_result = preflight_run_for_command(command.config, command.preflight_input)
            if strict_result.get("decision") == "REJECT":
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

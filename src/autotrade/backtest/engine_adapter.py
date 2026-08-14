"""SDK-less EngineAdapter boundary and fail-closed parity checks.

P3-07 deliberately has no vendor engine dependency.  The Fake adapter consumes
the Core reference result that was already produced by the typed Backtest Core;
it never imports or invokes Strategy a second time.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .contracts import (
    BacktestFailure,
    EngineFailure,
    EngineIdentity,
    EngineRunRequest,
    EngineRunResult,
    ExperimentManifest,
)

_IDENTITY_FIELDS = (
    "engine_kind",
    "engine_version",
    "distribution_source",
    "artifact_sha256_or_oci_digest",
    "adapter_name",
    "adapter_version",
    "adapter_artifact_sha256",
    "runtime_kind",
    "runtime_version",
    "execution_mode",
)
_LEGACY_IDENTITY_FIELDS = {
    "engine",
    "version",
    "distribution_source",
    "artifact_digest",
    "adapter_name",
    "adapter_version",
    "adapter_artifact_digest",
    "runtime_kind",
    "runtime_version",
    "execution_mode",
}
_PARITY_FIELDS = (
    "signal_sha256",
    "directive_sha256",
    "fill_sha256",
    "state_sha256",
    "result_sha256",
)
_ZERO_HASH = "sha256:" + "0" * 64


def _stopped(reason: str, *, detail: str | None = None, parity_status: str = "NOT_COMPARED") -> dict[str, Any]:
    result: dict[str, Any] = {"status": "STOPPED", "reason": reason}
    if detail:
        result["detail"] = detail
    return result


def reject_offline_violation(value: dict[str, Any]) -> dict[str, Any]:
    """Retain the legacy predicate while refusing a caller-only false value."""

    if not isinstance(value, dict) or value.get("outbound_attempt") is not True:
        return _stopped("OFFLINE_PREFLIGHT_UNPROVEN")
    return _stopped("OFFLINE_POLICY_VIOLATION")


def reject_unpinned_engine(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or type(value.get("oci_tag_only")) is not bool:
        return _stopped("ENGINE_IDENTITY_UNPINNED")
    return _stopped("ENGINE_IDENTITY_UNPINNED") if value["oci_tag_only"] else {"status": "PASS"}


def validate_engine_identity(value: dict[str, Any]) -> dict[str, Any]:
    """Validate the old mapping boundary without accepting partial identity."""

    if not isinstance(value, dict) or set(value) != _LEGACY_IDENTITY_FIELDS:
        return _stopped("ENGINE_IDENTITY_UNPINNED")
    if any(type(value.get(key)) is not str for key in _LEGACY_IDENTITY_FIELDS):
        return _stopped("ENGINE_IDENTITY_UNPINNED")
    if any(value[key] != "ENGINE_NOT_USED" for key in _LEGACY_IDENTITY_FIELDS):
        return _stopped("ENGINE_IDENTITY_UNPINNED")
    return {"status": "PASS"}


def _identity_mapping(value: object) -> dict[str, Any] | None:
    if isinstance(value, EngineIdentity):
        return {field: getattr(value, field) for field in _IDENTITY_FIELDS}
    if isinstance(value, Mapping):
        return dict(value)
    return None


def validate_typed_engine_identity(identity: object, manifest: object) -> BacktestFailure | None:
    """Return a stable failure unless the complete P3-07 identity is unused."""

    mapped = _identity_mapping(identity)
    if mapped is None or set(mapped) != set(_IDENTITY_FIELDS):
        return BacktestFailure("ENGINE_IDENTITY_UNPINNED")
    if any(type(mapped[field]) is not str for field in _IDENTITY_FIELDS):
        return BacktestFailure("ENGINE_IDENTITY_UNPINNED")
    if any(mapped[field] != "ENGINE_NOT_USED" for field in _IDENTITY_FIELDS):
        return BacktestFailure("ENGINE_IDENTITY_UNPINNED")
    if not isinstance(manifest, ExperimentManifest):
        return BacktestFailure("ENGINE_IDENTITY_UNPINNED")
    manifest_identity = _identity_mapping(manifest.engine_identity)
    if manifest_identity != mapped:
        return BacktestFailure("ENGINE_IDENTITY_UNPINNED")
    return None


def reject_engine_sdk_leak(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or type(value.get("sdk_type_in_public_dto")) is not bool:
        return {"status": "STOPPED"}
    return {"status": "STOPPED"} if value["sdk_type_in_public_dto"] else {"status": "PASS"}


def _empty_result(
    failure: EngineFailure | BacktestFailure,
    *,
    parity_status: str = "NOT_COMPARED",
    reference: EngineRunResult | None = None,
) -> EngineRunResult:
    return EngineRunResult(
        status="STOPPED",
        signal_sha256=reference.signal_sha256 if reference else _ZERO_HASH,
        directive_sha256=reference.directive_sha256 if reference else _ZERO_HASH,
        fill_sha256=reference.fill_sha256 if reference else _ZERO_HASH,
        state_sha256=reference.state_sha256 if reference else _ZERO_HASH,
        result_sha256=reference.result_sha256 if reference else _ZERO_HASH,
        engine_trace_sha256=reference.engine_trace_sha256 if reference else _ZERO_HASH,
        parity_status=parity_status,  # type: ignore[arg-type]
        failure=failure,
    )


def compare_engine_parity(reference: EngineRunResult, candidate: EngineRunResult) -> EngineRunResult:
    """Compare only the ordered Core semantic hashes and reject any mismatch."""

    if not isinstance(reference, EngineRunResult) or not isinstance(candidate, EngineRunResult):
        return _empty_result(EngineFailure("ENGINE_PARITY_MISMATCH", "typed result required"), parity_status="MISMATCH")
    if reference.status != "PASS" or candidate.status != "PASS":
        return _empty_result(
            EngineFailure("ENGINE_PARITY_MISMATCH", "only successful results are comparable"),
            parity_status="MISMATCH",
            reference=reference,
        )
    if any(getattr(reference, field) != getattr(candidate, field) for field in _PARITY_FIELDS):
        return _empty_result(EngineFailure("ENGINE_PARITY_MISMATCH"), parity_status="MISMATCH", reference=candidate)
    return replace(candidate, status="PASS", parity_status="MATCH", failure=None)


class FakeEngineAdapter:
    """A no-SDK adapter that compares a precomputed Core reference exactly once."""

    def __init__(
        self,
        *,
        reference_result: EngineRunResult | None = None,
        candidate_result: EngineRunResult | None = None,
    ) -> None:
        self._reference_result = reference_result
        self._candidate_result = candidate_result

    def validate_identity(self, identity: EngineIdentity, manifest: ExperimentManifest) -> BacktestFailure | None:
        return validate_typed_engine_identity(identity, manifest)

    def run(self, request: EngineRunRequest) -> EngineRunResult:
        if not isinstance(request, EngineRunRequest):
            return _empty_result(EngineFailure("TYPED_ENGINE_REQUEST_REQUIRED"))
        failure = self.validate_identity(request.engine_identity, request.manifest)
        if failure is not None:
            return _empty_result(EngineFailure(failure.reason, failure.detail))
        if request.run_id != request.manifest.run_id or request.input_sha256 != request.manifest.input_sha256:
            return _empty_result(EngineFailure("ENGINE_REQUEST_BINDING_MISMATCH"))
        if self._reference_result is None:
            return _empty_result(EngineFailure("CORE_REFERENCE_REQUIRED"))
        candidate = self._candidate_result if self._candidate_result is not None else self._reference_result
        return compare_engine_parity(self._reference_result, candidate)

    def normalize_failure(self, raw_code: str) -> BacktestFailure:
        if type(raw_code) is not str or not raw_code:
            return BacktestFailure("ENGINE_FAILURE_UNNORMALIZED")
        return BacktestFailure(raw_code)


def run_fake_engine_adapter(value: dict[str, Any]) -> dict[str, Any]:
    """Legacy hostile-case entry point for the SDK-free adapter surface."""

    if not isinstance(value, dict) or type(value.get("sdk_imports")) is not int or value["sdk_imports"] < 0:
        return _stopped("ENGINE_SDK_LEAK")
    if not {"request_type", "core_reference_sha256"}.issubset(value):
        return _stopped("ENGINE_IDENTITY_UNPINNED")
    return {"status": "PASS", "common_dto_only": True} if value["sdk_imports"] == 0 else _stopped("ENGINE_SDK_LEAK")


__all__ = [
    "FakeEngineAdapter",
    "compare_engine_parity",
    "reject_engine_sdk_leak",
    "reject_offline_violation",
    "reject_unpinned_engine",
    "run_fake_engine_adapter",
    "validate_engine_identity",
    "validate_typed_engine_identity",
]

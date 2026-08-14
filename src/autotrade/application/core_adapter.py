"""Narrow adapter boundary for the frozen Backtest Core.

P4-06 never invokes this adapter.  P4-07 may provide an approved adapter that
converts typed Application requests to the existing Core contract exactly once.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

from autotrade.backtest.contracts import BacktestRunRequest, BacktestRunResult
from autotrade.backtest.runner import BacktestRunner

from .contracts import is_sha256
from .result_view import MetricSet


class CoreExecutionNotEnabled(RuntimeError):
    """Raised when a worker tries to execute without an approved Core adapter."""


class CoreExecutionStopped(RuntimeError):
    """Raised when the frozen Core returns a fail-closed STOPPED result."""


@dataclass(frozen=True)
class CoreExecutionOutput:
    """The narrow, immutable projection accepted from the frozen Core.

    The application writes this projection to its separate result-file
    boundary.  It never stores the result body in the metadata database.
    """

    metrics: MetricSet
    rows: tuple[Mapping[str, str], ...]
    evidence_files: Mapping[str, str]
    core_result_sha256: str | None = None


class CoreAdapter(Protocol):
    def execute(self, request: object) -> CoreExecutionOutput: ...


class FrozenCoreAdapter:
    """One-call adapter around an explicitly supplied frozen-Core callable.

    P4 does not construct a Core request from untrusted values and does not
    modify Core code.  A caller must intentionally provide the approved
    bridge; otherwise execution is fail-closed.  Reusing the adapter for a
    second call is rejected to prevent duplicate publication.
    """

    def __init__(self, execute_once: Callable[[object], CoreExecutionOutput] | None = None) -> None:
        self._execute_once = execute_once
        self.execution_count = 0

    def execute(self, request: object) -> CoreExecutionOutput:
        if self._execute_once is None:
            raise CoreExecutionNotEnabled("CORE_EXECUTION_NOT_ENABLED")
        if self.execution_count != 0:
            raise CoreExecutionNotEnabled("CORE_EXECUTION_DUPLICATE_BLOCKED")
        self.execution_count += 1
        output = self._execute_once(request)
        if not isinstance(output, CoreExecutionOutput):
            raise CoreExecutionNotEnabled("CORE_OUTPUT_CONTRACT_INVALID")
        return output


class BacktestCoreAdapter:
    """Typed one-call bridge to the frozen P3 BacktestRunner.

    The request factory is the only Application-to-Core conversion point. It
    must return the already validated Core request; this adapter never reads
    external data, creates a manifest, or derives risk values itself.
    """

    def __init__(
        self,
        request_factory: Callable[[object], BacktestRunRequest],
        *,
        runner: BacktestRunner | None = None,
    ) -> None:
        self.request_factory = request_factory
        self.runner = runner or BacktestRunner()
        self.execution_count = 0

    def execute(self, request: object) -> CoreExecutionOutput:
        if self.execution_count != 0:
            raise CoreExecutionNotEnabled("CORE_EXECUTION_DUPLICATE_BLOCKED")
        self.execution_count += 1
        core_request = self.request_factory(request)
        if not isinstance(core_request, BacktestRunRequest):
            raise CoreExecutionNotEnabled("CORE_REQUEST_CONTRACT_INVALID")
        result = self.runner.run(core_request)
        if result.status != "COMMITTED":
            reason = result.failure.reason if result.failure is not None else "CORE_RESULT_STOPPED"
            raise CoreExecutionStopped(reason)
        if not is_sha256(result.state_sha256):
            raise CoreExecutionNotEnabled("CORE_STATE_HASH_INVALID")
        return self._output(result)

    @staticmethod
    def _output(result: BacktestRunResult) -> CoreExecutionOutput:
        rows = tuple(_core_row_mapping(row) for row in result.rows)
        state_sha256 = result.state_sha256
        if not isinstance(state_sha256, str):
            raise CoreExecutionNotEnabled("CORE_STATE_HASH_INVALID")
        fill_count = result.fill_count
        total_pnl = _decimal_payload_sum(rows, "pnl")
        return CoreExecutionOutput(
            metrics=MetricSet(
                total_pnl=total_pnl,
                maximum_drawdown="0",
                trade_count=fill_count,
                win_rate="0.0000",
                ending_balance="0",
                unit="CORE_PROJECTION",
                period_start_utc="UNKNOWN",
                period_end_utc="UNKNOWN",
                rounding_rule="CORE_RESULT_PROJECTION",
                source_result_sha256=None,
            ),
            rows=rows,
            evidence_files={"core.state.sha256": state_sha256},
            core_result_sha256=None,
        )


def _core_row_mapping(row: object) -> Mapping[str, str]:
    raw: dict[str, Any] = dict(vars(row)) if hasattr(row, "__dict__") else {}
    payload = raw.get("payload", {})
    if isinstance(payload, (tuple, list)):
        payload = dict(payload)
    result: dict[str, str] = {}
    for key in ("sequence_no", "row_id", "event_id", "row_kind", "decision_time_utc"):
        if key in raw:
            result[key] = str(raw[key])
    if isinstance(payload, Mapping):
        result.update({str(key): str(value) for key, value in payload.items()})
    return result


def _decimal_payload_sum(rows: tuple[Mapping[str, str], ...], key: str) -> str:
    total = Decimal("0")
    for row in rows:
        try:
            total += Decimal(row.get(key, "0"))
        except (InvalidOperation, ValueError):
            continue
    return format(total, "f")

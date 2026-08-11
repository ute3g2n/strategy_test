"""Narrow adapter boundary for the frozen Backtest Core.

P4-06 never invokes this adapter.  P4-07 may provide an approved adapter that
converts typed Application requests to the existing Core contract exactly once.
"""

from __future__ import annotations

from typing import Protocol


class CoreExecutionNotEnabled(RuntimeError):
    """Raised when a worker tries to execute without an approved Core adapter."""


class CoreAdapter(Protocol):
    def execute(self, request: object) -> object: ...


class FrozenCoreAdapter:
    def execute(self, request: object) -> object:
        del request
        raise CoreExecutionNotEnabled("CORE_EXECUTION_NOT_ENABLED_IN_P4_06")

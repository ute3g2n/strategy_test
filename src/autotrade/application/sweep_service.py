"""Sweep parent/candidate metadata expansion without starting worker Jobs."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import BacktestConfig, CreateRunCommand, PreflightReport, RunView, canonical_hash, utc_now
from .persistence import MetadataStore, PersistenceConflict
from .preflight import preflight_run, preflight_run_for_command

_ALLOWED_CANDIDATE_KEYS = frozenset(
    {"n", "entry_lookback", "exit_lookback", "initial_balance", "fee_bps", "slippage_bps", "force_fail"}
)
_FORBIDDEN_TEXT = re.compile(r"(?i)(api[_-]?key|secret|password|bearer|credential)\s*[:=]")


def _valid_candidate(candidate: object) -> bool:
    if not isinstance(candidate, Mapping) or not set(candidate).issubset(_ALLOWED_CANDIDATE_KEYS):
        return False
    integer_keys = {"n", "entry_lookback", "exit_lookback"}
    numeric_keys = {"initial_balance", "fee_bps", "slippage_bps"}
    for key, value in candidate.items():
        if isinstance(value, (Mapping, list, tuple)):
            return False
        if value is None:
            continue
        if key in integer_keys and (isinstance(value, bool) or not isinstance(value, int)):
            return False
        if key in numeric_keys and (isinstance(value, bool) or not isinstance(value, (int, float))):
            return False
        if key == "force_fail" and not isinstance(value, bool):
            return False
        if key not in integer_keys | numeric_keys | {"force_fail"}:
            return False
        if isinstance(value, float) and not math.isfinite(value):
            return False
    return True


@dataclass(frozen=True)
class SweepView:
    sweep_parent_id: str
    parent_run: RunView
    members: tuple[RunView, ...]
    candidate_set_sha256: str


class SweepService:
    def __init__(self, store: MetadataStore) -> None:
        self.store = store

    def create_sweep(
        self,
        client_request_id: str,
        base_config: BacktestConfig,
        candidates: tuple[dict[str, Any], ...],
        preflight: PreflightReport,
        *,
        correlation_id: str,
        preflight_input: Mapping[str, object] | None = None,
    ) -> SweepView:
        del preflight
        if preflight_run(base_config).status != "PASS":
            raise PersistenceConflict("PREFLIGHT_REQUIRED")
        if base_config.unit_key.timeframe in {"15m", "30m", "1h", "4h", "1d"}:
            if preflight_run_for_command(base_config, preflight_input).get("decision") == "REJECT":
                raise PersistenceConflict("PREFLIGHT_REQUIRED")
        if not isinstance(candidates, (tuple, list)):
            raise PersistenceConflict("SWEEP_CANDIDATE_SCHEMA_INVALID")
        candidates = tuple(candidates)
        if not candidates or len(candidates) > 200:
            raise PersistenceConflict("SWEEP_CANDIDATE_LIMIT")
        if any(not _valid_candidate(candidate) for candidate in candidates):
            raise PersistenceConflict("SWEEP_CANDIDATE_INVALID")
        try:
            candidate_hashes = tuple(canonical_hash(candidate) for candidate in candidates)
        except (TypeError, ValueError, OverflowError) as error:
            raise PersistenceConflict("SWEEP_CANDIDATE_INVALID") from error
        if len(set(candidate_hashes)) != len(candidate_hashes):
            raise PersistenceConflict("SWEEP_DUPLICATE_CANDIDATE")
        parent_command = CreateRunCommand(
            f"{client_request_id}-parent", "SINGLE_BACKTEST", base_config, utc_now(), None, preflight_input
        )
        child_commands: list[CreateRunCommand] = []
        for ordinal, candidate in enumerate(candidates):
            config = BacktestConfig(
                unit_key=base_config.unit_key,
                data=base_config.data,
                strategy=base_config.strategy,
                risk=base_config.risk,
                experiment_plan={**base_config.experiment_plan, "candidate": candidate, "ordinal": ordinal},
                cost_profile_sha256=base_config.cost_profile_sha256,
                calendar_version=base_config.calendar_version,
                calendar_sha256=base_config.calendar_sha256,
                output_policy=base_config.output_policy,
                config_sha256=canonical_hash({"base": base_config.config_sha256, "candidate": candidate}),
            )
            child_command = CreateRunCommand(f"{client_request_id}-{ordinal}", "SWEEP_CHILD", config, utc_now(), None)
            if preflight_run(config).status != "PASS":
                raise PersistenceConflict("PREFLIGHT_REQUIRED")
            if base_config.unit_key.timeframe in {"15m", "30m", "1h", "4h", "1d"}:
                if preflight_run_for_command(config, preflight_input).get("decision") == "REJECT":
                    raise PersistenceConflict("PREFLIGHT_REQUIRED")
                child_command = CreateRunCommand(
                    f"{client_request_id}-{ordinal}",
                    "SWEEP_CHILD",
                    config,
                    utc_now(),
                    None,
                    preflight_input,
                )
            child_commands.append(child_command)
        parent_id, parent, members, candidate_set_hash, _ = self.store.create_sweep(
            client_request_id,
            parent_command,
            tuple(child_commands),
            candidate_hashes,
            correlation_id,
        )
        return SweepView(parent_id, parent, tuple(members), candidate_set_hash)

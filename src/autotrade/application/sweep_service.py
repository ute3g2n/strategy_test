"""Sweep parent/candidate metadata expansion without starting worker Jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import BacktestConfig, CreateRunCommand, PreflightReport, RunView, canonical_hash, utc_now
from .persistence import MetadataStore, PersistenceConflict
from .preflight import preflight_run


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
    ) -> SweepView:
        del preflight
        if preflight_run(base_config).status != "PASS":
            raise PersistenceConflict("PREFLIGHT_REQUIRED")
        if not candidates or len(candidates) > 200:
            raise PersistenceConflict("SWEEP_CANDIDATE_LIMIT")
        candidate_hashes = tuple(canonical_hash(candidate) for candidate in candidates)
        if len(set(candidate_hashes)) != len(candidate_hashes):
            raise PersistenceConflict("SWEEP_DUPLICATE_CANDIDATE")
        parent_command = CreateRunCommand(
            f"{client_request_id}-parent", "SINGLE_BACKTEST", base_config, utc_now(), None
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
            child_commands.append(child_command)
        parent_id, parent, members, candidate_set_hash, _ = self.store.create_sweep(
            client_request_id,
            parent_command,
            tuple(child_commands),
            candidate_hashes,
            correlation_id,
        )
        return SweepView(parent_id, parent, tuple(members), candidate_set_hash)

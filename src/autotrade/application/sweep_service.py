"""Sweep parent/candidate metadata expansion without starting worker Jobs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from .contracts import BacktestConfig, CreateRunCommand, PreflightReport, RunView, canonical_hash, utc_now
from .persistence import MetadataStore, PersistenceConflict


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
        if preflight.status != "PASS":
            raise PersistenceConflict("PREFLIGHT_REQUIRED")
        if not candidates or len(candidates) > 200:
            raise PersistenceConflict("SWEEP_CANDIDATE_LIMIT")
        candidate_hashes = tuple(canonical_hash(candidate) for candidate in candidates)
        if len(set(candidate_hashes)) != len(candidate_hashes):
            raise PersistenceConflict("SWEEP_DUPLICATE_CANDIDATE")
        parent_command = CreateRunCommand(
            client_request_id, "SINGLE_BACKTEST", base_config, utc_now(), preflight.report_sha256
        )
        parent, _ = self.store.create_run(parent_command, correlation_id)
        members: list[RunView] = []
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
            child_command = CreateRunCommand(
                f"{client_request_id}-{ordinal}", "SWEEP_CHILD", config, utc_now(), preflight.report_sha256
            )
            child, _ = self.store.create_run(child_command, correlation_id)
            members.append(child)
        parent_id = f"sweep-{uuid.uuid4().hex}"
        candidate_set_hash = canonical_hash(candidate_hashes)
        with self.store.transaction():
            self.store.connection.execute(
                "INSERT INTO sweep_parent("
                "sweep_parent_id, parent_run_id, candidate_count, candidate_set_sha256, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    parent_id,
                    parent.run_id,
                    len(members),
                    candidate_set_hash,
                    utc_now().isoformat().replace("+00:00", "Z"),
                ),
            )
            for ordinal, member in enumerate(members):
                self.store.connection.execute(
                    "INSERT INTO sweep_member("
                    "sweep_member_id, sweep_parent_id, child_run_id, ordinal, candidate_sha256, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        f"member-{uuid.uuid4().hex}",
                        parent_id,
                        member.run_id,
                        ordinal,
                        candidate_hashes[ordinal],
                        utc_now().isoformat().replace("+00:00", "Z"),
                    ),
                )
        return SweepView(parent_id, parent, tuple(members), candidate_set_hash)

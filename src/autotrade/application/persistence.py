"""SQLite metadata persistence with transaction and idempotency boundaries.

Only Product/Application metadata is stored here.  Result bodies remain under
the frozen Core ResultStore contract and are represented by references and
 relative references and protected input identities.  The store is intentionally
 small, synchronous, and dependency-free;
P4 does not expose it as an HTTP or external database service.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .checkpoint import CheckpointReference
from .contracts import (
    CancelJobCommand,
    CreateRunCommand,
    EvidenceReference,
    FailureView,
    JobStatus,
    JobView,
    QueueReceipt,
    ResultReference,
    ResumeJobCommand,
    RunStatus,
    RunView,
    StartJobCommand,
    canonical_hash,
    canonical_json,
    utc_now,
)
from .state_machine import ensure_transition

SCHEMA_VERSION = "p4-metadata-v2-nonhash-management"
MAX_JOB_ATTEMPTS = 3


class PersistenceConflict(RuntimeError):
    """A deterministic conflict, such as a stale revision or duplicate key."""


class MetadataStore:
    """A local SQLite metadata repository.

    The constructor does not create a database until :meth:`initialize` is
    called.  Tests can use ``:memory:``; production-like callers must pass a
    workspace-local file path and never an arbitrary user path.
    """

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            path = Path(self.database_path)
            if path.is_absolute() and any(part == ".." for part in path.parts):
                raise ValueError("database path must not contain traversal")
            path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, isolation_level=None, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 2500")
        if self.database_path != ":memory:":
            self.connection.execute("PRAGMA journal_mode = WAL")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> MetadataStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def initialize(self) -> None:
        with self.transaction():
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migration (
                    migration_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL UNIQUE,
                    direction TEXT NOT NULL CHECK(direction IN ('FORWARD_ONLY', 'UP', 'DOWN')),
                    checksum TEXT,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run (
                    run_id TEXT PRIMARY KEY,
                    run_kind TEXT NOT NULL CHECK(run_kind IN ('SINGLE_BACKTEST', 'SWEEP_CHILD')),
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 0),
                    condition_sha256 TEXT NOT NULL,
                    manifest_sha256 TEXT,
                    config_json TEXT NOT NULL,
                    failure_code TEXT,
                    failure_message_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run_condition (
                    run_id TEXT PRIMARY KEY REFERENCES run(run_id) ON DELETE CASCADE,
                    condition_sha256 TEXT NOT NULL UNIQUE,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run_state_transition (
                    transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    expected_revision INTEGER NOT NULL,
                    resulting_revision INTEGER NOT NULL,
                    reason_code TEXT NOT NULL,
                    actor_kind TEXT NOT NULL,
                    payload_sha256 TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS job (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 0),
                    attempt INTEGER NOT NULL CHECK(attempt >= 0),
                    operation TEXT NOT NULL,
                    request_key TEXT NOT NULL,
                    expected_revision INTEGER,
                    checkpoint_sha256 TEXT,
                    failure_code TEXT,
                    failure_message_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(operation, request_key)
                );
                CREATE TABLE IF NOT EXISTS queue_item (
                    job_id TEXT PRIMARY KEY REFERENCES job(job_id) ON DELETE CASCADE,
                    queue_sequence INTEGER NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    lease_id TEXT,
                    fencing_token INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS checkpoint (
                    checkpoint_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES job(job_id) ON DELETE CASCADE,
                    run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    sequence_no INTEGER NOT NULL CHECK(sequence_no >= 0),
                    relative_ref TEXT NOT NULL,
                    checkpoint_sha256 TEXT NOT NULL,
                    manifest_sha256 TEXT,
                    commit_marker_sha256 TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(job_id, sequence_no)
                );
                CREATE TABLE IF NOT EXISTS result_reference (
                    run_id TEXT PRIMARY KEY REFERENCES run(run_id) ON DELETE CASCADE,
                    relative_root TEXT NOT NULL,
                    manifest_sha256 TEXT,
                    result_sha256 TEXT,
                    commit_marker_sha256 TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_reference (
                    evidence_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    job_id TEXT REFERENCES job(job_id),
                    relative_root TEXT NOT NULL,
                    evidence_sha256 TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sweep_parent (
                    sweep_parent_id TEXT PRIMARY KEY,
                    parent_run_id TEXT NOT NULL UNIQUE REFERENCES run(run_id) ON DELETE CASCADE,
                    candidate_count INTEGER NOT NULL CHECK(candidate_count >= 0),
                    candidate_set_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sweep_member (
                    sweep_member_id TEXT PRIMARY KEY,
                    sweep_parent_id TEXT NOT NULL REFERENCES sweep_parent(sweep_parent_id) ON DELETE CASCADE,
                    child_run_id TEXT NOT NULL UNIQUE REFERENCES run(run_id) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL,
                    candidate_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(sweep_parent_id, ordinal),
                    UNIQUE(sweep_parent_id, candidate_sha256)
                );
                CREATE TABLE IF NOT EXISTS csv_job (
                    csv_job_id TEXT PRIMARY KEY,
                    source_run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 0),
                    source_result_sha256 TEXT,
                    column_set_json TEXT NOT NULL,
                    filter_payload_sha256 TEXT NOT NULL,
                    relative_output_ref TEXT,
                    output_sha256 TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(source_run_id, source_result_sha256, filter_payload_sha256, column_set_json)
                );
                CREATE TABLE IF NOT EXISTS idempotency_record (
                    idempotency_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    request_key TEXT NOT NULL,
                    fingerprint TEXT,
                    target_kind TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(scope, request_key)
                );
                CREATE TABLE IF NOT EXISTS audit_event (
                    event_id TEXT PRIMARY KEY,
                    aggregate_kind TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    before_revision INTEGER,
                    after_revision INTEGER,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS holdout_assessment (
                    assessment_id TEXT PRIMARY KEY,
                    source_run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    source_condition_sha256 TEXT NOT NULL,
                    holdout_plan_sha256 TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason_code TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_run_status_updated ON run(status, updated_at);
                CREATE INDEX IF NOT EXISTS idx_job_run_status ON job(run_id, status, updated_at);
                CREATE INDEX IF NOT EXISTS idx_transition_run_revision
                    ON run_state_transition(run_id, resulting_revision);
                CREATE INDEX IF NOT EXISTS idx_audit_aggregate ON audit_event(aggregate_kind, aggregate_id, created_at);
                """
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO schema_migration(migration_id, version, direction, checksum, applied_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("P4-MIG-002", SCHEMA_VERSION, "FORWARD_ONLY", None, _now()),
            )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield self.connection
        except Exception:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            raise
        else:
            if self.connection.in_transaction:
                self.connection.execute("COMMIT")

    def _assert_initialized(self) -> None:
        if self.connection.execute("SELECT 1 FROM sqlite_master WHERE name='run'").fetchone() is None:
            self.initialize()

    def _idempotency(self, scope: str, request_key: str) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM idempotency_record WHERE scope = ? AND request_key = ?", (scope, request_key)
        ).fetchone()

    def _audit(
        self,
        aggregate_kind: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        correlation_id: str,
        before_revision: int | None,
        after_revision: int | None,
    ) -> None:
        payload_json = canonical_json(payload)
        self.connection.execute(
            """INSERT INTO audit_event
            (event_id, aggregate_kind, aggregate_id, event_type, correlation_id,
             before_revision, after_revision, payload_json, payload_sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)""",
            (
                str(uuid.uuid4()),
                aggregate_kind,
                aggregate_id,
                event_type,
                correlation_id,
                before_revision,
                after_revision,
                payload_json,
                _now(),
            ),
        )

    def _transition(
        self,
        run_id: str,
        from_status: str | None,
        to_status: str,
        expected_revision: int,
        resulting_revision: int,
        reason_code: str,
        *,
        actor_kind: str,
    ) -> None:
        if from_status is not None:
            ensure_transition(from_status, to_status, domain="run")
        self.connection.execute(
            """INSERT INTO run_state_transition
            (run_id, from_status, to_status, expected_revision, resulting_revision,
             reason_code, actor_kind, payload_sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)""",
            (
                run_id,
                from_status,
                to_status,
                expected_revision,
                resulting_revision,
                reason_code,
                actor_kind,
                _now(),
            ),
        )

    def _run_row(self, run_id: str) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM run WHERE run_id = ?", (run_id,)).fetchone()

    def _view_from_run(self, row: sqlite3.Row) -> RunView:
        result_row = self.connection.execute(
            "SELECT * FROM result_reference WHERE run_id = ?", (row["run_id"],)
        ).fetchone()
        evidence_row = self.connection.execute(
            "SELECT * FROM evidence_reference WHERE run_id = ? ORDER BY created_at DESC LIMIT 1", (row["run_id"],)
        ).fetchone()
        result = (
            ResultReference(
                row["run_id"],
                result_row["relative_root"],
                result_row["manifest_sha256"],
                result_row["result_sha256"],
                result_row["commit_marker_sha256"],
            )
            if result_row
            else None
        )
        evidence = (
            EvidenceReference(
                evidence_row["evidence_id"],
                evidence_row["run_id"],
                evidence_row["relative_root"],
                evidence_row["evidence_sha256"],
                evidence_row["status"],
            )
            if evidence_row
            else None
        )
        failure = (
            FailureView(
                row["failure_code"],
                row["failure_message_id"],
                recovery_required=row["status"] == RunStatus.RECOVERY_REQUIRED,
            )
            if row["failure_code"]
            else None
        )
        return RunView(
            run_id=row["run_id"],
            run_kind=row["run_kind"],
            status=RunStatus(row["status"]),
            revision=row["revision"],
            condition_sha256=row["condition_sha256"],
            manifest_sha256=row["manifest_sha256"],
            result=result,
            evidence=evidence,
            failure=failure,
        )

    def _job_view(self, row: sqlite3.Row) -> JobView:
        queue_row = self.connection.execute("SELECT * FROM queue_item WHERE job_id = ?", (row["job_id"],)).fetchone()
        receipt = (
            QueueReceipt(
                row["job_id"],
                queue_row["queue_sequence"],
                row["request_key"],
                "QUEUED" if queue_row["status"] == "WAITING" else "EXISTING",
            )
            if queue_row
            else None
        )
        failure = FailureView(row["failure_code"], row["failure_message_id"]) if row["failure_code"] else None
        return JobView(
            job_id=row["job_id"],
            run_id=row["run_id"],
            status=JobStatus(row["status"]),
            revision=row["revision"],
            attempt=row["attempt"],
            checkpoint_sha256=row["checkpoint_sha256"],
            failure=failure,
            queue=receipt,
        )

    def create_run(self, command: CreateRunCommand, correlation_id: str) -> tuple[RunView, bool]:
        self._assert_initialized()
        with self.transaction():
            return self._create_run_in_transaction(command, correlation_id)

    def _create_run_in_transaction(self, command: CreateRunCommand, correlation_id: str) -> tuple[RunView, bool]:
        """Create a Run while the caller owns the surrounding transaction."""

        existing = self._idempotency("create_run", command.client_request_id)
        if existing:
            row = self._run_row(existing["target_id"])
            if row is None:
                raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
            return self._view_from_run(row), True
        run_id = _new_id("run")
        condition_sha = canonical_hash(command.config.fingerprint_payload())
        now = _now()
        config_json = canonical_json(asdict(command.config))
        self.connection.execute(
            """INSERT INTO run(run_id, run_kind, status, revision, condition_sha256, manifest_sha256,
            config_json, failure_code, failure_message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)""",
            (
                run_id,
                command.run_kind,
                RunStatus.DRAFT,
                0,
                condition_sha,
                None,
                config_json,
                now,
                now,
            ),
        )
        self.connection.execute(
            "INSERT INTO run_condition(run_id, condition_sha256, config_json, created_at) VALUES (?, ?, ?, ?)",
            (run_id, condition_sha, config_json, now),
        )
        self.connection.execute(
            """INSERT INTO idempotency_record
            (idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                "create_run",
                command.client_request_id,
                None,
                "run",
                run_id,
                "{}",
                now,
            ),
        )
        self._transition(run_id, None, RunStatus.DRAFT, 0, 0, "RUN_CREATED", actor_kind="application")
        self._audit(
            "run",
            run_id,
            "RUN_CREATED",
            {
                "run_kind": command.run_kind,
                "condition_sha256": condition_sha,
            },
            correlation_id=correlation_id,
            before_revision=None,
            after_revision=0,
        )
        row = self._run_row(run_id)
        assert row is not None
        return self._view_from_run(row), False

    def get_run(self, run_id: str) -> RunView | None:
        self._assert_initialized()
        row = self._run_row(run_id)
        return self._view_from_run(row) if row else None

    def create_sweep(
        self,
        client_request_id: str,
        parent_command: CreateRunCommand,
        child_commands: tuple[CreateRunCommand, ...],
        candidate_hashes: tuple[str, ...],
        correlation_id: str,
    ) -> tuple[str, RunView, tuple[RunView, ...], str, bool]:
        """Create a sweep parent, members and their Runs in one transaction."""

        self._assert_initialized()
        with self.transaction():
            existing = self._idempotency("create_sweep", client_request_id)
            if existing:
                parent_row = self.connection.execute(
                    "SELECT * FROM sweep_parent WHERE sweep_parent_id = ?", (existing["target_id"],)
                ).fetchone()
                if parent_row is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                parent_run_row = self._run_row(parent_row["parent_run_id"])
                if parent_run_row is None:
                    raise PersistenceConflict("SWEEP_PARENT_RUN_MISSING")
                member_rows = self.connection.execute(
                    "SELECT child_run_id FROM sweep_member WHERE sweep_parent_id = ? ORDER BY ordinal",
                    (parent_row["sweep_parent_id"],),
                ).fetchall()
                child_views: list[RunView] = []
                for member_row in member_rows:
                    child_row = self._run_row(member_row["child_run_id"])
                    if child_row is None:
                        raise PersistenceConflict("SWEEP_MEMBER_RUN_MISSING")
                    child_views.append(self._view_from_run(child_row))
                children = tuple(child_views)
                if len(children) != len(member_rows):
                    raise PersistenceConflict("SWEEP_MEMBER_RUN_MISSING")
                return (
                    parent_row["sweep_parent_id"],
                    self._view_from_run(parent_run_row),
                    children,
                    parent_row["candidate_set_sha256"],
                    True,
                )
            if len(child_commands) != len(candidate_hashes):
                raise PersistenceConflict("SWEEP_CANDIDATE_BINDING_MISMATCH")
            parent, _ = self._create_run_in_transaction(parent_command, correlation_id)
            children = tuple(self._create_run_in_transaction(command, correlation_id)[0] for command in child_commands)
            sweep_parent_id = _new_id("sweep")
            candidate_set_hash = canonical_hash(candidate_hashes)
            now = _now()
            self.connection.execute(
                """INSERT INTO sweep_parent(
                sweep_parent_id, parent_run_id, candidate_count, candidate_set_sha256, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (sweep_parent_id, parent.run_id, len(children), candidate_set_hash, now),
            )
            for ordinal, (child, candidate_hash) in enumerate(zip(children, candidate_hashes, strict=True)):
                self.connection.execute(
                    """INSERT INTO sweep_member(
                    sweep_member_id, sweep_parent_id, child_run_id, ordinal, candidate_sha256, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (_new_id("member"), sweep_parent_id, child.run_id, ordinal, candidate_hash, now),
                )
            self.connection.execute(
                """INSERT INTO idempotency_record
                (idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    "create_sweep",
                    client_request_id,
                    None,
                    "sweep_parent",
                    sweep_parent_id,
                    "{}",
                    now,
                ),
            )
            self._audit(
                "sweep_parent",
                sweep_parent_id,
                "SWEEP_CREATED",
                {
                    "parent_run_id": parent.run_id,
                    "child_run_ids": [child.run_id for child in children],
                    "candidate_set_sha256": candidate_set_hash,
                },
                correlation_id=correlation_id,
                before_revision=None,
                after_revision=0,
            )
            return sweep_parent_id, parent, children, candidate_set_hash, False

    def list_runs(self, limit: int = 50, state: str | None = None) -> tuple[RunView, ...]:
        self._assert_initialized()
        safe_limit = max(1, min(limit, 200))
        if state:
            rows = self.connection.execute(
                "SELECT * FROM run WHERE status = ? ORDER BY created_at, run_id LIMIT ?", (state, safe_limit)
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM run ORDER BY created_at, run_id LIMIT ?", (safe_limit,)
            ).fetchall()
        return tuple(self._view_from_run(row) for row in rows)

    def start_job(self, command: StartJobCommand, correlation_id: str) -> tuple[JobView, bool]:
        self._assert_initialized()
        with self.transaction():
            existing = self._idempotency("start_job", command.request_key)
            if existing:
                row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (existing["target_id"],)).fetchone()
                if row is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                return self._job_view(row), True
            run = self._run_row(command.run_id)
            if run is None:
                raise PersistenceConflict("RUN_NOT_FOUND")
            if command.expected_revision != run["revision"]:
                raise PersistenceConflict("STALE_REVISION")
            if run["status"] not in {RunStatus.DRAFT, RunStatus.STOPPED, RunStatus.RECOVERY_REQUIRED}:
                raise PersistenceConflict("RUN_NOT_STARTABLE")
            next_run_revision = run["revision"] + 1
            ensure_transition(run["status"], RunStatus.QUEUED, domain="run")
            now = _now()
            job_id = _new_id("job")
            sequence = int(
                self.connection.execute("SELECT COALESCE(MAX(queue_sequence), 0) + 1 FROM queue_item").fetchone()[0]
            )
            self.connection.execute(
                """INSERT INTO job(job_id, run_id, status, revision, attempt, operation, request_key,
                expected_revision, checkpoint_sha256, failure_code, failure_message_id, created_at, updated_at)
                VALUES (?, ?, ?, 0, 0, 'BACKTEST', ?, ?, NULL, NULL, NULL, ?, ?)""",
                (
                    job_id,
                    command.run_id,
                    JobStatus.QUEUED,
                    command.request_key,
                    command.expected_revision,
                    now,
                    now,
                ),
            )
            self.connection.execute(
                """INSERT INTO queue_item(
                job_id, queue_sequence, status, lease_id, fencing_token, created_at, updated_at)
                VALUES (?, ?, 'WAITING', NULL, NULL, ?, ?)""",
                (job_id, sequence, now, now),
            )
            self.connection.execute(
                "UPDATE run SET status = ?, revision = ?, updated_at = ? WHERE run_id = ? AND revision = ?",
                (RunStatus.QUEUED, next_run_revision, now, command.run_id, command.expected_revision),
            )
            self._transition(
                command.run_id,
                run["status"],
                RunStatus.QUEUED,
                command.expected_revision,
                next_run_revision,
                "JOB_QUEUED",
                actor_kind="application",
            )
            self.connection.execute(
                "INSERT INTO idempotency_record VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    "start_job",
                    command.request_key,
                    None,
                    "job",
                    job_id,
                    "{}",
                    now,
                ),
            )
            self._audit(
                "job",
                job_id,
                "JOB_QUEUED",
                {
                    "run_id": command.run_id,
                    "queue_sequence": sequence,
                },
                correlation_id=correlation_id,
                before_revision=0,
                after_revision=0,
            )
            row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (job_id,)).fetchone()
            assert row is not None
            return self._job_view(row), False

    def get_job(self, job_id: str) -> JobView | None:
        self._assert_initialized()
        row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (job_id,)).fetchone()
        return self._job_view(row) if row else None

    def list_jobs(self, limit: int = 50, state: str | None = None) -> tuple[JobView, ...]:
        self._assert_initialized()
        safe_limit = max(1, min(limit, 200))
        if state:
            rows = self.connection.execute(
                "SELECT * FROM job WHERE status = ? ORDER BY created_at, job_id LIMIT ?", (state, safe_limit)
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM job ORDER BY created_at, job_id LIMIT ?", (safe_limit,)
            ).fetchall()
        return tuple(self._job_view(row) for row in rows)

    def cancel_job(self, command: CancelJobCommand, correlation_id: str) -> JobView:
        self._assert_initialized()
        with self.transaction():
            existing = self._idempotency("cancel_job", command.request_key)
            if existing:
                existing_row = self.connection.execute(
                    "SELECT * FROM job WHERE job_id = ?", (existing["target_id"],)
                ).fetchone()
                if existing_row is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                return self._job_view(existing_row)
            row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (command.job_id,)).fetchone()
            if row is None:
                raise PersistenceConflict("JOB_NOT_FOUND")
            if command.expected_revision is not None and command.expected_revision != row["revision"]:
                raise PersistenceConflict("STALE_REVISION")
            if row["status"] in {JobStatus.CANCELLED, JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.STOPPED}:
                return self._job_view(row)
            old_status = row["status"]
            if old_status == JobStatus.QUEUED:
                new_job_status = JobStatus.CANCELLED
                new_run_status = RunStatus.CANCELLED
                queue_status = "CANCELLED"
            else:
                new_job_status = JobStatus.CANCEL_REQUESTED
                new_run_status = RunStatus.STOP_REQUESTED
                queue_status = None
            ensure_transition(old_status, new_job_status, domain="job")
            run = self._run_row(row["run_id"])
            if run is None:
                raise PersistenceConflict("RUN_NOT_FOUND")
            ensure_transition(run["status"], new_run_status, domain="run")
            now = _now()
            job_revision = row["revision"] + 1
            run_revision = run["revision"] + 1
            self.connection.execute(
                "UPDATE job SET status = ?, revision = ?, updated_at = ? WHERE job_id = ? AND revision = ?",
                (new_job_status, job_revision, now, command.job_id, row["revision"]),
            )
            self.connection.execute(
                "UPDATE run SET status = ?, revision = ?, updated_at = ? WHERE run_id = ? AND revision = ?",
                (new_run_status, run_revision, now, row["run_id"], run["revision"]),
            )
            if queue_status:
                self.connection.execute(
                    "UPDATE queue_item SET status = ?, updated_at = ? WHERE job_id = ?",
                    (queue_status, now, command.job_id),
                )
            self._transition(
                row["run_id"],
                run["status"],
                new_run_status,
                run["revision"],
                run_revision,
                command.reason_code,
                actor_kind="application",
            )
            self._audit(
                "job",
                command.job_id,
                "JOB_CANCEL_REQUESTED" if new_job_status == JobStatus.CANCEL_REQUESTED else "JOB_CANCELLED",
                {"reason_code": command.reason_code, "from_status": old_status, "to_status": new_job_status},
                correlation_id=correlation_id,
                before_revision=row["revision"],
                after_revision=job_revision,
            )
            self.connection.execute(
                """INSERT INTO idempotency_record(
                idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
                VALUES (?, 'cancel_job', ?, ?, 'job', ?, '{}', ?)""",
                (
                    str(uuid.uuid4()),
                    command.request_key,
                    None,
                    command.job_id,
                    now,
                ),
            )
            updated = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (command.job_id,)).fetchone()
            assert updated is not None
            return self._job_view(updated)

    def claim_next_job(self, worker_id: str) -> JobView | None:
        self._assert_initialized()
        with self.transaction():
            row = self.connection.execute(
                "SELECT j.* FROM job j JOIN queue_item q ON q.job_id = j.job_id "
                "WHERE q.status = 'WAITING' ORDER BY q.queue_sequence LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            run = self._run_row(row["run_id"])
            if run is None or run["status"] != RunStatus.QUEUED:
                raise PersistenceConflict("QUEUE_RUN_STATE_MISMATCH")
            now = _now()
            fencing = int(
                self.connection.execute("SELECT COALESCE(MAX(fencing_token), 0) + 1 FROM queue_item").fetchone()[0]
            )
            lease_id = f"{worker_id}:{uuid.uuid4()}"
            self.connection.execute(
                "UPDATE queue_item SET status = 'LEASED', lease_id = ?, fencing_token = ?, updated_at = ? "
                "WHERE job_id = ? AND status = 'WAITING'",
                (lease_id, fencing, now, row["job_id"]),
            )
            self.connection.execute(
                "UPDATE queue_item SET status = 'RUNNING', updated_at = ? WHERE job_id = ? AND status = 'LEASED'",
                (now, row["job_id"]),
            )
            self.connection.execute(
                "UPDATE job SET status = 'RUNNING', revision = revision + 1, updated_at = ? WHERE job_id = ?",
                (now, row["job_id"]),
            )
            next_run_revision = run["revision"] + 1
            self.connection.execute(
                "UPDATE run SET status = 'RUNNING', revision = ?, updated_at = ? WHERE run_id = ?",
                (next_run_revision, now, run["run_id"]),
            )
            self._transition(
                run["run_id"],
                run["status"],
                RunStatus.RUNNING,
                run["revision"],
                next_run_revision,
                "WORKER_CLAIMED",
                actor_kind="worker",
            )
            updated = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (row["job_id"],)).fetchone()
            assert updated is not None
            return self._job_view(updated)

    def record_result_reference(self, reference: ResultReference) -> None:
        self._assert_initialized()
        with self.transaction():
            self.connection.execute(
                """INSERT INTO result_reference(
                run_id, relative_root, manifest_sha256, result_sha256, commit_marker_sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET relative_root=excluded.relative_root,
                manifest_sha256=excluded.manifest_sha256, result_sha256=excluded.result_sha256,
                commit_marker_sha256=excluded.commit_marker_sha256""",
                (
                    reference.run_id,
                    reference.relative_root,
                    reference.manifest_sha256,
                    reference.result_sha256,
                    reference.commit_marker_sha256,
                    _now(),
                ),
            )

    def record_evidence_reference(self, reference: EvidenceReference, job_id: str | None = None) -> None:
        self._assert_initialized()
        with self.transaction():
            self._record_evidence_reference_in_transaction(reference, job_id)

    def _record_evidence_reference_in_transaction(
        self, reference: EvidenceReference, job_id: str | None = None
    ) -> None:
        self.connection.execute(
            "INSERT INTO evidence_reference("
            "evidence_id, run_id, job_id, relative_root, evidence_sha256, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                reference.evidence_id,
                reference.run_id,
                job_id,
                reference.relative_root,
                reference.evidence_sha256,
                reference.status,
                _now(),
            ),
        )

    def complete_job_with_result(
        self,
        job_id: str,
        reference: ResultReference,
        evidence: EvidenceReference,
        *,
        correlation_id: str,
    ) -> JobView:
        """Commit result/evidence references and terminal state atomically."""

        self._assert_initialized()
        with self.transaction():
            self.connection.execute(
                """INSERT INTO result_reference(
                run_id, relative_root, manifest_sha256, result_sha256, commit_marker_sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET relative_root=excluded.relative_root,
                manifest_sha256=excluded.manifest_sha256, result_sha256=excluded.result_sha256,
                commit_marker_sha256=excluded.commit_marker_sha256""",
                (
                    reference.run_id,
                    reference.relative_root,
                    reference.manifest_sha256,
                    reference.result_sha256,
                    reference.commit_marker_sha256,
                    _now(),
                ),
            )
            existing = self.connection.execute(
                "SELECT evidence_id FROM evidence_reference WHERE evidence_id = ?", (evidence.evidence_id,)
            ).fetchone()
            if existing is None:
                self._record_evidence_reference_in_transaction(evidence, job_id)
            result = self._mark_job_terminal_in_transaction(job_id, JobStatus.SUCCEEDED, None, correlation_id)
            self._audit(
                "run",
                reference.run_id,
                "RESULT_REFERENCES_COMMITTED",
                {"relative_root": reference.relative_root, "evidence_id": evidence.evidence_id},
                correlation_id=correlation_id,
                before_revision=None,
                after_revision=None,
            )
            return result

    def create_csv_job(
        self,
        *,
        source_run_id: str,
        source_result_sha256: str,
        column_set: tuple[str, ...],
        filter_payload_sha256: str,
        request_key: str,
        correlation_id: str,
    ) -> tuple[dict[str, Any], bool]:
        self._assert_initialized()
        with self.transaction():
            existing = self._idempotency("create_csv_job", request_key)
            if existing:
                row = self.connection.execute(
                    "SELECT * FROM csv_job WHERE csv_job_id = ?", (existing["target_id"],)
                ).fetchone()
                if row is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                return dict(row), True
            source = self._run_row(source_run_id)
            if source is None:
                raise PersistenceConflict("RUN_NOT_FOUND")
            result = self.connection.execute(
                "SELECT * FROM result_reference WHERE run_id = ?", (source_run_id,)
            ).fetchone()
            if result is None:
                raise PersistenceConflict("RESULT_NOT_COMMITTED")
            csv_job_id = _new_id("csv")
            now = _now()
            self.connection.execute(
                """INSERT INTO csv_job(
                csv_job_id, source_run_id, status, revision, source_result_sha256,
                column_set_json, filter_payload_sha256, relative_output_ref, output_sha256,
                created_at, updated_at)
                VALUES (?, ?, 'QUEUED', 0, ?, ?, ?, NULL, NULL, ?, ?)""",
                (
                    csv_job_id,
                    source_run_id,
                    source_result_sha256,
                    canonical_json(column_set),
                    filter_payload_sha256,
                    now,
                    now,
                ),
            )
            self.connection.execute(
                """INSERT INTO idempotency_record(
                idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
                VALUES (?, 'create_csv_job', ?, ?, 'csv_job', ?, '{}', ?)""",
                (str(uuid.uuid4()), request_key, None, csv_job_id, now),
            )
            self._audit(
                "csv_job",
                csv_job_id,
                "CSV_JOB_CREATED",
                {"source_run_id": source_run_id, "column_set": list(column_set)},
                correlation_id=correlation_id,
                before_revision=0,
                after_revision=0,
            )
            row = self.connection.execute("SELECT * FROM csv_job WHERE csv_job_id = ?", (csv_job_id,)).fetchone()
            assert row is not None
            return dict(row), False

    def get_csv_job(self, csv_job_id: str) -> dict[str, Any] | None:
        self._assert_initialized()
        row = self.connection.execute("SELECT * FROM csv_job WHERE csv_job_id = ?", (csv_job_id,)).fetchone()
        return dict(row) if row else None

    def complete_csv_job(
        self,
        csv_job_id: str,
        *,
        relative_output_ref: str,
        output_sha256: str | None,
        correlation_id: str,
    ) -> dict[str, Any]:
        self._assert_initialized()
        with self.transaction():
            row = self.connection.execute("SELECT * FROM csv_job WHERE csv_job_id = ?", (csv_job_id,)).fetchone()
            if row is None:
                raise PersistenceConflict("CSV_JOB_NOT_FOUND")
            if row["status"] == "COMPLETED":
                if row["relative_output_ref"] != relative_output_ref:
                    raise PersistenceConflict("CSV_OUTPUT_MISMATCH")
                return dict(row)
            if row["status"] != "QUEUED":
                raise PersistenceConflict("CSV_JOB_NOT_STARTABLE")
            now = _now()
            self.connection.execute(
                "UPDATE csv_job SET status = 'COMPLETED', revision = revision + 1, relative_output_ref = ?, "
                "output_sha256 = ?, updated_at = ? WHERE csv_job_id = ? AND status = 'QUEUED'",
                (relative_output_ref, output_sha256, now, csv_job_id),
            )
            self._audit(
                "csv_job",
                csv_job_id,
                "CSV_JOB_COMPLETED",
                {"relative_output_ref": relative_output_ref},
                correlation_id=correlation_id,
                before_revision=row["revision"],
                after_revision=row["revision"] + 1,
            )
            updated = self.connection.execute("SELECT * FROM csv_job WHERE csv_job_id = ?", (csv_job_id,)).fetchone()
            assert updated is not None
            return dict(updated)

    def record_holdout_assessment(
        self,
        *,
        source_run_id: str,
        holdout_plan_sha256: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        self._assert_initialized()
        with self.transaction():
            source = self._run_row(source_run_id)
            if source is None:
                raise PersistenceConflict("RUN_NOT_FOUND")
            request_key = f"holdout:{source_run_id}:{holdout_plan_sha256}"
            existing_idempotency = self._idempotency("assess_holdout_reuse", request_key)
            if existing_idempotency:
                existing_assessment = self.connection.execute(
                    "SELECT * FROM holdout_assessment WHERE assessment_id = ?",
                    (existing_idempotency["target_id"],),
                ).fetchone()
                if existing_assessment is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                return dict(existing_assessment)
            existing = self.connection.execute(
                """SELECT * FROM holdout_assessment
                WHERE source_run_id = ? AND holdout_plan_sha256 = ?
                ORDER BY created_at DESC LIMIT 1""",
                (source_run_id, holdout_plan_sha256),
            ).fetchone()
            if existing is not None:
                return dict(existing)
            assessment_id = _new_id("holdout")
            now = _now()
            self.connection.execute(
                """INSERT INTO holdout_assessment(
                assessment_id, source_run_id, source_condition_sha256, holdout_plan_sha256,
                decision, reason_code, created_at)
                VALUES (?, ?, ?, ?, 'BLOCKED', 'HOLDOUT_REUSE_BLOCKED', ?)""",
                (assessment_id, source_run_id, source["condition_sha256"], holdout_plan_sha256, now),
            )
            self.connection.execute(
                """INSERT INTO idempotency_record(
                idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
                VALUES (?, 'assess_holdout_reuse', ?, ?, 'holdout_assessment', ?, '{}', ?)""",
                (str(uuid.uuid4()), request_key, None, assessment_id, now),
            )
            self._audit(
                "run",
                source_run_id,
                "HOLDOUT_REUSE_BLOCKED",
                {"assessment_id": assessment_id, "holdout_plan_sha256": holdout_plan_sha256},
                correlation_id=correlation_id,
                before_revision=source["revision"],
                after_revision=source["revision"],
            )
            row = self.connection.execute(
                "SELECT * FROM holdout_assessment WHERE assessment_id = ?", (assessment_id,)
            ).fetchone()
            assert row is not None
            return dict(row)

    def record_checkpoint(self, reference: CheckpointReference) -> None:
        """Store a verified checkpoint reference; the payload stays in a file."""

        reference.validate()
        self._assert_initialized()
        with self.transaction():
            job = self.connection.execute("SELECT run_id FROM job WHERE job_id = ?", (reference.job_id,)).fetchone()
            if job is None or job["run_id"] != reference.run_id:
                raise PersistenceConflict("CHECKPOINT_JOB_BINDING_MISMATCH")
            self.connection.execute(
                """INSERT INTO checkpoint(
                checkpoint_id, job_id, run_id, sequence_no, relative_ref,
                checkpoint_sha256, manifest_sha256, commit_marker_sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id, sequence_no) DO UPDATE SET
                relative_ref=excluded.relative_ref,
                checkpoint_sha256=excluded.checkpoint_sha256,
                manifest_sha256=excluded.manifest_sha256,
                commit_marker_sha256=excluded.commit_marker_sha256""",
                (
                    _new_id("checkpoint"),
                    reference.job_id,
                    reference.run_id,
                    reference.sequence_no,
                    reference.relative_ref,
                    reference.checkpoint_sha256,
                    reference.manifest_sha256,
                    reference.commit_marker_sha256,
                    _now(),
                ),
            )

    def resume_job(self, command: ResumeJobCommand, correlation_id: str) -> JobView:
        """Create a new queued Job only after checkpoint identity is verified."""

        self._assert_initialized()
        with self.transaction():
            run = self._run_row(command.run_id)
            if run is None:
                raise PersistenceConflict("RUN_NOT_FOUND")
            checkpoint = self.connection.execute(
                """SELECT * FROM checkpoint
                WHERE run_id = ? AND checkpoint_sha256 = ?
                ORDER BY sequence_no DESC LIMIT 1""",
                (command.run_id, command.checkpoint_sha256),
            ).fetchone()
            if checkpoint is None:
                raise PersistenceConflict("CHECKPOINT_VERIFICATION_REQUIRED")
            existing = self._idempotency("resume_job", command.request_key)
            if existing:
                row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (existing["target_id"],)).fetchone()
                if row is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                return self._job_view(row)
            max_attempt = int(
                self.connection.execute(
                    "SELECT COALESCE(MAX(attempt), 0) FROM job WHERE run_id = ?", (command.run_id,)
                ).fetchone()[0]
            )
            if max_attempt >= MAX_JOB_ATTEMPTS:
                raise PersistenceConflict("RETRY_LIMIT_EXCEEDED")
            if command.expected_revision is not None and command.expected_revision != run["revision"]:
                raise PersistenceConflict("STALE_REVISION")
            if run["status"] not in {RunStatus.STOPPED, RunStatus.RECOVERY_REQUIRED}:
                raise PersistenceConflict("RUN_NOT_RESUMABLE")
            ensure_transition(run["status"], RunStatus.QUEUED, domain="run")
            now = _now()
            job_id = _new_id("job")
            sequence = int(
                self.connection.execute("SELECT COALESCE(MAX(queue_sequence), 0) + 1 FROM queue_item").fetchone()[0]
            )
            self.connection.execute(
                """INSERT INTO job(job_id, run_id, status, revision, attempt, operation, request_key,
                expected_revision, checkpoint_sha256, failure_code, failure_message_id, created_at, updated_at)
                VALUES (?, ?, 'QUEUED', 0, ?, 'BACKTEST_RESUME', ?, ?, ?, NULL, NULL, ?, ?)""",
                (
                    job_id,
                    command.run_id,
                    max_attempt + 1,
                    command.request_key,
                    command.expected_revision,
                    command.checkpoint_sha256,
                    now,
                    now,
                ),
            )
            self.connection.execute(
                """INSERT INTO queue_item(
                job_id, queue_sequence, status, lease_id, fencing_token, created_at, updated_at)
                VALUES (?, ?, 'WAITING', NULL, NULL, ?, ?)""",
                (job_id, sequence, now, now),
            )
            next_revision = run["revision"] + 1
            self.connection.execute(
                "UPDATE run SET status = 'QUEUED', revision = ?, failure_code = NULL, failure_message_id = NULL, "
                "updated_at = ? WHERE run_id = ? AND revision = ?",
                (next_revision, now, command.run_id, run["revision"]),
            )
            self._transition(
                command.run_id,
                run["status"],
                RunStatus.QUEUED,
                run["revision"],
                next_revision,
                "JOB_RESUMED",
                actor_kind="application",
            )
            self.connection.execute(
                """INSERT INTO idempotency_record(
                idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
                VALUES (?, 'resume_job', ?, ?, 'job', ?, '{}', ?)""",
                (str(uuid.uuid4()), command.request_key, None, job_id, now),
            )
            self._audit(
                "job",
                job_id,
                "JOB_RESUMED",
                {"run_id": command.run_id, "checkpoint_sha256": command.checkpoint_sha256},
                correlation_id=correlation_id,
                before_revision=run["revision"],
                after_revision=next_revision,
            )
            row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (job_id,)).fetchone()
            assert row is not None
            return self._job_view(row)

    def mark_job_terminal(self, job_id: str, status: JobStatus, *, failure: FailureView | None = None) -> JobView:
        if status not in {
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.STOPPED,
            JobStatus.CANCELLED,
            JobStatus.RECOVERY_REQUIRED,
        }:
            raise ValueError("terminal job status required")
        self._assert_initialized()
        with self.transaction():
            return self._mark_job_terminal_in_transaction(job_id, status, failure, "application")

    def _mark_job_terminal_in_transaction(
        self,
        job_id: str,
        status: JobStatus,
        failure: FailureView | None,
        correlation_id: str,
    ) -> JobView:
        row = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise PersistenceConflict("JOB_NOT_FOUND")
        ensure_transition(row["status"], status, domain="job")
        run = self._run_row(row["run_id"])
        if run is None:
            raise PersistenceConflict("RUN_NOT_FOUND")
        run_status = {
            JobStatus.SUCCEEDED: RunStatus.SUCCEEDED,
            JobStatus.FAILED: RunStatus.FAILED,
            JobStatus.STOPPED: RunStatus.STOPPED,
            JobStatus.CANCELLED: RunStatus.CANCELLED,
            JobStatus.RECOVERY_REQUIRED: RunStatus.RECOVERY_REQUIRED,
        }[status]
        ensure_transition(run["status"], run_status, domain="run")
        now = _now()
        self.connection.execute(
            "UPDATE job SET status = ?, revision = revision + 1, failure_code = ?, "
            "failure_message_id = ?, updated_at = ? WHERE job_id = ?",
            (status, failure.code if failure else None, failure.message_id if failure else None, now, job_id),
        )
        self.connection.execute("UPDATE queue_item SET status = 'DONE', updated_at = ? WHERE job_id = ?", (now, job_id))
        self.connection.execute(
            "UPDATE run SET status = ?, revision = revision + 1, failure_code = ?, "
            "failure_message_id = ?, updated_at = ? WHERE run_id = ?",
            (
                run_status,
                failure.code if failure else None,
                failure.message_id if failure else None,
                now,
                run["run_id"],
            ),
        )
        self._transition(
            run["run_id"],
            run["status"],
            run_status,
            run["revision"],
            run["revision"] + 1,
            status,
            actor_kind="worker",
        )
        self._audit(
            "job",
            job_id,
            f"JOB_{status}",
            {"run_id": run["run_id"], "failure_code": failure.code if failure else None},
            correlation_id=correlation_id,
            before_revision=row["revision"],
            after_revision=row["revision"] + 1,
        )
        self._refresh_sweep_parent_in_transaction(run["run_id"], correlation_id)
        updated = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (job_id,)).fetchone()
        assert updated is not None
        return self._job_view(updated)

    def _refresh_sweep_parent_in_transaction(self, child_run_id: str, correlation_id: str) -> None:
        """Project terminal child statuses onto the non-executable Sweep parent."""

        parent = self.connection.execute(
            """SELECT sp.sweep_parent_id, sp.parent_run_id, r.status, r.revision
            FROM sweep_parent sp JOIN run r ON r.run_id = sp.parent_run_id
            JOIN sweep_member sm ON sm.sweep_parent_id = sp.sweep_parent_id
            WHERE sm.child_run_id = ?""",
            (child_run_id,),
        ).fetchone()
        if parent is None:
            return
        child_rows = self.connection.execute(
            "SELECT r.status FROM sweep_member sm JOIN run r ON r.run_id = sm.child_run_id "
            "WHERE sm.sweep_parent_id = ? ORDER BY sm.ordinal",
            (parent["sweep_parent_id"],),
        ).fetchall()
        statuses = tuple(str(row["status"]) for row in child_rows)
        terminal = {
            RunStatus.SUCCEEDED.value,
            RunStatus.FAILED.value,
            RunStatus.STOPPED.value,
            RunStatus.CANCELLED.value,
            RunStatus.RECOVERY_REQUIRED.value,
            RunStatus.PARTIAL_FAILED.value,
        }
        if not statuses or not all(status in terminal for status in statuses):
            return
        if all(status == RunStatus.SUCCEEDED.value for status in statuses):
            target = RunStatus.SUCCEEDED
        elif any(status == RunStatus.SUCCEEDED.value for status in statuses):
            target = RunStatus.PARTIAL_FAILED
        elif any(status == RunStatus.RECOVERY_REQUIRED.value for status in statuses):
            target = RunStatus.RECOVERY_REQUIRED
        elif any(status in {RunStatus.STOPPED.value, RunStatus.CANCELLED.value} for status in statuses):
            target = RunStatus.STOPPED
        else:
            target = RunStatus.FAILED
        current = RunStatus(parent["status"])
        if current == target:
            return
        ensure_transition(current, target, domain="run")
        now = _now()
        next_revision = parent["revision"] + 1
        self.connection.execute(
            "UPDATE run SET status = ?, revision = ?, updated_at = ? WHERE run_id = ? AND revision = ?",
            (target, next_revision, now, parent["parent_run_id"], parent["revision"]),
        )
        self._transition(
            parent["parent_run_id"],
            current,
            target,
            parent["revision"],
            next_revision,
            "SWEEP_CHILDREN_TERMINAL",
            actor_kind="sweep_aggregator",
        )
        self._audit(
            "sweep_parent",
            parent["sweep_parent_id"],
            "SWEEP_STATUS_PROJECTED",
            {"parent_status": target, "child_statuses": statuses},
            correlation_id=correlation_id,
            before_revision=parent["revision"],
            after_revision=next_revision,
        )


def _now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"

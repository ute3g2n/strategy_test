"""SQLite metadata persistence with transaction and idempotency boundaries.

Only Product/Application metadata is stored here.  Result bodies remain under
the frozen Core ResultStore contract and are represented by references and
hashes.  The store is intentionally small, synchronous, and dependency-free;
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

from .contracts import (
    CancelJobCommand,
    CreateRunCommand,
    EvidenceReference,
    FailureView,
    JobStatus,
    JobView,
    QueueReceipt,
    ResultReference,
    RunStatus,
    RunView,
    StartJobCommand,
    canonical_hash,
    canonical_json,
    utc_now,
)
from .state_machine import ensure_transition

SCHEMA_VERSION = "p4-metadata-v1"


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
                    checksum TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS run (
                    run_id TEXT PRIMARY KEY,
                    run_kind TEXT NOT NULL CHECK(run_kind IN ('SINGLE_BACKTEST', 'SWEEP_CHILD')),
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 0),
                    condition_sha256 TEXT NOT NULL,
                    manifest_sha256 TEXT NOT NULL,
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
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS job (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision >= 0),
                    attempt INTEGER NOT NULL CHECK(attempt >= 0),
                    operation TEXT NOT NULL,
                    request_fingerprint TEXT NOT NULL,
                    expected_revision INTEGER,
                    checkpoint_sha256 TEXT,
                    failure_code TEXT,
                    failure_message_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(operation, request_fingerprint)
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
                    manifest_sha256 TEXT NOT NULL,
                    commit_marker_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(job_id, sequence_no)
                );
                CREATE TABLE IF NOT EXISTS result_reference (
                    run_id TEXT PRIMARY KEY REFERENCES run(run_id) ON DELETE CASCADE,
                    relative_root TEXT NOT NULL,
                    manifest_sha256 TEXT NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    commit_marker_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_reference (
                    evidence_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES run(run_id) ON DELETE CASCADE,
                    job_id TEXT REFERENCES job(job_id),
                    relative_root TEXT NOT NULL,
                    evidence_sha256 TEXT NOT NULL,
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
                    source_result_sha256 TEXT NOT NULL,
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
                    fingerprint TEXT NOT NULL,
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
                    payload_sha256 TEXT NOT NULL,
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
                ("P4-MIG-001", SCHEMA_VERSION, "FORWARD_ONLY", canonical_hash(SCHEMA_VERSION), _now()),
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                aggregate_kind,
                aggregate_id,
                event_type,
                correlation_id,
                before_revision,
                after_revision,
                payload_json,
                canonical_hash(payload),
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                from_status,
                to_status,
                expected_revision,
                resulting_revision,
                reason_code,
                actor_kind,
                canonical_hash({"from": from_status, "to": to_status, "revision": resulting_revision}),
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
                row["request_fingerprint"],
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
        request_fingerprint = canonical_hash(
            {
                "kind": command.run_kind,
                "config": command.config.fingerprint_payload(),
                "preflight": command.preflight_report_sha256,
            }
        )
        with self.transaction():
            existing = self._idempotency("create_run", command.client_request_id)
            if existing:
                if existing["fingerprint"] != request_fingerprint:
                    raise PersistenceConflict("IDEMPOTENCY_FINGERPRINT_CONFLICT")
                row = self._run_row(existing["target_id"])
                if row is None:
                    raise PersistenceConflict("IDEMPOTENCY_TARGET_MISSING")
                return self._view_from_run(row), True
            run_id = _new_id("run")
            condition_sha = canonical_hash(command.config.fingerprint_payload())
            now = _now()
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
                    command.preflight_report_sha256,
                    canonical_json(asdict(command.config)),
                    now,
                    now,
                ),
            )
            self.connection.execute(
                "INSERT INTO run_condition(run_id, condition_sha256, config_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, condition_sha, canonical_json(asdict(command.config)), now),
            )
            self.connection.execute(
                """INSERT INTO idempotency_record
                (idempotency_id, scope, request_key, fingerprint, target_kind, target_id, response_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    "create_run",
                    command.client_request_id,
                    request_fingerprint,
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
                    "request_fingerprint": request_fingerprint,
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
            existing = self._idempotency("start_job", command.request_fingerprint)
            if existing:
                if existing["fingerprint"] != command.request_fingerprint:
                    raise PersistenceConflict("IDEMPOTENCY_FINGERPRINT_CONFLICT")
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
                """INSERT INTO job(job_id, run_id, status, revision, attempt, operation, request_fingerprint,
                expected_revision, checkpoint_sha256, failure_code, failure_message_id, created_at, updated_at)
                VALUES (?, ?, ?, 0, 0, 'BACKTEST', ?, ?, NULL, NULL, NULL, ?, ?)""",
                (
                    job_id,
                    command.run_id,
                    JobStatus.QUEUED,
                    command.request_fingerprint,
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
                    command.request_fingerprint,
                    command.request_fingerprint,
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
                    "request_fingerprint": command.request_fingerprint,
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
            self.connection.execute(
                "UPDATE queue_item SET status = 'DONE', updated_at = ? WHERE job_id = ?", (now, job_id)
            )
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
            updated = self.connection.execute("SELECT * FROM job WHERE job_id = ?", (job_id,)).fetchone()
            assert updated is not None
            return self._job_view(updated)


def _now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"

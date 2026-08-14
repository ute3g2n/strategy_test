from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from scripts.context_index.build_code_manifest import build_code_manifest
from scripts.context_index.build_context_index import build_index, build_state
from scripts.context_index.build_relation_graph import build_relation_graph
from scripts.context_index.check_context_gate import main as gate_main
from scripts.context_index.common import stable_id
from scripts.context_index.context_watch import main as context_watch_main


@pytest.fixture()
def policy() -> dict[str, object]:
    return {
        "schema_version": "ctxmap-policy-v0.1",
        "generator_version": "ctxmap-indexer-v0.1",
        "managed_extensions": [".md", ".html"],
        "managed_roots": ["docs"],
        "managed_source_roots": ["src", "config"],
        "managed_source_extensions": [".py", ".js", ".sh"],
        "managed_config_extensions": [".json"],
        "exclude_dirs": [".git", "node_modules", ".venv", "third_party"],
        "source_exclude_dirs": [".git", "node_modules", ".venv", "third_party"],
        "source_exclude_paths": [],
        "max_file_bytes": 20_000,
        "source_max_file_bytes": 20_000,
        "major_change_ratio": 0.20,
        "a07_min_confidence": 0.70,
        "secret_path_patterns": [".env", ".pem", ".key", "id_rsa", "credentials"],
        "secret_content_patterns": [
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
            r"\bAKIA[0-9A-Z]{16}\b",
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=_-]{8,}",
        ],
    }


def write_file(root: Path, relative_path: str, content: str) -> None:
    target = root / Path(relative_path.replace("/", os.sep))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def prepare_index(root: Path, policy: dict[str, object]) -> dict[str, Path]:
    docs = build_index(root, policy, observed_at="2026-08-14T00:00:00Z")
    state = build_state(docs, "2026-08-14T00:00:00Z")
    code = build_code_manifest(root, policy, observed_at="2026-08-14T00:00:00Z")
    graph = build_relation_graph(code, docs)
    context_dir = root / "context"
    paths = {
        "root": root,
        "policy": context_dir / "context_policy.json",
        "manifest": context_dir / "artifact_manifest.json",
        "state": context_dir / "manifest_state.json",
        "code": context_dir / "code_manifest.json",
        "graph": context_dir / "relation_graph.json",
        "report": root / "gate_report.json",
    }
    write_json(paths["policy"], policy)
    write_json(paths["manifest"], docs)
    write_json(paths["state"], state)
    write_json(paths["code"], code)
    write_json(paths["graph"], graph)
    return paths


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    )


def init_git(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "ctxmap-test")
    git(root, "add", "--", ".")
    git(root, "commit", "-qm", "baseline")


def decision_for(path: str, source_hash: str, existing: dict[str, Any] | None, action: str) -> dict[str, Any]:
    artifact_id = existing["artifact_id"] if existing else stable_id("art", f"document:{path}")
    return {
        "artifact_id": artifact_id,
        "action": action,
        "summary": "fixture summary",
        "purpose": "fixture purpose",
        "triggers": ["document_change"],
        "headings": [{"level": 1, "text": "Fixture", "line": 1}],
        "relations": [],
        "confidence": 0.95,
        "reason": "fixture decision",
        "source_hash": source_hash,
        "receipt": {"agent_id": "fixture-a07", "model": "gpt-5.1", "status": "completed"},
    }


def gate_args(paths: dict[str, Path], changed: str, *extra: str) -> list[str]:
    return [
        "--root",
        str(paths["root"]),
        "--policy",
        str(paths["policy"]),
        "--manifest",
        str(paths["manifest"]),
        "--state",
        str(paths["state"]),
        "--code-manifest",
        str(paths["code"]),
        "--relation-graph",
        str(paths["graph"]),
        "--report",
        str(paths["report"]),
        "--changed",
        changed,
        *extra,
    ]


def test_new_document_requires_a07_response_and_updates_only_explicit_outputs(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\noriginal\n")
    paths = prepare_index(tmp_path, policy)
    write_file(tmp_path, "docs/new.md", "# New\nnew document\n")
    source_hash = __import__("hashlib").sha256((tmp_path / "docs/new.md").read_bytes()).hexdigest()
    response = {
        "responses": {
            "docs/new.md": decision_for(
                "docs/new.md", source_hash, None, "record_add"
            )
        }
    }
    response_path = tmp_path / "a07.json"
    write_json(response_path, response)

    assert gate_main(gate_args(paths, "docs/new.md", "--a07-responses", str(response_path))) == 0
    report = json.loads(paths["report"].read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert "docs/new.md" in report["allowed_paths"]
    assert paths["manifest"].exists()
    assert any(
        item["relative_path"] == "docs/new.md"
        for item in json.loads(paths["manifest"].read_text(encoding="utf-8"))["artifacts"]
    )
    assert not any("safe_excerpt" in item for item in report.get("receipts", []))


def test_major_document_change_without_a07_is_pending_and_does_not_touch_index(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nsmall body\n")
    paths = prepare_index(tmp_path, policy)
    init_git(tmp_path)
    before_manifest = paths["manifest"].read_bytes()
    write_file(tmp_path, "docs/guide.md", "# New Guide\n" + ("expanded body " * 100) + "\n")

    result = gate_main(gate_args(paths, "docs/guide.md"))
    assert result == 1
    report = json.loads(paths["report"].read_text(encoding="utf-8"))
    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "A07_RUNTIME_UNAVAILABLE"
    assert paths["manifest"].read_bytes() == before_manifest
    assert git(tmp_path, "diff", "--cached", "--quiet").returncode == 0


def test_source_change_rebuilds_code_manifest_and_relation_graph(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "src/old.py", "def old():\n    return 1\n")
    paths = prepare_index(tmp_path, policy)
    write_file(tmp_path, "src/new.py", "def new():\n    return 2\n")

    assert gate_main(gate_args(paths, "src/new.py", "--snapshot-output", "snapshot.json")) == 0
    assert (tmp_path / "snapshot.json").exists()
    code = json.loads(paths["code"].read_text(encoding="utf-8"))
    assert any(item["relative_path"] == "src/new.py" for item in code["artifacts"])
    report = json.loads(paths["report"].read_text(encoding="utf-8"))
    assert report["source_manifest_updated"] is True
    assert "context/code_manifest.json" in report["allowed_paths"]


def test_secret_rename_and_delete_fail_closed(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "docs/old.md", "# Old\nbody\n")
    paths = prepare_index(tmp_path, policy)
    write_file(tmp_path, "docs/secret.md", "TOKEN=abcdefghijk\n")
    assert gate_main(gate_args(paths, "docs/secret.md")) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == "SECRET_CONTENT"

    (tmp_path / "docs/old.md").rename(tmp_path / "docs/renamed.md")
    assert gate_main(gate_args(paths, "docs/renamed.md")) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] in {
        "RENAME_OR_DELETE_REQUIRES_RECONCILIATION",
        "DOCUMENT_NOT_IN_MANIFEST",
    }


def test_gate_rejects_out_of_scope_and_invalid_manifest_inputs(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    paths = prepare_index(tmp_path, policy)
    assert gate_main(gate_args(paths, "personal.txt")) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == "OUT_OF_SCOPE_TARGET"
    paths["code"].write_text("not-json", encoding="utf-8")
    write_file(tmp_path, "src/new.py", "def new():\n    return 1\n")
    assert gate_main(gate_args(paths, "src/new.py")) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == "JSON_INPUT_INVALID"


def test_gate_rejects_external_control_input_paths(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    paths = prepare_index(tmp_path, policy)
    init_git(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-external-input.txt"
    outside.write_text("docs/guide.md\n", encoding="utf-8")

    assert gate_main(gate_args(paths, "docs/guide.md", "--changed-list", str(outside))) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == (
        "INPUT_PATH_OUTSIDE_REPOSITORY"
    )

    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    response_path = tmp_path.parent / f"{tmp_path.name}-external-a07.json"
    write_json(response_path, {"responses": {}})
    assert gate_main(gate_args(paths, "docs/new.md", "--a07-responses", str(response_path))) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == (
        "INPUT_PATH_OUTSIDE_REPOSITORY"
    )

    snapshot_path = tmp_path.parent / f"{tmp_path.name}-external-snapshot.json"
    write_json(snapshot_path, {"schema_version": "ctxmap-snapshot-v0.1", "paths": {}})
    baseline_args = [
        "--root",
        str(paths["root"]),
        "--policy",
        str(paths["policy"]),
        "--manifest",
        str(paths["manifest"]),
        "--state",
        str(paths["state"]),
        "--code-manifest",
        str(paths["code"]),
        "--relation-graph",
        str(paths["graph"]),
        "--report",
        str(paths["report"]),
        "--baseline-snapshot",
        str(snapshot_path),
    ]
    assert gate_main(baseline_args) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == (
        "INPUT_PATH_OUTSIDE_REPOSITORY"
    )


def test_gate_h1_requirement_fails_closed_before_work(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    paths = prepare_index(tmp_path, policy)
    assert gate_main(gate_args(paths, "docs/guide.md", "--require-h1")) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] == "H1_RECEIPT_MISSING"


def test_git_rename_status_is_parsed_and_blocked(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "docs/old.md", "# Old\nbody\n")
    paths = prepare_index(tmp_path, policy)
    init_git(tmp_path)
    git(tmp_path, "mv", "--", "docs/old.md", "docs/new.md")
    assert gate_main(gate_args(paths, "docs/new.md")) == 1
    assert (
        json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"]
        == "RENAME_OR_DELETE_REQUIRES_RECONCILIATION"
    )


def test_generated_manifest_path_is_ignored_by_watch_loop() -> None:
    from scripts.context_index.context_watch import is_generated_path

    assert is_generated_path("context/artifact_manifest.json")
    assert is_generated_path("plan/context_index/runtime/pending.json")
    assert not is_generated_path("docs/guide.md")


def test_snapshot_tracks_only_hashes_and_detects_source_change(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    from scripts.context_index.check_context_gate import capture_worktree_snapshot
    from scripts.context_index.context_watch import _changed_since

    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    write_file(tmp_path, "src/tool.py", "def tool():\n    return 1\n")
    before = capture_worktree_snapshot(tmp_path, policy)
    write_file(tmp_path, "src/tool.py", "def tool():\n    return 2\n")
    after = capture_worktree_snapshot(tmp_path, policy)
    assert _changed_since(before, after) == ["src/tool.py"]
    assert set(before["paths"]["docs/guide.md"]) == {"exists", "sha256"}


def test_gate_report_allowlist_is_revalidated(tmp_path: Path, policy: dict[str, object]) -> None:
    from scripts.context_index.check_context_gate import (
        GateError,
        approved_paths_from_report,
        verify_index_matches_report,
    )

    report = tmp_path / "report.json"
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    write_json(
        report,
        {
            "schema_version": "ctxmap-gate-report-v0.1",
            "status": "PASS",
            "allowed_paths": ["docs/guide.md"],
            "approved_hashes": {
                "docs/guide.md": hashlib.sha256(b"# Guide\nbody\n").hexdigest()
            },
        },
    )
    assert approved_paths_from_report(report, tmp_path) == ["docs/guide.md"]
    with pytest.raises(GateError, match="GATE_CONTENT_CHANGED"):
        write_file(tmp_path, "docs/guide.md", "# Changed\nbody\n")
        approved_paths_from_report(report, tmp_path)
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    init_git(tmp_path)
    write_file(tmp_path, "docs/guide.md", "# Tampered\nbody\n")
    git(tmp_path, "add", "--", "docs/guide.md")
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    with pytest.raises(GateError, match="GATE_INDEX_CONTENT_CHANGED"):
        verify_index_matches_report(report, tmp_path)
    write_json(
        report,
        {
            "schema_version": "ctxmap-gate-report-v0.1",
            "status": "PASS",
            "allowed_paths": ["../outside.txt"],
        },
    )
    with pytest.raises(GateError):
        approved_paths_from_report(report, tmp_path)
    write_json(
        report,
        {
            "schema_version": "ctxmap-gate-report-v0.1",
            "status": "BLOCKED",
            "allowed_paths": ["docs/guide.md"],
        },
    )
    with pytest.raises(GateError, match="GATE_REPORT_NOT_APPROVED"):
        approved_paths_from_report(report, tmp_path)


def test_watch_loop_propagates_event_failure_to_process_exit(
    tmp_path: Path, policy: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.context_index.context_watch as context_watch

    write_json(tmp_path / "context" / "context_policy.json", policy)
    snapshots = iter(
        [
            {"schema_version": "ctxmap-snapshot-v0.1", "paths": {}},
            {
                "schema_version": "ctxmap-snapshot-v0.1",
                "paths": {"docs/guide.md": {"exists": True, "sha256": "changed"}},
            },
        ]
    )
    monkeypatch.setattr(context_watch, "capture_worktree_snapshot", lambda *_args: next(snapshots))
    monkeypatch.setattr(context_watch, "process_event", lambda *_args: 1)
    args = SimpleNamespace(
        policy=Path("context/context_policy.json"),
        h1_receipt=Path("h1.json"),
        max_cycles=1,
        poll_interval=0.01,
        debounce=0.0,
        a07_responses=None,
        no_commit=True,
        no_push=True,
    )

    assert context_watch.watch_loop(tmp_path, args) == 1


def test_stale_lock_recovery_requires_dead_pid_and_is_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.context_index.context_watch import LOCK_PATH, recover_stale_lock

    lock = tmp_path / LOCK_PATH
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("12345", encoding="ascii")
    monkeypatch.setattr(os, "kill", lambda _pid, _signal: (_ for _ in ()).throw(ProcessLookupError()))

    assert recover_stale_lock(tmp_path) is True
    assert not lock.exists()


def test_h1_invalid_receipts_are_rejected_without_fallback(tmp_path: Path) -> None:
    from scripts.context_index.check_context_gate import GateError, require_h1_approval

    receipt = tmp_path / "h1.json"
    write_json(receipt, {"gate_id": "CTXMAP-H1", "status": "PENDING", "approval_text": "CTXMAP-H1を承認します"})
    with pytest.raises(GateError, match="H1_NOT_APPROVED"):
        require_h1_approval(tmp_path, receipt)


def test_symlink_target_is_rejected_when_platform_allows_symlinks(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    paths = prepare_index(tmp_path, policy)
    outside = tmp_path.parent / "ctxmap-outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    link = tmp_path / "docs" / "link.md"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")
    assert gate_main(gate_args(paths, "docs/link.md")) == 1
    assert json.loads(paths["report"].read_text(encoding="utf-8"))["reason_code"] in {
        "SYMLINK_PATH",
        "RENAME_OR_DELETE_REQUIRES_RECONCILIATION",
    }


def test_h1_start_is_rejected_until_approval_receipt_exists(tmp_path: Path) -> None:
    receipt = tmp_path / "h1.json"
    assert context_watch_main(["--root", str(tmp_path), "--check-start", "--h1-receipt", str(receipt)]) == 1
    write_json(
        receipt,
        {
            "gate_id": "CTXMAP-H1",
            "status": "APPROVED",
            "approval_text": "CTXMAP-H1を承認します",
        },
    )
    assert context_watch_main(["--root", str(tmp_path), "--check-start", "--h1-receipt", str(receipt)]) == 0


def test_watch_once_ignores_generated_event_and_watch_loop_serializes(tmp_path: Path) -> None:
    from scripts.context_index.check_context_gate import GateError
    from scripts.context_index.context_watch import (
        _acquire_lock,
        _changed_since,
        _write_pending,
    )

    policy = {
        "schema_version": "ctxmap-policy-v0.1",
        "generator_version": "ctxmap-indexer-v0.1",
        "managed_extensions": [".md", ".html"],
        "managed_roots": ["docs"],
        "managed_source_roots": ["src"],
        "managed_source_extensions": [".py"],
        "managed_config_extensions": [],
        "exclude_dirs": [".git"],
        "source_exclude_dirs": [".git"],
        "source_exclude_paths": [],
        "max_file_bytes": 20_000,
        "source_max_file_bytes": 20_000,
        "secret_path_patterns": [".env"],
        "secret_content_patterns": [],
    }
    write_json(tmp_path / "context" / "context_policy.json", policy)
    receipt = tmp_path / "h1.json"
    write_json(receipt, {"gate_id": "CTXMAP-H1", "status": "APPROVED", "approval_text": "CTXMAP-H1を承認します"})
    assert context_watch_main(
        [
            "--root",
            str(tmp_path),
            "--once",
            "--changed",
            "context/artifact_manifest.json",
            "--h1-receipt",
            str(receipt),
        ]
    ) == 0
    _write_pending(tmp_path, "PENDING", "TEST", ["docs/guide.md"])
    lock = _acquire_lock(tmp_path)
    try:
        with pytest.raises(GateError, match="WATCH_ALREADY_RUNNING"):
            _acquire_lock(tmp_path)
    finally:
        lock.unlink(missing_ok=True)
    assert _changed_since(
        {"paths": {"docs/a.md": {"sha256": "a"}}},
        {"paths": {"docs/a.md": {"sha256": "b"}}},
    ) == ["docs/a.md"]


def test_watch_loop_runs_one_local_cycle_and_records_auto_commit_pending(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    prepare_index(tmp_path, policy)
    shutil.copytree(Path(__file__).resolve().parents[2] / "scripts", tmp_path / "scripts")
    receipt = tmp_path / "h1.json"
    write_json(receipt, {"gate_id": "CTXMAP-H1", "status": "APPROVED", "approval_text": "CTXMAP-H1を承認します"})
    assert context_watch_main(
        [
            "--root",
            str(tmp_path),
            "--watch-commit",
            "--max-cycles",
            "1",
            "--poll-interval",
            "0.01",
            "--h1-receipt",
            str(receipt),
        ]
    ) == 0
    assert (tmp_path / "plan/context_index/runtime/context_watch_snapshot.json").exists()

    write_file(tmp_path, "src/new.py", "def new():\n    return 1\n")
    assert context_watch_main(
        [
            "--root",
            str(tmp_path),
            "--once",
            "--changed",
            "src/new.py",
            "--h1-receipt",
            str(receipt),
        ]
    ) == 1
    pending = json.loads(
        (tmp_path / "plan/context_index/runtime/context_watch_pending.json").read_text(encoding="utf-8")
    )
    assert pending["status"] == "BLOCKED"
    assert pending["reason_code"] == "AUTO_COMMIT_FAILED"


def test_watch_document_event_stays_pending_when_a07_is_unavailable(tmp_path: Path, policy: dict[str, object]) -> None:
    from scripts.context_index.context_watch import _run_auto_commit

    write_file(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    prepare_index(tmp_path, policy)
    shutil.copytree(Path(__file__).resolve().parents[2] / "scripts", tmp_path / "scripts")
    receipt = tmp_path / "h1.json"
    write_json(receipt, {"gate_id": "CTXMAP-H1", "status": "APPROVED", "approval_text": "CTXMAP-H1を承認します"})
    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    assert context_watch_main(
        [
            "--root",
            str(tmp_path),
            "--once",
            "--changed",
            "docs/new.md",
            "--h1-receipt",
            str(receipt),
        ]
    ) == 1
    pending = json.loads(
        (tmp_path / "plan/context_index/runtime/context_watch_pending.json").read_text(encoding="utf-8")
    )
    assert pending["reason_code"] == "A07_RUNTIME_UNAVAILABLE"
    assert _run_auto_commit(tmp_path, type("Args", (), {"no_commit": True, "no_push": True})()) == 1


def test_auto_commit_stages_only_gate_allowlist_and_never_user_untracked(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "src/base.py", "def base():\n    return 1\n")
    prepare_index(tmp_path, policy)
    init_git(tmp_path)
    write_file(tmp_path, "src/new.py", "def new():\n    return 2\n")
    write_file(tmp_path, "personal_notes.txt", "must not be staged\n")
    allowlist = tmp_path / "event_paths.txt"
    allowlist.write_text("src/new.py\n", encoding="utf-8", newline="\n")
    script_root = Path(__file__).resolve().parents[2]
    shutil.copy2(script_root / "auto-commit.sh", tmp_path / "auto-commit.sh")
    shutil.copytree(script_root / "scripts", tmp_path / "scripts")
    env = os.environ.copy()
    env["CTXMAP_PYTHON"] = sys.executable
    result = subprocess.run(
        ["bash", "auto-commit.sh", "--allowlist-file", "event_paths.txt", "--no-commit", "--no-push"],
        cwd=tmp_path,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    staged = set(git(tmp_path, "diff", "--cached", "--name-only").stdout.splitlines())
    assert "personal_notes.txt" not in staged
    assert "src/new.py" in staged
    assert "context/code_manifest.json" in staged

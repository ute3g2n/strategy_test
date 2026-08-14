from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from scripts.context_index.build_code_manifest import build_code_manifest, validate_code_manifest
from scripts.context_index.build_context_index import build_index, build_state
from scripts.context_index.check_context_gate import capture_worktree_snapshot, run_gate
from scripts.context_index.context_mcp_server import ContextMcpServer, McpRejected
from scripts.context_index.context_router import load_router_snapshot, route_request
from scripts.context_index.detect_code_delta import detect_code_delta
from scripts.context_index.detect_context_delta import detect_delta
from scripts.context_index.run_context_maintenance import main as maintenance_main
from scripts.context_index.run_context_maintenance import maintain_document
from scripts.context_index.validate_context_index import validate_manifest


def _policy() -> dict[str, object]:
    return {
        "schema_version": "ctxmap-policy-v0.1",
        "generator_version": "ctxmap-indexer-v0.1",
        "managed_extensions": [".md", ".html"],
        "managed_roots": ["docs"],
        "managed_source_roots": ["src"],
        "managed_source_extensions": [".py"],
        "managed_config_extensions": [".json"],
        "exclude_dirs": [".git", ".venv"],
        "source_exclude_dirs": [".git", ".venv"],
        "max_file_bytes": 100_000,
        "source_max_file_bytes": 100_000,
        "major_change_ratio": 0.20,
        "secret_path_patterns": [".env", ".pem", ".key"],
        "secret_content_patterns": [r"(?i)\btoken\s*[:=]", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"],
    }


def _write(root: Path, relative: str, content: str) -> None:
    target = root / Path(relative.replace("/", "\\"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def _empty_manifest() -> dict[str, object]:
    return {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}


def test_document_builder_state_and_validator_use_metadata_only(tmp_path: Path) -> None:
    policy = _policy()
    _write(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    manifest = build_index(tmp_path, policy, observed_at="2026-08-15T00:00:00Z")
    state = build_state(manifest, "2026-08-15T00:00:00Z")
    assert all("source_hash" not in record for record in manifest["artifacts"])
    assert all("source_hash" not in record for record in state["states"])

    _write(tmp_path, "docs/guide.md", "# Guide\nchanged body with the same heading\n")
    report = validate_manifest(manifest, tmp_path, policy, state=state)
    assert report.valid
    assert all(item["code"] not in {"STALE_HASH", "STATE_STALE"} for item in report.errors)


def test_metadata_maintenance_adds_and_updates_without_dispatch_or_hash(tmp_path: Path) -> None:
    policy = _policy()
    _write(tmp_path, "docs/new.md", "# New\nbody\n")
    result = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        _empty_manifest(),
        dispatcher=None,
        observed_at="2026-08-15T00:00:00Z",
    )
    assert result.status == "PASS"
    assert result.action == "record_add"
    assert "source_hash" not in result.manifest["artifacts"][0]
    assert "source_hash" not in result.receipt
    assert result.receipt["dispatch"]["status"] == "NOT_RUN"

    _write(tmp_path, "docs/new.md", "# New revised\nupdated body\n")
    updated = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        result.manifest,
        dispatcher=lambda _payload: pytest.fail("A07 must not be dispatched"),
        state=result.state,
        observed_at="2026-08-15T00:01:00Z",
    )
    assert updated.status == "PASS"
    assert updated.action == "record_update"
    assert "source_hash" not in updated.state["states"][0]


def test_document_delta_has_no_content_digest_fields(tmp_path: Path) -> None:
    policy = _policy()
    before_root = tmp_path / "before"
    after_root = tmp_path / "after"
    _write(before_root, "docs/guide.md", "# Guide\nold\n")
    _write(after_root, "docs/guide.md", "# Guide\nnew content with a different size\n")
    _write(after_root, "docs/new.md", "# New\nbody\n")
    deltas = detect_delta(before_root, after_root, policy)
    assert {item["change_kind"] for item in deltas} == {"modified_major", "added"}
    assert all(not any(key.endswith("hash") for key in item) for item in deltas)


def test_code_manifest_and_delta_use_structure_and_path_only(tmp_path: Path) -> None:
    policy = _policy()
    _write(tmp_path, "src/app.py", "def run():\n    return 1\n")
    before = build_code_manifest(tmp_path, policy, observed_at="2026-08-15T00:00:00Z")
    assert all("source_hash" not in record for record in before["artifacts"])
    assert validate_code_manifest(before, tmp_path, policy).valid
    _write(tmp_path, "src/app.py", "def run_changed():\n    return 2\n")
    after = build_code_manifest(tmp_path, policy, observed_at="2026-08-15T00:01:00Z", existing_manifest=before)
    assert validate_code_manifest(before, tmp_path, policy).valid
    changes = detect_code_delta(before, after)
    assert changes and changes[0]["change_kind"] == "modified_structural"
    assert all("hash" not in key for item in changes for key in item)


def test_gate_checks_path_secret_and_human_gate_without_digest(tmp_path: Path) -> None:
    policy = _policy()
    policy_path = tmp_path / "context_policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    _write(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    h1 = tmp_path / "h1.json"
    h1.write_text(json.dumps({"status": "APPROVED"}), encoding="utf-8")

    report = run_gate(tmp_path, policy_path, changed=["docs/guide.md"], require_h1=True, h1_receipt=h1)
    assert report["status"] == "PASS"
    assert "report_sha256" not in report
    assert "approved_hashes" not in report

    snapshot = capture_worktree_snapshot(tmp_path, policy)
    assert "snapshot_hash" not in snapshot
    assert all("sha" not in json.dumps(item).lower() for item in snapshot["paths"].values())

    _write(tmp_path, "docs/secret.md", "token: must stop\n")
    with pytest.raises(Exception, match="SECRET_CONTENT"):
        run_gate(tmp_path, policy_path, changed=["docs/secret.md"])


def test_router_and_mcp_use_nonhash_snapshot_and_bounded_reads(tmp_path: Path) -> None:
    policy = _policy()
    _write(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    _write(tmp_path, "src/app.py", "def run():\n    return 1\n")
    artifact = build_index(tmp_path, policy, observed_at="2026-08-15T00:00:00Z")
    code = build_code_manifest(tmp_path, policy, observed_at="2026-08-15T00:00:00Z")
    _write(tmp_path, "context/artifact_manifest.json", json.dumps(artifact, ensure_ascii=False))
    _write(tmp_path, "context/code_manifest.json", json.dumps(code, ensure_ascii=False))
    _write(tmp_path, "context/relation_graph.json", json.dumps({"status": "PASS", "edges": [], "nodes": []}))
    _write(tmp_path, "context/context_policy.json", json.dumps(policy, ensure_ascii=False))
    snapshot = load_router_snapshot(tmp_path, tmp_path / "context/context_policy.json")
    assert "snapshot_hash" not in snapshot
    routed = route_request("guide", snapshot)
    assert "manifest_snapshot_hash" not in routed
    artifact_id = artifact["artifacts"][0]["artifact_id"]
    server = ContextMcpServer.from_paths(root=tmp_path, policy=tmp_path / "context/context_policy.json")
    result = server.get_artifact(artifact_id, {"line_start": 1, "line_end": 1})
    assert "source_hash" not in result

    _write(tmp_path, "docs/guide.md", "token: blocked\n")
    with pytest.raises(McpRejected, match="SECRET_CONTENT"):
        server.get_artifact(artifact_id, {"line_start": 1, "line_end": 1})


def test_watch_and_auto_commit_entrypoints_do_not_perform_git_or_hash_flow(tmp_path: Path) -> None:
    policy = _policy()
    policy_path = tmp_path / "context_policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    h1 = tmp_path / "h1.json"
    h1.write_text(json.dumps({"status": "APPROVED"}), encoding="utf-8")
    _write(tmp_path, "docs/guide.md", "# Guide\nbody\n")
    from scripts.context_index.context_watch import main as watch_main

    assert watch_main(
        ["--root", str(tmp_path), "--policy", str(policy_path), "--h1-receipt", str(h1), "--check-start"]
    ) == 0
    assert watch_main(
        [
            "--root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--h1-receipt",
            str(h1),
            "--once",
            "--changed",
            "docs/guide.md",
        ]
    ) == 0

    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    assert maintenance_main(
        [
            "--root", str(tmp_path), "--policy", str(policy_path), "--manifest", str(manifest),
            "--output", str(manifest), "--receipt-output", str(receipt), "--changed", "docs/guide.md",
        ]
    ) == 0
    assert "source_hash" not in receipt.read_text(encoding="utf-8")

    completed = subprocess.run(
        ["bash", "./auto-commit.sh", "--watch-mode", "--no-commit", "--no-push"],
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "RETIRED" in completed.stdout

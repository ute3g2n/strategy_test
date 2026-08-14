from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from scripts.context_index.build_context_index import build_index, build_state
from scripts.context_index.common import stable_id
from scripts.context_index.run_context_maintenance import (
    A07DispatchError,
    maintain_document,
    process_delta,
)
from scripts.context_index.run_context_maintenance import (
    main as maintenance_main,
)
from scripts.context_index.run_context_maintenance import (
    _safe_dispatch_info,
)
from scripts.context_index.validate_context_index import validate_manifest


@pytest.fixture()
def policy() -> dict[str, object]:
    return {
        "schema_version": "ctxmap-policy-v0.1",
        "generator_version": "ctxmap-indexer-v0.1",
        "managed_extensions": [".md", ".html"],
        "managed_roots": ["docs"],
        "exclude_dirs": ["third_party", "node_modules", ".venv"],
        "max_file_bytes": 20_000,
        "major_change_ratio": 0.20,
        "a07_min_confidence": 0.70,
        "secret_path_patterns": [".env", ".pem", ".key", "id_rsa"],
        "secret_content_patterns": [
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
            r"\bAKIA[0-9A-Z]{16}\b",
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=_-]{8,}",
        ],
    }


def write_file(root: Path, relative_path: str, content: str) -> None:
    target = root / Path(relative_path.replace("/", "\\"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def decision_for(payload: dict[str, Any], *, action: str | None = None, confidence: float = 0.95) -> dict[str, Any]:
    existing = payload.get("existing_record")
    selected_action = action or ("record_add" if existing is None else "record_update")
    artifact_id = (
        existing["artifact_id"]
        if isinstance(existing, dict)
        else stable_id("art", f"document:{payload['relative_path']}")
    )
    return {
        "artifact_id": artifact_id,
        "action": selected_action,
        "summary": "approved summary",
        "purpose": "approved purpose",
        "triggers": ["document_change"],
        "headings": payload["structural_diff"].get("after_headings", []),
        "relations": [],
        "confidence": confidence,
        "reason": "fixture decision",
        "source_hash": payload["source_hash"],
        "receipt": {
            "agent_id": "fixture-a07",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "low",
            "status": "completed",
            "run_id": "fixture-run",
        },
    }


def test_active_a07_dispatch_profile_is_luna_low() -> None:
    dispatch_info = _safe_dispatch_info(attempts=1, status="completed")

    assert dispatch_info["model"] == "gpt-5.6-luna"
    assert dispatch_info["reasoning_effort"] == "low"


def test_new_markdown_and_html_require_a07_and_update_manifest(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/new.md", "# New\nA document.\n")
    calls: list[dict[str, Any]] = []

    def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
        calls.append(payload)
        return decision_for(payload)

    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}
    markdown = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        empty,
        dispatcher=dispatch,
        request_id="req-md",
        observed_at="2026-08-14T00:00:00Z",
    )
    write_file(tmp_path, "docs/new.html", "<title>New HTML</title><h1>New HTML</h1>")
    html = maintain_document(
        tmp_path,
        "docs/new.html",
        policy,
        markdown.manifest,
        dispatcher=dispatch,
        request_id="req-html",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert markdown.status == "PASS" and markdown.action == "record_add"
    assert html.status == "PASS" and html.action == "record_add"
    assert len(calls) == 2
    assert set(calls[0]) == {
        "relative_path",
        "kind",
        "source_hash",
        "structural_diff",
        "existing_record",
        "safe_excerpt",
        "request_id",
        "schema_version",
        "generator_version",
        "input_hash",
    }
    assert len(calls[0]["safe_excerpt"]) <= 18_000
    assert validate_manifest(html.manifest, tmp_path, policy).valid
    assert "A document" not in json.dumps(markdown.receipt)


def test_major_change_requires_a07_update_or_metadata_unchanged(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Guide\nold body\n")
    before = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    write_file(tmp_path, "docs/guide.md", "# New Guide\n" + ("new body " * 30) + "\nREQ-NEW-001\n")

    updated = maintain_document(
        tmp_path,
        "docs/guide.md",
        policy,
        before,
        dispatcher=lambda payload: decision_for(payload, action="record_update"),
        request_id="req-major-update",
        observed_at="2026-08-14T00:01:00Z",
    )
    assert updated.status == "PASS" and updated.action == "record_update"
    assert updated.manifest["artifacts"][0]["artifact_id"] == before["artifacts"][0]["artifact_id"]
    assert updated.manifest["artifacts"][0]["summary"] == "approved summary"

    unchanged = maintain_document(
        tmp_path,
        "docs/guide.md",
        policy=policy,
        manifest=before,
        dispatcher=lambda payload: decision_for(payload, action="metadata_unchanged"),
        request_id="req-major-unchanged",
        observed_at="2026-08-14T00:01:00Z",
    )
    assert unchanged.status == "PASS" and unchanged.action == "metadata_unchanged"


def test_minor_change_updates_hash_without_rewriting_semantic_metadata(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/note.md", "# Note\nold\n")
    before = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    old_record = before["artifacts"][0]
    write_file(tmp_path, "docs/note.md", "# Note\nnew\n")
    result = maintain_document(
        tmp_path,
        "docs/note.md",
        policy,
        before,
        dispatcher=None,
        request_id="req-minor",
        observed_at="2026-08-14T00:01:00Z",
    )
    record = result.manifest["artifacts"][0]
    assert result.status == "PASS" and result.action == "metadata_unchanged"
    assert record["source_hash"] != old_record["source_hash"]
    assert record["summary"] == old_record["summary"]
    assert result.receipt["dispatch"]["status"] == "NOT_REQUIRED"


def test_unavailable_a07_blocks_new_and_major_without_partial_manifest(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}
    result = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        empty,
        dispatcher=None,
        request_id="req-blocked",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert result.status == "BLOCKED"
    assert result.action == "blocked"
    assert result.manifest == empty
    assert result.receipt["reason_code"] == "RUNTIME_DISPATCH_FALLBACK_REQUIRED"
    assert "body" not in json.dumps(result.receipt)


@pytest.mark.parametrize(
    "bad_decision",
    [
        {"summary": None},
        {"action": "record_add", "extra": "reject"},
        {"action": "record_add", "confidence": 0.2},
        {"action": "record_add", "source_hash": "0" * 64},
    ],
)
def test_invalid_a07_output_is_fail_closed(
    tmp_path: Path, policy: dict[str, object], bad_decision: dict[str, Any]
) -> None:
    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}

    def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
        value = decision_for(payload)
        value.update(bad_decision)
        return value

    result = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        empty,
        dispatcher=dispatch,
        request_id="req-invalid",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert result.status == "BLOCKED"
    assert result.manifest == empty
    assert result.receipt["reason_code"] in {"A07_OUTPUT_INVALID", "A07_CONFIDENCE_INSUFFICIENT"}


def test_secret_and_invalid_path_are_rejected_without_receipt_leak(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/secret.md", "TOKEN=abcdefghijk\n")
    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}
    secret = maintain_document(
        tmp_path,
        "docs/secret.md",
        policy,
        empty,
        dispatcher=lambda payload: pytest.fail("A07 must not start"),
        request_id="req-secret",
        observed_at="2026-08-14T00:00:00Z",
    )
    traversal = maintain_document(
        tmp_path,
        "../outside.md",
        policy,
        empty,
        dispatcher=lambda payload: pytest.fail("A07 must not start"),
        request_id="req-path",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert secret.status == "BLOCKED" and secret.receipt["reason_code"] == "SECRET_CONTENT"
    assert traversal.status == "BLOCKED" and traversal.receipt["reason_code"] == "PATH_TRAVERSAL"
    assert "abcdefghijk" not in json.dumps(secret.receipt)
    assert "C:\\" not in json.dumps(traversal.receipt)


def test_excluded_document_is_rejected_before_a07(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/third_party/vendor.md", "# Vendor\n")
    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}
    result = maintain_document(
        tmp_path,
        "docs/third_party/vendor.md",
        policy,
        empty,
        dispatcher=lambda payload: pytest.fail("A07 must not start"),
        request_id="req-excluded",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert result.status == "BLOCKED"
    assert result.receipt["reason_code"] == "OUT_OF_SCOPE"


def test_timeout_retries_are_bounded_and_sanitized(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}
    attempts = 0

    def retry_once(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise A07DispatchError("TIMEOUT", "secret stdout and C:\\Users\\user\\private")
        return decision_for(payload)

    result = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        empty,
        dispatcher=retry_once,
        max_attempts=2,
        request_id="req-retry",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert result.status == "PASS" and attempts == 2
    assert result.receipt["dispatch"]["attempts"] == 2
    assert "Users" not in json.dumps(result.receipt)

    write_file(tmp_path, "docs/other.md", "# Other\nbody\n")
    result = maintain_document(
        tmp_path,
        "docs/other.md",
        policy,
        empty,
        dispatcher=lambda payload: (_ for _ in ()).throw(A07DispatchError("TIMEOUT", "token=hidden")),
        max_attempts=2,
        request_id="req-retry-fail",
        observed_at="2026-08-14T00:00:00Z",
    )
    assert result.status == "BLOCKED" and result.receipt["dispatch"]["attempts"] == 2
    assert "hidden" not in json.dumps(result.receipt)


def test_replay_conflict_is_blocked_and_same_replay_is_idempotent(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    empty = {"schema_version": "ctxmap-manifest-v0.1", "generator_version": "ctxmap-indexer-v0.1", "artifacts": []}
    source_hash = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")["artifacts"][0]["source_hash"]
    history = [{"request_id": "req-replay", "source_hash": source_hash, "status": "PASS"}]
    first = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        empty,
        dispatcher=lambda payload: decision_for(payload),
        request_id="req-replay",
        observed_at="2026-08-14T00:00:00Z",
    )
    history = [{"request_id": "req-replay", "source_hash": source_hash, "status": "PASS"}]
    same = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        first.manifest,
        dispatcher=None,
        request_id="req-replay",
        history=history,
        observed_at="2026-08-14T00:00:00Z",
    )
    assert same.status == "PASS" and same.action == "idempotent_replay"
    conflict = maintain_document(
        tmp_path,
        "docs/new.md",
        policy,
        empty,
        dispatcher=None,
        request_id="req-replay",
        history=[{"request_id": "req-replay", "source_hash": "1" * 64, "status": "PASS"}],
        observed_at="2026-08-14T00:00:00Z",
    )
    assert conflict.status == "BLOCKED" and conflict.receipt["reason_code"] == "REPLAY_CONFLICT"


def test_rename_and_delete_delta_preserve_history_without_a07(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/old.md", "# Same\nbody\n")
    before = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    old_id = before["artifacts"][0]["artifact_id"]
    (tmp_path / "docs" / "old.md").rename(tmp_path / "docs" / "new.md")
    renamed = process_delta(
        tmp_path,
        policy,
        before,
        {"change_kind": "renamed", "before_path": "docs/old.md", "after_path": "docs/new.md"},
        request_id="req-rename",
        observed_at="2026-08-14T00:01:00Z",
    )
    assert renamed.status == "PASS" and renamed.action == "renamed"
    assert renamed.manifest["artifacts"][0]["relative_path"] == "docs/new.md"
    assert renamed.manifest["artifacts"][0]["artifact_id"] == old_id
    assert validate_manifest(renamed.manifest, tmp_path, policy).valid

    (tmp_path / "docs" / "new.md").unlink()
    deleted = process_delta(
        tmp_path,
        policy,
        renamed.manifest,
        {"change_kind": "deleted", "before_path": "docs/new.md"},
        request_id="req-delete",
        observed_at="2026-08-14T00:02:00Z",
    )
    assert deleted.status == "PASS" and deleted.action == "deleted"
    assert deleted.manifest["artifacts"][0]["status"] == "deleted"
    assert validate_manifest(deleted.manifest, tmp_path, policy).valid


def test_state_hash_is_updated_when_state_is_supplied(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/note.md", "# Note\nold\n")
    before = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    state = build_state(before, "2026-08-14T00:00:00Z")
    write_file(tmp_path, "docs/note.md", "# Note\nnew\n")
    result = maintain_document(
        tmp_path,
        "docs/note.md",
        policy,
        before,
        state=state,
        dispatcher=None,
        request_id="req-state",
        observed_at="2026-08-14T00:01:00Z",
    )
    assert result.status == "PASS"
    assert result.state is not None
    assert result.state["states"][0]["source_hash"] == result.manifest["artifacts"][0]["source_hash"]


def test_cli_writes_sanitized_blocked_receipt_and_does_not_write_manifest(
    tmp_path: Path, policy: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    write_file(tmp_path, "docs/new.md", "# New\nbody\n")
    policy_path = tmp_path / "context_policy.json"
    manifest_path = tmp_path / "context" / "manifest.json"
    output_path = tmp_path / "context" / "next-manifest.json"
    receipt_path = tmp_path / "context" / "receipts" / "new.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    exit_code = maintenance_main(
        [
            "--root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
            "--receipt-output",
            str(receipt_path),
            "--changed",
            "docs/new.md",
            "--request-id",
            "req-cli",
            "--observed-at",
            "2026-08-14T00:00:00Z",
        ]
    )
    assert exit_code == 1
    assert receipt_path.exists()
    assert not output_path.exists()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["reason_code"] == "RUNTIME_DISPATCH_FALLBACK_REQUIRED"
    assert "body" not in json.dumps(receipt)
    assert '"status": "BLOCKED"' in capsys.readouterr().out


def test_cli_processes_delta_and_writes_manifest_atomically(
    tmp_path: Path, policy: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    write_file(tmp_path, "docs/old.md", "# Same\nbody\n")
    before = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    (tmp_path / "docs" / "old.md").rename(tmp_path / "docs" / "new.md")
    policy_path = tmp_path / "context_policy.json"
    manifest_path = tmp_path / "context" / "manifest.json"
    output_path = tmp_path / "context" / "next-manifest.json"
    delta_path = tmp_path / "context" / "delta.json"
    receipt_path = tmp_path / "context" / "receipts" / "rename.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(before), encoding="utf-8")
    delta_path.write_text(
        json.dumps(
            {
                "change_kind": "renamed",
                "before_path": "docs/old.md",
                "after_path": "docs/new.md",
            }
        ),
        encoding="utf-8",
    )
    assert (
        maintenance_main(
            [
                "--root",
                str(tmp_path),
                "--policy",
                str(policy_path),
                "--manifest",
                str(manifest_path),
                "--output",
                str(output_path),
                "--receipt-output",
                str(receipt_path),
                "--delta-json",
                str(delta_path),
                "--request-id",
                "req-cli-rename",
                "--observed-at",
                "2026-08-14T00:01:00Z",
            ]
        )
        == 0
    )
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["artifacts"][0]["relative_path"] == "docs/new.md"
    assert '"status": "PASS"' in capsys.readouterr().out

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.context_index.build_context_index import (
    PolicyViolation,
    build_index,
    normalize_relative_path,
)
from scripts.context_index.detect_context_delta import detect_delta
from scripts.context_index.query_context import QueryRejected, query_manifest
from scripts.context_index.validate_context_index import (
    ManifestInputError,
    load_manifest_file,
    validate_manifest,
)


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


def test_normalize_windows_relative_path_and_reject_escape() -> None:
    assert normalize_relative_path(r"docs\guide.md") == "docs/guide.md"
    assert normalize_relative_path("docs/guide.md") == "docs/guide.md"
    with pytest.raises(PolicyViolation):
        normalize_relative_path("../outside.md")
    with pytest.raises(PolicyViolation):
        normalize_relative_path(r"C:\outside.md")
    with pytest.raises(PolicyViolation):
        normalize_relative_path("/absolute.md")


def test_build_index_extracts_document_metadata_and_is_reproducible(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(
        tmp_path,
        "docs/guide.md",
        "# Guide\n\n## Scope\nThis is a guide.\n\nSee [HTML](./page.html).\n\nREQ-CTX-001 DEC-CTX-002\n",
    )
    write_file(tmp_path, "docs/page.html", "<html><head><title>Page</title></head><body><h1>Page</h1><h2>Use</h2></body></html>\n")
    first = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    second = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")

    assert first == second
    assert [r["relative_path"] for r in first["artifacts"]] == ["docs/guide.md", "docs/page.html"]
    guide = first["artifacts"][0]
    assert guide["title"] == "Guide"
    assert [(h["level"], h["text"]) for h in guide["headings"]] == [(1, "Guide"), (2, "Scope")]
    assert guide["line_count"] == 8
    assert guide["local_links"] == ["docs/page.html"]
    assert guide["trace_ids"] == ["REQ-CTX-001", "DEC-CTX-002"]
    assert len(guide["source_hash"]) == 64


def test_build_index_excludes_third_party_and_rejects_secret_file(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/ok.md", "# OK\n")
    write_file(tmp_path, "docs/third_party/vendor.md", "# Vendor\n")
    policy["exclude_dirs"] = ["third_party", "node_modules", ".venv"]
    indexed = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    assert [r["relative_path"] for r in indexed["artifacts"]] == ["docs/ok.md"]

    write_file(tmp_path, "docs/.env", "TOKEN=not-a-real-secret\n")
    with pytest.raises(PolicyViolation) as exc:
        build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    assert "not-a-real-secret" not in str(exc.value)


def test_detect_delta_distinguishes_small_heading_large_and_trace_changes(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    write_file(before, "docs/note.md", "# Note\nsmall\n")
    write_file(after, "docs/note.md", "# Note\nsmall change\n")
    small = detect_delta(before, after, policy)
    assert small[0]["change_kind"] == "modified_minor"
    assert small[0]["major_change"] is False

    write_file(after, "docs/note.md", "# Changed\nsmall change\n")
    heading = detect_delta(before, after, policy)
    assert heading[0]["change_kind"] == "modified_major"
    assert heading[0]["major_change"] is True

    write_file(after, "docs/note.md", "# Note\n" + ("x" * 100) + "\n")
    large = detect_delta(before, after, policy)
    assert large[0]["change_kind"] == "modified_major"

    write_file(after, "docs/note.md", "# Note\nREQ-NEW-001\n")
    trace = detect_delta(before, after, policy)
    assert trace[0]["change_kind"] == "modified_major"


def test_detect_delta_reports_rename_and_delete_deterministically(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    write_file(before, "docs/old.md", "# Same\n")
    write_file(before, "docs/deleted.md", "# Deleted\n")
    write_file(after, "docs/new.md", "# Same\n")
    deltas = detect_delta(before, after, policy)
    assert [d["change_kind"] for d in deltas] == ["renamed", "deleted"]
    assert deltas[0]["before_path"] == "docs/old.md"
    assert deltas[0]["after_path"] == "docs/new.md"
    assert deltas[1]["relative_path"] == "docs/deleted.md"


def test_validate_manifest_detects_unregistered_document_and_stale_hash(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/registered.md", "# Registered\n")
    manifest = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    assert validate_manifest(manifest, tmp_path, policy).valid

    write_file(tmp_path, "docs/unregistered.md", "# New\n")
    report = validate_manifest(manifest, tmp_path, policy)
    assert not report.valid
    assert any(error["code"] == "UNREGISTERED_DOCUMENT" for error in report.errors)

    write_file(tmp_path, "docs/registered.md", "# Changed\n")
    stale = validate_manifest(
        {**manifest, "artifacts": [dict(manifest["artifacts"][0])]}, tmp_path, policy
    )
    assert not stale.valid
    assert any(error["code"] == "STALE_HASH" for error in stale.errors)


def test_validate_manifest_rejects_schema_error_and_malformed_json(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/registered.md", "# Registered\n")
    manifest = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    invalid = json.loads(json.dumps(manifest))
    del invalid["artifacts"][0]["source_hash"]
    report = validate_manifest(invalid, tmp_path, policy)
    assert not report.valid
    assert any(error["code"] == "SCHEMA_INVALID" for error in report.errors)

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ManifestInputError):
        load_manifest_file(malformed)


def test_query_uses_manifest_metadata_only_and_rejects_traversal(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Routing Guide\ninternal body\n")
    manifest = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    results = query_manifest(manifest, "routing")
    assert len(results) == 1
    assert "internal body" not in json.dumps(results)
    with pytest.raises(QueryRejected):
        query_manifest(manifest, "../guide")

# ruff: noqa: E402

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="Legacy context hash contract; superseded by nonhash runtime tests")
from scripts.context_index.build_context_index import (
    PolicyViolation,
    build_index,
    build_record,
    build_state,
    write_json,
)
from scripts.context_index.build_context_index import (
    main as build_main,
)
from scripts.context_index.common import (
    SecretDetected,
    assert_safe_document,
    ensure_repo_path,
    extract_headings,
    extract_local_links,
    extract_summary,
    extract_title,
    extract_trace_ids,
    is_managed_document,
    load_policy,
    normalize_relative_path,
    scan_secret_content,
    scan_secret_path,
)
from scripts.context_index.detect_context_delta import detect_delta
from scripts.context_index.detect_context_delta import main as delta_main
from scripts.context_index.query_context import (
    QueryRejected,
    query_manifest,
    validate_path_filter,
)
from scripts.context_index.query_context import (
    main as query_main,
)
from scripts.context_index.validate_context_index import (
    ManifestInputError,
    load_manifest_file,
    validate_manifest,
)
from scripts.context_index.validate_context_index import (
    main as validate_main,
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
    write_file(
        tmp_path,
        "docs/page.html",
        "<html><head><title>Page</title></head><body><h1>Page</h1><h2>Use</h2></body></html>\n",
    )
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
    write_file(after, "docs/note.md", "# Note\nsmall!\n")
    small = detect_delta(before, after, policy)
    assert small[0]["change_kind"] == "modified_minor"
    assert small[0]["major_change"] is False

    write_file(after, "docs/note.md", "# Changed\nsmall!\n")
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


def test_policy_loading_and_scope_filters(tmp_path: Path, policy: dict[str, object]) -> None:
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, policy)
    assert load_policy(policy_path)["schema_version"] == "ctxmap-policy-v0.1"
    assert is_managed_document("docs/note.md", policy)
    assert not is_managed_document("docs/note.txt", policy)
    assert not is_managed_document("docs/third_party/note.md", policy)

    malformed = tmp_path / "malformed-policy.json"
    malformed.write_text("{not-json", encoding="utf-8")
    with pytest.raises(PolicyViolation, match="POLICY_INPUT_INVALID"):
        load_policy(malformed)
    with pytest.raises(PolicyViolation, match="POLICY_SCHEMA_INVALID"):
        load_policy({**policy, "schema_version": "wrong"})
    with pytest.raises(PolicyViolation, match="POLICY_REQUIRED_FIELD_MISSING"):
        load_policy({"schema_version": "ctxmap-policy-v0.1"})
    with pytest.raises(PolicyViolation, match="POLICY_TYPE_INVALID"):
        load_policy({**policy, "managed_extensions": ".md"})


def test_path_and_secret_boundaries_are_safe(tmp_path: Path, policy: dict[str, object]) -> None:
    for invalid in ("", "docs//note.md", "docs/./note.md", "docs/../note.md", "docs\x00.md"):
        with pytest.raises(PolicyViolation):
            normalize_relative_path(invalid)
    with pytest.raises(PolicyViolation, match="PATH_UNC"):
        normalize_relative_path(r"\\server\share\note.md")
    assert ensure_repo_path(tmp_path, "docs/does-not-escape.md").parent == tmp_path / "docs"

    assert scan_secret_path("docs/.env.local", policy)
    assert scan_secret_path("docs/id_rsa", policy)
    assert not scan_secret_path("docs/normal.md", policy)
    assert scan_secret_content("password=secretvalue", policy)
    assert not scan_secret_content("ordinary text", policy)
    with pytest.raises(PolicyViolation, match="POLICY_SECRET_PATTERN_INVALID"):
        scan_secret_content("text", {**policy, "secret_content_patterns": ["["]})


def test_assert_safe_document_rejects_read_size_encoding_and_secret(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/ok.md", "# OK\n")
    target, data, text = assert_safe_document(tmp_path, "docs\\ok.md", policy)
    assert target.name == "ok.md" and data == b"# OK\n" and text == "# OK\n"
    with pytest.raises(PolicyViolation, match="FILE_READ_FAILED"):
        assert_safe_document(tmp_path, "docs/missing.md", policy)

    write_file(tmp_path, "docs/large.md", "x" * 100)
    with pytest.raises(PolicyViolation, match="FILE_SIZE_LIMIT"):
        assert_safe_document(tmp_path, "docs/large.md", {**policy, "max_file_bytes": 10})

    binary = tmp_path / "docs" / "binary.md"
    binary.write_bytes(b"\xff\xfe")
    with pytest.raises(PolicyViolation, match="UTF8_REQUIRED"):
        assert_safe_document(tmp_path, "docs/binary.md", policy)

    write_file(tmp_path, "docs/secret.md", "API_KEY=abcdefghijk\n")
    with pytest.raises(SecretDetected, match="SECRET_CONTENT"):
        assert_safe_document(tmp_path, "docs/secret.md", policy)
    with pytest.raises(SecretDetected, match="SECRET_PATH"):
        assert_safe_document(tmp_path, "docs/.env", policy)


def test_extractors_cover_html_markdown_links_and_empty_summaries(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    html_text = (
        "<html><head><title> A &amp; B </title></head><body>\n"
        "<h1>Main</h1><h2><em>Sub</em></h2><a href=\"./next.html#part\">next</a>"
        "<a href=\"https://example.test/x\">external</a><a href=\"#anchor\">anchor</a>"
        "<a href=\"./missing.html\">missing</a></body></html>"
    )
    write_file(tmp_path, "docs/page.html", html_text)
    write_file(tmp_path, "docs/next.html", "<title>Next</title>")
    headings = extract_headings(html_text, ".html")
    assert [(item["level"], item["text"]) for item in headings] == [(1, "Main"), (2, "Sub")]
    assert extract_title(html_text, ".html", headings) == "A & B"
    assert extract_local_links(
        "[next](./next.html) ![image](./next.html) [up](../../outside.md) "
        "<a href='./next.html?x=1'>duplicate</a>",
        "docs/page.md",
        tmp_path,
        policy,
    ) == ["docs/next.html"]
    assert extract_trace_ids("REQ-X REQ-X DEC-Y") == ["REQ-X", "DEC-Y"]
    assert extract_summary("# Head\n```code```\n", ".md") == ""
    assert extract_summary("<html>\n<body>\n<main>\n</main>\n", ".html") == ""


def test_discovery_handles_file_roots_missing_roots_and_exclude_paths(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    from scripts.context_index.common import discover_managed_paths

    write_file(tmp_path, "single.md", "# Single\n")
    file_policy = {**policy, "managed_roots": ["single.md"]}
    assert discover_managed_paths(tmp_path, file_policy) == ["single.md"]
    missing_policy = {**policy, "managed_roots": ["missing"]}
    assert discover_managed_paths(tmp_path, missing_policy) == []
    excluded_policy = {**policy, "exclude_paths": ["docs/private.md"]}
    write_file(tmp_path, "docs/private.md", "# Private\n")
    assert not is_managed_document("docs/private.md", excluded_policy)


def test_build_existing_records_state_and_cli_outputs(
    tmp_path: Path, policy: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    write_file(tmp_path, "docs/note.md", "# Note\nbody\n")
    first = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    record = first["artifacts"][0]
    changed = build_index(
        tmp_path,
        policy,
        observed_at="2026-08-15T00:00:00Z",
        existing_manifest=first,
    )
    assert changed["artifacts"][0]["artifact_id"] == record["artifact_id"]
    assert changed["artifacts"][0]["first_seen_at"] == "2026-08-14T00:00:00Z"
    rebuilt = build_record(tmp_path, "docs/note.md", policy, "2026-08-14T00:00:00Z", record)
    assert rebuilt["artifact_id"] == record["artifact_id"]
    state = build_state(first, "2026-08-14T00:00:00Z")
    assert state["states"][0]["subject_id"] == record["artifact_id"]

    output = tmp_path / "out" / "manifest.json"
    state_output = tmp_path / "out" / "state.json"
    policy_path = tmp_path / "policy.json"
    assert build_main(
        [
            "--root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
        ]
    ) == 1
    write_json(policy_path, policy)
    assert build_main(
        [
            "--root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
            "--state-output",
            str(state_output),
            "--observed-at",
            "2026-08-14T00:00:00Z",
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["artifacts"]
    assert json.loads(state_output.read_text(encoding="utf-8"))["states"]
    assert '"status": "PASS"' in capsys.readouterr().out


def test_delta_reports_added_ambiguous_and_cli_output(
    tmp_path: Path, policy: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    write_file(before, "docs/a.md", "# Same\n")
    write_file(before, "docs/b.md", "# Same\n")
    write_file(after, "docs/x.md", "# Same\n")
    write_file(after, "docs/y.md", "# Same\n")
    ambiguous = detect_delta(before, after, policy)
    assert ambiguous[0]["change_kind"] == "rename_ambiguous"

    write_file(after, "docs/new.md", "# New\n")
    changes = detect_delta(before, after, policy)
    assert any(item["change_kind"] == "added" for item in changes)
    assert detect_delta(before, before, policy) == []
    output = tmp_path / "delta.json"
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, policy)
    assert delta_main(
        [
            "--before",
            str(before),
            "--after",
            str(after),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))[0]["change_kind"] == "rename_ambiguous"
    assert '"status": "PASS"' in capsys.readouterr().out


def test_query_filters_limits_path_validation_and_cli(
    tmp_path: Path, policy: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    write_file(tmp_path, "docs/guide.md", "# Routing Guide\nbody\n")
    manifest = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    record = manifest["artifacts"][0]
    archived = dict(record)
    archived["status"] = "deleted"
    mixed = {**manifest, "artifacts": [record, archived, "bad"]}
    assert query_manifest(mixed, "routing", kind="managed_document")
    assert query_manifest(mixed, "routing", status="deleted")[0]["status"] == "deleted"
    assert query_manifest(mixed, "no-match") == []
    assert validate_path_filter(r"docs\guide.md") == "docs/guide.md"
    with pytest.raises(QueryRejected, match="QUERY_PATH_INVALID"):
        validate_path_filter("../guide.md")
    with pytest.raises(QueryRejected, match="QUERY_EMPTY"):
        query_manifest(manifest, " ")
    with pytest.raises(QueryRejected, match="QUERY_PATH_TRAVERSAL"):
        query_manifest(manifest, "/guide")
    with pytest.raises(QueryRejected, match="QUERY_LIMIT_INVALID"):
        query_manifest(manifest, "guide", limit=0)

    manifest_path = tmp_path / "manifest.json"
    write_json(manifest_path, manifest)
    assert query_main(["--manifest", str(manifest_path), "--query", "routing"]) == 0
    assert query_main(["--manifest", str(manifest_path), "--query", "../routing"]) == 1
    assert '"relative_path": "docs/guide.md"' in capsys.readouterr().out


def test_validate_manifest_covers_state_schema_duplicates_and_scope_errors(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "docs/registered.md", "# Registered\n")
    manifest = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    state = build_state(manifest, "2026-08-14T00:00:00Z")
    assert validate_manifest(manifest, tmp_path, policy, state=state).valid
    stale_state = {**state, "states": [dict(state["states"][0], state="blocked")]}
    stale = validate_manifest(manifest, tmp_path, policy, state=stale_state)
    assert any(error["code"] == "STATE_STALE" for error in stale.errors)
    state_bad_schema = {**state, "schema_version": "wrong"}
    assert any(
        error["code"] == "STATE_SCHEMA_INVALID"
        for error in validate_manifest(manifest, tmp_path, policy, state=state_bad_schema).errors
    )

    duplicate = {"schema_version": manifest["schema_version"], "generator_version": "x", "artifacts": [
        manifest["artifacts"][0], manifest["artifacts"][0]
    ]}
    assert any(
        error["code"] == "DUPLICATE_ID_OR_PATH"
        for error in validate_manifest(duplicate, tmp_path, policy).errors
    )
    out_of_scope = dict(manifest["artifacts"][0], relative_path="outside.txt")
    assert any(
        error["code"] == "OUT_OF_SCOPE"
        for error in validate_manifest({**manifest, "artifacts": [out_of_scope]}, tmp_path, policy).errors
    )
    deleted = dict(manifest["artifacts"][0], status="deleted")
    assert validate_manifest({**manifest, "artifacts": [deleted]}, tmp_path, policy).counts == {"deleted": 1}
    assert any(
        error["code"] == "POLICY_SCHEMA_INVALID"
        for error in validate_manifest(manifest, tmp_path, {**policy, "schema_version": "wrong"}).errors
    )
    assert any(
        error["code"] == "SCHEMA_INVALID"
        for error in validate_manifest({"artifacts": []}, tmp_path, policy).errors
    )
    malformed_record = {
        "schema_version": manifest["schema_version"],
        "generator_version": "x",
        "artifacts": [None],
    }
    assert any(
        error["code"] == "SCHEMA_INVALID"
        for error in validate_manifest(malformed_record, tmp_path, policy).errors
    )


def test_validate_cli_reports_valid_and_invalid_manifests(
    tmp_path: Path, policy: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    write_file(tmp_path, "docs/registered.md", "# Registered\n")
    policy_path = tmp_path / "policy.json"
    manifest_path = tmp_path / "manifest.json"
    state_path = tmp_path / "state.json"
    write_json(policy_path, policy)
    manifest = build_index(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    write_json(manifest_path, manifest)
    write_json(state_path, build_state(manifest, "2026-08-14T00:00:00Z"))
    assert validate_main(
        [
            "--root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--manifest",
            str(manifest_path),
            "--state",
            str(state_path),
        ]
    ) == 0
    manifest_path.write_text("[]", encoding="utf-8")
    assert validate_main(
        [
            "--root",
            str(tmp_path),
            "--policy",
            str(policy_path),
            "--manifest",
            str(manifest_path),
        ]
    ) == 1
    assert '"valid": true' in capsys.readouterr().out

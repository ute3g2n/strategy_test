"""Step 08 in-memory pilot scenarios; no management hash is calculated or stored."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from scripts.ai_foundation.protected_hash_policy_guard import scan_text

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_new_markdown_and_major_html_use_nonhash_policy() -> None:
    markdown = scan_text("plan/pilot-new.md", "# Pilot\n\nUse path, schema, and state.")
    html = scan_text("doc/pilot.html", "<!doctype html><html><body><h1>Pilot</h1></body></html>")

    assert markdown["decision"] == "ALLOW"
    assert html["decision"] == "ALLOW"


def test_html_index_link_and_source_change_are_structurally_checked() -> None:
    index_text = (REPO_ROOT / "doc/index.html").read_text(encoding="utf-8")
    source = scan_text("src/autotrade/application/api.py", "def changed_source():\n    return {'status': 'READY'}")

    HTMLParser().feed(index_text)
    assert "21_資料コード参照基盤システム詳細解説.html" in index_text
    assert source["decision"] == "ALLOW"


def test_phase_acceptance_change_has_no_management_hash_requirement() -> None:
    report = scan_text(
        "plan/pilot-acceptance.md",
        "Acceptance uses path, schema, links, protected input purpose, and state.",
    )

    assert report["decision"] == "ALLOW"


def test_unknown_hash_is_not_automatically_allowed() -> None:
    report = scan_text("plan/pilot-unknown.md", "Keep a checksum for convenience")

    assert report["decision"] == "NEEDS_HUMAN_GATE"

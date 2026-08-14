"""Step 07 tests for the static protected-hash policy guard."""

from __future__ import annotations

from scripts.ai_foundation.protected_hash_policy_guard import scan_text


def test_management_hash_reintroduction_is_blocked() -> None:
    report = scan_text("plan/example.md", "add manifest_sha256 and retry on hash mismatch")

    assert report["decision"] == "BLOCKED"
    assert report["candidates"][0]["category"] == "MANAGEMENT"


def test_protected_data_hash_requires_explicit_purpose_but_can_be_allowed() -> None:
    report = scan_text(
        "tests/fixture.json",
        "fixture_sha256 protects reproducibility and stops closed on mismatch",
    )

    assert report["decision"] == "ALLOW"
    assert report["candidates"][0]["category"] == "PROTECTED"


def test_unknown_hash_requires_human_gate() -> None:
    report = scan_text("doc/new.html", "store a checksum for future validation")

    assert report["decision"] == "NEEDS_HUMAN_GATE"
    assert report["candidates"][0]["category"] == "UNKNOWN"

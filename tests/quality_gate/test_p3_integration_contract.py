"""RED contract tests for the P3-10 integration execution entry."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gate.p3_integration_runner import (
    REQUIRED_ACCEPTANCE_IDS,
    build_p3_10_summary,
)

ROOT = Path(__file__).parents[2]


def test_p3_10_assigns_every_phase3_acceptance_condition() -> None:
    summary = build_p3_10_summary(ROOT)

    assert tuple(summary["acceptance"].keys()) == REQUIRED_ACCEPTANCE_IDS
    assert all(item["status"] == "PASS" for item in summary["acceptance"].values())


def test_p3_10_excludes_stale_blocked_golden_attempt_without_calling_it_pass() -> None:
    summary = build_p3_10_summary(ROOT)

    stale = summary["source_runs"]["RUN-P3-GOLD-001"]
    assert stale["observed_status"] == "BLOCKED"
    assert stale["used_for_final_pass"] is False
    assert stale["replacement_evidence"] == "current_fixed_quality_suite"


def test_p3_10_retains_long_horizon_unknowns_as_unknown() -> None:
    summary = build_p3_10_summary(ROOT)

    assert summary["robustness"]["status"] == "UNKNOWN"
    assert {item["id"] for item in summary["robustness"]["unknowns"]} == {
        "UNK-P3-01",
        "UNK-P3-05",
        "UNK-P3-07",
    }


def test_p3_10_has_complete_traceability_and_review_results() -> None:
    summary = build_p3_10_summary(ROOT)

    for requirement_id in REQUIRED_ACCEPTANCE_IDS:
        trace = summary["traceability"][requirement_id]
        assert trace["design_refs"]
        assert trace["test_ids"]
        assert trace["implementation_paths"]
        assert trace["run_evidence"]
        assert trace["review_results"]
        assert trace["status"] == "PASS"

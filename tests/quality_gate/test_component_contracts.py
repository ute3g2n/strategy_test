"""Contracts for the Phase 2–5 implementation quality AI components."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS = {
    "AutoTrade_A110_PythonTestEngineer_v0_1": "autotrade_skill_python_test_quality_v0_1",
    "AutoTrade_A120_PythonImplementer_v0_1": "autotrade_skill_python_implementation_v0_1",
    "AutoTrade_A130_VerificationEngineer_v0_1": "autotrade_skill_python_test_quality_v0_1",
    "AutoTrade_A140_DebugEngineer_v0_1": "autotrade_skill_debug_recovery_v0_1",
    "AutoTrade_A150_PythonCodeReviewer_v0_1": "autotrade_skill_python_code_review_v0_1",
    "AutoTrade_A160_TradingSecurityReviewer_v0_1": "autotrade_skill_python_code_review_v0_1",
    "AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1": "autotrade_skill_protected_hash_policy_guard_v0_1",
}
SKILLS = {
    "autotrade_skill_python_implementation_v0_1",
    "autotrade_skill_python_test_quality_v0_1",
    "autotrade_skill_debug_recovery_v0_1",
    "autotrade_skill_python_code_review_v0_1",
}


def test_orchestrator_declares_explicit_components_and_safety_constraints() -> None:
    path = ROOT / ".codex/orchestrators/AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["model"] == "gpt-5.6-terra"
    assert payload["global_constraints"]["do_not_change_default_orchestrator"] is True
    assert payload["global_constraints"]["must_not_use_network"] is True
    assert set(payload["agents"]) == {name.split("_")[1] for name in AGENTS}
    assert payload["ecc_source_revision"] == "historical metadata; not used as a current integrity check"


def test_agents_reference_only_the_minimal_new_skills() -> None:
    for agent_name, primary_skill in AGENTS.items():
        payload = json.loads((ROOT / ".codex/agents" / f"{agent_name}.json").read_text(encoding="utf-8"))
        assert payload["name"] == agent_name
        assert payload["skill"] == primary_skill
        assert "ecc_source_commit" not in payload
        boundaries = payload["boundaries"]
        assert "Broker" in json.dumps(boundaries, ensure_ascii=False)
        assert "secret" in json.dumps(boundaries, ensure_ascii=False).lower()


def test_skills_have_required_safety_and_evidence_contracts() -> None:
    for skill_name in SKILLS:
        skill_text = (ROOT / ".codex/skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        assert f"name: {skill_name}" in skill_text
        assert "ecc_source_commit:" not in skill_text
        assert "source_reference:" in skill_text
        assert "tests/evidence" in skill_text
        assert "Broker" in skill_text
        assert "Secret" in skill_text

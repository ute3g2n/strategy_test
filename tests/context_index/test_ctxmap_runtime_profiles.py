from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "agent_file",
    [
        ".codex/agents/AutoTrade_A07_ContextManifestMaintainer_v0_1.json",
        ".codex/agents/AutoTrade_A08_ContextRouter_v0_1.json",
        ".codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json",
    ],
)
def test_current_ctxmap_agents_use_luna_low_profile(agent_file: str) -> None:
    definition = json.loads((ROOT / agent_file).read_text(encoding="utf-8"))

    assert definition["model"] == "gpt-5.6-luna"
    assert definition["reasoning_effort"] == "low"

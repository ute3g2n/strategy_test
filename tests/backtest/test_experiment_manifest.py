"""P3-07 ExperimentManifest mutation and immutable-bias contracts."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "phase3" / "bias_manifest_v1.json"


def _fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validate_manifest():
    try:
        module = importlib.import_module("autotrade.backtest.experiment_manifest")
    except ModuleNotFoundError as error:
        pytest.fail(f"P3-07 must provide autotrade.backtest.experiment_manifest: {error}")
    operation = getattr(module, "validate_manifest", None)
    assert callable(operation), "autotrade.backtest.experiment_manifest.validate_manifest is required"
    return operation


def test_bias_manifest_schema_and_reject_catalog_are_pinned() -> None:
    fixture = _fixture()
    assert fixture["schema_version"] == "p3-bias-manifest-v1"
    assert fixture["reject_cases"] == [
        "PARTIAL_BAR_REJECTED",
        "DUPLICATE_1M_CONFLICT",
        "STR_TIME_REGRESSION",
        "FUTURE_CALENDAR_OR_ROLL",
        "HOLDOUT_EARLY_ACCESS",
        "WALL_CLOCK_DEPENDENCY",
        "EXPERIMENT_PLAN_MUTATED",
        "MANIFEST_INTEGRITY_VIOLATION",
        "ENGINE_IDENTITY_UNPINNED",
        "OFFLINE_POLICY_VIOLATION",
    ]
    assert fixture["manifest_mutations"] == [
        "timeframe_rule_version",
        "calendar_sha256",
        "ordering_rule_version",
        "engine_identity_sha256",
        "adapter_artifact_sha256",
        "strategy_code_revision",
    ]


@pytest.mark.parametrize(
    "mutation_key",
    [
        "timeframe_rule_version",
        "calendar_sha256",
        "ordering_rule_version",
        "engine_identity_sha256",
        "adapter_artifact_sha256",
        "strategy_code_revision",
    ],
)
def test_each_manifest_binding_mutation_stops_publication(mutation_key: str) -> None:
    result = _validate_manifest()({mutation_key: True})
    assert result == {"status": "STOPPED", "reason": "MANIFEST_INTEGRITY_VIOLATION"}


def test_calendar_hash_mutation_matches_the_primary_contract() -> None:
    assert _validate_manifest()({"calendar_hash_changed": True}) == {
        "status": "STOPPED",
        "reason": "MANIFEST_INTEGRITY_VIOLATION",
    }

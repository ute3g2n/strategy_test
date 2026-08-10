"""P3-08A contract tests for the pinned LEAN preparation manifest."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).parents[1] / "evidence" / "phase3" / "RUN-P3-LEAN-PREP-001" / "run-manifest.json"
EXPECTED_IMAGE_INDEX_DIGEST = "sha256:bc01b22a27262ff1e69bdd7f451234e565463292350626aaa2479bda7a54765d"
EXPECTED_AMD64_DIGEST = "sha256:9712dfd8c52d05e7292848cf0b365a02f6d603551bc883d423d2ce0877363263"
EXPECTED_SOURCE_COMMIT = "c6cc3b743ed7b65d5e0b9fa2bfc18b7d3ac2aea0"


def test_lean_manifest_is_fully_pinned_and_local_only() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    engine = manifest["engine"]
    artifact = manifest["artifact"]
    execution = manifest["execution"]

    assert manifest["run_id"] == "RUN-P3-LEAN-PREP-001"
    assert engine["tag"] == "17991"
    assert engine["image_index_digest"] == EXPECTED_IMAGE_INDEX_DIGEST
    assert engine["linux_amd64_digest"] == EXPECTED_AMD64_DIGEST
    assert engine["source_commit"] == EXPECTED_SOURCE_COMMIT
    assert engine["license"] == "Apache-2.0"
    assert engine["distribution_source"] == "official_quantconnect_dockerhub"
    assert artifact["image_tar_sha256"].startswith("sha256:")
    assert "PENDING" not in artifact["image_tar_sha256"]
    assert artifact["license_sha256"].startswith("sha256:")
    assert "PENDING" not in artifact["license_sha256"]
    assert execution["network_mode"] == "none"
    assert execution["data_provider"] == "Local"
    assert execution["cloud"] == "NOT_USED"
    assert execution["broker"] == "NOT_USED"
    assert execution["secret"] == "NOT_USED"
    assert execution["automatic_data_download"] is False


def test_lean_manifest_has_reproducible_offline_entrypoint_and_scope() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    execution = manifest["execution"]
    scope = manifest["scope"]

    assert "--network none" in execution["preflight_command"]
    assert "--read-only" in execution["preflight_command"]
    assert execution["input_root"] == "E:\\strategy_test_data\\phase3\\engine_poc\\lean"
    assert execution["write_roots"] == ["/tmp", "/results"]
    assert scope["core_engine_import_boundary"] == "ENGINE_NOT_USED"
    assert scope["strategy_vendor_imports"] == []
    assert scope["p3_09_only_after_prep_pass"] is True

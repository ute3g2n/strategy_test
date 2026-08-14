from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.context_index.build_code_manifest import (
    build_code_manifest,
    extract_code_file,
    validate_code_manifest,
)
from scripts.context_index.build_relation_graph import build_relation_graph
from scripts.context_index.detect_code_delta import detect_code_delta


@pytest.fixture()
def policy() -> dict[str, object]:
    return {
        "schema_version": "ctxmap-policy-v0.1",
        "generator_version": "ctxmap-indexer-v0.1",
        "managed_extensions": [".md", ".html"],
        "managed_roots": ["docs"],
        "managed_source_roots": ["src", "config"],
        "managed_source_extensions": [".py", ".js", ".mjs", ".ts", ".tsx", ".ps1", ".sh", ".bash"],
        "managed_config_extensions": [".json", ".toml", ".yaml", ".yml"],
        "source_exclude_dirs": ["third_party", "node_modules", ".venv"],
        "exclude_dirs": ["third_party", "node_modules", ".venv"],
        "max_file_bytes": 20_000,
        "secret_path_patterns": [".env", ".pem", ".key", "id_rsa", "credentials"],
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


def test_python_ast_extracts_nested_symbols_imports_decorators_and_ranges(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(
        tmp_path,
        "src/main.py",
        "import os as operating_system\nfrom .worker import run as execute\n"
        "@decorator\nclass Outer:\n    def method(self):\n        def nested():\n"
        "            return 1\n        return nested()\n\nasync def top():\n"
        "    return await execute()\n",
    )
    record = extract_code_file(tmp_path, "src/main.py", policy)
    assert record["language"] == "python"
    assert record["extraction_status"] == "COMPLETE"
    assert {item["name"] for item in record["symbols"]} == {"Outer", "method", "nested", "top"}
    method = next(item for item in record["symbols"] if item["name"] == "method")
    nested = next(item for item in record["symbols"] if item["name"] == "nested")
    assert method["kind"] == "method"
    assert nested["qualified_name"] == "Outer.method.nested"
    assert nested["line_start"] < nested["line_end"]
    assert any(item["module"] == "os" and item["alias"] == "operating_system" for item in record["imports"])
    assert any(item["module"] == "worker" and item["level"] == 1 for item in record["imports"])
    assert record["symbols"][0]["decorators"] == ["decorator"]


def test_python_syntax_error_is_partial_without_source_excerpt(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "src/broken.py", "def broken(:\n    SECRET_VALUE = 'do-not-output'\n")
    record = extract_code_file(tmp_path, "src/broken.py", policy)
    assert record["extraction_status"] == "PARTIAL"
    assert any(item["code"] == "PYTHON_SYNTAX_ERROR" for item in record["diagnostics"])
    assert "do-not-output" not in json.dumps(record)


def test_typescript_javascript_are_conservative_partial_and_ignore_dynamic_import(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(
        tmp_path,
        "src/app.ts",
        "import { helper as h } from './helper';\nexport function run() { return h(); }\n"
        "export class App {}\nconst value = () => 1;\nconst module = import(dynamicName);\n",
    )
    record = extract_code_file(tmp_path, "src/app.ts", policy)
    assert record["extraction_status"] == "PARTIAL"
    assert record["parser"] == "conservative-regex-v0.1"
    assert any(item["name"] == "run" for item in record["symbols"])
    assert any(item["module"] == "./helper" for item in record["imports"])
    assert not any(item.get("module") == "dynamicName" for item in record["imports"])
    assert any(item["code"] == "DYNAMIC_IMPORT_UNRESOLVED" for item in record["diagnostics"])


def test_powershell_and_shell_extract_only_explicit_functions_and_sources(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "src/tool.ps1", "function Invoke-Tool { param($Name) }\n. ./common.ps1\n")
    write_file(tmp_path, "src/tool.sh", "run_tool() { echo ok; }\nsource ./common.sh\n")
    powershell = extract_code_file(tmp_path, "src/tool.ps1", policy)
    shell = extract_code_file(tmp_path, "src/tool.sh", policy)
    assert powershell["extraction_status"] == "PARTIAL"
    assert shell["extraction_status"] == "PARTIAL"
    assert powershell["symbols"][0]["name"] == "Invoke-Tool"
    assert shell["symbols"][0]["name"] == "run_tool"
    assert any(item["module"] == "./common.ps1" for item in powershell["imports"])
    assert any(item["module"] == "./common.sh" for item in shell["imports"])


def test_json_config_omits_secret_keys_values_and_keeps_safe_metadata(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(
        tmp_path,
        "config/app.json",
        json.dumps(
            {
                "name": "demo",
                "api_key": "secret-value-should-not-appear",
                "nested": {"password": "another-secret-value"},
                "path": "./src/main.py",
            }
        ),
    )
    record = extract_code_file(tmp_path, "config/app.json", policy)
    encoded = json.dumps(record)
    assert record["kind"] == "managed_config"
    assert "secret-value-should-not-appear" not in encoded
    assert "another-secret-value" not in encoded
    assert "api_key" not in encoded
    assert "password" not in encoded
    assert "name" in record["config"]["safe_top_level_keys"]
    assert "config/app.json" == record["relative_path"]


def test_build_manifest_is_deterministic_and_validates_hashes_and_exclusions(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "src/b.py", "def b():\n    return 1\n")
    write_file(tmp_path, "src/a.py", "from .b import b\n")
    write_file(tmp_path, "src/third_party/vendor.py", "def vendor():\n    pass\n")
    first = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    second = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    assert first == second
    assert [item["relative_path"] for item in first["artifacts"]] == ["src/a.py", "src/b.py"]
    assert validate_code_manifest(first, tmp_path, policy).valid
    write_file(tmp_path, "src/a.py", "from .b import b\n# changed\n")
    stale = validate_code_manifest(first, tmp_path, policy)
    assert not stale.valid
    assert any(item["code"] == "STALE_SOURCE" for item in stale.errors)


def test_relation_graph_resolves_cycles_and_marks_missing_targets(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "src/a.py", "from .b import b\nfrom .missing import x\n")
    write_file(tmp_path, "src/b.py", "from .a import a\ndef b():\n    pass\n")
    code_manifest = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    graph = build_relation_graph(code_manifest)
    assert graph["status"] == "PARTIAL"
    assert len(graph["edges"]) == len({json.dumps(edge, sort_keys=True) for edge in graph["edges"]})
    assert any(edge["resolution"] == "resolved" for edge in graph["edges"])
    assert any(edge["resolution"] == "unresolved" for edge in graph["edges"])
    assert len(graph["nodes"]) < 100


def test_relation_graph_links_document_trace_and_local_link_metadata(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "src/main.py", "def main():\n    pass\n")
    code_manifest = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    document_manifest = {
        "artifacts": [
            {
                "artifact_id": "art-00000000-0000-0000-0000-000000000001",
                "relative_path": "docs/guide.md",
                "local_links": ["docs/other.md"],
                "trace_ids": ["REQ-CTX-005"],
            }
        ]
    }
    graph = build_relation_graph(code_manifest, document_manifest)
    assert any(edge["relation_type"] == "references_trace_id" for edge in graph["edges"])
    assert any(edge["relation_type"] == "links_to" for edge in graph["edges"])


def test_rename_preserves_code_id_and_ambiguous_hash_is_not_silently_selected(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    write_file(tmp_path, "src/old.py", "def same():\n    pass\n")
    before = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    code_id = before["artifacts"][0]["code_id"]
    (tmp_path / "src" / "old.py").rename(tmp_path / "src" / "new.py")
    after = build_code_manifest(
        tmp_path,
        policy,
        observed_at="2026-08-14T00:01:00Z",
        existing_manifest=before,
    )
    assert after["artifacts"][0]["code_id"] == code_id
    assert after["artifacts"][0]["relative_path"] == "src/new.py"

    write_file(tmp_path, "src/other.py", "def same():\n    pass\n")
    ambiguous = build_code_manifest(
        tmp_path,
        policy,
        observed_at="2026-08-14T00:02:00Z",
        existing_manifest=after,
    )
    assert any(item["code"] == "RENAME_AMBIGUOUS" for item in ambiguous["diagnostics"])


def test_code_delta_distinguishes_comment_only_and_structure_changes(tmp_path: Path, policy: dict[str, object]) -> None:
    write_file(tmp_path, "src/a.py", "def run():\n    return 1\n")
    before = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    write_file(tmp_path, "src/a.py", "# comment only\ndef run():\n    return 1\n")
    comment_after = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    comment_delta = detect_code_delta(before, comment_after)
    assert comment_delta[0]["change_kind"] == "modified_non_structural"
    write_file(tmp_path, "src/a.py", "def run():\n    return 1\n\ndef added():\n    pass\n")
    structure_after = build_code_manifest(tmp_path, policy, observed_at="2026-08-14T00:00:00Z")
    structure_delta = detect_code_delta(comment_after, structure_after)
    assert structure_delta[0]["change_kind"] == "modified_structural"

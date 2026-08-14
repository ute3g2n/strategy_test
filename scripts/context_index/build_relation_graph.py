from __future__ import annotations

import argparse
import json
import posixpath
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from .common import normalize_relative_path, stable_id

RELATION_GRAPH_SCHEMA_VERSION = "ctxmap-relation-graph-v0.1"
RELATION_GRAPH_GENERATOR_VERSION = "ctxmap-relation-graph-v0.1"


def _node(node_id: str, node_type: str, label: str, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "node_id": node_id,
        "node_type": node_type,
        "label": label[:500],
    }
    value.update(extra)
    return value


def _edge(
    source_id: str,
    target_id: str | None,
    relation_type: str,
    *,
    resolution: str,
    target_ref: str | None = None,
    explicit: bool = True,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "resolution": resolution,
        "evidence": "explicit" if explicit else "heuristic",
    }
    if target_ref is not None:
        value["target_ref"] = target_ref[:500]
    return value


def _symbol_id(code_id: str, qualified_name: str) -> str:
    return f"{code_id}::symbol::{qualified_name}"


def _trace_id_node(trace_id: str) -> str:
    return stable_id("trace", trace_id)


def _path_candidates(relative_path: str, module: str, level: int = 0) -> list[str]:
    """Return safe local candidates for a Python, JS, shell, or PowerShell import."""

    normalized = relative_path.replace("\\", "/")
    parent = posixpath.dirname(normalized)
    suffix = PurePosixPath(normalized).suffix.lower()
    module = module.strip().replace("\\", "/")
    if not module:
        return []
    if level > 0:
        base_parts = parent.split("/") if parent else []
        # A single leading dot means the importing file's directory. Each
        # additional dot walks one more package directory upwards.
        for _ in range(max(level - 1, 0)):
            if base_parts:
                base_parts.pop()
        base = "/".join(base_parts)
        module_path = module.lstrip(".")
        candidate_base = posixpath.join(base, module_path) if base else module_path
    elif module.startswith(("./", "../")):
        candidate_base = posixpath.normpath(posixpath.join(parent, module))
    else:
        module_path = module.lstrip("./")
        if suffix == ".py":
            module_path = module_path.replace(".", "/")
        candidate_base = module_path

    candidates: list[str] = []
    if PurePosixPath(candidate_base).suffix:
        candidates.append(candidate_base)
    extension_candidates = [suffix] if suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx"} else []
    extension_candidates.extend([".py", ".ts", ".tsx", ".js", ".mjs", ".cjs"])
    if suffix in {".ps1", ".sh", ".bash", ".cmd"}:
        extension_candidates.extend([suffix])
    for extension in extension_candidates:
        candidate = f"{candidate_base}{extension}"
        if candidate not in candidates:
            candidates.append(candidate)
    for index_name in ("__init__.py", "index.ts", "index.tsx", "index.js"):
        candidate = posixpath.join(candidate_base, index_name)
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _resolve_import(
    record: Mapping[str, Any],
    imported: Mapping[str, Any],
    path_to_id: Mapping[str, str],
) -> tuple[str | None, str, str, bool]:
    module = str(imported.get("module") or "").strip()
    level_value = imported.get("level", 0)
    try:
        level = int(level_value)
    except (TypeError, ValueError):
        level = 0
    relative = level > 0 or module.startswith(("./", "../"))
    candidates = _path_candidates(str(record.get("relative_path", "")), module, level)
    for candidate in candidates:
        try:
            normalized = normalize_relative_path(candidate)
        except ValueError:
            continue
        if normalized in path_to_id:
            return path_to_id[normalized], "resolved", normalized, relative
    if relative:
        safe_ref = posixpath.normpath(posixpath.join(posixpath.dirname(str(record.get("relative_path", ""))), module))
        return None, "unresolved", safe_ref[:500], relative
    # Bare package names are deliberately represented as external rather than
    # being treated as missing local files.
    return None, "external", module[:500], False


def _deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda value: str(value)):
        key = repr(sorted(item.items()))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def build_relation_graph(
    code_manifest: Mapping[str, Any],
    document_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, evidence-labelled graph from safe manifests.

    The graph stores paths, identifiers, parser findings, and trace IDs only;
    it never reads source or document bodies. Unresolved local references are
    retained as PARTIAL evidence instead of being guessed into a node.
    """

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    path_to_id: dict[str, str] = {}
    records = code_manifest.get("artifacts", [])
    if not isinstance(records, list):
        records = []

    for record in records:
        if not isinstance(record, Mapping):
            diagnostics.append({"code": "CODE_RECORD_INVALID", "message": "code record was not an object"})
            continue
        code_id = record.get("code_id")
        relative_path = record.get("relative_path")
        if not isinstance(code_id, str) or not isinstance(relative_path, str):
            diagnostics.append({"code": "CODE_RECORD_ID_INVALID", "message": "code record lacks safe identity"})
            continue
        path_to_id[relative_path] = code_id
        nodes.append(_node(code_id, "code_file", relative_path, relative_path=relative_path))
        symbols = record.get("symbols", [])
        if isinstance(symbols, list):
            for symbol in symbols:
                if not isinstance(symbol, Mapping) or not isinstance(symbol.get("qualified_name"), str):
                    continue
                symbol_id = _symbol_id(code_id, str(symbol["qualified_name"]))
                nodes.append(
                    _node(
                        symbol_id,
                        "code_symbol",
                        str(symbol["qualified_name"]),
                        code_id=code_id,
                        kind=str(symbol.get("kind", "unknown")),
                    )
                )
                edges.append(
                    _edge(
                        code_id,
                        symbol_id,
                        "contains",
                        resolution="resolved",
                        target_ref=str(symbol["qualified_name"]),
                    )
                )

    for record in records:
        if not isinstance(record, Mapping):
            continue
        code_id = record.get("code_id")
        if not isinstance(code_id, str):
            continue
        imports = record.get("imports", [])
        if not isinstance(imports, list):
            continue
        for imported in imports:
            if not isinstance(imported, Mapping):
                continue
            target_id, resolution, target_ref, relative = _resolve_import(record, imported, path_to_id)
            edges.append(
                _edge(
                    code_id,
                    target_id,
                    "imports",
                    resolution=resolution,
                    target_ref=target_ref,
                    explicit=True,
                )
            )
            if relative and resolution == "unresolved":
                diagnostics.append({"code": "LOCAL_REFERENCE_UNRESOLVED", "message": target_ref})

    document_records = (document_manifest or {}).get("artifacts", [])
    document_by_path: dict[str, str] = {}
    if isinstance(document_records, list):
        for record in document_records:
            if not isinstance(record, Mapping):
                continue
            artifact_id = record.get("artifact_id")
            relative_path = record.get("relative_path")
            if not isinstance(artifact_id, str) or not isinstance(relative_path, str):
                continue
            document_by_path[relative_path] = artifact_id
            nodes.append(_node(artifact_id, "document", relative_path, relative_path=relative_path))
        for record in document_records:
            if not isinstance(record, Mapping):
                continue
            source_id = record.get("artifact_id")
            source_path = record.get("relative_path")
            if not isinstance(source_id, str) or not isinstance(source_path, str):
                continue
            local_links = record.get("local_links", [])
            if isinstance(local_links, list):
                for link in local_links:
                    if not isinstance(link, str):
                        continue
                    target_path = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), link))
                    target_id = document_by_path.get(target_path)
                    resolution = "resolved" if target_id else "unresolved"
                    edges.append(
                        _edge(
                            source_id,
                            target_id,
                            "links_to",
                            resolution=resolution,
                            target_ref=target_path,
                            explicit=True,
                        )
                    )
                    if not target_id:
                        diagnostics.append({"code": "DOCUMENT_LINK_UNRESOLVED", "message": target_path})
            trace_ids = record.get("trace_ids", [])
            if isinstance(trace_ids, list):
                for trace_id in trace_ids:
                    if not isinstance(trace_id, str):
                        continue
                    trace_node = _trace_id_node(trace_id)
                    nodes.append(_node(trace_node, "trace_id", trace_id))
                    edges.append(
                        _edge(
                            source_id,
                            trace_node,
                            "references_trace_id",
                            resolution="resolved",
                            target_ref=trace_id,
                            explicit=True,
                        )
                    )

    nodes = _deduplicate(nodes)
    edges = _deduplicate(edges)
    diagnostics = _deduplicate(diagnostics)
    has_partial_code = any(
        isinstance(record, Mapping) and str(record.get("extraction_status")) != "COMPLETE" for record in records
    )
    has_unresolved = any(edge.get("resolution") == "unresolved" for edge in edges)
    return {
        "schema_version": RELATION_GRAPH_SCHEMA_VERSION,
        "generator_version": RELATION_GRAPH_GENERATOR_VERSION,
        "status": "PARTIAL" if has_partial_code or has_unresolved or diagnostics else "COMPLETE",
        "nodes": nodes,
        "edges": edges,
        "diagnostics": diagnostics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic context relation graph from manifests.")
    parser.add_argument("--code-manifest", type=Path, required=True)
    parser.add_argument("--document-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        code_manifest = json.loads(args.code_manifest.read_text(encoding="utf-8"))
        document_manifest = (
            json.loads(args.document_manifest.read_text(encoding="utf-8"))
            if args.document_manifest
            else None
        )
        graph = build_relation_graph(code_manifest, document_manifest)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(graph, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": graph["status"], "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

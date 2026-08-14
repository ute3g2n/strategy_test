from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .build_code_manifest import validate_code_manifest
from .common import (
    ContextIndexError,
    PolicyViolation,
    ensure_repo_path,
    load_policy,
    normalize_relative_path,
    sha256_bytes,
    stable_id,
)
from .validate_context_index import load_manifest_file, validate_manifest

ROUTER_SCHEMA_VERSION = "ctxmap-router-v0.1"
MAX_QUERY_CHARS = 2_000
MAX_PRIMARY = 3
MAX_SUPPORTING = 6
MAX_JIT_RANGES = 3

_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:@+-]+|[一-龯ぁ-んァ-ンー]{2,}")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RouterRejected(ContextIndexError):
    """Raised when manifest-only routing cannot safely proceed."""


def _records(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise RouterRejected("SNAPSHOT_SCHEMA_INVALID")
    return [item for item in artifacts if isinstance(item, Mapping)]


def _query_terms(query: str) -> list[str]:
    if not isinstance(query, str) or not query.strip():
        raise RouterRejected("QUERY_EMPTY")
    if len(query) > MAX_QUERY_CHARS:
        raise RouterRejected("QUERY_TOO_LONG")
    if "\x00" in query:
        raise RouterRejected("QUERY_INVALID")
    if ".." in query or query.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", query):
        raise RouterRejected("QUERY_PATH_TRAVERSAL")
    terms = [item.casefold() for item in _TOKEN_RE.findall(query) if item.strip()]
    if not terms:
        raise RouterRejected("QUERY_EMPTY")
    return sorted(set(terms))


def _safe_request_id(value: str | None, query: str) -> str:
    if value is None:
        return stable_id("request", query)
    if not isinstance(value, str) or not _REQUEST_ID_RE.fullmatch(value):
        raise RouterRejected("REQUEST_ID_INVALID")
    return value


def _record_id(record: Mapping[str, Any]) -> str | None:
    for key in ("artifact_id", "code_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _record_text(record: Mapping[str, Any]) -> str:
    values: list[str] = []
    for key in ("relative_path", "title", "summary", "purpose", "language", "parser"):
        value = record.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ("trace_ids", "relation_ids", "public_candidates", "exports"):
        value = record.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, (str, int)))
    headings = record.get("headings")
    if isinstance(headings, list):
        values.extend(
            str(item.get("text", ""))
            for item in headings
            if isinstance(item, Mapping) and isinstance(item.get("text"), str)
        )
    symbols = record.get("symbols")
    if isinstance(symbols, list):
        for symbol in symbols:
            if isinstance(symbol, Mapping):
                values.extend(
                    str(symbol.get(key, ""))
                    for key in ("name", "qualified_name", "kind")
                    if isinstance(symbol.get(key), str)
                )
    config = record.get("config")
    if isinstance(config, Mapping):
        for key in ("safe_top_level_keys", "reference_paths"):
            value = config.get(key)
            if isinstance(value, list):
                values.extend(str(item) for item in value if isinstance(item, str))
    return " ".join(values).casefold()


def _score_record(record: Mapping[str, Any], terms: list[str], query: str) -> tuple[int, int, list[str]]:
    record_id = _record_id(record)
    haystack = _record_text(record)
    matched = [term for term in terms if term in haystack]
    direct = int(query.casefold() in haystack or query.casefold() == str(record_id).casefold())
    return len(matched), direct, matched


def _record_kind(record: Mapping[str, Any]) -> str:
    value = record.get("kind")
    return value if isinstance(value, str) else "unknown"


def _all_records(snapshot: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result: list[Mapping[str, Any]] = []
    for key in ("artifact_manifest", "code_manifest"):
        manifest = snapshot.get(key)
        if not isinstance(manifest, Mapping):
            raise RouterRejected("SNAPSHOT_SCHEMA_INVALID")
        result.extend(_records(manifest))
    return result


def _validate_snapshot(snapshot: Mapping[str, Any]) -> str:
    if snapshot.get("verified") is not True:
        raise RouterRejected("SNAPSHOT_NOT_VERIFIED")
    snapshot_hash = snapshot.get("snapshot_hash")
    if not isinstance(snapshot_hash, str) or not snapshot_hash or len(snapshot_hash) > 128:
        raise RouterRejected("SNAPSHOT_HASH_INVALID")
    records = _all_records(snapshot)
    graph = snapshot.get("relation_graph")
    if not isinstance(graph, Mapping) or not isinstance(graph.get("edges"), list):
        raise RouterRejected("SNAPSHOT_SCHEMA_INVALID")
    if graph.get("status") == "BLOCKED":
        raise RouterRejected("SNAPSHOT_BLOCKED")
    if re.fullmatch(r"[a-f0-9]{64}", snapshot_hash):
        payload = json.dumps(
            {
                "artifact_manifest": snapshot.get("artifact_manifest"),
                "code_manifest": snapshot.get("code_manifest"),
                "relation_graph": graph,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if sha256_bytes(payload) != snapshot_hash:
            raise RouterRejected("SNAPSHOT_STALE")
    if not records:
        raise RouterRejected("SNAPSHOT_EMPTY")
    return snapshot_hash


def _relation_neighbors(snapshot: Mapping[str, Any], selected: set[str]) -> set[str]:
    graph = snapshot["relation_graph"]
    if not isinstance(graph, Mapping) or not isinstance(graph.get("edges"), list):
        return set()
    neighbors: set[str] = set()
    for edge in graph["edges"]:
        if not isinstance(edge, Mapping):
            continue
        source = edge.get("source_id")
        target = edge.get("target_id")
        if source in selected and isinstance(target, str):
            neighbors.add(target)
        if target in selected and isinstance(source, str):
            neighbors.add(source)
    return neighbors - selected


def _jit_range(record: Mapping[str, Any]) -> dict[str, Any] | None:
    path = record.get("relative_path")
    record_id = _record_id(record)
    if not isinstance(path, str) or not isinstance(record_id, str):
        return None
    try:
        normalized = normalize_relative_path(path)
    except PolicyViolation:
        return None
    if record.get("kind") == "managed_document":
        headings = record.get("headings")
        heading = None
        if isinstance(headings, list) and headings and isinstance(headings[0], Mapping):
            if isinstance(headings[0].get("text"), str):
                heading = headings[0]["text"]
        result: dict[str, Any] = {
            "id": record_id,
            "relative_path": normalized,
            "range_type": "heading",
            "max_chars": 12_000,
            "reason": "manifest-selected document range",
        }
        if heading:
            result["heading"] = heading
        return result
    symbols = record.get("symbols")
    if isinstance(symbols, list):
        for symbol in symbols:
            if not isinstance(symbol, Mapping):
                continue
            start = symbol.get("line_start")
            end = symbol.get("line_end")
            if isinstance(start, int) and isinstance(end, int) and start >= 1 and end >= start:
                return {
                    "id": record_id,
                    "relative_path": normalized,
                    "range_type": "lines",
                    "line_start": start,
                    "line_end": end,
                    "max_chars": 12_000,
                    "reason": "manifest-selected public symbol range",
                }
    return {
        "id": record_id,
        "relative_path": normalized,
        "range_type": "lines",
        "line_start": 1,
        "line_end": max(1, min(int(record.get("line_count", 1)), 20)),
        "max_chars": 12_000,
        "reason": "manifest-selected bounded range",
    }


def route_request(
    query: str,
    snapshot: Mapping[str, Any],
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Select IDs and JIT ranges using only verified manifest metadata."""

    snapshot_hash = _validate_snapshot(snapshot)
    terms = _query_terms(query)
    safe_request_id = _safe_request_id(request_id, query)
    candidates: list[tuple[int, int, str, Mapping[str, Any], list[str]]] = []
    for record in _all_records(snapshot):
        if record.get("status", "active") != "active":
            continue
        record_id = _record_id(record)
        if record_id is None:
            continue
        score, direct, matched = _score_record(record, terms, query)
        if score == len(terms):
            candidates.append((score, direct, str(record.get("relative_path", "")), record, matched))
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2], str(_record_id(item[3]))))
    selected = candidates[:MAX_PRIMARY]
    primary_ids = [str(_record_id(item[3])) for item in selected]
    selected_set = set(primary_ids)
    record_by_id = {
        record_id: record for record in _all_records(snapshot) if (record_id := _record_id(record)) is not None
    }
    supporting_candidates: list[Mapping[str, Any]] = []
    for neighbor_id in sorted(_relation_neighbors(snapshot, selected_set)):
        neighbor = record_by_id.get(neighbor_id)
        if neighbor is not None and neighbor.get("status", "active") == "active":
            supporting_candidates.append(neighbor)
    supporting_candidates.extend(item[3] for item in candidates[MAX_PRIMARY:])
    seen_supporting: set[str] = set()
    supporting_ids: list[str] = []
    for record in supporting_candidates:
        record_id = _record_id(record)
        if record_id is None or record_id in selected_set or record_id in seen_supporting:
            continue
        seen_supporting.add(record_id)
        supporting_ids.append(record_id)
        if len(supporting_ids) == MAX_SUPPORTING:
            break
    rationale: dict[str, Any] = {}
    for score, direct, path, record, matched in selected:
        record_id = str(_record_id(record))
        rationale[record_id] = {
            "reason": "manifest fields matched request terms",
            "matched_terms": matched,
            "score": score,
            "direct_match": bool(direct),
            "kind": _record_kind(record),
            "relative_path": path,
        }
    jit_ranges = [item for item in (_jit_range(record) for _, _, _, record, _ in selected) if item is not None]
    missing_information: list[str] = []
    if not primary_ids:
        missing_information.append("manifest did not contain a record matching every request term")
    return {
        "primary_ids": primary_ids,
        "supporting_ids": supporting_ids,
        "jit_ranges": jit_ranges[:MAX_JIT_RANGES],
        "rationale_by_id": rationale,
        "missing_information": missing_information,
        "manifest_snapshot_hash": snapshot_hash,
        "request_id": safe_request_id,
        "receipt": {
            "schema_version": ROUTER_SCHEMA_VERSION,
            "status": "PASS" if primary_ids else "PARTIAL",
            "body_read": False,
            "code_body_read": False,
            "primary_count": len(primary_ids),
            "supporting_count": len(supporting_ids),
        },
    }


def load_router_snapshot(
    root: Path,
    policy: Mapping[str, Any] | Path | str,
    *,
    artifact_manifest_path: str = "context/artifact_manifest.json",
    code_manifest_path: str = "context/code_manifest.json",
    relation_graph_path: str = "context/relation_graph.json",
) -> dict[str, Any]:
    """Load and validate local snapshots before exposing them to a router."""

    repository = root.resolve()
    loaded_policy = load_policy(policy)
    try:
        artifact_path = ensure_repo_path(repository, artifact_manifest_path)
        code_path = ensure_repo_path(repository, code_manifest_path)
        graph_path = ensure_repo_path(repository, relation_graph_path)
    except PolicyViolation as exc:
        raise RouterRejected("SNAPSHOT_PATH_INVALID") from exc
    try:
        artifact_manifest = load_manifest_file(artifact_path)
        code_manifest = json.loads(code_path.read_text(encoding="utf-8"))
        relation_graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RouterRejected("SNAPSHOT_INPUT_INVALID") from exc
    artifact_report = validate_manifest(artifact_manifest, repository, loaded_policy)
    code_report = validate_code_manifest(code_manifest, repository, loaded_policy)
    if not artifact_report.valid or not code_report.valid:
        raise RouterRejected("SNAPSHOT_NOT_VERIFIED")
    if not isinstance(relation_graph, Mapping) or not isinstance(relation_graph.get("edges"), list):
        raise RouterRejected("SNAPSHOT_SCHEMA_INVALID")
    serial = json.dumps(
        {
            "artifact_manifest": artifact_manifest,
            "code_manifest": code_manifest,
            "relation_graph": relation_graph,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "verified": True,
        "snapshot_hash": sha256_bytes(serial),
        "artifact_manifest": artifact_manifest,
        "code_manifest": code_manifest,
        "relation_graph": relation_graph,
    }

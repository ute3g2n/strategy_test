from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

from .build_code_manifest import load_code_policy
from .common import (
    ContextIndexError,
    PolicyViolation,
    ensure_repo_path,
    is_managed_document,
    normalize_relative_path,
    scan_secret_content,
    scan_secret_path,
    sha256_bytes,
)
from .context_router import _query_terms, _record_text, load_router_snapshot

MAX_SEARCH_LIMIT = 20
MAX_RELATED_DEPTH = 1
MAX_RESPONSE_CHARS = 12_000
_PROMPT_INJECTION_RE = re.compile(
    r"(?:ignore\s+(?:all\s+)?previous|system\s+prompt|reveal\s+(?:the\s+)?prompt|"
    r"disregard\s+(?:all\s+)?instructions|jailbreak)",
    re.IGNORECASE,
)


class McpRejected(ContextIndexError):
    """Raised for a safe, machine-readable local MCP rejection."""


def _require_mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise McpRejected(code)
    return value


def _limit(value: Any, *, maximum: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximum:
        raise McpRejected(code)
    return value


def _safe_id(value: Any, code: str = "ID_INVALID") -> str:
    if not isinstance(value, str) or not value or len(value) > 200 or "\x00" in value:
        raise McpRejected(code)
    return value


def _safe_path(value: Any) -> str:
    if not isinstance(value, str):
        raise McpRejected("PATH_INVALID")
    try:
        return normalize_relative_path(value)
    except PolicyViolation as exc:
        raise McpRejected("PATH_INVALID") from exc


def _manifest_result(record: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "artifact_id",
        "code_id",
        "relative_path",
        "kind",
        "status",
        "source_hash",
        "title",
        "summary",
        "purpose",
        "language",
        "parser",
        "extraction_status",
        "headings",
        "trace_ids",
        "public_candidates",
        "exports",
    ):
        if key in record and isinstance(record[key], (str, int, list, dict)):
            result[key] = record[key]
    return result


class ContextMcpServer:
    """In-process tools for a local stdio adapter; never opens a network socket."""

    def __init__(
        self,
        *,
        root: Path,
        policy: Mapping[str, Any] | Path | str,
        artifact_manifest: Mapping[str, Any],
        code_manifest: Mapping[str, Any],
        relation_graph: Mapping[str, Any],
    ) -> None:
        self.root = root.resolve()
        self.policy = load_code_policy(policy)
        self.artifact_manifest = dict(artifact_manifest)
        self.code_manifest = dict(code_manifest)
        self.relation_graph = dict(relation_graph)
        self._artifacts = self._index_records(self.artifact_manifest, "artifact_id")
        self._codes = self._index_records(self.code_manifest, "code_id")
        nodes = self.relation_graph.get("nodes", [])
        self._node_ids = {
            str(item.get("node_id"))
            for item in nodes
            if isinstance(item, Mapping) and isinstance(item.get("node_id"), str)
        }

    @staticmethod
    def _index_records(manifest: Mapping[str, Any], id_key: str) -> dict[str, Mapping[str, Any]]:
        records = manifest.get("artifacts")
        if not isinstance(records, list):
            raise McpRejected("MANIFEST_SCHEMA_INVALID")
        result: dict[str, Mapping[str, Any]] = {}
        for record in records:
            if not isinstance(record, Mapping) or not isinstance(record.get(id_key), str):
                continue
            identifier = str(record[id_key])
            if identifier in result:
                raise McpRejected("DUPLICATE_ID")
            result[identifier] = record
        return result

    @classmethod
    def from_paths(
        cls,
        *,
        root: Path,
        policy: Mapping[str, Any] | Path | str,
        artifact_manifest_path: str = "context/artifact_manifest.json",
        code_manifest_path: str = "context/code_manifest.json",
        relation_graph_path: str = "context/relation_graph.json",
    ) -> ContextMcpServer:
        snapshot = load_router_snapshot(
            root,
            policy,
            artifact_manifest_path=artifact_manifest_path,
            code_manifest_path=code_manifest_path,
            relation_graph_path=relation_graph_path,
        )
        return cls(
            root=root,
            policy=policy,
            artifact_manifest=snapshot["artifact_manifest"],
            code_manifest=snapshot["code_manifest"],
            relation_graph=snapshot["relation_graph"],
        )

    def _record_path(self, record: Mapping[str, Any], *, document: bool) -> tuple[str, Path]:
        relative_path = _safe_path(record.get("relative_path"))
        if document:
            if not is_managed_document(relative_path, self.policy):
                raise McpRejected("OUT_OF_SCOPE")
        else:
            from .build_code_manifest import is_managed_code_path

            if not is_managed_code_path(relative_path, self.policy):
                raise McpRejected("OUT_OF_SCOPE")
        try:
            return relative_path, ensure_repo_path(self.root, relative_path)
        except PolicyViolation as exc:
            raise McpRejected("PATH_OUTSIDE_REPO") from exc

    def _read_verified(self, record: Mapping[str, Any], *, document: bool) -> tuple[str, bytes, str]:
        relative_path, target = self._record_path(record, document=document)
        if scan_secret_path(relative_path, self.policy):
            raise McpRejected("SECRET_PATH")
        expected_hash = record.get("source_hash")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
            raise McpRejected("MANIFEST_HASH_INVALID")
        try:
            first_stat = target.stat()
            first = target.read_bytes()
            second_stat = target.stat()
            second = target.read_bytes()
        except (OSError, ValueError) as exc:
            raise McpRejected("FILE_READ_FAILED") from exc
        if first != second or first_stat.st_size != second_stat.st_size or sha256_bytes(first) != expected_hash:
            raise McpRejected("STALE_HASH")
        try:
            text = first.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise McpRejected("INVALID_UTF8") from exc
        max_bytes = int(self.policy.get("max_file_bytes", 0))
        if not document:
            max_bytes = int(self.policy.get("source_max_file_bytes", max_bytes))
        if max_bytes <= 0 or len(first) > max_bytes:
            raise McpRejected("FILE_SIZE_LIMIT")
        if scan_secret_content(text, self.policy):
            raise McpRejected("SECRET_CONTENT")
        if _PROMPT_INJECTION_RE.search(text):
            raise McpRejected("PROMPT_INJECTION_SUSPECTED")
        return relative_path, first, text

    def search_context(
        self,
        query: str,
        *,
        kinds: Sequence[str] | None = None,
        kind: str | None = None,
        limit: int = MAX_SEARCH_LIMIT,
    ) -> list[dict[str, Any]]:
        limit = _limit(limit, maximum=MAX_SEARCH_LIMIT, code="QUERY_LIMIT_INVALID")
        try:
            terms = _query_terms(query)
        except ContextIndexError as exc:
            raise McpRejected(str(exc)) from exc
        allowed_kinds = set(kinds or [])
        if kind is not None:
            allowed_kinds.add(kind)
        if len(allowed_kinds) > 3 or any(not isinstance(item, str) for item in allowed_kinds):
            raise McpRejected("KIND_INVALID")
        candidates: list[tuple[int, str, Mapping[str, Any]]] = []
        for record in [*self._artifacts.values(), *self._codes.values()]:
            if record.get("status", "active") != "active":
                continue
            record_kind = record.get("kind")
            if allowed_kinds and record_kind not in allowed_kinds:
                continue
            haystack = _record_text(record)
            score = sum(term in haystack for term in terms)
            if score == len(terms):
                candidates.append((score, str(record.get("relative_path", "")), record))
        candidates.sort(key=lambda item: (-item[0], item[1], str(item[2].get("artifact_id") or item[2].get("code_id"))))
        return [_manifest_result(record) | {"score": score} for score, _, record in candidates[:limit]]

    def _range_from_input(
        self,
        record: Mapping[str, Any],
        value: Mapping[str, Any] | None,
        line_count: int,
        *,
        document: bool,
    ) -> tuple[int, int, str | None]:
        if value is not None and not isinstance(value, Mapping):
            raise McpRejected("RANGE_INVALID")
        if value is None:
            return 1, min(line_count, 200), None
        if "heading" in value:
            if not document or not isinstance(value.get("heading"), str) or not value["heading"].strip():
                raise McpRejected("HEADING_INVALID")
            heading_text = value["heading"].strip()
            headings = record.get("headings", [])
            matches = [
                item
                for item in headings
                if isinstance(item, Mapping) and item.get("text") == heading_text and isinstance(item.get("line"), int)
            ]
            if len(matches) != 1:
                raise McpRejected("HEADING_NOT_FOUND")
            start = int(matches[0]["line"])
            level = int(matches[0].get("level", 1))
            ends = [
                int(item["line"]) - 1
                for item in headings
                if isinstance(item, Mapping)
                and isinstance(item.get("line"), int)
                and int(item.get("line", 0)) > start
                and int(item.get("level", 99)) <= level
            ]
            end = min(ends[0] if ends else line_count, line_count)
            return start, end, heading_text
        raw_start = value.get("line_start")
        raw_end = value.get("line_end")
        if (
            isinstance(raw_start, bool)
            or isinstance(raw_end, bool)
            or not isinstance(raw_start, int)
            or not isinstance(raw_end, int)
        ):
            raise McpRejected("RANGE_INVALID")
        start = raw_start
        end = raw_end
        if start < 1 or end < start or end > line_count:
            raise McpRejected("RANGE_INVALID")
        return start, end, None

    @staticmethod
    def _bounded_content(lines: list[str], start: int, end: int, max_chars: int) -> str:
        content = "".join(lines[start - 1 : end])
        if len(content) > max_chars:
            raise McpRejected("RESPONSE_TOO_LARGE")
        return content

    def _max_chars(self, value: Any) -> int:
        if value is None:
            return MAX_RESPONSE_CHARS
        return _limit(value, maximum=MAX_RESPONSE_CHARS, code="RESPONSE_LIMIT_INVALID")

    def get_artifact(
        self,
        artifact_id: str,
        heading_or_line_range: Mapping[str, Any] | None = None,
        *,
        max_chars: int = MAX_RESPONSE_CHARS,
    ) -> dict[str, Any]:
        identifier = _safe_id(artifact_id)
        record = self._artifacts.get(identifier)
        if record is None or record.get("status", "active") != "active":
            raise McpRejected("ID_NOT_FOUND")
        max_chars = self._max_chars(max_chars)
        relative_path, _, text = self._read_verified(record, document=True)
        lines = text.splitlines(keepends=True)
        start, end, heading = self._range_from_input(record, heading_or_line_range, len(lines), document=True)
        content = self._bounded_content(lines, start, end, max_chars)
        return {
            "artifact_id": identifier,
            "relative_path": relative_path,
            "source_hash": record["source_hash"],
            "line_start": start,
            "line_end": end,
            "heading": heading,
            "content": content,
        }

    def _registered_code_range(self, record: Mapping[str, Any], start: int, end: int) -> Mapping[str, Any] | None:
        symbols = record.get("symbols", [])
        if not isinstance(symbols, list):
            return None
        for symbol in symbols:
            if not isinstance(symbol, Mapping):
                continue
            symbol_start = symbol.get("line_start")
            symbol_end = symbol.get("line_end")
            if (
                isinstance(symbol_start, int)
                and isinstance(symbol_end, int)
                and symbol_start <= start <= end <= symbol_end
            ):
                return symbol
        return None

    def get_code_slice(
        self,
        code_id: str,
        symbol_or_line_range: Mapping[str, Any] | None = None,
        *,
        max_chars: int = MAX_RESPONSE_CHARS,
    ) -> dict[str, Any]:
        identifier = _safe_id(code_id)
        record = self._codes.get(identifier)
        if record is None or record.get("status", "active") != "active":
            raise McpRejected("ID_NOT_FOUND")
        if record.get("extraction_status") == "BLOCKED":
            raise McpRejected("CODE_BLOCKED")
        if not isinstance(symbol_or_line_range, Mapping):
            raise McpRejected("RANGE_REQUIRED")
        max_chars = self._max_chars(max_chars)
        relative_path, _, text = self._read_verified(record, document=False)
        lines = text.splitlines(keepends=True)
        requested_symbol: str | None = None
        if "symbol" in symbol_or_line_range:
            requested_symbol = symbol_or_line_range.get("symbol")
            if not isinstance(requested_symbol, str) or not requested_symbol:
                raise McpRejected("SYMBOL_INVALID")
            symbols = record.get("symbols", [])
            matches = [
                symbol
                for symbol in symbols
                if isinstance(symbol, Mapping)
                and requested_symbol in {symbol.get("name"), symbol.get("qualified_name")}
            ]
            if len(matches) != 1:
                raise McpRejected("SYMBOL_NOT_FOUND")
            start = matches[0].get("line_start")
            end = matches[0].get("line_end")
            if not isinstance(start, int) or not isinstance(end, int):
                raise McpRejected("RANGE_INVALID")
        else:
            start = symbol_or_line_range.get("line_start")
            end = symbol_or_line_range.get("line_end")
            if (
                isinstance(start, bool)
                or isinstance(end, bool)
                or not isinstance(start, int)
                or not isinstance(end, int)
            ):
                raise McpRejected("RANGE_INVALID")
        if start < 1 or end < start or end > len(lines):
            raise McpRejected("RANGE_INVALID")
        if self._registered_code_range(record, start, end) is None:
            raise McpRejected("RANGE_NOT_REGISTERED")
        content = self._bounded_content(lines, start, end, max_chars)
        return {
            "code_id": identifier,
            "relative_path": relative_path,
            "source_hash": record["source_hash"],
            "extraction_status": record.get("extraction_status"),
            "symbol": requested_symbol,
            "line_start": start,
            "line_end": end,
            "content": content,
        }

    def get_related(
        self,
        subject_id: str,
        *,
        relation_types: Sequence[str] | None = None,
        depth: int = 1,
        limit: int = MAX_SEARCH_LIMIT,
    ) -> dict[str, Any]:
        identifier = _safe_id(subject_id)
        if identifier not in self._node_ids and identifier not in self._artifacts and identifier not in self._codes:
            raise McpRejected("ID_NOT_FOUND")
        if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0 or depth > MAX_RELATED_DEPTH:
            raise McpRejected("DEPTH_INVALID")
        limit = _limit(limit, maximum=MAX_SEARCH_LIMIT, code="QUERY_LIMIT_INVALID")
        allowed = set(relation_types or [])
        if any(not isinstance(item, str) or len(item) > 100 for item in allowed):
            raise McpRejected("RELATION_TYPE_INVALID")
        edges = self.relation_graph.get("edges", [])
        if not isinstance(edges, list):
            raise McpRejected("GRAPH_SCHEMA_INVALID")
        selected: list[Mapping[str, Any]] = []
        frontier = {identifier}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for edge in edges:
                if not isinstance(edge, Mapping):
                    continue
                relation_type = edge.get("relation_type")
                if allowed and relation_type not in allowed:
                    continue
                source = edge.get("source_id")
                target = edge.get("target_id")
                if source in frontier or target in frontier:
                    selected.append(edge)
                    if isinstance(source, str):
                        next_frontier.add(source)
                    if isinstance(target, str):
                        next_frontier.add(target)
            frontier = next_frontier
        selected = sorted(
            {json.dumps(dict(edge), ensure_ascii=False, sort_keys=True): edge for edge in selected}.values(),
            key=lambda edge: json.dumps(dict(edge), ensure_ascii=False, sort_keys=True),
        )[:limit]
        node_ids = {identifier}
        for edge in selected:
            for key in ("source_id", "target_id"):
                value = edge.get(key)
                if isinstance(value, str):
                    node_ids.add(value)
        nodes = [
            dict(node)
            for node in self.relation_graph.get("nodes", [])
            if isinstance(node, Mapping) and node.get("node_id") in node_ids
        ]
        return {"subject_id": identifier, "depth": depth, "edges": [dict(edge) for edge in selected], "nodes": nodes}

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        request = _require_mapping(request, "REQUEST_INVALID")
        tool = request.get("tool")
        arguments = request.get("arguments", {})
        if not isinstance(tool, str) or tool not in {"search_context", "get_artifact", "get_code_slice", "get_related"}:
            raise McpRejected("TOOL_NOT_FOUND")
        arguments = _require_mapping(arguments, "ARGUMENTS_INVALID")
        result: Any
        if tool == "search_context":
            query = arguments.get("query")
            if not isinstance(query, str):
                raise McpRejected("QUERY_INVALID")
            result = self.search_context(
                query,
                kinds=arguments.get("kinds"),
                kind=arguments.get("kind"),
                limit=arguments.get("limit", MAX_SEARCH_LIMIT),
            )
        elif tool == "get_artifact":
            result = self.get_artifact(
                _safe_id(arguments.get("artifact_id")),
                arguments.get("heading_or_line_range"),
                max_chars=arguments.get("max_chars", MAX_RESPONSE_CHARS),
            )
        elif tool == "get_code_slice":
            result = self.get_code_slice(
                _safe_id(arguments.get("code_id")),
                arguments.get("symbol_or_line_range"),
                max_chars=arguments.get("max_chars", MAX_RESPONSE_CHARS),
            )
        else:
            result = self.get_related(
                _safe_id(arguments.get("subject_id")),
                relation_types=arguments.get("relation_types"),
                depth=arguments.get("depth", MAX_RELATED_DEPTH),
                limit=arguments.get("limit", MAX_SEARCH_LIMIT),
            )
        return {"ok": True, "result": result}

    def serve_stdio(self, input_stream: TextIO | None = None, output_stream: TextIO | None = None) -> None:
        """Serve newline-delimited JSON over stdin/stdout only."""

        input_stream = input_stream or sys.stdin
        output_stream = output_stream or sys.stdout
        for line in input_stream:
            try:
                request = json.loads(line)
                result = self.dispatch(request)
            except McpRejected as exc:
                result = {"ok": False, "error": {"code": str(exc)}}
            except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                result = {"ok": False, "error": {"code": "REQUEST_INVALID"}}
            output_stream.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
            output_stream.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve local CTXMAP tools over stdio; no HTTP listener is created.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--artifact-manifest", default="context/artifact_manifest.json")
    parser.add_argument("--code-manifest", default="context/code_manifest.json")
    parser.add_argument("--relation-graph", default="context/relation_graph.json")
    parser.add_argument("--stdio", action="store_true", help="serve JSONL requests over stdin/stdout")
    args = parser.parse_args(argv)
    if not args.stdio:
        print("STDIO_REQUIRED")
        return 2
    try:
        server = ContextMcpServer.from_paths(
            root=args.root,
            policy=args.policy,
            artifact_manifest_path=args.artifact_manifest,
            code_manifest_path=args.code_manifest,
            relation_graph_path=args.relation_graph,
        )
        server.serve_stdio()
    except (McpRejected, OSError, PolicyViolation) as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

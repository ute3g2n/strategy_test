from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .common import ContextIndexError, normalize_relative_path
from .validate_context_index import load_manifest_file


class QueryRejected(ContextIndexError):
    """Raised when a manifest-only query violates its boundary."""


def _query_terms(query: str) -> list[str]:
    if not isinstance(query, str) or not query.strip():
        raise QueryRejected("QUERY_EMPTY")
    if "\x00" in query or ".." in query or query.startswith(("/", "\\")):
        raise QueryRejected("QUERY_PATH_TRAVERSAL")
    return [term.casefold() for term in query.split() if term]


def _search_text(record: Mapping[str, Any]) -> str:
    heading_text = " ".join(str(item.get("text", "")) for item in record.get("headings", []))
    traces = " ".join(str(item) for item in record.get("trace_ids", []))
    return " ".join(
        str(record.get(key, "")) for key in ("relative_path", "title", "summary", "purpose")
    ) + " " + heading_text + " " + traces


def query_manifest(
    manifest: Mapping[str, Any],
    query: str,
    *,
    kind: str | None = None,
    status: str = "active",
    limit: int = 20,
) -> list[dict[str, Any]]:
    terms = _query_terms(query)
    if limit < 1 or limit > 100:
        raise QueryRejected("QUERY_LIMIT_INVALID")
    results: list[dict[str, Any]] = []
    for record in manifest.get("artifacts", []):
        if not isinstance(record, Mapping):
            continue
        if status and record.get("status") != status:
            continue
        if kind and record.get("kind") != kind:
            continue
        haystack = _search_text(record).casefold()
        score = sum(1 for term in terms if term in haystack)
        if score == len(terms):
            results.append(
                {
                    "artifact_id": record.get("artifact_id"),
                    "relative_path": record.get("relative_path"),
                    "kind": record.get("kind"),
                    "status": record.get("status"),
                    "source_hash": record.get("source_hash"),
                    "title": record.get("title", ""),
                    "headings": record.get("headings", []),
                    "trace_ids": record.get("trace_ids", []),
                    "score": score,
                }
            )
    return sorted(results, key=lambda item: (-int(item["score"]), str(item["relative_path"])))[:limit]


def validate_path_filter(value: str) -> str:
    try:
        return normalize_relative_path(value)
    except ContextIndexError as exc:
        raise QueryRejected("QUERY_PATH_INVALID") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query CTXMAP metadata without reading document bodies.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--kind")
    parser.add_argument("--status", default="active")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest_file(args.manifest)
        result = query_manifest(manifest, args.query, kind=args.kind, status=args.status, limit=args.limit)
    except (OSError, QueryRejected, ValueError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .common import ContextIndexError
from .context_mcp_server import ContextMcpServer
from .context_router import load_router_snapshot, route_request


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--artifact-manifest", default="context/artifact_manifest.json")
    parser.add_argument("--code-manifest", default="context/code_manifest.json")
    parser.add_argument("--relation-graph", default="context/relation_graph.json")


def _server(args: argparse.Namespace) -> ContextMcpServer:
    return ContextMcpServer.from_paths(
        root=args.root,
        policy=args.policy,
        artifact_manifest_path=args.artifact_manifest,
        code_manifest_path=args.code_manifest,
        relation_graph_path=args.relation_graph,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query CTXMAP metadata and bounded JIT content locally.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    route = subparsers.add_parser("route")
    _common(route)
    route.add_argument("--query", required=True)
    route.add_argument("--request-id")

    search = subparsers.add_parser("search")
    _common(search)
    search.add_argument("--query", required=True)
    search.add_argument("--kind")
    search.add_argument("--limit", type=int, default=20)

    artifact = subparsers.add_parser("get-artifact")
    _common(artifact)
    artifact.add_argument("--artifact-id", required=True)
    artifact.add_argument("--heading")
    artifact.add_argument("--line-start", type=int)
    artifact.add_argument("--line-end", type=int)
    artifact.add_argument("--max-chars", type=int, default=12_000)

    code = subparsers.add_parser("get-code-slice")
    _common(code)
    code.add_argument("--code-id", required=True)
    code.add_argument("--symbol")
    code.add_argument("--line-start", type=int)
    code.add_argument("--line-end", type=int)
    code.add_argument("--max-chars", type=int, default=12_000)

    related = subparsers.add_parser("get-related")
    _common(related)
    related.add_argument("--subject-id", required=True)
    related.add_argument("--depth", type=int, default=1)
    related.add_argument("--limit", type=int, default=20)

    stdio = subparsers.add_parser("stdio")
    _common(stdio)

    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            snapshot = load_router_snapshot(
                args.root,
                args.policy,
                artifact_manifest_path=args.artifact_manifest,
                code_manifest_path=args.code_manifest,
                relation_graph_path=args.relation_graph,
            )
            result: Any = route_request(args.query, snapshot, request_id=args.request_id)
        elif args.command == "search":
            result = _server(args).search_context(args.query, kind=args.kind, limit=args.limit)
        elif args.command == "get-artifact":
            range_value: dict[str, Any] | None = None
            if args.heading:
                range_value = {"heading": args.heading}
            elif args.line_start is not None or args.line_end is not None:
                range_value = {"line_start": args.line_start, "line_end": args.line_end}
            result = _server(args).get_artifact(args.artifact_id, range_value, max_chars=args.max_chars)
        elif args.command == "get-code-slice":
            if args.symbol:
                range_value = {"symbol": args.symbol}
            else:
                range_value = {"line_start": args.line_start, "line_end": args.line_end}
            result = _server(args).get_code_slice(args.code_id, range_value, max_chars=args.max_chars)
        elif args.command == "get-related":
            result = _server(args).get_related(args.subject_id, depth=args.depth, limit=args.limit)
        else:
            _server(args).serve_stdio()
            return 0
    except ContextIndexError as exc:
        print(json.dumps({"ok": False, "error": {"code": str(exc)}}, ensure_ascii=False))
        return 1
    except (OSError, UnicodeError, json.JSONDecodeError):
        print(json.dumps({"ok": False, "error": {"code": "CLI_INPUT_INVALID"}}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

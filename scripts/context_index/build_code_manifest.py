from __future__ import annotations

import argparse
import ast
import json
import os
import posixpath
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import (
    PolicyViolation,
    ensure_repo_path,
    load_policy,
    normalize_relative_path,
    scan_secret_content,
    scan_secret_path,
    sha256_bytes,
    stable_id,
)

CODE_MANIFEST_SCHEMA_VERSION = "ctxmap-code-manifest-v0.1"
CODE_GENERATOR_VERSION = "ctxmap-code-indexer-v0.1"
PARTIAL_REMEDIATION_OWNER = "AutoTrade_A06_AiComponentEngineer_v0_1"
PARTIAL_REMEDIATION_DEADLINE = "2026-08-21"
_CODE_EXTENSIONS = [".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".ps1", ".sh", ".bash", ".cmd"]
_CONFIG_EXTENSIONS = [".json", ".toml", ".yaml", ".yml"]
_SECRET_KEY_RE = re.compile(
    r"(?:password|passwd|token|secret|api[_-]?key|private[_-]?key|credential|authorization|cookie|access[_-]?key)",
    re.IGNORECASE,
)
_SAFE_MODULE_RE = re.compile(r"^[A-Za-z0-9_./@$:+~-]{1,256}$")


@dataclass(frozen=True)
class CodeValidationReport:
    valid: bool
    status: str
    errors: list[dict[str, str]]
    counts: dict[str, int]


def load_code_policy(policy: Mapping[str, Any] | Path | str) -> dict[str, Any]:
    loaded = load_policy(policy)
    loaded.setdefault("managed_source_roots", loaded.get("managed_roots", []))
    loaded.setdefault("managed_source_extensions", _CODE_EXTENSIONS)
    loaded.setdefault("managed_config_extensions", _CONFIG_EXTENSIONS)
    loaded.setdefault("source_exclude_dirs", loaded.get("exclude_dirs", []))
    loaded.setdefault("source_exclude_paths", [])
    if not isinstance(loaded["managed_source_roots"], list):
        raise PolicyViolation("CODE_POLICY_TYPE_INVALID")
    if not isinstance(loaded["managed_source_extensions"], list):
        raise PolicyViolation("CODE_POLICY_TYPE_INVALID")
    if not isinstance(loaded["managed_config_extensions"], list):
        raise PolicyViolation("CODE_POLICY_TYPE_INVALID")
    if not isinstance(loaded["source_exclude_paths"], list):
        raise PolicyViolation("CODE_POLICY_TYPE_INVALID")
    return loaded


def _is_config(relative_path: str, policy: Mapping[str, Any]) -> bool:
    return Path(relative_path).suffix.lower() in {
        str(item).lower() for item in policy.get("managed_config_extensions", _CONFIG_EXTENSIONS)
    }


def _is_code(relative_path: str, policy: Mapping[str, Any]) -> bool:
    return Path(relative_path).suffix.lower() in {
        str(item).lower() for item in policy.get("managed_source_extensions", _CODE_EXTENSIONS)
    }


def _is_source_excluded(relative_path: str, policy: Mapping[str, Any]) -> bool:
    normalized = normalize_relative_path(relative_path)
    return any(
        normalized == normalize_relative_path(str(item))
        or normalized.startswith(normalize_relative_path(str(item)) + "/")
        for item in policy.get("source_exclude_paths", [])
    )


def is_managed_code_path(relative_path: str, policy: Mapping[str, Any]) -> bool:
    normalized = normalize_relative_path(relative_path)
    if scan_secret_path(normalized, policy):
        return False
    if _is_source_excluded(normalized, policy):
        return False
    if any(
        any(part == str(pattern) or part.startswith(str(pattern) + ".") for part in normalized.split("/"))
        for pattern in policy.get("source_exclude_dirs", [])
    ):
        return False
    roots = [normalize_relative_path(str(item)) for item in policy["managed_source_roots"]]
    if not any(normalized == root or normalized.startswith(root + "/") for root in roots):
        return False
    return _is_code(normalized, policy) or _is_config(normalized, policy)


def discover_code_paths(root: Path, policy: Mapping[str, Any]) -> list[str]:
    root_resolved = root.resolve()
    candidates: list[str] = []
    for raw_root in policy["managed_source_roots"]:
        root_value = normalize_relative_path(str(raw_root))
        root_path = ensure_repo_path(root_resolved, root_value)
        if not root_path.exists():
            continue
        if root_path.is_file():
            relative = root_value
            if scan_secret_path(relative, policy):
                raise PolicyViolation("SECRET_PATH")
            if is_managed_code_path(relative, policy):
                candidates.append(relative)
            continue
        for current, dirs, files in os.walk(root_path, topdown=True, followlinks=False):
            current_path = Path(current)
            dirs[:] = [
                name for name in dirs if name not in set(str(item) for item in policy.get("source_exclude_dirs", []))
            ]
            for name in sorted(files):
                absolute = current_path / name
                try:
                    relative = absolute.resolve().relative_to(root_resolved).as_posix()
                except ValueError as exc:
                    raise PolicyViolation("PATH_OUTSIDE_REPOSITORY") from exc
                if scan_secret_path(relative, policy):
                    raise PolicyViolation("SECRET_PATH")
                if is_managed_code_path(relative, policy):
                    candidates.append(relative)
    return sorted(set(candidates))


def _read_file(
    root: Path, relative_path: str, policy: Mapping[str, Any], *, allow_secret_content: bool
) -> tuple[bytes, str]:
    normalized = normalize_relative_path(relative_path)
    if scan_secret_path(normalized, policy):
        raise PolicyViolation("SECRET_PATH")
    target = ensure_repo_path(root, normalized)
    try:
        data = target.read_bytes()
    except (OSError, ValueError) as exc:
        raise PolicyViolation("FILE_READ_FAILED") from exc
    max_bytes = int(policy.get("source_max_file_bytes", policy.get("max_file_bytes", 0)))
    if max_bytes <= 0 or len(data) > max_bytes:
        raise PolicyViolation("FILE_SIZE_LIMIT")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyViolation("UTF8_REQUIRED") from exc
    if not allow_secret_content and scan_secret_content(text, policy):
        raise PolicyViolation("SECRET_CONTENT")
    return data, text


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _safe_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _safe_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return "dynamic"


class _PythonExtractor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols: list[dict[str, Any]] = []
        self.imports: list[dict[str, Any]] = []
        self._scope: list[str] = []

    def _add_symbol(self, node: ast.AST, name: str, kind: str, decorators: list[str]) -> None:
        line_start = int(getattr(node, "lineno", 1))
        line_end = int(getattr(node, "end_lineno", line_start))
        qualified = ".".join([*self._scope, name])
        self.symbols.append(
            {
                "name": name,
                "qualified_name": qualified,
                "kind": kind,
                "line_start": line_start,
                "line_end": line_end,
                "parent": ".".join(self._scope) or None,
                "decorators": sorted(decorators),
                "public": not name.startswith("_"),
            }
        )

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            self.imports.append(
                {
                    "kind": "import",
                    "module": item.name,
                    "name": item.name,
                    "alias": item.asname,
                    "level": 0,
                    "line": node.lineno,
                }
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for item in node.names:
            self.imports.append(
                {
                    "kind": "from_import",
                    "module": module,
                    "name": item.name,
                    "alias": item.asname,
                    "level": node.level,
                    "line": node.lineno,
                }
            )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add_symbol(node, node.name, "class", [_safe_name(item) for item in node.decorator_list])
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = (
            "method"
            if any(
                item["kind"] == "class"
                for item in self.symbols
                if item["qualified_name"].startswith(".".join(self._scope))
            )
            else "function"
        )
        self._add_symbol(node, node.name, kind, [_safe_name(item) for item in node.decorator_list])
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)


def _base_record(
    relative_path: str,
    data: bytes,
    *,
    language: str,
    parser: str,
    kind: str,
    extraction_status: str,
    symbols: list[dict[str, Any]] | None = None,
    imports: list[dict[str, Any]] | None = None,
    exports: list[str] | None = None,
    config: dict[str, Any] | None = None,
    diagnostics: list[dict[str, str]] | None = None,
    existing_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    old_id = existing_record.get("code_id") if existing_record else None
    code_id = (
        str(old_id)
        if isinstance(old_id, str) and old_id.startswith("code-")
        else stable_id("code", f"file:{relative_path}")
    )
    symbols = sorted(
        symbols or [], key=lambda item: (int(item.get("line_start", 0)), str(item.get("qualified_name", "")))
    )
    imports = sorted(
        imports or [],
        key=lambda item: (int(item.get("line", 0)), str(item.get("module", "")), str(item.get("name", ""))),
    )
    exports = sorted(set(exports or []))
    diagnostics = sorted(diagnostics or [], key=lambda item: (str(item.get("code", "")), str(item.get("message", ""))))
    record = {
        "code_id": code_id,
        "kind": kind,
        "status": "active" if extraction_status != "BLOCKED" else "blocked",
        "relative_path": relative_path,
        "source_hash": sha256_bytes(data) if data else None,
        "schema_version": CODE_MANIFEST_SCHEMA_VERSION,
        "generator_version": CODE_GENERATOR_VERSION,
        "language": language,
        "parser": parser,
        "extraction_status": extraction_status,
        "symbols": symbols,
        "imports": imports,
        "exports": exports,
        "public_candidates": sorted(item["qualified_name"] for item in symbols if item.get("public")),
        "config": config or {},
        "diagnostics": diagnostics,
        "line_count": len(data.decode("utf-8").splitlines()) if data else 0,
        "byte_size": len(data),
    }
    if extraction_status == "PARTIAL":
        record["remediation"] = {
            "status": "OPEN",
            "owner": PARTIAL_REMEDIATION_OWNER,
            "deadline": PARTIAL_REMEDIATION_DEADLINE,
            "acceptance": "parser-specific diagnostics are resolved or explicitly accepted with a dated review receipt",
        }
    return record


def _extract_python(relative_path: str, data: bytes, text: str, existing: Mapping[str, Any] | None) -> dict[str, Any]:
    try:
        tree = ast.parse(text, filename=relative_path)
    except SyntaxError:
        return _base_record(
            relative_path,
            data,
            language="python",
            parser="python-ast-v0.1",
            kind="managed_source",
            extraction_status="PARTIAL",
            diagnostics=[{"code": "PYTHON_SYNTAX_ERROR", "message": "syntax could not be parsed"}],
            existing_record=existing,
        )
    extractor = _PythonExtractor()
    extractor.visit(tree)
    return _base_record(
        relative_path,
        data,
        language="python",
        parser="python-ast-v0.1",
        kind="managed_source",
        extraction_status="COMPLETE",
        symbols=extractor.symbols,
        imports=extractor.imports,
        existing_record=existing,
    )


def _safe_module(value: str) -> str | None:
    value = value.strip()
    if not value or value.startswith(("//", "http:", "https:")) or not _SAFE_MODULE_RE.fullmatch(value):
        return None
    return value


def _regex_record(relative_path: str, data: bytes, text: str, existing: Mapping[str, Any] | None) -> dict[str, Any]:
    suffix = Path(relative_path).suffix.lower()
    language = (
        "typescript"
        if suffix in {".ts", ".tsx"}
        else "javascript"
        if suffix in {".js", ".mjs", ".cjs"}
        else "powershell"
        if suffix == ".ps1"
        else "shell"
    )
    symbols: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    exports: list[str] = []

    if language in {"typescript", "javascript"}:
        symbol_patterns = [
            (r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", "function"),
            (r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", "class"),
            (
                r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
                "function",
            ),
        ]
        for pattern, kind in symbol_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                line = _line(text, match.start())
                line_text = text.splitlines()[line - 1].lstrip()
                if line_text.startswith("//"):
                    continue
                name = match.group(1)
                symbols.append(
                    {
                        "name": name,
                        "qualified_name": name,
                        "kind": kind,
                        "line_start": line,
                        "line_end": line,
                        "parent": None,
                        "decorators": [],
                        "public": not name.startswith("_") or line_text.startswith("export"),
                    }
                )
        for match in re.finditer(r"^\s*import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", text, re.MULTILINE):
            module = _safe_module(match.group(1))
            if module:
                imports.append(
                    {
                        "kind": "import",
                        "module": module,
                        "name": None,
                        "alias": None,
                        "level": 0,
                        "line": _line(text, match.start()),
                    }
                )
        for match in re.finditer(r"^\s*import\s+['\"]([^'\"]+)['\"]", text, re.MULTILINE):
            module = _safe_module(match.group(1))
            if module:
                imports.append(
                    {
                        "kind": "import",
                        "module": module,
                        "name": None,
                        "alias": None,
                        "level": 0,
                        "line": _line(text, match.start()),
                    }
                )
        for match in re.finditer(r"\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)", text):
            module = _safe_module(match.group(1))
            if module:
                imports.append(
                    {
                        "kind": "require",
                        "module": module,
                        "name": None,
                        "alias": None,
                        "level": 0,
                        "line": _line(text, match.start()),
                    }
                )
        for match in re.finditer(r"^\s*export\s*\{([^}]+)\}", text, re.MULTILINE):
            exports.extend(item.strip().split(" as ")[0] for item in match.group(1).split(",") if item.strip())
        diagnostics = [{"code": "CONSERVATIVE_REGEX_ONLY", "message": "full parser dependency not added"}]
        if re.search(r"\bimport\s*\(", text):
            diagnostics.append({"code": "DYNAMIC_IMPORT_UNRESOLVED", "message": "dynamic import was not resolved"})
    elif language == "powershell":
        for match in re.finditer(r"^\s*function\s+([A-Za-z_][\w-]*)", text, re.MULTILINE | re.IGNORECASE):
            symbols.append(
                {
                    "name": match.group(1),
                    "qualified_name": match.group(1),
                    "kind": "function",
                    "line_start": _line(text, match.start()),
                    "line_end": _line(text, match.start()),
                    "parent": None,
                    "decorators": [],
                    "public": True,
                }
            )
        for match in re.finditer(r"^\s*\.\s+([./][^\s;]+)", text, re.MULTILINE):
            imports.append(
                {
                    "kind": "dot_source",
                    "module": match.group(1),
                    "name": None,
                    "alias": None,
                    "level": 0,
                    "line": _line(text, match.start()),
                }
            )
        diagnostics = [{"code": "CONSERVATIVE_REGEX_ONLY", "message": "PowerShell grammar was not added"}]
    else:
        for match in re.finditer(r"^\s*([A-Za-z_]\w*)\s*\(\)\s*\{", text, re.MULTILINE):
            symbols.append(
                {
                    "name": match.group(1),
                    "qualified_name": match.group(1),
                    "kind": "function",
                    "line_start": _line(text, match.start()),
                    "line_end": _line(text, match.start()),
                    "parent": None,
                    "decorators": [],
                    "public": True,
                }
            )
        for match in re.finditer(r"^\s*(?:source|\.)\s+([./][^\s;]+)", text, re.MULTILINE):
            imports.append(
                {
                    "kind": "source",
                    "module": match.group(1),
                    "name": None,
                    "alias": None,
                    "level": 0,
                    "line": _line(text, match.start()),
                }
            )
        diagnostics = [{"code": "CONSERVATIVE_REGEX_ONLY", "message": "shell grammar was not added"}]
    return _base_record(
        relative_path,
        data,
        language=language,
        parser="conservative-regex-v0.1",
        kind="managed_source",
        extraction_status="PARTIAL",
        symbols=symbols,
        imports=imports,
        exports=exports,
        diagnostics=diagnostics,
        existing_record=existing,
    )


def _is_secret_key(key: str) -> bool:
    return bool(_SECRET_KEY_RE.search(key))


def _config_metadata(value: Any, policy: Mapping[str, Any]) -> tuple[list[str], list[str], int, int]:
    safe_keys: list[str] = []
    reference_paths: list[str] = []
    secret_key_count = 0
    secret_value_count = 0
    if isinstance(value, dict):
        for key, child in value.items():
            key_string = str(key)
            if _is_secret_key(key_string):
                secret_key_count += 1
            elif len(safe_keys) < 100:
                safe_keys.append(key_string[:200])
            child_keys, child_refs, child_secret_keys, child_secret_values = _config_metadata(child, policy)
            reference_paths.extend(child_refs)
            secret_key_count += child_secret_keys
            secret_value_count += child_secret_values
    elif isinstance(value, list):
        for child in value[:100]:
            _, child_refs, child_secret_keys, child_secret_values = _config_metadata(child, policy)
            reference_paths.extend(child_refs)
            secret_key_count += child_secret_keys
            secret_value_count += child_secret_values
    elif isinstance(value, str):
        if scan_secret_content(value, policy):
            secret_value_count += 1
        elif value.startswith(("./", "../")):
            normalized = posixpath.normpath(value.replace("\\", "/"))
            if normalized not in {".", ".."} and not normalized.startswith("../"):
                reference_paths.append(normalized)
    return sorted(set(safe_keys)), sorted(set(reference_paths)), secret_key_count, secret_value_count


def _extract_config(
    relative_path: str, data: bytes, text: str, policy: Mapping[str, Any], existing: Mapping[str, Any] | None
) -> dict[str, Any]:
    if Path(relative_path).suffix.lower() == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return _base_record(
                relative_path,
                data,
                language="json",
                parser="json-metadata-v0.1",
                kind="managed_config",
                extraction_status="PARTIAL",
                diagnostics=[{"code": "JSON_SYNTAX_ERROR", "message": "JSON could not be parsed"}],
                existing_record=existing,
            )
        safe_keys, reference_paths, secret_key_count, secret_value_count = _config_metadata(value, policy)
        diagnostics: list[dict[str, str]] = []
        if secret_key_count or secret_value_count:
            diagnostics.append({"code": "SECRET_METADATA_OMITTED", "message": "secret-like metadata was omitted"})
        return _base_record(
            relative_path,
            data,
            language="json",
            parser="json-metadata-v0.1",
            kind="managed_config",
            extraction_status="PARTIAL" if diagnostics else "COMPLETE",
            config={
                "safe_top_level_keys": safe_keys,
                "reference_paths": sorted(set(reference_paths)),
                "secret_key_count": secret_key_count,
                "secret_value_count": secret_value_count,
            },
            diagnostics=diagnostics,
            existing_record=existing,
        )
    keys = sorted(
        set(match.group(1) for match in re.finditer(r"^\s*[\"']?([A-Za-z0-9_.-]+)[\"']?\s*:", text, re.MULTILINE))
    )
    return _base_record(
        relative_path,
        data,
        language=Path(relative_path).suffix.lower().lstrip(".") or "config",
        parser="config-key-regex-v0.1",
        kind="managed_config",
        extraction_status="PARTIAL",
        config={"safe_top_level_keys": [key for key in keys if not _is_secret_key(key)][:100], "reference_paths": []},
        diagnostics=[{"code": "CONSERVATIVE_CONFIG_KEYS_ONLY", "message": "config parser is intentionally partial"}],
        existing_record=existing,
    )


def _mark_secret_like_source(record: dict[str, Any], text: str, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Mark source content as partial without retaining the matching value."""

    if not scan_secret_content(text, policy):
        return record
    diagnostics = list(record.get("diagnostics", []))
    diagnostics.append(
        {
            "code": "SECRET_LIKE_CONTENT_OMITTED",
            "message": "secret-like source content was not retained",
        }
    )
    record["diagnostics"] = sorted(
        diagnostics,
        key=lambda item: (str(item.get("code", "")), str(item.get("message", ""))),
    )
    if record.get("extraction_status") == "COMPLETE":
        record["extraction_status"] = "PARTIAL"
    return record


def extract_code_file(
    root: Path,
    relative_path: str,
    policy: Mapping[str, Any] | Path | str,
    existing_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    loaded = load_code_policy(policy)
    normalized = normalize_relative_path(relative_path)
    if not is_managed_code_path(normalized, loaded):
        raise PolicyViolation("OUT_OF_SCOPE")
    data, text = _read_file(root.resolve(), normalized, loaded, allow_secret_content=True)
    if _is_config(normalized, loaded):
        return _extract_config(normalized, data, text, loaded, existing_record)
    if Path(normalized).suffix.lower() == ".py":
        record = _extract_python(normalized, data, text, existing_record)
    else:
        record = _regex_record(normalized, data, text, existing_record)
    return _mark_secret_like_source(record, text, loaded)


def _blocked_record(relative_path: str, code: str, existing_record: Mapping[str, Any] | None = None) -> dict[str, Any]:
    record = _base_record(
        relative_path,
        b"",
        language=Path(relative_path).suffix.lower().lstrip(".") or "unknown",
        parser="none",
        kind="managed_config" if Path(relative_path).suffix.lower() in _CONFIG_EXTENSIONS else "managed_source",
        extraction_status="BLOCKED",
        diagnostics=[{"code": code, "message": "extraction stopped safely"}],
        existing_record=existing_record,
    )
    record["source_hash"] = None
    return record


def _existing_by_path(existing_manifest: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not existing_manifest or not isinstance(existing_manifest.get("artifacts"), list):
        return {}
    return {
        str(item["relative_path"]): item
        for item in existing_manifest["artifacts"]
        if isinstance(item, dict) and isinstance(item.get("relative_path"), str)
    }


def build_code_manifest(
    root: Path,
    policy: Mapping[str, Any] | Path | str,
    *,
    observed_at: str | None = None,
    existing_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    loaded = load_code_policy(policy)
    timestamp = observed_at if observed_at and re.fullmatch(r"[0-9T:Z+._-]{1,64}", observed_at) else "UNSPECIFIED"
    existing_by_path = _existing_by_path(existing_manifest)
    paths = discover_code_paths(root.resolve(), loaded)
    old_by_hash: dict[str, list[dict[str, Any]]] = {}
    for record in existing_by_path.values():
        if isinstance(record.get("source_hash"), str):
            old_by_hash.setdefault(record["source_hash"], []).append(record)
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for relative_path in paths:
        existing = existing_by_path.get(relative_path)
        if existing is None:
            try:
                data, _ = _read_file(
                    root.resolve(), relative_path, loaded, allow_secret_content=True
                )
                candidates = [
                    item for item in old_by_hash.get(sha256_bytes(data), []) if item.get("relative_path") not in paths
                ]
                if len(candidates) == 1:
                    existing = candidates[0]
                    renamed_from = str(existing["relative_path"])
                else:
                    renamed_from = None
                    if len(candidates) > 1:
                        diagnostics.append({"code": "RENAME_AMBIGUOUS", "relative_path": relative_path})
                record = extract_code_file(root.resolve(), relative_path, loaded, existing)
                if renamed_from:
                    record["last_known_path"] = renamed_from
                    record["rename_status"] = "renamed"
            except PolicyViolation as exc:
                record = _blocked_record(relative_path, str(exc), existing)
        else:
            try:
                record = extract_code_file(root.resolve(), relative_path, loaded, existing)
            except PolicyViolation as exc:
                record = _blocked_record(relative_path, str(exc), existing)
        records.append(record)
    records.sort(key=lambda item: str(item["relative_path"]))
    # Two live paths with the same content make hash-only rename recovery
    # ambiguous. Keep the condition explicit in the manifest so a later
    # maintenance run cannot silently assign either path's historical ID.
    current_by_hash: dict[str, list[str]] = {}
    for record in records:
        record_hash = record.get("source_hash")
        current_path = record.get("relative_path")
        if isinstance(record_hash, str) and isinstance(current_path, str):
            current_by_hash.setdefault(record_hash, []).append(current_path)
    for _source_hash, relative_paths in sorted(current_by_hash.items()):
        if len(relative_paths) > 1:
            diagnostics.append(
                {
                    "code": "RENAME_AMBIGUOUS",
                    "relative_path": ",".join(sorted(relative_paths)),
                }
            )
    diagnostics.sort(key=lambda item: (item.get("code", ""), item.get("relative_path", "")))
    statuses = {str(item["extraction_status"]) for item in records}
    status = "BLOCKED" if "BLOCKED" in statuses else "PARTIAL" if "PARTIAL" in statuses or diagnostics else "COMPLETE"
    return {
        "schema_version": CODE_MANIFEST_SCHEMA_VERSION,
        "generator_version": CODE_GENERATOR_VERSION,
        "observed_at": timestamp,
        "status": status,
        "artifacts": records,
        "diagnostics": diagnostics,
        "coverage": {"discovered": len(paths), "registered": len(records)},
    }


def validate_code_manifest(
    manifest: Mapping[str, Any],
    root: Path,
    policy: Mapping[str, Any] | Path | str,
) -> CodeValidationReport:
    errors: list[dict[str, str]] = []
    try:
        loaded = load_code_policy(policy)
        paths = set(discover_code_paths(root.resolve(), loaded))
    except PolicyViolation as exc:
        return CodeValidationReport(False, "BLOCKED", [{"code": str(exc)}], {})
    if manifest.get("schema_version") != CODE_MANIFEST_SCHEMA_VERSION or not isinstance(
        manifest.get("artifacts"), list
    ):
        return CodeValidationReport(False, "BLOCKED", [{"code": "SCHEMA_INVALID"}], {})
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    counts: dict[str, int] = {}
    for record in manifest["artifacts"]:
        if not isinstance(record, dict):
            errors.append({"code": "SCHEMA_INVALID"})
            continue
        path = record.get("relative_path")
        code_id = record.get("code_id")
        if not isinstance(path, str) or not isinstance(code_id, str):
            errors.append({"code": "SCHEMA_INVALID"})
            continue
        try:
            normalized = normalize_relative_path(path)
        except PolicyViolation:
            errors.append({"code": "PATH_INVALID"})
            continue
        if normalized in seen_paths or code_id in seen_ids:
            errors.append({"code": "DUPLICATE_ID_OR_PATH", "relative_path": normalized})
        seen_paths.add(normalized)
        seen_ids.add(code_id)
        extraction_status = record.get("extraction_status")
        counts[str(extraction_status)] = counts.get(str(extraction_status), 0) + 1
        if extraction_status == "BLOCKED":
            errors.append({"code": "BLOCKED_EXTRACTION", "relative_path": normalized})
            continue
        try:
            data, _ = _read_file(
                root.resolve(), normalized, loaded, allow_secret_content=True
            )
        except PolicyViolation as exc:
            errors.append({"code": str(exc), "relative_path": normalized})
            continue
        if record.get("source_hash") != sha256_bytes(data):
            errors.append({"code": "STALE_SOURCE", "relative_path": normalized})
    for path in sorted(paths - seen_paths):
        errors.append({"code": "UNREGISTERED_SOURCE", "relative_path": path})
    status = "BLOCKED" if errors else str(manifest.get("status", "COMPLETE"))
    return CodeValidationReport(not errors, status, errors, counts)


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic code manifest without executing source.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--existing-manifest", type=Path)
    parser.add_argument("--observed-at")
    args = parser.parse_args(argv)
    try:
        existing = json.loads(args.existing_manifest.read_text(encoding="utf-8")) if args.existing_manifest else None
        manifest = build_code_manifest(args.root, args.policy, observed_at=args.observed_at, existing_manifest=existing)
        write_json(args.output, manifest)
    except (OSError, UnicodeError, json.JSONDecodeError, PolicyViolation) as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": manifest["status"], "artifact_count": len(manifest["artifacts"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

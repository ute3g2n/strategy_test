from __future__ import annotations

# Step 02 user authority: context-management hash generation and comparison
# are retired. Shared helpers enforce only path, scope, UTF-8, size, Secret,
# and metadata extraction boundaries.
import fnmatch
import html
import os
import posixpath
import re
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

SCHEMA_VERSION = "ctxmap-manifest-v0.1"
POLICY_SCHEMA_VERSION = "ctxmap-policy-v0.1"
GENERATOR_VERSION = "ctxmap-indexer-v0.1"
_UUID_NAMESPACE = uuid.UUID("1a1c0d8e-2f1a-4f2d-8f3c-6c6cde9b3a11")
_TRACE_ID_RE = re.compile(r"\b(?:REQ|DEC|UNK|ART|CTXMAP)-[A-Za-z0-9._-]+\b")
_MD_HEADING_RE = re.compile(r"^(#{1,3})[ \t]+(.+?)\s*$")
_HTML_HEADING_RE = re.compile(r"<h([1-3])(?:\s[^>]*)?>(.*?)</h\1\s*>", re.IGNORECASE | re.DOTALL)
_HTML_TITLE_RE = re.compile(r"<title(?:\s[^>]*)?>(.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
_MD_LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
_HTML_HREF_RE = re.compile(r"\bhref\s*=\s*([\"'])(.*?)\1", re.IGNORECASE | re.DOTALL)


class ContextIndexError(ValueError):
    """Base error with safe, non-content-bearing messages."""


class PolicyViolation(ContextIndexError):
    """Raised when a path or input violates the local policy."""


class SecretDetected(PolicyViolation):
    """Raised without including the detected secret value."""


def normalize_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PolicyViolation("PATH_INVALID")
    normalized = value.replace("\\", "/")
    if normalized.startswith("//"):
        raise PolicyViolation("PATH_UNC")
    if re.match(r"^[A-Za-z]:", normalized) or normalized.startswith("/"):
        raise PolicyViolation("PATH_ABSOLUTE")
    parts = normalized.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise PolicyViolation("PATH_TRAVERSAL")
    return "/".join(parts)


def ensure_repo_path(root: Path, relative_path: str) -> Path:
    normalized = normalize_relative_path(relative_path)
    root_resolved = root.resolve()
    candidate = (root_resolved / Path(*normalized.split("/"))).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise PolicyViolation("PATH_OUTSIDE_REPOSITORY")
    return candidate


def load_policy(policy: Mapping[str, Any] | Path | str) -> dict[str, Any]:
    if isinstance(policy, (Path, str)):
        import json

        try:
            loaded = json.loads(Path(policy).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PolicyViolation("POLICY_INPUT_INVALID") from exc
    else:
        loaded = dict(policy)
    if loaded.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise PolicyViolation("POLICY_SCHEMA_INVALID")
    required = ("managed_extensions", "managed_roots", "exclude_dirs", "max_file_bytes")
    if any(key not in loaded for key in required):
        raise PolicyViolation("POLICY_REQUIRED_FIELD_MISSING")
    if not isinstance(loaded["managed_extensions"], list) or not isinstance(loaded["managed_roots"], list):
        raise PolicyViolation("POLICY_TYPE_INVALID")
    return loaded


def _matches_excluded(relative_path: str, policy: Mapping[str, Any]) -> bool:
    parts = relative_path.split("/")
    for pattern in policy.get("exclude_dirs", []):
        if any(fnmatch.fnmatch(part, str(pattern)) for part in parts):
            return True
    for pattern in policy.get("exclude_paths", []):
        if fnmatch.fnmatch(relative_path, str(pattern)):
            return True
    return False


def is_managed_document(relative_path: str, policy: Mapping[str, Any]) -> bool:
    normalized = normalize_relative_path(relative_path)
    if _matches_excluded(normalized, policy):
        return False
    roots = [normalize_relative_path(str(item)) for item in policy["managed_roots"]]
    suffix = Path(normalized).suffix.lower()
    if suffix not in {str(item).lower() for item in policy["managed_extensions"]}:
        return False
    return any(normalized == root or normalized.startswith(root + "/") for root in roots)


def scan_secret_path(relative_path: str, policy: Mapping[str, Any]) -> bool:
    normalized = normalize_relative_path(relative_path)
    patterns = [str(item).lower() for item in policy.get("secret_path_patterns", [])]
    for part in normalized.lower().split("/"):
        if part in patterns:
            return True
        if any(part.startswith(pattern + ".") for pattern in patterns if pattern.startswith(".env")):
            return True
    return False


def scan_secret_content(text: str, policy: Mapping[str, Any]) -> bool:
    for raw_pattern in policy.get("secret_content_patterns", []):
        try:
            if re.search(str(raw_pattern), text):
                return True
        except re.error as exc:
            raise PolicyViolation("POLICY_SECRET_PATTERN_INVALID") from exc
    return False


def assert_safe_document(root: Path, relative_path: str, policy: Mapping[str, Any]) -> tuple[Path, bytes, str]:
    normalized = normalize_relative_path(relative_path)
    if scan_secret_path(normalized, policy):
        raise SecretDetected("SECRET_PATH")
    target = ensure_repo_path(root, normalized)
    try:
        data = target.read_bytes()
    except (OSError, ValueError) as exc:
        raise PolicyViolation("FILE_READ_FAILED") from exc
    max_bytes = int(policy.get("max_file_bytes", 0))
    if max_bytes <= 0 or len(data) > max_bytes:
        raise PolicyViolation("FILE_SIZE_LIMIT")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyViolation("UTF8_REQUIRED") from exc
    if scan_secret_content(text, policy):
        raise SecretDetected("SECRET_CONTENT")
    return target, data, text


def discover_managed_paths(root: Path, policy: Mapping[str, Any]) -> list[str]:
    root_resolved = root.resolve()
    candidates: list[str] = []
    for raw_root in policy["managed_roots"]:
        root_value = normalize_relative_path(str(raw_root))
        root_path = ensure_repo_path(root_resolved, root_value)
        if root_path.is_file():
            relative = root_value
            if scan_secret_path(relative, policy):
                raise SecretDetected("SECRET_PATH")
            if is_managed_document(relative, policy):
                candidates.append(relative)
            continue
        if not root_path.exists():
            continue
        for current, dirs, files in os.walk(root_path, topdown=True, followlinks=False):
            current_path = Path(current)
            dirs[:] = [name for name in dirs if not _matches_excluded(name, policy)]
            for name in sorted(files):
                absolute = current_path / name
                try:
                    relative = absolute.resolve().relative_to(root_resolved).as_posix()
                except ValueError as exc:
                    raise PolicyViolation("PATH_OUTSIDE_REPOSITORY") from exc
                if scan_secret_path(relative, policy):
                    raise SecretDetected("SECRET_PATH")
                if is_managed_document(relative, policy):
                    candidates.append(relative)
    return sorted(set(candidates))


def stable_id(prefix: str, key: str) -> str:
    return f"{prefix}-{uuid.uuid5(_UUID_NAMESPACE, key)}"


def _clean_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def extract_headings(text: str, suffix: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    if suffix.lower() == ".md":
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = _MD_HEADING_RE.match(line)
            if match:
                headings.append({"level": len(match.group(1)), "text": match.group(2).strip(), "line": line_number})
    else:
        for match in _HTML_HEADING_RE.finditer(text):
            headings.append(
                {
                    "level": int(match.group(1)),
                    "text": _clean_markup(match.group(2)),
                    "line": _line_number(text, match.start()),
                }
            )
    return headings


def extract_title(text: str, suffix: str, headings: list[dict[str, Any]]) -> str:
    if suffix.lower() == ".html":
        title_match = _HTML_TITLE_RE.search(text)
        if title_match:
            return _clean_markup(title_match.group(1))[:500]
    for heading in headings:
        if heading["level"] == 1:
            return str(heading["text"])[:500]
    return ""


def extract_local_links(text: str, relative_path: str, root: Path, policy: Mapping[str, Any]) -> list[str]:
    raw_links = [match.group(1).strip().strip("<>") for match in _MD_LINK_RE.finditer(text)]
    raw_links.extend(match.group(2).strip() for match in _HTML_HREF_RE.finditer(text))
    links: list[str] = []
    parent = posixpath.dirname(relative_path)
    for raw in raw_links:
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc or raw.startswith(("#", "//")):
            continue
        path_part = unquote(parsed.path)
        if not path_part:
            continue
        candidate = posixpath.normpath(posixpath.join(parent, path_part.replace("\\", "/")))
        if candidate == "." or candidate == ".." or candidate.startswith("../"):
            continue
        try:
            normalized = normalize_relative_path(candidate)
        except PolicyViolation:
            continue
        if scan_secret_path(normalized, policy):
            continue
        try:
            ensure_repo_path(root, normalized)
        except PolicyViolation:
            continue
        if normalized not in links:
            links.append(normalized)
    return sorted(links)


def extract_trace_ids(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for match in _TRACE_ID_RE.finditer(text):
        value = match.group(0)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def extract_summary(text: str, suffix: str) -> str:
    for raw_line in text.splitlines():
        line = _clean_markup(raw_line).strip()
        if not line or line.startswith("#") or line.startswith("```"):
            continue
        if suffix.lower() == ".html" and line.lower() in {"html", "body", "main"}:
            continue
        return line[:2000]
    return ""

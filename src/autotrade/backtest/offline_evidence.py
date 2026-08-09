"""Observed offline preflight/postflight evidence for the local Backtest Core."""

from __future__ import annotations

import ast
import hashlib
import os
import re
import socket
import stat
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_URL_RE = re.compile(r"(?:https?|wss?)://", re.IGNORECASE)
_SECRET_RE = re.compile(
    r"(?:api[_-]?key|secret(?:[_-]?key)?|password|access[_-]?token|private[_-]?key)\s*[:=]",
    re.IGNORECASE,
)
_FORBIDDEN_IMPORT_ROOTS = {"broker", "cloud", "databento", "lean", "nautilus", "quantconnect"}
_OBSERVED_FIELDS = {"filesystem_observed", "network_guard_observed", "root_observed"}
_REQUIRED_FIELDS = {
    "schema_version",
    "allowed_input_root",
    "input_sha256s",
    "output_sha256s",
    "dependency_sha256s",
    "forbidden_import_count",
    "secret_scan_count",
    "outbound_attempts",
    "broker_cloud_url_count",
    "observation_id",
}


def _failure(reason: str) -> dict[str, str]:
    return {"status": "STOPPED", "reason": reason}


def _safe_root(value: object) -> Path | None:
    if not isinstance(value, (str, os.PathLike)):
        return None
    raw = os.fspath(value)
    if not isinstance(raw, str) or not raw or raw.startswith(("\\\\", "//")):
        return None
    path = Path(raw)
    if not path.is_absolute() or not path.exists() or not path.is_dir():
        return None
    if path.is_symlink() or _is_reparse(path):
        return None
    return path.resolve()


def _is_reparse(path: Path) -> bool:
    try:
        attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & 0x400)


def _safe_file(value: object, root: Path) -> Path | None:
    if not isinstance(value, (str, os.PathLike)):
        return None
    path = Path(value)
    if not path.is_absolute() or path.is_symlink() or _is_reparse(path):
        return None
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    if not resolved.is_file() or stat.S_ISLNK(resolved.stat().st_mode):
        return None
    return resolved


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _files_for_scan(values: Iterable[Path], root: Path) -> tuple[Path, ...] | None:
    found: set[Path] = set()
    for value in values:
        safe = _safe_file(value, root)
        if safe is not None:
            found.add(safe)
            continue
        path = Path(value)
        if not path.is_absolute() or path.is_symlink() or _is_reparse(path):
            return None
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            return None
        if not resolved.is_dir():
            return None
        for child in resolved.rglob("*"):
            if child.is_file() and not child.is_symlink() and not _is_reparse(child):
                found.add(child.resolve())
    return tuple(sorted(found, key=str))


def _scan_files(paths: Sequence[Path]) -> tuple[int, int, int]:
    forbidden_import_count = 0
    secret_scan_count = 0
    broker_cloud_url_count = 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _URL_RE.search(text) and any(token in text.lower() for token in ("broker", "cloud")):
            broker_cloud_url_count += 1
        secret_scan_count += len(_SECRET_RE.findall(text))
        if path.suffix.lower() != ".py":
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            forbidden_import_count += 1
            continue
        for node in ast.walk(tree):
            imported = None
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".", 1)[0].lower() for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = [node.module.split(".", 1)[0].lower()]
            if imported:
                forbidden_import_count += sum(name in _FORBIDDEN_IMPORT_ROOTS for name in imported)
    return forbidden_import_count, secret_scan_count, broker_cloud_url_count


class OfflineNetworkGuard:
    """In-process outbound guard used while observed evidence is collected."""

    def __init__(self) -> None:
        self.attempts = 0
        self.observed = False
        self._originals: dict[tuple[object, str], object] = {}

    def _deny(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        self.attempts += 1
        raise RuntimeError("offline evidence forbids outbound network access")

    def __enter__(self) -> OfflineNetworkGuard:
        self.observed = True
        patches = (
            (socket, "create_connection"),
            (socket, "getaddrinfo"),
            (socket.socket, "connect"),
            (socket.socket, "connect_ex"),
            (socket.socket, "sendto"),
        )
        for target, name in patches:
            self._originals[(target, name)] = getattr(target, name)
            setattr(target, name, self._deny)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        for (target, name), original in self._originals.items():
            setattr(target, name, original)
        self._originals.clear()


def collect_offline_evidence(
    *,
    input_root: Path,
    input_paths: Sequence[Path],
    output_paths: Sequence[Path],
    dependency_paths: Sequence[Path],
    scan_paths: Sequence[Path],
    observation_id: str,
    network_guard: OfflineNetworkGuard | None = None,
) -> dict[str, Any]:
    """Hash actual local files and scan actual source files before PASS is possible."""

    root = _safe_root(input_root)
    if root is None or type(observation_id) is not str or not observation_id:
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    guard = network_guard or OfflineNetworkGuard()
    with guard:
        input_files = tuple(_safe_file(path, root) for path in input_paths)
        output_files = tuple(_safe_file(path, root) for path in output_paths)
        dependency_files = tuple(_safe_file(path, root) for path in dependency_paths)
        if any(path is None for path in (*input_files, *output_files, *dependency_files)):
            return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
        scan_files = _files_for_scan(scan_paths, root)
        if scan_files is None:
            return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
        forbidden, secrets, urls = _scan_files(scan_files)
    return {
        "schema_version": "p3-offline-evidence-v1",
        "allowed_input_root": str(root),
        "input_sha256s": tuple(_sha256_file(path) for path in input_files if path is not None),
        "output_sha256s": tuple(_sha256_file(path) for path in output_files if path is not None),
        "dependency_sha256s": tuple(_sha256_file(path) for path in dependency_files if path is not None),
        "forbidden_import_count": forbidden,
        "secret_scan_count": secrets,
        "outbound_attempts": guard.attempts,
        "broker_cloud_url_count": urls,
        "observation_id": observation_id,
        "filesystem_observed": True,
        "network_guard_observed": guard.observed,
        "root_observed": True,
    }


def _valid_hash_sequence(value: object) -> bool:
    return (
        isinstance(value, (tuple, list))
        and bool(value)
        and all(type(item) is str and _HASH_RE.fullmatch(item) for item in value)
    )


def validate_offline_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _REQUIRED_FIELDS | _OBSERVED_FIELDS:
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    root = _safe_root(value.get("allowed_input_root"))
    if root is None:
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    if not _valid_hash_sequence(value.get("input_sha256s")) or not _valid_hash_sequence(value.get("output_sha256s")):
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    if not _valid_hash_sequence(value.get("dependency_sha256s")):
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    counts = ("forbidden_import_count", "secret_scan_count", "outbound_attempts", "broker_cloud_url_count")
    if any(type(value.get(key)) is not int or value[key] < 0 for key in counts):
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    if type(value.get("observation_id")) is not str or not value["observation_id"]:
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    if any(type(value.get(key)) is not bool or not value[key] for key in _OBSERVED_FIELDS):
        return _failure("OFFLINE_PREFLIGHT_UNPROVEN")
    if value["forbidden_import_count"] or value["secret_scan_count"] or value["broker_cloud_url_count"]:
        return _failure("OFFLINE_POLICY_VIOLATION")
    if value["outbound_attempts"]:
        return _failure("OFFLINE_POLICY_VIOLATION")
    return {"status": "PASS", "evidence": dict(value)}


def build_offline_preflight(**kwargs: Any) -> dict[str, Any]:
    return collect_offline_evidence(**kwargs)


def build_offline_postflight(**kwargs: Any) -> dict[str, Any]:
    return collect_offline_evidence(**kwargs)


__all__ = [
    "OfflineNetworkGuard",
    "build_offline_postflight",
    "build_offline_preflight",
    "collect_offline_evidence",
    "validate_offline_evidence",
]

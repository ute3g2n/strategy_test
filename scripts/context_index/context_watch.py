from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .check_context_gate import (
    DEFAULT_H1_RECEIPT,
    GateError,
    _assert_no_reparse,
    _inside_root,
    _write_json_atomic,
    capture_worktree_snapshot,
    is_generated_path,
    require_h1_approval,
    sha256_bytes,
)
from .common import load_policy

RUNTIME_DIR = Path("plan/context_index/runtime")
PENDING_PATH = RUNTIME_DIR / "context_watch_pending.json"
SNAPSHOT_PATH = RUNTIME_DIR / "context_watch_snapshot.json"
LOCK_PATH = RUNTIME_DIR / "context_watch.lock"
EVENT_LOG_PATH = RUNTIME_DIR / "context_watch_events.jsonl"
LOCK_SCHEMA_VERSION = "ctxmap-watch-lock-v0.2"


def _runtime_path(root: Path, relative: Path) -> Path:
    return _inside_root(root, relative)


def _write_pending(root: Path, status: str, reason_code: str, paths: list[str]) -> None:
    _write_json_atomic(
        _runtime_path(root, PENDING_PATH),
        {
            "schema_version": "ctxmap-watch-pending-v0.1",
            "status": status,
            "reason_code": reason_code,
            "paths": sorted(set(paths))[:100],
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    )


def _append_event(root: Path, event: dict[str, Any]) -> None:
    target = _runtime_path(root, EVENT_LOG_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _root_fingerprint(root: Path) -> str:
    return sha256_bytes(str(root.resolve()).encode("utf-8"))


def _process_start_marker(pid: int) -> str | None:
    """Return an OS process-start identity to protect against PID reuse."""

    if pid <= 0:
        return None
    if os.name == "nt":
        try:
            from ctypes import wintypes

            class _FileTime(ctypes.Structure):
                _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            open_process = kernel32.OpenProcess
            open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            open_process.restype = wintypes.HANDLE
            get_process_times = kernel32.GetProcessTimes
            get_process_times.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(_FileTime),
                ctypes.POINTER(_FileTime),
                ctypes.POINTER(_FileTime),
                ctypes.POINTER(_FileTime),
            ]
            get_process_times.restype = wintypes.BOOL
            close_handle = kernel32.CloseHandle
            close_handle.argtypes = [wintypes.HANDLE]
            close_handle.restype = wintypes.BOOL
            handle = open_process(0x1000, False, pid)
            if not handle:
                return None
            try:
                creation = _FileTime()
                exit_time = _FileTime()
                kernel_time = _FileTime()
                user_time = _FileTime()
                if not get_process_times(
                    handle,
                    ctypes.byref(creation),
                    ctypes.byref(exit_time),
                    ctypes.byref(kernel_time),
                    ctypes.byref(user_time),
                ):
                    return None
                value = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
                return str(value)
            finally:
                close_handle(handle)
        except (AttributeError, OSError, TypeError, ValueError):
            return None
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        closing_parenthesis = stat.rfind(")")
        fields = stat[closing_parenthesis + 2 :].split()
        return fields[19] if len(fields) > 19 else None
    except (OSError, UnicodeError, ValueError):
        return None


def _lock_metadata(root: Path) -> dict[str, str | int]:
    pid = os.getpid()
    marker = _process_start_marker(pid)
    if marker is None:
        raise GateError("WATCH_PROCESS_IDENTITY_UNAVAILABLE")
    return {
        "schema_version": LOCK_SCHEMA_VERSION,
        "pid": pid,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_fingerprint": _root_fingerprint(root),
        "process_start_marker": marker,
    }


def _load_lock_metadata(root: Path, target: Path) -> dict[str, Any]:
    _assert_no_reparse(root, LOCK_PATH.as_posix())
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError("WATCH_LOCK_INVALID") from exc
    if not isinstance(value, dict):
        raise GateError("WATCH_LOCK_INVALID")
    if value.get("schema_version") != LOCK_SCHEMA_VERSION:
        raise GateError("WATCH_LOCK_INVALID")
    if type(value.get("pid")) is not int or value["pid"] <= 0:
        raise GateError("WATCH_LOCK_INVALID")
    if not isinstance(value.get("started_at"), str) or not value["started_at"]:
        raise GateError("WATCH_LOCK_INVALID")
    if value.get("root_fingerprint") != _root_fingerprint(root):
        raise GateError("WATCH_LOCK_ROOT_MISMATCH")
    if not isinstance(value.get("process_start_marker"), str) or not value["process_start_marker"]:
        raise GateError("WATCH_LOCK_INVALID")
    return value


def _acquire_lock(root: Path) -> Path:
    target = _runtime_path(root, LOCK_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(_lock_metadata(root), ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise GateError("WATCH_ALREADY_RUNNING") from exc
    return target


def recover_stale_lock(root: Path) -> bool:
    """Remove a lock only when its owner identity is demonstrably gone."""

    target = _runtime_path(root, LOCK_PATH)
    if not target.exists():
        return False
    metadata = _load_lock_metadata(root, target)
    pid = int(metadata["pid"])
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        target.unlink(missing_ok=True)
        return True
    except PermissionError as exc:
        raise GateError("WATCH_LOCK_OWNER_UNKNOWN") from exc
    except OSError as exc:
        raise GateError("WATCH_LOCK_OWNER_UNKNOWN") from exc
    current_marker = _process_start_marker(pid)
    if current_marker is None or current_marker != metadata["process_start_marker"]:
        raise GateError("WATCH_LOCK_OWNER_UNKNOWN")
    raise GateError("WATCH_LOCK_ACTIVE")


def _changed_since(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    old = before.get("paths", {})
    new = after.get("paths", {})
    if not isinstance(old, dict) or not isinstance(new, dict):
        return []
    result = [
        path
        for path in sorted(set(old) | set(new))
        if old.get(path) != new.get(path) and not is_generated_path(path)
    ]
    return result


def _python_executable() -> str:
    return os.environ.get("CTXMAP_PYTHON", sys.executable)


def _run_gate(root: Path, paths: list[str], args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    event_path = _runtime_path(root, RUNTIME_DIR / "current_event_paths.txt")
    event_path.write_text("\n".join(paths) + "\n", encoding="utf-8", newline="\n")
    report_path = _runtime_path(root, RUNTIME_DIR / "context_gate_report.json")
    command = [
        _python_executable(),
        "-m",
        "scripts.context_index.check_context_gate",
        "--root",
        str(root),
        "--changed-list",
        str(RUNTIME_DIR / "current_event_paths.txt"),
        "--report",
        str(report_path),
        "--require-h1",
        "--h1-receipt",
        str(args.h1_receipt),
    ]
    if args.a07_responses:
        command.extend(["--a07-responses", str(args.a07_responses)])
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        report = {"status": "BLOCKED", "reason_code": "GATE_REPORT_UNAVAILABLE"}
    return completed.returncode, report


def _run_auto_commit(root: Path, args: argparse.Namespace) -> int:
    allowlist = _runtime_path(root, RUNTIME_DIR / "gate_allowlist.txt")
    report_path = _runtime_path(root, RUNTIME_DIR / "context_gate_report.json")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        allowed = report.get("allowed_paths", [])
        if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
            return 1
        allowlist.write_text("\n".join(allowed) + "\n", encoding="utf-8", newline="\n")
    except (OSError, UnicodeError, json.JSONDecodeError):
        return 1
    script = root / "auto-commit.cmd"
    if not script.exists():
        script = root / "auto-commit.sh"
    if not script.exists():
        return 1
    command = [str(script), "--allowlist-file", RUNTIME_DIR.joinpath("gate_allowlist.txt").as_posix(), "--watch-mode"]
    if args.no_commit:
        command.append("--no-commit")
    if args.no_push:
        command.append("--no-push")
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    return completed.returncode


def process_event(root: Path, paths: list[str], args: argparse.Namespace) -> int:
    safe_paths = sorted({path for path in paths if not is_generated_path(path)})
    if not safe_paths:
        return 0
    _write_pending(root, "PENDING", "EVENT_RECEIVED", safe_paths)
    _append_event(root, {"status": "PENDING", "paths": safe_paths})
    gate_status, report = _run_gate(root, safe_paths, args)
    if gate_status != 0 or report.get("status") != "PASS":
        reason = str(report.get("reason_code", "GATE_FAILED"))
        _write_pending(root, "BLOCKED", reason, safe_paths)
        _append_event(root, {"status": "BLOCKED", "reason_code": reason, "paths": safe_paths})
        return 1
    if _run_auto_commit(root, args) != 0:
        _write_pending(root, "BLOCKED", "AUTO_COMMIT_FAILED", safe_paths)
        _append_event(root, {"status": "BLOCKED", "reason_code": "AUTO_COMMIT_FAILED", "paths": safe_paths})
        return 1
    _write_pending(root, "PASS", "GATE_AND_COMMIT_PASS", safe_paths)
    _append_event(root, {"status": "PASS", "reason_code": "GATE_AND_COMMIT_PASS", "paths": safe_paths})
    return 0


def watch_loop(root: Path, args: argparse.Namespace) -> int:
    policy = load_policy(_inside_root(root, args.policy))
    lock = _acquire_lock(root)
    try:
        before = capture_worktree_snapshot(root, policy)
        _write_json_atomic(_runtime_path(root, SNAPSHOT_PATH), before)
        pending: set[str] = set()
        last_event_at = 0.0
        cycles = 0
        while args.max_cycles <= 0 or cycles < args.max_cycles:
            time.sleep(max(0.05, float(args.poll_interval)))
            cycles += 1
            after = capture_worktree_snapshot(root, policy)
            events = _changed_since(before, after)
            if events:
                pending.update(events)
                last_event_at = time.monotonic()
            if pending and time.monotonic() - last_event_at >= max(0.0, float(args.debounce)):
                event_paths = sorted(pending)
                pending.clear()
                if process_event(root, event_paths, args) != 0:
                    return 1
                before = after
                _write_json_atomic(_runtime_path(root, SNAPSHOT_PATH), before)
            else:
                before = after
    finally:
        lock.unlink(missing_ok=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H1-gated local context change watcher.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("context/context_policy.json"))
    parser.add_argument("--h1-receipt", type=Path, default=Path(DEFAULT_H1_RECEIPT))
    parser.add_argument("--check-start", action="store_true")
    parser.add_argument("--watch-commit", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--changed", action="append", default=[])
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--debounce", type=float, default=3.0)
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--a07-responses", type=Path)
    parser.add_argument("--no-commit", action="store_true")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--recover-stale-lock", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.recover_stale_lock:
        try:
            recovered = recover_stale_lock(root)
        except GateError as exc:
            print(f"WATCH_LOCK_RECOVERY_REJECTED: {exc}")
            return 1
        print("WATCH_LOCK_RECOVERED" if recovered else "WATCH_LOCK_NOT_PRESENT")
        return 0
    try:
        require_h1_approval(root, args.h1_receipt)
    except GateError as exc:
        if args.check_start or args.watch_commit or args.once:
            print(f"WATCH_START_REJECTED: {exc}")
            return 1
        raise
    if args.check_start:
        print("WATCH_START_ALLOWED")
        return 0
    if args.once:
        return process_event(root, args.changed, args) if args.changed else 0
    if args.watch_commit:
        return watch_loop(root, args)
    parser.error("one of --check-start, --watch-commit, or --once is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

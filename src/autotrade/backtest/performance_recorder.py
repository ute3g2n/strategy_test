"""Measured performance evidence with deterministic two-run result hashes."""

from __future__ import annotations

import importlib
import os
import platform
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import canonical_hash

_HASH_PREFIX = "sha256:"
_HASH_LENGTH = len(_HASH_PREFIX) + 64
_FULL_REQUIRED = {
    "generator_version",
    "schema_version",
    "seed",
    "input_sha256",
    "derived_bar_sha256s",
    "manifest_sha256",
    "host_cpu",
    "host_ram_bytes",
    "host_os",
    "python_version",
    "measurement_tool",
    "measurement_tool_version",
    "measurement_unit",
    "elapsed_ms",
    "peak_rss_bytes",
    "first_result_sha256",
    "second_result_sha256",
    "observation_id",
    "measurement_observed",
    "host_observed",
}


@dataclass(frozen=True)
class PerformanceEvidence:
    """Legacy compact evidence DTO retained for callers of ``record``."""

    elapsed_ms: int
    peak_rss_bytes: int
    event_count: int
    input_sha256: str
    result_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _valid_hash(value: object, *, reject_zero: bool = False) -> bool:
    if type(value) is not str or not value.startswith(_HASH_PREFIX) or len(value) != _HASH_LENGTH:
        return False
    digest = value[len(_HASH_PREFIX) :]
    if any(character not in "0123456789abcdef" for character in digest):
        return False
    return not reject_zero or digest != "0" * 64


def validate_performance_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate evidence from an actual measurement, not a caller assertion."""

    if not isinstance(value, Mapping) or set(value) != _FULL_REQUIRED | {"storage_kind", "formal_threshold_status"}:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    if type(value["seed"]) is not int or value["seed"] < 0:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if not _valid_hash(value["input_sha256"], reject_zero=True) or not _valid_hash(
        value["manifest_sha256"], reject_zero=True
    ):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    derived = value["derived_bar_sha256s"]
    if (
        not isinstance(derived, (tuple, list))
        or not derived
        or not all(_valid_hash(item, reject_zero=True) for item in derived)
    ):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if not _valid_hash(value["first_result_sha256"], reject_zero=True) or not _valid_hash(
        value["second_result_sha256"], reject_zero=True
    ):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if value["first_result_sha256"] != value["second_result_sha256"]:
        return {"status": "STOPPED", "reason": "PERFORMANCE_RESULT_MISMATCH"}
    if any(
        type(value[key]) is not str or not value[key]
        for key in (
            "generator_version",
            "schema_version",
            "host_cpu",
            "host_os",
            "python_version",
            "measurement_tool",
            "measurement_tool_version",
            "measurement_unit",
            "observation_id",
            "storage_kind",
        )
    ):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    if type(value["host_ram_bytes"]) is not int or value["host_ram_bytes"] <= 0:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    if type(value["elapsed_ms"]) is not int or value["elapsed_ms"] < 0:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if type(value["peak_rss_bytes"]) is not int or value["peak_rss_bytes"] <= 0:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    if value["measurement_unit"] != "ms/bytes" or value["formal_threshold_status"] != "NOT_ASSESSED":
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if type(value["measurement_observed"]) is not bool or not value["measurement_observed"]:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    if type(value["host_observed"]) is not bool or not value["host_observed"]:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    return {"status": "PASS", "evidence": dict(value)}


def _peak_rss_bytes() -> tuple[int, str, str] | None:
    """Return current process RSS using an OS measurement API and its unit."""

    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class _Counters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = _Counters()
            counters.cb = ctypes.sizeof(_Counters)
            win_dll = getattr(ctypes, "WinDLL", None)
            if not callable(win_dll):
                return None
            process_api = win_dll("kernel32")
            memory_api = win_dll("psapi")
            get_process = process_api.GetCurrentProcess
            get_process.restype = wintypes.HANDLE
            get_memory = memory_api.GetProcessMemoryInfo
            get_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Counters), wintypes.DWORD]
            get_memory.restype = wintypes.BOOL
            if get_memory(get_process(), ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize), "GetProcessMemoryInfo", platform.version()
        except (AttributeError, OSError, TypeError):
            return None
        return None
    try:
        resource_module: Any = importlib.import_module("resource")
        value = int(resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss)
        if sys.platform != "darwin":
            value *= 1024
        return value, "resource.getrusage", platform.python_version()
    except (ImportError, OSError, ValueError):
        return None


def measure_performance_run(
    input_value: Mapping[str, Any], run_callable: Callable[[Mapping[str, Any]], Any]
) -> dict[str, Any]:
    """Execute the same deterministic input twice and record real observations."""

    if not isinstance(input_value, Mapping) or not callable(run_callable):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    required = ("generator_version", "schema_version", "seed", "input_sha256", "derived_bar_sha256s", "manifest_sha256")
    if any(key not in input_value for key in required):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    rss_before = _peak_rss_bytes()
    start = time.monotonic_ns()
    try:
        first = run_callable(input_value)
        second = run_callable(input_value)
    except Exception:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    elapsed_ms = max(0, (time.monotonic_ns() - start) // 1_000_000)
    rss_after = _peak_rss_bytes()
    if rss_before is None or rss_after is None:
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_UNPROVEN"}
    first_hash = canonical_hash(first)
    second_hash = canonical_hash(second)
    host_cpu = platform.processor() or platform.machine() or "unknown"
    host_ram = _host_ram_bytes()
    tool = rss_after[1]
    tool_version = rss_after[2]
    evidence = {
        "generator_version": input_value["generator_version"],
        "schema_version": "p3-performance-evidence-v1",
        "seed": input_value["seed"],
        "input_sha256": input_value["input_sha256"],
        "derived_bar_sha256s": tuple(input_value["derived_bar_sha256s"]),
        "manifest_sha256": input_value["manifest_sha256"],
        "host_cpu": host_cpu,
        "host_ram_bytes": host_ram,
        "host_os": platform.platform(),
        "python_version": platform.python_version(),
        "measurement_tool": tool,
        "measurement_tool_version": tool_version,
        "measurement_unit": "ms/bytes",
        "elapsed_ms": elapsed_ms,
        "peak_rss_bytes": max(rss_before[0], rss_after[0]),
        "first_result_sha256": first_hash,
        "second_result_sha256": second_hash,
        "observation_id": "OBS-P3-BT-REPAIR-004",
        "storage_kind": "LOCAL_TEMP_ONLY",
        "measurement_observed": True,
        "host_observed": host_ram > 0 and host_cpu != "unknown",
        "formal_threshold_status": "NOT_ASSESSED",
    }
    result = validate_performance_evidence(evidence)
    if result["status"] != "PASS":
        return result
    return {"status": "PASS", **evidence}


def _host_ram_bytes() -> int:
    if os.name == "nt":
        try:
            import ctypes

            class _MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_uint32),
                    ("memory_load", ctypes.c_uint32),
                    ("total", ctypes.c_uint64),
                    ("available", ctypes.c_uint64),
                    ("page_total", ctypes.c_uint64),
                    ("page_available", ctypes.c_uint64),
                    ("virtual_total", ctypes.c_uint64),
                    ("virtual_available", ctypes.c_uint64),
                    ("extended", ctypes.c_uint64),
                ]

            status = _MemoryStatus()
            status.length = ctypes.sizeof(_MemoryStatus)
            windll = getattr(ctypes, "windll", None)
            kernel32 = getattr(windll, "kernel32", None)
            global_memory_status_ex = getattr(kernel32, "GlobalMemoryStatusEx", None)
            if callable(global_memory_status_ex) and global_memory_status_ex(ctypes.byref(status)):
                return int(status.total)
        except (AttributeError, OSError, TypeError):
            return 0
    try:
        os_module: Any = os
        return int(os_module.sysconf("SC_PHYS_PAGES") * os_module.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError):
        return 0


def record(input_value: Mapping[str, Any]) -> dict[str, Any]:
    """Legacy compact recorder; full evidence uses ``validate_performance_evidence``."""

    required = ("elapsed_ms", "peak_rss_bytes", "event_count", "input_sha256", "result_sha256")
    if not all(key in input_value for key in required):
        return {"status": "NOT_EXECUTED", "evidence_required": True}
    numeric = ("elapsed_ms", "peak_rss_bytes", "event_count")
    if any(type(input_value[key]) is not int or input_value[key] < 0 for key in numeric):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    if any(not _valid_hash(input_value[key]) for key in ("input_sha256", "result_sha256")):
        return {"status": "STOPPED", "reason": "PERFORMANCE_EVIDENCE_INVALID"}
    return {"status": "PASS", "evidence_required": True, **{key: input_value[key] for key in required}}


__all__ = ["PerformanceEvidence", "measure_performance_run", "record", "validate_performance_evidence"]

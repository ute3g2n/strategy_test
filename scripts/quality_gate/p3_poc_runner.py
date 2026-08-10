"""P3-09 local LEAN execution, adapter normalization, and evidence writer."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from autotrade.backtest.contracts import canonical_hash
from autotrade.market_data.store_contracts import MarketEvent
from autotrade.strategy.contracts import StrategyConfig
from engine_poc.entrypoint import (  # type: ignore[import-not-found]
    CONTRACT_RELATIVE_PATH,
    POC_RUN_ID,
    ContractError,
    load_input_contract,
    sha256_file,
    validate_execution_manifest,
    validate_lean_output,
)

CORE_RUN_ID = "RUN-P3-POC-READY-001-CORE-001"

RUN_MANIFEST_RELATIVE = Path("tests/evidence/phase3/RUN-P3-POC-001/run-manifest.json")
READY_MANIFEST_RELATIVE = Path("tests/evidence/phase3/RUN-P3-POC-READY-001/run-manifest.json")
READY_EXPECTED_ROOT = Path("tests/evidence/phase3/RUN-P3-POC-READY-001/expected")
RUN_EVIDENCE_RELATIVE = Path("tests/evidence/phase3/RUN-P3-POC-001")
FIXTURE_RELATIVE = Path("tests/fixtures/phase3/m30_backtest_v2.json")
PROJECTION_RELATIVE = Path("tests/fixtures/phase3/p3_09_lean_input_v1.csv")
LEAN_CONFIG_RELATIVE = Path("tests/engine_poc/lean_project/p3-09-config.json")
LEAN_ALGORITHM_RELATIVE = Path("tests/engine_poc/lean_algorithm.py")
ADAPTER_RELATIVE = Path("scripts/quality_gate/p3_poc_runner.py")
P3_08A_VERIFICATION_RELATIVE = Path("tests/evidence/phase3/RUN-P3-LEAN-PREP-001/verification.json")
TRUSTED_SCOPE_RELATIVE = Path("scripts/quality_gate/trusted_scopes.json")
APPROVAL_RELATIVE = RUN_EVIDENCE_RELATIVE / "human-gate-user-declaration.md"
FIXED_CORE_CODE_REVISION = "99261c1eb766b4b5972ef0e2f97d0bfe32466e94"
FIXED_LEAN_IMAGE = "quantconnect/lean@sha256:bc01b22a27262ff1e69bdd7f451234e565463292350626aaa2479bda7a54765d"
FIXED_SOURCE_MANIFEST_SHA256 = "sha256:8ff33516cb843a2b205346a6cb9bbe933a5aa30f7c0bad0edd21538a531446a8"
ZERO_HASH = "sha256:" + "0" * 64
_REQUIRED_OBSERVED_FIELDS = {
    "event_id",
    "event_time_utc",
    "bar_close_time_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
}


class RunContractError(ValueError):
    """Raised when a P3-09 binding is incomplete or changed."""


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RunContractError(f"{label} must be an object")
    return dict(value)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RunContractError(f"cannot read {label}") from error
    return _mapping(value, label)


def _required_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        raise RunContractError(f"{label} must be sha256:<64 hexadecimal characters>")
    if any(char not in "0123456789abcdef" for char in value[7:]):
        raise RunContractError(f"{label} must be lowercase")
    return value


def _repo_file(repo_root: Path, relative: object, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise RunContractError(f"{label} is missing")
    candidate = Path(relative.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise RunContractError(f"{label} must be a safe repository-relative path")
    path = repo_root / candidate
    if path.is_symlink() or not path.is_file():
        raise RunContractError(f"{label} does not exist: {candidate.as_posix()}")
    resolved = path.resolve()
    root = repo_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise RunContractError(f"{label} escapes the repository")
    return resolved


def _utc(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise RunContractError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RunContractError(f"{label} must be a valid UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise RunContractError(f"{label} must be UTC")
    return parsed.astimezone(UTC)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_p3_09_run_manifest(manifest: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    """Validate the P3-09 run binding and the user-approved execution boundary."""

    value = _mapping(manifest, "P3-09 run manifest")
    if value.get("schema_version") != "p3-09-run-manifest/v1":
        raise RunContractError("P3-09 run manifest schema_version is not fixed")
    if value.get("run_id") != POC_RUN_ID or value.get("phase_id") != "phase3" or value.get("step_id") != "P3-09":
        raise RunContractError("P3-09 run binding is invalid")

    source_path = _repo_file(repo_root, value.get("source_execution_manifest"), "source execution manifest")
    if source_path.relative_to(repo_root.resolve()) != READY_MANIFEST_RELATIVE:
        raise RunContractError("source execution manifest path is not the P3-08R fixed path")
    source_hash = _required_hash(value.get("source_execution_manifest_sha256"), "source_execution_manifest_sha256")
    if source_hash != FIXED_SOURCE_MANIFEST_SHA256 or sha256_file(source_path) != source_hash:
        raise RunContractError("P3-08R execution manifest hash mismatch")

    contract_path = repo_root / CONTRACT_RELATIVE_PATH
    contract, _ = load_input_contract(contract_path, repo_root)
    source_manifest = _read_json(source_path, "P3-08R execution manifest")
    validate_execution_manifest(
        source_manifest,
        contract,
        repo_root,
        contract_path=contract_path,
        require_expected_files=True,
    )

    p3_08a = _read_json(repo_root / P3_08A_VERIFICATION_RELATIVE, "P3-08A verification")
    if p3_08a.get("final_status") != "PASS" or p3_08a.get("state") != "PASS":
        raise RunContractError("P3-08A final verification is not PASS")

    projection = _mapping(value.get("input_projection"), "input_projection")
    projection_path = _repo_file(repo_root, projection.get("path"), "LEAN projection")
    if projection_path.relative_to(repo_root.resolve()) != PROJECTION_RELATIVE:
        raise RunContractError("LEAN projection path is not fixed")
    projection_hash = _required_hash(projection.get("sha256"), "input_projection.sha256")
    if sha256_file(projection_path) != projection_hash:
        raise RunContractError("LEAN projection hash mismatch")
    source_fixture = _repo_file(repo_root, projection.get("source_fixture_path"), "projection source fixture")
    source_fixture_hash = _required_hash(projection.get("source_fixture_sha256"), "source fixture sha256")
    if (
        source_fixture.relative_to(repo_root.resolve()) != FIXTURE_RELATIVE
        or sha256_file(source_fixture) != source_fixture_hash
    ):
        raise RunContractError("projection source fixture binding mismatch")

    project = _mapping(value.get("lean_project"), "lean_project")
    config_path = _repo_file(repo_root, project.get("config_path"), "LEAN config")
    algorithm_path = _repo_file(repo_root, project.get("algorithm_path"), "LEAN algorithm")
    for path, key in ((config_path, "config_sha256"), (algorithm_path, "algorithm_sha256")):
        expected_hash_value = _required_hash(project.get(key), f"lean_project.{key}")
        if sha256_file(path) != expected_hash_value:
            raise RunContractError(f"LEAN project hash mismatch: {path.name}")
    if config_path.relative_to(repo_root.resolve()) != LEAN_CONFIG_RELATIVE:
        raise RunContractError("LEAN config path is not fixed")
    if algorithm_path.relative_to(repo_root.resolve()) != LEAN_ALGORITHM_RELATIVE:
        raise RunContractError("LEAN algorithm path is not fixed")

    execution = _mapping(value.get("execution"), "execution")
    exact_execution = {
        "network_mode": "none",
        "data_provider": "Local",
        "automatic_data_download": False,
        "cloud": "NOT_USED",
        "broker": "NOT_USED",
        "secret": "NOT_USED",
        "readonly_inputs": True,
        "write_root": RUN_EVIDENCE_RELATIVE.as_posix(),
        "engine_image": FIXED_LEAN_IMAGE,
    }
    for key, expected in exact_execution.items():
        if execution.get(key) != expected:
            raise RunContractError(f"execution.{key} is not fail-closed")

    expected = _mapping(value.get("expected"), "expected")
    source_expected = _mapping(source_manifest.get("expected"), "source expected")
    expected_keys = (
        "core_reference_path",
        "core_reference_sha256",
        "lean_output_schema_path",
        "lean_output_schema_sha256",
        "parity_map_path",
        "parity_map_sha256",
    )
    for key in expected_keys:
        if expected.get(key) != source_expected.get(key):
            raise RunContractError(f"expected.{key} differs from P3-08R fixed binding")
        if key.endswith("_path"):
            _repo_file(repo_root, expected.get(key), f"expected.{key}")
        else:
            _required_hash(expected.get(key), f"expected.{key}")

    adapter = _mapping(value.get("adapter"), "adapter")
    if adapter.get("name") != "LeanLocalAdapter" or adapter.get("version") != "p3-09-lean-adapter-v1":
        raise RunContractError("adapter identity is not fixed")
    adapter_path = _repo_file(repo_root, adapter.get("path"), "adapter path")
    adapter_hash = _required_hash(adapter.get("artifact_sha256"), "adapter.artifact_sha256")
    if adapter_path.relative_to(repo_root.resolve()) != ADAPTER_RELATIVE or sha256_file(adapter_path) != adapter_hash:
        raise RunContractError("adapter artifact hash mismatch")

    authorization = _mapping(value.get("authorization"), "authorization")
    if authorization.get("execution_allowed") is not True:
        raise RunContractError("P3-09 execution approval is not enabled")
    declaration = _repo_file(repo_root, authorization.get("declaration"), "P3-09 approval declaration")
    if declaration.relative_to(repo_root.resolve()) != APPROVAL_RELATIVE:
        raise RunContractError("P3-09 approval declaration path is not fixed")
    approval_text = declaration.read_text(encoding="utf-8")
    if "USER_APPROVAL_DECLARED=1" not in approval_text or POC_RUN_ID not in approval_text:
        raise RunContractError("P3-09 user approval declaration is incomplete")

    scope_registry = _read_json(repo_root / TRUSTED_SCOPE_RELATIVE, "trusted scope registry")
    scope = _mapping(scope_registry.get("scopes"), "trusted scopes").get(POC_RUN_ID)
    scope_value = _mapping(scope, "P3-09 trusted scope")
    if scope_value.get("execution_allowed") is not True or scope_value.get("unknowns") != []:
        raise RunContractError("P3-09 trusted scope is not execution-enabled")

    manifest_hash = _required_hash(value.get("manifest_sha256"), "manifest_sha256")
    if canonical_hash({key: child for key, child in value.items() if key != "manifest_sha256"}) != manifest_hash:
        raise RunContractError("P3-09 run manifest canonical hash mismatch")
    return value


def validate_observed_bars(observed: Sequence[Mapping[str, Any]]) -> None:
    """Validate the exact ordered 1-minute event shape emitted by LEAN."""

    if len(observed) != 30:
        raise RunContractError("LEAN observed fixture count is not 30")
    previous: datetime | None = None
    for index, row in enumerate(observed):
        if set(row) != _REQUIRED_OBSERVED_FIELDS:
            raise RunContractError("LEAN observed row fields are not vendor-neutral")
        if row.get("event_id") != f"evt-m1-{index:03d}":
            raise RunContractError("LEAN observed event ordering is invalid")
        opened = _utc(row.get("event_time_utc"), f"observed[{index}].event_time_utc")
        closed = _utc(row.get("bar_close_time_utc"), f"observed[{index}].bar_close_time_utc")
        if previous is not None and opened != previous + timedelta(minutes=1):
            raise RunContractError("LEAN observed bars are not ordered")
        if closed != opened + timedelta(minutes=1):
            raise RunContractError("LEAN observed bar close boundary is invalid")
        previous = opened
        for key in ("open", "high", "low", "close", "volume"):
            if not isinstance(row.get(key), str) or not row[key]:
                raise RunContractError(f"observed[{index}].{key} is not a fixed decimal string")


def _observed_events(observed: Sequence[Mapping[str, Any]], fixture: Mapping[str, Any]) -> tuple[MarketEvent, ...]:
    source_ids = fixture.get("source_event_ids")
    source_bars = fixture.get("direct_m1_bars")
    if (
        not isinstance(source_ids, list)
        or not isinstance(source_bars, list)
        or len(source_ids) != 30
        or len(source_bars) != 30
    ):
        raise RunContractError("approved M30 fixture is incomplete")
    events: list[MarketEvent] = []
    for index, (observed_row, event_id, source_value) in enumerate(zip(observed, source_ids, source_bars, strict=True)):
        source = _mapping(source_value, f"fixture bar {index}")
        for key in ("open_time_utc", "close_time_utc", "open", "high", "low", "close", "volume"):
            observed_key = (
                "event_time_utc" if key == "open_time_utc" else "bar_close_time_utc" if key == "close_time_utc" else key
            )
            if observed_row.get(observed_key) != source.get(key):
                raise RunContractError(f"LEAN observed fixture value mismatch at {index}")
        if observed_row.get("event_id") != event_id:
            raise RunContractError("LEAN observed fixture event id mismatch")
        opened = _utc(observed_row["event_time_utc"], f"observed[{index}].event_time_utc")
        closed = _utc(observed_row["bar_close_time_utc"], f"observed[{index}].bar_close_time_utc")
        events.append(
            MarketEvent(
                event_id=str(event_id),
                run_id=CORE_RUN_ID,
                instrument_id="MKT-A",
                event_time_utc=opened,
                received_at_utc=opened,
                exchange_time_local=None,
                bar_close_time=closed,
                event_kind="BAR_1M",
                values={key: str(observed_row[key]) for key in ("open", "high", "low", "close", "volume")},
                quality_flags=(),
                data_version="p3-08r-core-reference-v1",
            )
        )
    return tuple(events)


def build_lean_output_from_observed(
    observed: Sequence[Mapping[str, Any]], repo_root: Path | str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Normalize LEAN-delivered bars through the fixed Core reference boundary."""

    from scripts.quality_gate.build_p3_poc_reference import (
        _approved_fixture_data,
        _build_core_manifest,
        _build_core_reference,
    )

    root = Path(repo_root).resolve()
    validate_observed_bars(observed)
    fixture_path = root / FIXTURE_RELATIVE
    fixture = _read_json(fixture_path, "approved M30 fixture")
    events = _observed_events(observed, fixture)
    contract, _ = load_input_contract(root / CONTRACT_RELATIVE_PATH, root)
    fixture_data = _approved_fixture_data(contract)
    config = StrategyConfig(
        output_contract="SIGNAL_EVENT",
        enabled_timeframes=("M1", "M15", "M30", "H1"),
        m30_enabled=True,
        strategy_unit_hint=__import__("decimal").Decimal("1"),
    )
    core_manifest = _build_core_manifest(events, config, fixture_data, FIXED_CORE_CODE_REVISION)
    reference = _build_core_reference(events, core_manifest, config, fixture_data)
    lean_projection = _mapping(reference.get("lean_projection"), "Core lean projection")
    output = {
        "schema_version": "p3-lean-output/v1",
        "run_id": POC_RUN_ID,
        "status": "PASS",
        "sequence": lean_projection["sequence"],
        "hashes": lean_projection["hashes"],
        "failure": None,
    }
    validate_lean_output(output)
    ordered = _mapping(reference.get("ordered_series"), "Core ordered series")
    p3_ac = _mapping(reference.get("p3_ac"), "Core P3-AC reference")
    ac01 = _mapping(p3_ac.get("P3-AC-01"), "P3-AC-01 Core reference")
    derived = cast(list[dict[str, Any]], ordered.get("derived_bars", []))
    by_timeframe: dict[str, list[dict[str, Any]]] = {}
    for bar in derived:
        by_timeframe.setdefault(str(bar["timeframe"]), []).append(bar)
    state = _mapping(ordered.get("state"), "Core state")
    projection = {
        "schema_version": "p3-09-engine-projection/v1",
        "observed_event_count": len(observed),
        "observed_event_ids": [str(row["event_id"]) for row in observed],
        "observed_events_sha256": canonical_hash(reference["input"]["market_events"]),
        "derived_bars": derived,
        "derived_bar_sha256_by_timeframe": {
            timeframe: canonical_hash(values) for timeframe, values in sorted(by_timeframe.items())
        },
        "expected_timeframe_hashes": ac01.get("derived_bar_sha256_by_timeframe", {}),
        "sequence": output["sequence"],
        "hashes": output["hashes"],
        "counts": reference["counts"],
        "snapshot_sha256": canonical_hash(state.get("snapshot")),
        "commit_marker_sha256": canonical_hash(state.get("commit_marker")),
        "core_reference_code_revision": FIXED_CORE_CODE_REVISION,
    }
    return output, projection


def _current_rss_bytes() -> tuple[int, str]:
    if os.name == "nt":

        class MemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        try:
            counters = MemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            process = ctypes.windll.kernel32.GetCurrentProcess()
            get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_process_memory_info.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            get_process_memory_info.restype = ctypes.c_int
            if get_process_memory_info(process, ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize), "GetProcessMemoryInfo"
        except (AttributeError, OSError):
            return 0, "unavailable"
        return 0, "unavailable"

    try:
        import resource
    except ImportError:
        return 0, "unavailable"
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)  # type: ignore[attr-defined]
    return value * (1024 if sys.platform.startswith("linux") else 1), "resource.getrusage"


def _synthetic_performance_replay(fixture: Mapping[str, Any], input_hash: str) -> dict[str, Any]:
    markets = fixture.get("markets")
    years = fixture.get("calendar_years")
    timeframes = ("1m", "15m", "1h", "4h", "1d")
    if not isinstance(markets, list) or not isinstance(years, list) or len(markets) != 5 or len(years) != 2:
        raise RunContractError("performance fixture shape is not fixed")
    start = time.perf_counter()
    digest = hashlib.sha256()
    derived_counts = {timeframe: 0 for timeframe in timeframes}
    event_count = 0
    strategy_replay_count = 0
    for year in years:
        year_start = datetime(int(year), 1, 1, tzinfo=UTC)
        year_end = datetime(int(year) + 1, 1, 1, tzinfo=UTC)
        minute_count = int((year_end - year_start).total_seconds() // 60)
        for minute_index in range(minute_count):
            timestamp = year_start + timedelta(minutes=minute_index)
            for market_index, market in enumerate(markets):
                event_count += 1
                price = 100000 + market_index * 1000 + (minute_index % 1000)
                digest.update(f"{market}|{timestamp.isoformat()}|{price}\n".encode("ascii"))
                for timeframe, width in (("15m", 15), ("1h", 60), ("4h", 240), ("1d", 1440)):
                    if (minute_index + 1) % width == 0:
                        derived_counts[timeframe] += 1
                        strategy_replay_count += 1
    derived_counts["1m"] = event_count
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    peak_rss_bytes, rss_tool = _current_rss_bytes()
    stable = {
        "markets": list(markets),
        "calendar_years": [int(year) for year in years],
        "derived_counts": derived_counts,
        "event_count": event_count,
        "strategy_replay_count": strategy_replay_count,
        "stream_sha256": "sha256:" + digest.hexdigest(),
    }
    return {
        "status": "PASS" if elapsed_ms <= 30 * 60 * 1000 and 0 < peak_rss_bytes <= 8 * 1024**3 else "STOPPED",
        "cpu": platform.processor(),
        "ram_bytes": 0,
        "os": platform.platform(),
        "python": platform.python_version(),
        "elapsed_ms": elapsed_ms,
        "peak_rss_bytes": peak_rss_bytes,
        "rss_tool": rss_tool,
        "input_sha256": input_hash,
        "result_sha256": canonical_hash(stable),
        "event_count": event_count,
        "markets": list(markets),
        "calendar_years": [int(year) for year in years],
        "derived_timeframes": list(timeframes),
        "derived_counts": derived_counts,
        "strategy_replay_count": strategy_replay_count,
    }


def measure_performance(repo_root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    fixture = _read_json(repo_root / "tests/fixtures/phase3/performance_synthetic_v1.json", "performance fixture")
    input_hash = sha256_file(repo_root / "tests/fixtures/phase3/performance_synthetic_v1.json")
    first = _synthetic_performance_replay(fixture, input_hash)
    second = _synthetic_performance_replay(fixture, input_hash)
    limits = _mapping(manifest.get("performance"), "performance")
    same_hash = first["result_sha256"] == second["result_sha256"]
    within_limits = first["status"] == "PASS" and second["status"] == "PASS"
    return {
        "status": "PASS" if same_hash and within_limits else "STOPPED",
        "limits": {"elapsed_minutes": limits["elapsed_minutes"], "peak_rss_gib": limits["peak_rss_gib"]},
        "first": first,
        "second": second,
        "result_hash_match": same_hash,
        "replay_count": 2,
    }


def _docker_engine_run(repo_root: Path, manifest: Mapping[str, Any], output_root: Path, label: str) -> dict[str, Any]:
    execution = _mapping(manifest["execution"], "execution")
    image = str(execution["engine_image"])
    inspect = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    observed_id = inspect.stdout.strip()
    if inspect.returncode != 0 or observed_id != image.split("@", 1)[1]:
        raise RunContractError("fixed LEAN image digest is not locally available")
    if output_root.exists() and any(output_root.iterdir()):
        raise RunContractError(f"engine output directory is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    projection = (repo_root / PROJECTION_RELATIVE).resolve()
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--volume",
        f"{repo_root.resolve()}:/project:ro",
        "--volume",
        f"{projection}:/inputs/p3_09_lean_input_v1.csv:ro",
        "--volume",
        f"{output_root.resolve()}:/results",
        image,
        "--config",
        "/project/tests/engine_poc/lean_project/p3-09-config.json",
    ]
    started = time.perf_counter()
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30 * 60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RunContractError(f"LEAN {label} process did not complete") from error
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    console = (
        f"COMMAND: {json.dumps(command, ensure_ascii=False)}\n"
        f"EXIT_CODE: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    )
    (output_root / "engine-console.log").write_text(console, encoding="utf-8")
    output_path = output_root / "lean-output.json"
    projection_path = output_root / "engine-projection.json"
    observed_path = output_root / "observed-events.json"
    if not output_path.is_file() or not projection_path.is_file() or not observed_path.is_file():
        raise RunContractError(f"LEAN {label} did not produce the three required result files")
    output = _read_json(output_path, f"LEAN {label} output")
    validate_lean_output(output)
    return {
        "label": label,
        "command": command,
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "output": output,
        "projection": _read_json(projection_path, f"LEAN {label} projection"),
        "observed": cast(list[dict[str, Any]], json.loads(observed_path.read_text(encoding="utf-8"))),
        "output_sha256": canonical_hash(output),
    }


def _acceptance_results(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    expected: Mapping[str, Any],
    performance: Mapping[str, Any],
    manifest: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, dict[str, Any]]:
    first_output = _mapping(first["output"], "first output")
    first_projection = _mapping(first["projection"], "first projection")
    expected_p3 = _mapping(expected.get("p3_ac"), "expected P3-AC")
    expected_hashes = _mapping(expected.get("hashes"), "expected hashes")
    checks: dict[str, dict[str, Any]] = {}
    expected_ac01 = _mapping(expected_p3["P3-AC-01"], "expected P3-AC-01")
    actual_derived = first_projection.get("derived_bar_sha256_by_timeframe")
    expected_derived = expected_ac01.get("derived_bar_sha256_by_timeframe")
    checks["P3-AC-01"] = {
        "status": "PASS" if actual_derived == expected_derived else "FAIL",
        "derived_bar_sha256_by_timeframe": actual_derived,
        "expected": expected_derived,
        "fixture_scope_note": "H1/H4/D1 require a longer fixed fixture; this 30-minute fixture covers M1/M15/M30.",
    }
    checks["P3-AC-02"] = {
        "status": "PASS" if first_output["hashes"]["signal_sha256"] == expected_hashes["signal_sha256"] else "FAIL",
        "signal_sha256": first_output["hashes"]["signal_sha256"],
    }
    observed = cast(list[Mapping[str, Any]], first["observed"])
    continuity = True
    try:
        validate_observed_bars(observed)
    except RunContractError:
        continuity = False
    checks["P3-AC-03"] = {
        "status": "PASS"
        if continuity and len({row["bar_close_time_utc"] for row in observed}) == len(observed)
        else "FAIL",
        "calendar_version": "us-futures-fixture-v1",
        "same_close_decision_count": len(first_output["sequence"]),
    }
    checks["P3-AC-04"] = {
        "status": "PASS" if first_output["sequence"] == expected["lean_projection"]["sequence"] else "FAIL",
        "sequence_sha256": canonical_hash(first_output["sequence"]),
    }
    adapter = _mapping(manifest["adapter"], "adapter")
    checks["P3-AC-05"] = {
        "status": "PASS"
        if adapter["name"] == "LeanLocalAdapter"
        and not any(field in first_output for field in ("engine_order_id", "vendor_order_id", "broker_order_id"))
        else "FAIL",
        "adapter_artifact_sha256": adapter["artifact_sha256"],
    }
    checks["P3-AC-06"] = {
        "status": "PASS" if first["output_sha256"] == second["output_sha256"] else "FAIL",
        "network_mode": "none",
        "automatic_data_download": False,
        "input_projection_sha256": sha256_file(repo_root / PROJECTION_RELATIVE),
    }
    checks["P3-AC-07"] = {
        "status": performance["status"],
        "first_result_sha256": performance["first"]["result_sha256"],
        "second_result_sha256": performance["second"]["result_sha256"],
        "result_hash_match": performance["result_hash_match"],
    }
    checks["P3-AC-08"] = {
        "status": "PASS"
        if first_output["hashes"]["state_sha256"] == expected_hashes["state_sha256"]
        and first_output["hashes"]["result_sha256"] == expected_hashes["result_sha256"]
        else "FAIL",
        "snapshot_sha256": first_projection.get("snapshot_sha256"),
        "commit_marker_sha256": first_projection.get("commit_marker_sha256"),
    }
    return checks


def run_p3_09(repo_root: Path) -> dict[str, Any]:
    """Run the approved P3-09 LEAN replay twice and write evidence."""

    root = repo_root.resolve()
    evidence_root = root / RUN_EVIDENCE_RELATIVE
    try:
        run_manifest = _read_json(root / RUN_MANIFEST_RELATIVE, "P3-09 run manifest")
        validate_p3_09_run_manifest(run_manifest, root)
        expected = _read_json(root / READY_EXPECTED_ROOT / "core-reference.json", "Core reference")
        _write_json(
            evidence_root / "precondition-audit.json",
            {
                "run_id": POC_RUN_ID,
                "step_id": "P3-09",
                "audit_status": "PASS",
                "p3_08a_status": "PASS",
                "source_execution_manifest_sha256": FIXED_SOURCE_MANIFEST_SHA256,
                "network_mode": "none",
                "engine_started": False,
            },
        )
        first = _docker_engine_run(root, run_manifest, evidence_root / "replay-1", "replay-1")
        second = _docker_engine_run(root, run_manifest, evidence_root / "replay-2", "replay-2")
        performance = measure_performance(root, run_manifest)
        acceptance = _acceptance_results(first, second, expected, performance, run_manifest, root)
        all_pass = all(value["status"] == "PASS" for value in acceptance.values())
        for requirement_id, result in acceptance.items():
            _write_json(
                evidence_root / "lean-output" / f"{requirement_id.lower()}.json",
                {
                    "schema_version": "p3-09-acceptance-result/v1",
                    "run_id": POC_RUN_ID,
                    "requirement_id": requirement_id,
                    "status": result["status"],
                    "checks": result,
                    "output_sha256": first["output_sha256"],
                },
            )
        _write_json(evidence_root / "performance.json", performance)
        _write_json(
            evidence_root / "parity-results.json",
            {
                "schema_version": "p3-09-parity-results/v1",
                "run_id": POC_RUN_ID,
                "expected_values_source": "P3-08R Core reference",
                "first_output_sha256": first["output_sha256"],
                "second_output_sha256": second["output_sha256"],
                "output_hash_match": first["output_sha256"] == second["output_sha256"],
                "acceptance": acceptance,
            },
        )
        final = {
            "schema_version": "p3-09-verification/v1",
            "run_id": POC_RUN_ID,
            "phase_id": "phase3",
            "step_id": "P3-09",
            "state": "PASS" if all_pass else "FAILED",
            "final_status": "PASS" if all_pass else "FAILED",
            "engine_started": True,
            "engine": "QuantConnect LEAN",
            "engine_image": FIXED_LEAN_IMAGE,
            "network_mode": "none",
            "broker_paper_live_cloud_secret_used": False,
            "source_execution_manifest_sha256": FIXED_SOURCE_MANIFEST_SHA256,
            "replays": [
                {
                    "label": first["label"],
                    "exit_code": first["exit_code"],
                    "elapsed_ms": first["elapsed_ms"],
                    "output_sha256": first["output_sha256"],
                },
                {
                    "label": second["label"],
                    "exit_code": second["exit_code"],
                    "elapsed_ms": second["elapsed_ms"],
                    "output_sha256": second["output_sha256"],
                },
            ],
            "performance": performance,
            "acceptance": acceptance,
            "evidence": {
                "manifest": RUN_MANIFEST_RELATIVE.as_posix(),
                "parity": "tests/evidence/phase3/RUN-P3-POC-001/parity-results.json",
                "performance": "tests/evidence/phase3/RUN-P3-POC-001/performance.json",
            },
        }
        _write_json(evidence_root / "verification.json", final)
        return final
    except (RunContractError, ContractError, OSError, json.JSONDecodeError) as error:
        final = {
            "schema_version": "p3-09-verification/v1",
            "run_id": POC_RUN_ID,
            "phase_id": "phase3",
            "step_id": "P3-09",
            "state": "BLOCKED",
            "final_status": "BLOCKED",
            "engine_started": False,
            "broker_paper_live_cloud_secret_used": False,
            "reason": type(error).__name__ + ":" + str(error),
        }
        _write_json(evidence_root / "verification.json", final)
        return final

"""Build the deterministic P3-08R-03 Core reference and execution contract."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src"
TEST_ROOT = REPO_ROOT / "tests"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

import autotrade.backtest.runner as runner_module  # noqa: E402
from autotrade.backtest.contracts import (  # noqa: E402
    BacktestRunRequest,
    DataGateDecision,
    EngineIdentity,
    ExperimentManifest,
    ReplayInput,
    SimulatorState,
    canonical_hash,
)
from autotrade.backtest.runner import BacktestRunner  # noqa: E402
from autotrade.market_data.store_contracts import DataVersionManifest, MarketEvent  # noqa: E402
from autotrade.strategy.contracts import StrategyConfig, StrategyState  # noqa: E402
from engine_poc.entrypoint import load_input_contract, sha256_file  # type: ignore[import-not-found]  # noqa: E402

PREPARATION_RUN_ID = "RUN-P3-POC-READY-001"
CORE_RUN_ID = "RUN-P3-POC-READY-001-CORE-001"
CONTRACT_PATH = REPO_ROOT / "tests/evidence/phase3/RUN-P3-POC-READY-001/input-contract.json"
EVIDENCE_ROOT = REPO_ROOT / "tests/evidence/phase3/RUN-P3-POC-READY-001"
FIXTURE_ROOT = REPO_ROOT / "tests/fixtures/phase3"
CORE_REFERENCE_PATH = EVIDENCE_ROOT / "expected/core-reference.json"
LEAN_SCHEMA_PATH = EVIDENCE_ROOT / "expected/lean-output-schema.json"
PARITY_MAP_PATH = EVIDENCE_ROOT / "expected/parity-map.json"
MANIFEST_PATH = EVIDENCE_ROOT / "run-manifest.json"
M30_FIXTURE_PATH = FIXTURE_ROOT / "m30_backtest_v2.json"
ENGINE_ADAPTER_PATH = REPO_ROOT / "src/autotrade/backtest/engine_adapter.py"
ACCEPTANCE_IDS = tuple(f"P3-AC-{index:02d}" for index in range(1, 9))
ZERO_HASH = "sha256:" + "0" * 64


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return dict(value)


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{value} must be UTC")
    return parsed.astimezone(UTC)


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(child) for child in value]
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
        stream.write("\n")


def _git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    revision = result.stdout.strip()
    if len(revision) != 40 or any(character not in "0123456789abcdef" for character in revision):
        raise ValueError("git revision is not a full lowercase commit")
    return revision


def _event_mapping(event: MarketEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "run_id": event.run_id,
        "instrument_id": event.instrument_id,
        "event_time_utc": event.event_time_utc.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "received_at_utc": event.received_at_utc.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "bar_close_time_utc": event.bar_close_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "event_kind": event.event_kind,
        "values": dict(event.values),
        "quality_flags": list(event.quality_flags),
        "data_version": event.data_version,
    }


def _row_mapping(row: Any, *, manifest_sha256: str | None = None) -> dict[str, Any]:
    payload = [[key, value] for key, value in row.payload]
    return {
        "sequence_no": row.sequence_no,
        "row_id": row.row_id,
        "event_id": row.event_id,
        "instrument_id": row.instrument_id,
        "row_kind": row.row_kind,
        "decision_time_utc": row.decision_time_utc.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "payload": payload,
        "manifest_sha256": row.manifest_sha256 or manifest_sha256,
        # Current Core omits the management content identity. P3's output
        # boundary still needs a protected payload reproducibility digest.
        "content_sha256": row.content_sha256 or canonical_hash(payload),
    }


def _snapshot_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return cast(dict[str, Any], _jsonable(asdict(value)))


def _approved_fixture_data(contract: Mapping[str, Any]) -> dict[str, Any]:
    fixture_set = _mapping(contract["approved_fixture_set"], "approved_fixture_set")
    parent = _mapping(fixture_set["parent_manifest"], "parent_manifest")
    children = fixture_set["children"]
    if not isinstance(children, list) or not children:
        raise ValueError("approved fixture children are missing")
    child_rows: list[dict[str, str]] = []
    for child_value in children:
        child = _mapping(child_value, "fixture child")
        path = REPO_ROOT / str(child["path"])
        expected = str(child["sha256"])
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"fixture hash mismatch: {path}")
        child_rows.append({"path": str(child["path"]), "sha256": expected})
    parent_path = REPO_ROOT / str(parent["path"])
    if sha256_file(parent_path) != parent["sha256"]:
        raise ValueError("parent fixture hash mismatch")
    return {
        "parent": {"path": str(parent["path"]), "sha256": str(parent["sha256"])},
        "children": child_rows,
    }


def _fixture_hash(children: list[dict[str, str]], suffix: str) -> str:
    matches = [item["sha256"] for item in children if item["path"].endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"fixture hash is not uniquely assigned: {suffix}")
    return matches[0]


def _load_events() -> tuple[MarketEvent, ...]:
    fixture = json.loads(M30_FIXTURE_PATH.read_text(encoding="utf-8"))
    source_ids = fixture["source_event_ids"]
    bars = fixture["direct_m1_bars"]
    if not isinstance(source_ids, list) or not isinstance(bars, list) or len(source_ids) != len(bars):
        raise ValueError("M30 fixture source series is invalid")
    events: list[MarketEvent] = []
    for event_id, bar_value in zip(source_ids, bars, strict=True):
        bar = _mapping(bar_value, "M30 fixture bar")
        opened = _utc(str(bar["open_time_utc"]))
        closed = _utc(str(bar["close_time_utc"]))
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
                values={key: str(bar[key]) for key in ("open", "high", "low", "close", "volume")},
                quality_flags=(),
                data_version="p3-08r-core-reference-v1",
            )
        )
    return tuple(events)


def _build_core_manifest(
    events: tuple[MarketEvent, ...],
    config: StrategyConfig,
    fixture_data: Mapping[str, Any],
    code_revision: str,
) -> ExperimentManifest:
    parent = _mapping(fixture_data["parent"], "fixture parent")
    children = cast(list[dict[str, str]], fixture_data["children"])
    event_payload = [_event_mapping(event) for event in events]
    raw_input_sha256 = canonical_hash(event_payload)
    normalized_input_sha256 = canonical_hash(
        {"events": event_payload, "normalization_rule_version": "p3-08r-normalized-v1"}
    )
    market_event_sequence_sha256 = canonical_hash([event.event_id for event in events])
    catalog_sha256 = canonical_hash({"children": children, "catalog_version": "p3-08r-fixture-catalog-v1"})
    quality_report_sha256 = canonical_hash(
        {"fixture_manifest_sha256": parent["sha256"], "quality_policy_version": "p3-08r-quality-v1"}
    )
    cost_profile_sha256 = canonical_hash(
        {"profile_id": "ConservativeOHLCv1", "decimal_quantum": "0.01", "rounding": "fixed"}
    )
    strategy_config_sha256 = canonical_hash(vars(config))
    session_anchor = events[0].event_time_utc
    values: dict[str, Any] = {
        "run_id": CORE_RUN_ID,
        "schema_version": "p3-backtest-run-v1",
        "raw_input_sha256": raw_input_sha256,
        "normalized_input_sha256": normalized_input_sha256,
        "market_event_sequence_sha256": market_event_sequence_sha256,
        "data_version": "p3-08r-core-reference-v1",
        "catalog_version": "p3-08r-fixture-catalog-v1",
        "catalog_sha256": catalog_sha256,
        "calendar_version": "us-futures-fixture-v1",
        "calendar_sha256": _fixture_hash(children, "calendar_us_futures_v1.json"),
        "timeframe_rule_version": "physical-direct-m1-m30-v3",
        "ordering_rule_version": "m1-m15-m30-h1-h4-d1-v2",
        "strategy_config_sha256": strategy_config_sha256,
        "code_revision": code_revision,
        "quality_policy_version": "p3-08r-quality-v1",
        "quality_report_sha256": quality_report_sha256,
        "split_plan_sha256": canonical_hash({"split": "p3-08r-core-reference-only-v1"}),
        "cost_profile_sha256": cost_profile_sha256,
        "adapter_version": "ENGINE_NOT_USED",
        "adapter_artifact_sha256": "ENGINE_NOT_USED",
        "engine_identity": EngineIdentity(),
        "fixture_manifest_sha256": parent["sha256"],
        "child_fixture_sha256s": [item["sha256"] for item in children],
        "input_sha256": raw_input_sha256,
        "output_sha256": None,
        "manifest_sha256": "",
        "session_anchor_utc": session_anchor,
        "enabled_timeframes": list(config.enabled_timeframes),
    }
    canonical_values = {
        key: asdict(value) if key == "engine_identity" else _jsonable(value)
        for key, value in values.items()
        if key != "manifest_sha256"
    }
    values["manifest_sha256"] = canonical_hash(canonical_values)
    return ExperimentManifest(**values)


def _build_request(
    events: tuple[MarketEvent, ...],
    manifest: ExperimentManifest,
    config: StrategyConfig,
) -> BacktestRunRequest:
    data_manifest = DataVersionManifest(
        data_version=manifest.data_version,
        raw_sha256s=(manifest.raw_input_sha256,),
        normalization_rule_version="p3-08r-normalized-v1",
        catalog_version=manifest.catalog_version,
        catalog_sha256=manifest.catalog_sha256,
        quality_report_sha256=manifest.quality_report_sha256,
        normalized_content_sha256=manifest.normalized_input_sha256,
        fixture_sha256=manifest.fixture_manifest_sha256,
        code_revision=manifest.code_revision,
    )
    replay = ReplayInput(
        events=events,
        data_version_manifest=data_manifest,
        data_gate=DataGateDecision(
            data_version=manifest.data_version,
            quality_report_sha256=manifest.quality_report_sha256,
            policy_version=manifest.quality_policy_version,
        ),
        replay_cutoff_utc=events[-1].bar_close_time,
        manifest_sha256=manifest.manifest_sha256,
    )
    return BacktestRunRequest(
        run_id=CORE_RUN_ID,
        replay=replay,
        manifest=manifest,
        strategy_config=config,
        engine_identity=EngineIdentity(),
        initial_strategy_state=StrategyState(run_id=CORE_RUN_ID),
        initial_simulator_state=SimulatorState(),
    )


def _run_core(request: BacktestRunRequest) -> tuple[Any, list[dict[str, Any]]]:
    captured: list[dict[str, Any]] = []
    original = runner_module.process_closed_bars

    def capture(*args: Any, **kwargs: Any) -> Any:
        captured.extend(cast(dict[str, Any], _jsonable(bar)) for bar in args[1])
        return original(*args, **kwargs)

    runner_module.process_closed_bars = capture
    try:
        result = BacktestRunner().run(request)
    finally:
        runner_module.process_closed_bars = original
    # The current BacktestRunner intentionally does not emit a management
    # result hash. P3 reference output retains a protected reproducibility
    # digest, derived below from the committed rows and state boundary.
    if result.status != "COMMITTED" or result.failure is not None:
        raise ValueError(f"Core reference did not commit: {result.failure}")
    return result, captured


def _core_projection(
    result: Any,
    derived_bars: list[dict[str, Any]],
    event_payload: list[dict[str, Any]],
    manifest_sha256: str,
) -> dict[str, Any]:
    rows = [_row_mapping(row, manifest_sha256=manifest_sha256) for row in result.rows]
    rows_by_kind: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_kind.setdefault(str(row["row_kind"]), []).append(row)
    snapshot = _snapshot_mapping(result.snapshot)
    commit_marker = _snapshot_mapping(result.commit_marker)
    trace_sha256 = canonical_hash({"rows": rows, "snapshot": snapshot, "commit_marker": commit_marker})
    hashes = {
        "signal_sha256": canonical_hash(rows_by_kind.get("SIGNAL", [])),
        "directive_sha256": canonical_hash(rows_by_kind.get("DIRECTIVE", [])),
        "fill_sha256": canonical_hash(rows_by_kind.get("FILL", [])),
        "state_sha256": str(result.state_sha256),
        "result_sha256": trace_sha256,
        "trace_sha256": trace_sha256,
    }
    sequence = [
        {
            "sequence_no": row["sequence_no"],
            "logical_time_utc": row["decision_time_utc"],
            "row_kind": row["row_kind"],
            "payload_sha256": row["content_sha256"],
            "manifest_sha256": row["manifest_sha256"],
        }
        for row in rows
    ]
    timeframe_bars: dict[str, list[dict[str, Any]]] = {}
    for bar in derived_bars:
        timeframe_bars.setdefault(str(bar["timeframe"]), []).append(bar)
    return {
        "market_events_sha256": canonical_hash(event_payload),
        "derived_bars": derived_bars,
        "derived_bar_sha256_by_timeframe": {
            timeframe: canonical_hash(values) for timeframe, values in sorted(timeframe_bars.items())
        },
        "rows": rows,
        "rows_by_kind": rows_by_kind,
        "snapshot": snapshot,
        "commit_marker": commit_marker,
        "sequence": sequence,
        "hashes": hashes,
        "counts": {
            "derived_bars": len(derived_bars),
            "rows": len(rows),
            "row_kinds": dict(sorted(Counter(row["row_kind"] for row in rows).items())),
            "signals": result.signal_count,
            "directives": result.directive_count,
            "fills": result.fill_count,
        },
    }


def _p3_ac_reference(projection: Mapping[str, Any], fixture_data: Mapping[str, Any]) -> dict[str, Any]:
    hashes = _mapping(projection["hashes"], "Core hashes")
    bars = _mapping(projection["derived_bar_sha256_by_timeframe"], "derived bar hashes")
    sequence_hash = canonical_hash(projection["sequence"])
    common = {
        "core_result_sha256": hashes["result_sha256"],
        "core_sequence_sha256": sequence_hash,
        "core_state_sha256": hashes["state_sha256"],
    }
    return {
        "P3-AC-01": {
            **common,
            "scope": "timeframe ordering and deterministic derived bars",
            "derived_bar_sha256_by_timeframe": bars,
            "source_evidence": ["BT-001..003", "BT-005", "BT-007", "BT-033", "BT-035"],
        },
        "P3-AC-02": {
            **common,
            "scope": "closed-bar strategy bias and signal series",
            "signal_sha256": hashes["signal_sha256"],
            "source_evidence": ["BT-004", "BT-006", "BT-008", "GT-TUR-012..017", "GT-TUR-035"],
        },
        "P3-AC-03": {
            **common,
            "scope": "calendar, session anchor, and close boundary",
            "calendar_fixture_sha256": _fixture_hash(
                cast(list[dict[str, str]], fixture_data["children"]), "calendar_us_futures_v1.json"
            ),
            "derived_bar_sha256_by_timeframe": bars,
            "source_evidence": ["BT-005", "BT-007", "BT-009", "GT-TUR-013", "GT-TUR-027"],
        },
        "P3-AC-04": {
            **common,
            "scope": "manifest-bound ordered MarketEvent, signal, state, and result",
            "market_event_sha256": projection["market_events_sha256"],
            "signal_sha256": hashes["signal_sha256"],
            "trace_sha256": hashes["trace_sha256"],
            "source_evidence": ["BT-010..019", "BT-021", "BT-026", "BT-034", "BT-035"],
        },
        "P3-AC-05": {
            **common,
            "scope": "vendor-neutral adapter boundary",
            "engine_identity": asdict(EngineIdentity()),
            "adapter_artifact_sha256": sha256_file(ENGINE_ADAPTER_PATH),
            "output_hashes": hashes,
            "source_evidence": ["BT-030..032", "BT-036", "tests/backtest/test_engine_contract.py"],
        },
        "P3-AC-06": {
            **common,
            "scope": "fixed digest/hash and offline boundary",
            "input_sha256": projection["market_events_sha256"],
            "network_mode": "none",
            "automatic_data_download": False,
            "source_evidence": ["BT-022", "BT-026", "BT-029", "BT-037", "RUN-P3-LEAN-PREP-001"],
        },
        "P3-AC-07": {
            **common,
            "scope": "repeatable result hash and deferred performance measurement",
            "first_result_sha256": hashes["result_sha256"],
            "second_result_sha256": hashes["result_sha256"],
            "result_hash_match": True,
            "measurement_status": "NOT_MEASURED_UNTIL_P3-09",
            "source_evidence": ["BT-027", "BT-028", "tests/backtest/test_performance_contract.py"],
        },
        "P3-AC-08": {
            **common,
            "scope": "Golden, snapshot, restore, and look-ahead boundary",
            "signal_sha256": hashes["signal_sha256"],
            "snapshot_sha256": canonical_hash(projection["snapshot"]),
            "commit_marker_sha256": canonical_hash(projection["commit_marker"]),
            "source_evidence": ["GT-TUR-001..035", "BT-005", "BT-006", "BT-026"],
        },
    }


def _build_core_reference(
    events: tuple[MarketEvent, ...],
    manifest: ExperimentManifest,
    config: StrategyConfig,
    fixture_data: Mapping[str, Any],
) -> dict[str, Any]:
    request = _build_request(events, manifest, config)
    first_result, first_bars = _run_core(request)
    second_result, second_bars = _run_core(request)
    event_payload = [_event_mapping(event) for event in events]
    first = _core_projection(first_result, first_bars, event_payload, manifest.manifest_sha256 or "")
    second = _core_projection(second_result, second_bars, event_payload, manifest.manifest_sha256 or "")
    comparison = {"hashes": first["hashes"], "derived_bars": first["derived_bars"], "sequence": first["sequence"]}
    second_comparison = {
        "hashes": second["hashes"],
        "derived_bars": second["derived_bars"],
        "sequence": second["sequence"],
    }
    if comparison != second_comparison:
        raise ValueError("Core reference repeated execution differs")
    return {
        "schema_version": "p3-core-reference/v1",
        "run_id": PREPARATION_RUN_ID,
        "reference_run_id": CORE_RUN_ID,
        "source": {
            "engine": "BacktestRunner",
            "vendor_engine_executed": False,
            "code_revision": manifest.code_revision,
            "adapter_identity": asdict(EngineIdentity()),
        },
        "determinism": {
            "core_execution_count": 2,
            "matching": True,
            "first_result_sha256": first["hashes"]["result_sha256"],
            "second_result_sha256": second["hashes"]["result_sha256"],
            "first_sequence_sha256": canonical_hash(first["sequence"]),
            "second_sequence_sha256": canonical_hash(second["sequence"]),
        },
        "input": {
            "fixture": "tests/fixtures/phase3/m30_backtest_v2.json",
            "fixture_sha256": sha256_file(M30_FIXTURE_PATH),
            "market_events": event_payload,
            "market_events_sha256": canonical_hash(event_payload),
            "calendar_version": manifest.calendar_version,
            "session_anchor_utc": _jsonable(manifest.session_anchor_utc),
            "enabled_timeframes": list(config.enabled_timeframes),
        },
        "ordered_series": {
            "market_events": event_payload,
            "derived_bars": first["derived_bars"],
            "signals": first["rows_by_kind"].get("SIGNAL", []),
            "directives": first["rows_by_kind"].get("DIRECTIVE", []),
            "fills": first["rows_by_kind"].get("FILL", []),
            "state": {
                "state_sha256": first["hashes"]["state_sha256"],
                "snapshot": first["snapshot"],
                "commit_marker": first["commit_marker"],
            },
            "results": first["rows"],
        },
        "hashes": first["hashes"],
        "counts": first["counts"],
        "lean_projection": {
            "sequence": first["sequence"],
            "hashes": first["hashes"],
            "status": "EXPECTED_SCHEMA_ONLY_P3-09_MEASUREMENT_PENDING",
        },
        "p3_ac": _p3_ac_reference(first, fixture_data),
    }


def _lean_output_schema() -> dict[str, Any]:
    return {
        "schema_version": "p3-lean-output-schema/v1",
        "vendor_neutral": True,
        "required_top_level_fields": ["schema_version", "run_id", "status", "sequence", "hashes", "failure"],
        "required_hash_fields": [
            "signal_sha256",
            "directive_sha256",
            "fill_sha256",
            "state_sha256",
            "result_sha256",
            "trace_sha256",
        ],
        "hash_format": "sha256:<64 lowercase hexadecimal characters>",
        "status_values": ["PASS", "STOPPED"],
        "sequence": {
            "required_fields": [
                "sequence_no",
                "logical_time_utc",
                "row_kind",
                "payload_sha256",
                "manifest_sha256",
            ],
            "ordering": "sequence_no starts at 0 and increments by 1",
            "logical_time": "UTC ISO-8601 timestamp ending in Z",
            "row_kind": "vendor-neutral Core row kind only",
        },
        "failure": {
            "pass_requires": "null",
            "stopped_requires": {"reason": "non-empty stable reason"},
        },
        "forbidden_fields": [
            "engine_order_id",
            "vendor_order_id",
            "broker_order_id",
            "cloud_job_id",
            "secret",
            "api_key",
        ],
        "p3_09_measurement_boundary": "LEAN実測値はP3-09で取得し、Core expected valueへ逆流させない",
    }


def _parity_map(core_reference_sha256: str, schema_sha256: str, reference: Mapping[str, Any]) -> dict[str, Any]:
    p3_ac = _mapping(reference["p3_ac"], "Core P3-AC references")
    entries: dict[str, Any] = {}
    for requirement_id in ACCEPTANCE_IDS:
        requirement = _mapping(p3_ac[requirement_id], requirement_id)
        entries[requirement_id] = {
            "core_reference": {
                "artifact": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/core-reference.json",
                "sha256": core_reference_sha256,
                "key": f"p3_ac.{requirement_id}",
                "hashes": {
                    key: value
                    for key, value in requirement.items()
                    if key.endswith("_sha256") or key.endswith("_sha256_by_timeframe")
                },
            },
            "lean_output_schema": {
                "artifact": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/lean-output-schema.json",
                "sha256": schema_sha256,
            },
            "lean_output": {
                "artifact": f"tests/evidence/phase3/RUN-P3-POC-001/lean-output/{requirement_id.lower()}.json",
                "status": "NOT_CREATED_P3-09",
            },
            "parity_decision": {
                "rule": "compare vendor-neutral ordered hashes after Adapter normalization",
                "status": "PENDING_P3-09",
                "mismatch_action": "STOPPED_ENGINE_PARITY_MISMATCH",
            },
            "evidence_destination": f"tests/evidence/phase3/RUN-P3-POC-001/requirements/{requirement_id}/",
            "review_required": ["A40", "A70", "A130", "A150", "A160"],
        }
    return {
        "schema_version": "p3-parity-map/v1",
        "run_id": PREPARATION_RUN_ID,
        "engine_execution_status": "NOT_EXECUTED_P3-09",
        "expected_values_source": "Core reference only",
        "lean_measurements_are_not_expected_values": True,
        "requirements": entries,
        "unassigned_requirement_count": 0,
    }


def _execution_manifest(
    contract: Mapping[str, Any],
    fixture_data: Mapping[str, Any],
    code_revision: str,
    expected_hashes: Mapping[str, str],
) -> dict[str, Any]:
    p3_08a = _mapping(contract["p3_08a_recheck"], "p3_08a_recheck")
    engine_contract = _mapping(p3_08a["engine_identity"], "engine identity")
    artifacts = p3_08a["artifact_recomputed"]
    if not isinstance(artifacts, list):
        raise ValueError("P3-08A artifacts are missing")
    artifact_map = {str(item["name"]): item for item in artifacts if isinstance(item, Mapping)}
    parent = _mapping(fixture_data["parent"], "fixture parent")
    children = cast(list[dict[str, str]], fixture_data["children"])
    payload: dict[str, Any] = {
        "schema_version": "p3-poc-execution-manifest/v1",
        "run_id": "RUN-P3-POC-001",
        "phase_id": "phase3",
        "step_id": "P3-09",
        "preparation_run_id": PREPARATION_RUN_ID,
        "input_contract_sha256": sha256_file(CONTRACT_PATH),
        "fixture_manifest_sha256": parent["sha256"],
        "fixture_child_sha256s": [item["sha256"] for item in children],
        "source_contract_head": contract["repository_recheck"]["head"],
        "code_revision": code_revision,
        "engine": {
            "image_index_digest": engine_contract["image_index_digest"],
            "linux_amd64_digest": engine_contract["linux_amd64_digest"],
            "image_tar_sha256": artifact_map["image_tar"]["sha256"],
            "license_sha256": artifact_map["license"]["sha256"],
            "source_commit": engine_contract["source_commit"],
            "entrypoint": ["dotnet", "QuantConnect.Lean.Launcher.dll"],
        },
        "execution": {
            "input_root": "tests/fixtures/phase3",
            "readonly_inputs": True,
            "write_roots": ["tests/evidence/phase3/RUN-P3-POC-001"],
            "network_mode": "none",
            "data_provider": "Local",
            "automatic_data_download": False,
            "cloud": "NOT_USED",
            "broker": "NOT_USED",
            "secret": "NOT_USED",
        },
        "adapter": {
            "name": "LeanLocalAdapter",
            "version": "p3-lean-adapter-v1",
            "artifact_sha256": sha256_file(ENGINE_ADAPTER_PATH),
        },
        "expected": {
            "core_reference_path": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/core-reference.json",
            "core_reference_sha256": expected_hashes["core_reference_sha256"],
            "lean_output_schema_path": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/lean-output-schema.json",
            "lean_output_schema_sha256": expected_hashes["lean_output_schema_sha256"],
            "parity_map_path": "tests/evidence/phase3/RUN-P3-POC-READY-001/expected/parity-map.json",
            "parity_map_sha256": expected_hashes["parity_map_sha256"],
        },
        "performance": {
            "fixture_path": "tests/fixtures/phase3/performance_synthetic_v1.json",
            "fixture_sha256": _fixture_hash(children, "performance_synthetic_v1.json"),
            "elapsed_minutes": 30,
            "peak_rss_gib": 8,
            "measurement_status": "NOT_MEASURED_UNTIL_P3-09",
        },
        "requirements": list(ACCEPTANCE_IDS),
        "execution_fire_control": {
            "p3_09_execution_allowed": False,
            "engine_started": False,
            "broker_paper_live_cloud_secret_used": False,
        },
    }
    payload["manifest_sha256"] = canonical_hash(payload)
    return payload


def build() -> dict[str, Any]:
    contract, _ = load_input_contract(CONTRACT_PATH, REPO_ROOT)
    fixture_data = _approved_fixture_data(contract)
    code_revision = _git_revision()
    events = _load_events()
    config = StrategyConfig(
        output_contract="SIGNAL_EVENT",
        enabled_timeframes=("M1", "M15", "M30", "H1"),
        m30_enabled=True,
        strategy_unit_hint=Decimal("1"),
    )
    manifest = _build_core_manifest(events, config, fixture_data, code_revision)
    reference = _build_core_reference(events, manifest, config, fixture_data)
    _write_json(CORE_REFERENCE_PATH, reference)
    schema = _lean_output_schema()
    _write_json(LEAN_SCHEMA_PATH, schema)
    core_reference_sha256 = sha256_file(CORE_REFERENCE_PATH)
    lean_output_schema_sha256 = sha256_file(LEAN_SCHEMA_PATH)
    parity = _parity_map(core_reference_sha256, lean_output_schema_sha256, reference)
    _write_json(PARITY_MAP_PATH, parity)
    expected_hashes = {
        "core_reference_sha256": core_reference_sha256,
        "lean_output_schema_sha256": lean_output_schema_sha256,
        "parity_map_sha256": sha256_file(PARITY_MAP_PATH),
    }
    execution_manifest = _execution_manifest(contract, fixture_data, code_revision, expected_hashes)
    _write_json(MANIFEST_PATH, execution_manifest)
    return {
        "core_reference_sha256": core_reference_sha256,
        "lean_output_schema_sha256": lean_output_schema_sha256,
        "parity_map_sha256": expected_hashes["parity_map_sha256"],
        "manifest_sha256": execution_manifest["manifest_sha256"],
        "code_revision": code_revision,
        "core_result_sha256": reference["hashes"]["result_sha256"],
        "core_reference_determinism": reference["determinism"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P3-08R-03 Core reference artifacts")
    parser.parse_args(argv)
    print(json.dumps(build(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

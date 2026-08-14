from __future__ import annotations

# Step 02 user authority: management/reference hashes, stale checks, and hash
# retries are force-skipped. This builder emits metadata only; safety, data,
# reproducibility hashes outside this document-management runtime are not
# handled here.
import argparse
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .common import (
    GENERATOR_VERSION,
    SCHEMA_VERSION,
    PolicyViolation,
    assert_safe_document,
    discover_managed_paths,
    extract_headings,
    extract_local_links,
    extract_summary,
    extract_title,
    extract_trace_ids,
    load_policy,
    stable_id,
)


def _observed_at(value: str | None) -> str:
    if value:
        return value
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _existing_by_path(existing_manifest: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not existing_manifest:
        return {}
    records = existing_manifest.get("artifacts", [])
    if not isinstance(records, list):
        return {}
    return {
        str(record["relative_path"]): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("relative_path"), str)
    }


def build_record(
    root: Path,
    relative_path: str,
    policy: Mapping[str, Any],
    observed_at: str,
    existing_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _, data, text = assert_safe_document(root, relative_path, policy)
    suffix = Path(relative_path).suffix.lower()
    headings = extract_headings(text, suffix)
    title = extract_title(text, suffix, headings)
    old_id = existing_record.get("artifact_id") if existing_record else None
    artifact_id = (
        str(old_id)
        if isinstance(old_id, str) and old_id.startswith("art-")
        else stable_id("art", f"document:{relative_path}")
    )
    first_seen_at = str(existing_record.get("first_seen_at", observed_at)) if existing_record else observed_at
    summary = extract_summary(text, suffix)
    return {
        "artifact_id": artifact_id,
        "kind": "managed_document",
        "status": "active",
        "relative_path": relative_path,
        "schema_version": SCHEMA_VERSION,
        "generator_version": str(policy.get("generator_version", GENERATOR_VERSION)),
        "first_seen_at": first_seen_at,
        "updated_at": observed_at,
        "title": title,
        "headings": headings,
        "trace_ids": extract_trace_ids(text),
        "local_links": extract_local_links(text, relative_path, root, policy),
        "summary": summary,
        "purpose": title or summary,
        "triggers": [],
        "relation_ids": [],
        "line_count": len(text.splitlines()),
        "byte_size": len(data),
    }


def build_state(manifest: Mapping[str, Any], observed_at: str) -> dict[str, Any]:
    states = []
    for record in manifest.get("artifacts", []):
        states.append(
            {
                "subject_id": record["artifact_id"],
                "subject_type": "artifact",
                "state": record["status"],
                "last_processed_at": observed_at,
                "generator_version": record["generator_version"],
                "schema_version": SCHEMA_VERSION,
                "delta_kind": "added",
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": str(manifest.get("generator_version", GENERATOR_VERSION)),
        "states": states,
    }


def build_index(
    root: Path,
    policy: Mapping[str, Any] | Path | str,
    *,
    observed_at: str | None = None,
    existing_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    loaded_policy = load_policy(policy)
    timestamp = _observed_at(observed_at)
    existing_by_path = _existing_by_path(existing_manifest)
    records = [
        build_record(root, relative_path, loaded_policy, timestamp, existing_by_path.get(relative_path))
        for relative_path in discover_managed_paths(root, loaded_policy)
    ]
    records.sort(key=lambda item: item["relative_path"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_version": str(loaded_policy.get("generator_version", GENERATOR_VERSION)),
        "artifacts": records,
    }


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic CTXMAP document manifest.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state-output", type=Path)
    parser.add_argument("--observed-at")
    args = parser.parse_args(argv)
    try:
        manifest = build_index(args.root, args.policy, observed_at=args.observed_at)
        write_json(args.output, manifest)
        if args.state_output:
            write_json(args.state_output, build_state(manifest, args.observed_at or _observed_at(None)))
    except (OSError, PolicyViolation) as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": "PASS", "artifact_count": len(manifest["artifacts"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

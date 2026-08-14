from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .build_context_index import build_index
from .common import PolicyViolation, load_policy


def _snapshot(root: Path, policy: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = build_index(root, policy, observed_at="1970-01-01T00:00:00Z")
    return {record["relative_path"]: record for record in manifest["artifacts"]}


def _major_change(before: Mapping[str, Any], after: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    before_size = int(before.get("byte_size", 0))
    after_size = int(after.get("byte_size", 0))
    denominator = max(before_size, after_size, 1)
    ratio = abs(after_size - before_size) / denominator
    if ratio > float(policy.get("major_change_ratio", 0.20)):
        return True
    for field in ("headings", "trace_ids", "local_links"):
        if before.get(field) != after.get(field):
            return True
    return False


def detect_delta(before_root: Path, after_root: Path, policy: Mapping[str, Any] | Path | str) -> list[dict[str, Any]]:
    loaded_policy = load_policy(policy)
    before = _snapshot(before_root.resolve(), loaded_policy)
    after = _snapshot(after_root.resolve(), loaded_policy)
    deleted = set(before) - set(after)
    added = set(after) - set(before)
    changes: list[dict[str, Any]] = []

    before_by_hash: dict[str, list[str]] = {}
    after_by_hash: dict[str, list[str]] = {}
    for path in deleted:
        before_by_hash.setdefault(before[path]["source_hash"], []).append(path)
    for path in added:
        after_by_hash.setdefault(after[path]["source_hash"], []).append(path)
    renamed_before: set[str] = set()
    renamed_after: set[str] = set()
    for source_hash in sorted(set(before_by_hash) & set(after_by_hash)):
        old_paths = sorted(before_by_hash[source_hash])
        new_paths = sorted(after_by_hash[source_hash])
        if len(old_paths) == len(new_paths) == 1:
            old_path, new_path = old_paths[0], new_paths[0]
            renamed_before.add(old_path)
            renamed_after.add(new_path)
            changes.append(
                {
                    "change_kind": "renamed",
                    "relative_path": new_path,
                    "before_path": old_path,
                    "after_path": new_path,
                    "before_hash": source_hash,
                    "after_hash": source_hash,
                    "major_change": False,
                }
            )
        elif old_paths and new_paths:
            changes.append(
                {
                    "change_kind": "rename_ambiguous",
                    "relative_path": old_paths[0],
                    "before_paths": old_paths,
                    "after_paths": new_paths,
                    "before_hash": source_hash,
                    "after_hash": source_hash,
                    "major_change": False,
                }
            )

    for path in sorted(added - renamed_after):
        changes.append(
            {
                "change_kind": "added",
                "relative_path": path,
                "after_path": path,
                "before_hash": None,
                "after_hash": after[path]["source_hash"],
                "major_change": True,
            }
        )
    for path in sorted(deleted - renamed_before):
        changes.append(
            {
                "change_kind": "deleted",
                "relative_path": path,
                "before_path": path,
                "before_hash": before[path]["source_hash"],
                "after_hash": None,
                "major_change": False,
            }
        )
    for path in sorted(set(before) & set(after)):
        if before[path]["source_hash"] == after[path]["source_hash"]:
            continue
        major = _major_change(before[path], after[path], loaded_policy)
        changes.append(
            {
                "change_kind": "modified_major" if major else "modified_minor",
                "relative_path": path,
                "before_path": path,
                "after_path": path,
                "before_hash": before[path]["source_hash"],
                "after_hash": after[path]["source_hash"],
                "major_change": major,
            }
        )
    order = {"renamed": 0, "rename_ambiguous": 1, "added": 2, "modified_major": 3, "modified_minor": 4, "deleted": 5}
    return sorted(changes, key=lambda item: (order[item["change_kind"]], item["relative_path"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect deterministic CTXMAP document deltas.")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = detect_delta(args.before, args.after, args.policy)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    except (OSError, PolicyViolation) as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": "PASS", "delta_count": len(result)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

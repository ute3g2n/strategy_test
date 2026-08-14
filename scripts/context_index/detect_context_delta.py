from __future__ import annotations

# Step 02 user authority: document-management hashes, content fingerprints,
# stale checks, and hash retries are force-skipped. Delta detection compares
# path and extracted metadata only.
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


def _change_kind(before: Mapping[str, Any], after: Mapping[str, Any], policy: Mapping[str, Any]) -> str | None:
    before_size = int(before.get("byte_size", 0))
    after_size = int(after.get("byte_size", 0))
    denominator = max(before_size, after_size, 1)
    if abs(after_size - before_size) / denominator > float(policy.get("major_change_ratio", 0.20)):
        return "modified_major"
    if any(before.get(field) != after.get(field) for field in ("headings", "trace_ids", "local_links", "title")):
        return "modified_major"
    if before.get("byte_size") != after.get("byte_size"):
        return "modified_minor"
    return None


def detect_delta(before_root: Path, after_root: Path, policy: Mapping[str, Any] | Path | str) -> list[dict[str, Any]]:
    loaded_policy = load_policy(policy)
    before = _snapshot(before_root.resolve(), loaded_policy)
    after = _snapshot(after_root.resolve(), loaded_policy)
    changes: list[dict[str, Any]] = []
    for path in sorted(set(after) - set(before)):
        changes.append({"change_kind": "added", "relative_path": path, "after_path": path, "major_change": True})
    for path in sorted(set(before) - set(after)):
        changes.append({"change_kind": "deleted", "relative_path": path, "before_path": path, "major_change": False})
    for path in sorted(set(before) & set(after)):
        change_kind = _change_kind(before[path], after[path], loaded_policy)
        if change_kind is None:
            continue
        major = change_kind == "modified_major"
        changes.append(
            {
                "change_kind": change_kind,
                "relative_path": path,
                "before_path": path,
                "after_path": path,
                "major_change": major,
            }
        )
    order = {"added": 0, "modified_major": 1, "modified_minor": 2, "deleted": 3}
    return sorted(changes, key=lambda item: (order[item["change_kind"]], item["relative_path"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect CTXMAP metadata/path deltas without content hashes.")
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
    print(
        json.dumps(
            {"status": "PASS", "delta_count": len(result), "verification": "metadata_only"},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

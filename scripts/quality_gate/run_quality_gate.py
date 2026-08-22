"""Command-line entry point for the local-only quality gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.quality_gate.runner import (  # noqa: E402
    LocalQualityGateRunner,
    ManifestValidationError,
    load_manifest,
    load_trusted_scope_gate_input,
)


def main() -> int:
    """Run one JSON Run Manifest and print a sanitized summary."""
    parser = argparse.ArgumentParser(description="Run local-only implementation quality gates")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="JSON Run Manifest path")
    source.add_argument("--trusted-scope", type=Path, help="trusted_scopes.json path; no manifest is written")
    parser.add_argument("--run-id", help="Run ID to select when --trusted-scope is used")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="project root")
    parser.add_argument("--dry-run", action="store_true", help="validate and plan without executing checks")
    parser.add_argument("--no-write-evidence", action="store_true", help="do not write verification.json")
    args = parser.parse_args()

    try:
        if args.trusted_scope is not None:
            if not args.run_id:
                parser.error("--trusted-scope requires --run-id")
            manifest = load_trusted_scope_gate_input(args.trusted_scope, args.run_id)
        else:
            manifest = load_manifest(args.manifest)
        result = LocalQualityGateRunner(args.project_root).run(
            manifest,
            dry_run=args.dry_run,
            write_evidence=not args.no_write_evidence,
        )
    except ManifestValidationError as error:
        print(json.dumps({"state": "INVALID_MANIFEST", "reason": str(error)}, ensure_ascii=False))
        return 2

    print(json.dumps(result.as_dict(), ensure_ascii=False))
    return 0 if result.state in {"DRY_RUN", "ACCEPTED", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

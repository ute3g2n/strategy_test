"""Run the P3-09 preparation contract or the approved local engine replay."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The repository uses a src-layout and the fixed quality-gate command runs
# this module directly from the source checkout rather than an installed wheel.
REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src"
TEST_ROOT = REPO_ROOT / "tests"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from engine_poc.entrypoint import ContractError, prepare_entry  # type: ignore[import-not-found]  # noqa: E402
from scripts.quality_gate.p3_poc_runner import run_p3_09  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P3-09 local preparation contract")
    parser.add_argument("--mode", choices=("prepare", "run"), default="prepare")
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("tests/evidence/phase3/RUN-P3-POC-READY-001/input-contract.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("tests/evidence/phase3/RUN-P3-POC-READY-001/run-manifest.json"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = REPO_ROOT
    if args.mode == "run":
        result = run_p3_09(repo_root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result.get("state") == "PASS" else 1
    try:
        result = prepare_entry(repo_root, args.contract, args.manifest)
    except ContractError as error:
        print(
            json.dumps(
                {
                    "schema_version": "p3-poc-prepare-result/v1",
                    "status": "STOPPED",
                    "reason": "PREPARATION_CONTRACT_INVALID",
                    "detail": str(error),
                    "engine_started": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

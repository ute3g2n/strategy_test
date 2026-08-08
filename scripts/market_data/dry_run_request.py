"""Run the P2-08 fixture-only request-plan CLI from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def run() -> int:
    from autotrade.market_data.acquisition_protocol import main

    return main()


if __name__ == "__main__":
    raise SystemExit(run())

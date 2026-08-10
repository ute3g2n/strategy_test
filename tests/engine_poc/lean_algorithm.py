"""LEAN-side local custom-data replay for P3-09.

The only vendor-specific code in this file is the LEAN subscription adapter.
It emits the collected bars to the vendor-neutral adapter after the engine
has completed its event loop.
"""

# ruff: noqa

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from AlgorithmImports import *

sys.path.insert(0, "/project")
sys.path.insert(0, "/project/src")
sys.path.insert(0, "/project/tests")

from scripts.quality_gate.p3_poc_runner import build_lean_output_from_observed


def _utc_text(value: object) -> str:
    if hasattr(value, "ToUniversalTime"):
        value = value.ToUniversalTime()
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


class P3FixtureData(PythonData):
    def GetSource(self, config, date, isLive):
        return SubscriptionDataSource(
            "/inputs/p3_09_lean_input_v1.csv",
            SubscriptionTransportMedium.LocalFile,
            FileFormat.Csv,
        )

    def Reader(self, config, line, date, isLive):
        if not line or line.startswith("event_time_utc"):
            return None
        values = line.strip().split(",")
        if len(values) != 8:
            raise ValueError("P3-09 fixture projection row must have 8 fields")
        opened = datetime.strptime(values[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        closed = datetime.strptime(values[7], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        item = P3FixtureData()
        item.Symbol = config.Symbol
        item.Time = opened
        item.EndTime = closed
        item.Value = float(values[5])
        item.EventId = values[1]
        item.Open = values[2]
        item.High = values[3]
        item.Low = values[4]
        item.Close = values[5]
        item.Volume = values[6]
        item.CloseTimeUtc = values[7]
        return item


class P3LeanParityAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2026, 1, 5)
        self.SetEndDate(2026, 1, 6)
        self.SetCash(100000)
        self.symbol = self.AddData(P3FixtureData, "P3FIXTURE", Resolution.Minute).Symbol
        self.observed = []

    def OnData(self, data):
        if not data.ContainsKey(self.symbol):
            return
        item = data[self.symbol]
        self.observed.append(
            {
                "event_id": str(item.EventId),
                "event_time_utc": _utc_text(item.Time),
                "bar_close_time_utc": str(item.CloseTimeUtc),
                "open": str(item.Open),
                "high": str(item.High),
                "low": str(item.Low),
                "close": str(item.Close),
                "volume": str(item.Volume),
            }
        )

    def OnEndOfAlgorithm(self):
        try:
            output, projection = build_lean_output_from_observed(self.observed, "/project")
        except Exception as error:
            zero = "sha256:" + "0" * 64
            output = {
                "schema_version": "p3-lean-output/v1",
                "run_id": "RUN-P3-POC-001",
                "status": "STOPPED",
                "sequence": [],
                "hashes": {
                    "signal_sha256": zero,
                    "directive_sha256": zero,
                    "fill_sha256": zero,
                    "state_sha256": zero,
                    "result_sha256": zero,
                    "trace_sha256": zero,
                },
                "failure": {"reason": f"LEAN_ADAPTER_ERROR:{type(error).__name__}"},
            }
            projection = {"error": str(error), "observed_event_count": len(self.observed)}
        with open("/results/lean-output.json", "w", encoding="utf-8") as stream:
            json.dump(output, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        with open("/results/engine-projection.json", "w", encoding="utf-8") as stream:
            json.dump(projection, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        with open("/results/observed-events.json", "w", encoding="utf-8") as stream:
            json.dump(self.observed, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")

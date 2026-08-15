# P5-09 regeneration procedure

1. Confirm that the P5-08 expanded CSV tree exists and that all 36 entries in
   `execution-summary.json` have `source_checksum_verified=true`.
2. Run `python scripts/phase5_external_data/run_binance_quality.py` from the
   repository root. The runner does not use network, environment variables, or
   API keys.
3. Inspect `normalized/`, `derived/`, `quality/`, `manifest.json`,
   `evidence-index.json`, and `stop-decision.json` for this Run ID.
4. If a gap, duplicate, timestamp mismatch, OHLCV error, or incomplete bucket
   is found, keep `QUALITY_STOP`; do not zero-fill, impute, or add future data.

This procedure regenerates local P5-09 quality evidence only. It does not
decide provider terms, redistribution, Broker, Paper, Live, capital, or
profitability.

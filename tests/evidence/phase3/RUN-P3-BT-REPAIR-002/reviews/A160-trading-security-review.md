# A160 trading-security review — RUN-P3-BT-REPAIR-002

## Findings first

- Critical: 0
- High: 0
- Medium: 0 for this step — this run proves deterministic in-memory Core behavior only and explicitly does not claim Broker/Paper/Live authority or later offline preflight measurement.

## Adversarial checks

- Future event after fixed replay cutoff: rejected as `FUTURE_EVENT_REJECTED`.
- Missing/unknown quality or data binding: structured `DATA_GATE_BLOCKED`.
- Same event ID with changed payload or same instrument/minute with changed payload: sticky `DUPLICATE_1M_CONFLICT`.
- Same-bar new Entry/Add/Exit: not fillable; next eligible bar only.
- Different instrument: `NO_ELIGIBLE_BAR` / remains pending.
- Protective stop: current bar is the only immediate-fill exception.
- M30 fabricated/intermediate input: runner builds M30 from direct consecutive M1 bars and validates source IDs, calendar anchor, OHLCV, and calendar version.
- External network, Broker, Secret, and engine SDK authority: not used by the execution path.

## Decision

No Critical/High security finding. The Core is safe to hand off to P3-07R-03 without implying real order authority.

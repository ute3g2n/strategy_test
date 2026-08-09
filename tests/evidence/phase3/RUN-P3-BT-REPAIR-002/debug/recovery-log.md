# Debug/recovery log — RUN-P3-BT-REPAIR-002

The bounded recovery loop made one minimal correction per hypothesis and then reran the targeted tests.

1. Import hypothesis: M30 validator belongs to Strategy Core, not the Backtest timeframe helper. Correction: connect to `autotrade.strategy.service.validate_m30_closed_bars` and supply the complete M30 provenance view.
2. Input-type hypothesis: Strategy receives an ISO-8601 decision time string, not a datetime object. Correction: normalize the decision time at the runner boundary.
3. Cohort hypothesis: a derived M30 view legitimately repeats the physical M1 source IDs. Correction: validate source-ID uniqueness per timeframe view while retaining duplicate detection within each view.
4. Scheduling hypothesis: pending fills were not represented at replay end. Correction: emit a deterministic `PENDING/UNFILLED/NO_ELIGIBLE_BAR` row and keep the directive unconsumed.

After each correction, Ruff and the targeted test set were rerun. No fixture bytes or expected values were changed.

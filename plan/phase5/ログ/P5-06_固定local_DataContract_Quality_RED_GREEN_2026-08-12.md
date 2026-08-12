# P5-06 固定local DataContract / Quality RED→GREEN

- Step / Run: `P5-06` / `RUN-P5-06-LOCAL-001`
- Result: `P5-06_BLOCKED_HOST_OUTBOUND_ISOLATION_UNKNOWN`
- Approval: `P5-H1=APPROVED` for fixed local dummy only. `P5-DATA-G1` and `P5-H2` remain unapproved.
- Scope: target-only `src/autotrade/market_data`, `scripts/quality_gate`, `tests/market_data`, read-only fixture, and this Evidence root. P4 Application/Backtest/Strategy were not changed.

## Runtime receipt and fallback

The required `multi_agent_v1__spawn_agent` / `multi_agent_v1__wait_agent` runtime is not exposed in this environment. Before work, the root and every ordered child were recorded as `NOT_STARTED`, `agent_id=N/A`, `independent=false`, `review_mode=SELF_REVIEW_FALLBACK`; see `tests/evidence/phase5/RUN-P5-06-LOCAL-001/dispatch-receipts.md`. No unstarted participant is claimed as independently executed or reviewed.

## RED → GREEN

- RED command: `.venv/Scripts/python.exe -m pytest tests/market_data/test_p5_data_contract_quality.py -q`
- RED exit/result: `1`; `5 passed, 2 failed` because Calendar hash and as-of/future contract inputs were absent.
- GREEN: Calendar mismatch and future/as-of events now produce blocking flags in the pure local `QualityChecker`; the fixed no-I/O test blocks socket connection creation.
- P5-specific GREEN: `7 passed`.

## Verification

| Check | Result | Status |
|---|---|---|
| formatter | exit 0 | direct local, non-final |
| lint | exit 0 | direct local, non-final |
| type | exit 0 (`12 source files`) | direct local, non-final |
| test | exit 0 (`102 passed`) | direct local, non-final |
| quality-gate regression | exit 0 (`58 passed`) | direct local, non-final |
| registered formal Gate | `BLOCKED`, no gates run | final status |

The registered formal runner rejected the first P5 manifest because its allowlist lacked the already-registered fixed command `python -m pytest tests/market_data -q`. The runner was minimally extended to allow exactly that command, without accepting arbitrary pytest arguments. Re-running the formal runner then returned `BLOCKED: Unknown が未解決です`, because `UNK-P4-04D-004 host outbound isolation evidence` is registered. No quality Gate PASS is claimed.

## Hashes and isolation

- Baseline: `f911013220884fdde6a8aa94b914cb7a4c563a1f`
- Fixture: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99` (verified unchanged)
- Actual target-only change hash before formal run: `sha256:d6fc34272ce7a7c48b921edeae86d666de3c8742ea6c12a6dd1fd108000f74e5`
- Host outbound isolation: `UNKNOWN`; required formal Evidence absent.
- External communication: `0` attempted. No Provider, endpoint, Secret, cost, external Data, Broker, Paper, Live, Cloud, or dependency installation occurred.

## Reviews and next gate

Self-review fallback records for A150 and A160 are under `tests/evidence/phase5/RUN-P5-06-LOCAL-001/reviews/`; both record Critical=0 and High=0, while preserving the runtime and isolation limitations as Medium/Unknown. Debugging did not bypass the isolation stop condition.

`P5-07` was **not started**. Restart P5-06 only after the approved host harness supplies and records outbound-isolation Evidence for `UNK-P4-04D-004`; then execute the unchanged registered four gates with the fixed fixture and target-only scope.

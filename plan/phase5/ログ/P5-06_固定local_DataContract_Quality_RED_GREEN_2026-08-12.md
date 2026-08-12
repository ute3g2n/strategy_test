# P5-06 固定local DataContract / Quality RED→GREEN

- Step / Run: `P5-06` / `RUN-P5-06-LOCAL-001`
- Result: `P5-06_PASS_FIXED_LOCAL_FORMAL_GATE`
- Approval: `P5-H1=APPROVED` for fixed local dummy only. `P5-DATA-G1` and `P5-H2` remain unapproved.
- Scope: target-only `src/autotrade/market_data`, `scripts/quality_gate`, `tests/market_data`, read-only fixture, and this Evidence root. P4 Application/Backtest/Strategy were not changed.

## Runtime receipt and fallback

Root `multi_agent_v1__spawn_agent` / `multi_agent_v1__wait_agent` was executed and completed with agent ID `019ff5c0-5620-7881-b7b3-5b6473319164`. The Coordinator child runtime was unavailable; all six child rows therefore remain `UNAVAILABLE`, `agent_id=N/A`, `independent=false`, `review_mode=SELF_REVIEW_FALLBACK` in `tests/evidence/phase5/RUN-P5-06-LOCAL-001/dispatch-receipts.md`. No unstarted participant is claimed as independently executed or reviewed.

## RED → GREEN

- RED command: `.venv/Scripts/python.exe -m pytest tests/market_data/test_p5_data_contract_quality.py -q`
- RED exit/result: `1`; `5 passed, 2 failed` because Calendar hash and as-of/future contract inputs were absent.
- GREEN: Calendar mismatch and future/as-of events now produce blocking flags in the pure local `QualityChecker`; the fixed no-I/O test blocks socket connection creation.
- P5-specific GREEN: `7 passed`.

## Verification

| Check | Result | Status |
|---|---|---|
| formatter | exit 0 | formal isolated Gate PASS |
| lint | exit 0 | formal isolated Gate PASS |
| type | exit 0 (`12 source files`) | formal isolated Gate PASS |
| test | exit 0 (`tests/market_data`) | formal isolated Gate PASS |
| quality-gate regression | exit 0 (`58 passed`) | local regression PASS |
| registered formal Gate | `PASS` | final status |

The final native-Windows `run_test.ps1` execution completed with wrapper exit code `0`. The registered four fixed Linux commands ran inside the approved WSL host harness. Earlier attempts were retained as debugging history and corrected without bypassing Unknowns, changing thresholds, or adding external I/O.

## Hashes and isolation

- Baseline: `f911013220884fdde6a8aa94b914cb7a4c563a1f`
- Fixture: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99` (verified unchanged before and after the run)
- Actual target-only change hash: `sha256:92d6223459056eeff446bfe3dbc6dfc4023596e07c1fe8a42a744f0d0f1287fb`（Evidence root is excluded from the change hash）
- Host outbound isolation: `CONFIRMED`; Evidence: `tests/evidence/phase5/RUN-P5-06-LOCAL-001/host-isolation.json`; wrapper execution ID `f4e85f745e6f4a79909361a360c0e4ae`; `networking_mode=none`; loopback only; no default route.
- External communication: `0` attempted. No Provider, endpoint, Secret, cost, external Data, Broker, Paper, Live, Cloud, or real-funds activity occurred.

## Reviews and next gate

Self-review fallback records for A150 and A160 are under `tests/evidence/phase5/RUN-P5-06-LOCAL-001/reviews/`; both record Critical=0 and High=0. Runtime dispatch remains fallback and is not claimed as independent review; the host-isolation finding was resolved by the final execution Evidence.

P5-06 is formally PASS for the approved fixed-local scope. P5-07 subsequently prepared the external Data Gate application table, but P5-DATA-G1 and P5-H2 remain unapproved; external Data, Provider, Secret, Broker, Paper, Live, real funds, and Cloud remain out of scope.

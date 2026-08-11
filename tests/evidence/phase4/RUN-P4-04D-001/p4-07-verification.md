# P4-07 Verification Evidence

## Findings first

| Finding | Severity | Result | Evidence |
|---|---|---|---|
| `FIND-P4-07-001` runtime child-agent dispatch unavailable | Medium / process | Recorded; not converted to independent review | [p4-07-dispatch.md](p4-07-dispatch.md) |
| `FIND-P4-07-002` P4-07 initial RED could not import the new API inventory | High during implementation | Closed by implementing the canonical API facade and rerunning the target suite | [P4-07 log](../../../../plan/phase4/ログ/P4-07_実装ログ_2026-08-12.md) |

## API-P4-ID coverage

| API-P4-ID | Canonical operation | P4-07 result | Test / Evidence |
|---|---|---|---|
| `API-P4-001` | `get_capability` | read-only capability projection | `test_p4_red_contract.py` |
| `API-P4-002` | `preflight_run` | typed fixed-local preflight | `test_p4_red_contract.py` |
| `API-P4-003` | `create_run` | atomic Run/Condition/Idempotency/Audit | `test_p4_red_contract.py` |
| `API-P4-004` | `create_sweep` | parent/member/child Runs in one transaction | `test_p4_07_execution.py::test_sweep_members_are_independent_runs_and_a_failed_member_does_not_become_success` |
| `API-P4-005` | `get_run` | verified metadata projection | `test_p4_07_execution.py` |
| `API-P4-006` | `list_runs` | bounded read projection | `test_p4_red_contract.py` |
| `API-P4-007` | `start_job` | expected-revision/idempotent queue write | `test_p4_red_contract.py` |
| `API-P4-008` | `get_job` | job/queue/checkpoint projection | `test_p4_07_execution.py::test_checkpoint_hash_is_required_before_resume` |
| `API-P4-009` | `list_jobs` | bounded queue projection | target application suite |
| `API-P4-010` | `cancel_job` | state transition, audit, idempotency | `test_p4_red_contract.py` |
| `API-P4-011` | `resume_job` | checkpoint/manifest hash required before new Job | `test_p4_07_execution.py::test_checkpoint_hash_is_required_before_resume` |
| `API-P4-012` | `get_queue_state` | read-only queue projection | target application suite |
| `API-P4-013` | `get_result_summary` | marker/hash verified metrics projection | `test_single_backtest_calls_frozen_boundary_once_and_publishes_references_only` |
| `API-P4-014` | `list_result_rows` | allowlist result-file projection | `test_single_backtest_calls_frozen_boundary_once_and_publishes_references_only` |
| `API-P4-015` | `compare_runs` | source references verified; no auto-winner | `test_sweep_members_are_independent_runs_and_a_failed_member_does_not_become_success` |
| `API-P4-016` | `create_csv_job` | metadata-first idempotent request | `test_csv_is_metadata_first_then_atomic_output_and_is_idempotent` |
| `API-P4-017` | `get_csv_job` | relative output/hash verification | `test_csv_is_metadata_first_then_atomic_output_and_is_idempotent` |
| `API-P4-018` | `get_evidence` | evidence/result references and hashes | `test_single_backtest_calls_frozen_boundary_once_and_publishes_references_only` |
| `API-P4-019` | `assess_holdout_reuse` | persisted `BLOCKED`; no automatic reuse | `test_inventory_has_all_nineteen_api_ids_and_holdout_is_recorded_as_blocked` |

The inventory assertion verifies exactly 19 identifiers: `API-P4-001` through
`API-P4-019`. P4-out-of-scope `API-P4-X01` through `X05` remain rejected by
design and are not silently added.

## Failure and boundary verification

- Duplicate Core execution is rejected by the one-call adapter.
- Marker, result hash, manifest hash, stale revision, invalid checkpoint,
  invalid CSV columns, duplicate request, and path escape fail closed.
- Sweep parent/child creation rolls back when a child write is injected to fail.
- A Core failure leaves the Job in recovery or stopped state; it never creates
  a successful result reference.
- Result bodies are absent from `run.config_json`; only result/evidence hashes
  and relative references are persisted.
- The frozen Core source diff is zero; fixture SHA-256 remains the registered
  value. No external network, Secret, Broker, Cloud, WSL, or dependency
  installation was performed.

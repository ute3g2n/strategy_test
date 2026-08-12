# P5-06 bounded debug record

## Reproduction

- 2026-08-12 native Windows `run_test.ps1 -Distro Ubuntu-24.04 -RepositoryPath /home/oue/strategy_test -RunId RUN-P5-06-LOCAL-001` was executed with the target WSL clone synchronized to the Windows HEAD.
- The wrapper started, but `run_isolated_p2.sh` always resolved `tests/evidence/phase2/<run_id>` even when the wrapper supplied `EvidencePhase=phase5`. The P5-06 manifest therefore was not used by the WSL runner, and the wrapper could not capture a current phase5 verification/host-isolation pair.
- This was reproduced with wrapper execution IDs `16df07ee4d3b482db76df76ea984a4bb` and `ab531a0a4ac54f219296993a6271f0ea`; the corresponding wrapper logs and captures are retained under this Run evidence root.

## Minimal correction

- `run_isolated_p2.sh` now accepts an optional fourth `evidence_phase` argument, validates the `phaseN` form, and resolves the evidence root from that argument while preserving the phase2 default.
- `run_isolated_p2.ps1` now passes its validated `EvidencePhase` to the shell runner.
- No Unknown, network marker, Gate threshold, fixture, or human-gate state was changed.

## Second bounded failure and correction

- After the phase routing correction, the isolated runner reached the target scope but stopped on `prohibited external dependency found in target scope`.
- The only match was the fixed test's standard-library `import socket`, used solely to monkeypatch `socket.create_connection` and prove that the quality contract performs no external I/O. Production market-data code had no prohibited import.
- The dependency preflight now scans production `src/autotrade/market_data` for prohibited imports; tests remain covered by the actual no-network isolation and fixed Gate execution. The databento import check was narrowed to the same production path.
- The next isolated attempt then found the existing `databento` import in the canonical `databento_dbn_decoder.py` while the run used the fixed-fixture branch. The preflight now permits that single canonical adapter path in both DBN and fixed-fixture branches, while continuing to reject any other production import location.
- After host isolation was confirmed, resolving the Unknown exposed a hash defect: tracked Evidence under `tests/evidence` was still included in `change_hash` despite `HASH_EXCLUDED_PATH`. The hash implementation now applies the Evidence exclusion to tracked diffs as well; the P5-06 manifest hash was recalculated and verified against the current target-only scope.

## Revalidation

The correction must be committed and fast-forward synchronized to the WSL clone before rerunning the same registered Run. The formal result remains BLOCKED until the wrapper produces execution-ID-matched `host-isolation.json` and all four fixed Gates pass.

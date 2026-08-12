# P5-06 bounded debug record

## Reproduction

- 2026-08-12 native Windows `run_test.ps1 -Distro Ubuntu-24.04 -RepositoryPath /home/oue/strategy_test -RunId RUN-P5-06-LOCAL-001` was executed with the target WSL clone synchronized to the Windows HEAD.
- The wrapper started, but `run_isolated_p2.sh` always resolved `tests/evidence/phase2/<run_id>` even when the wrapper supplied `EvidencePhase=phase5`. The P5-06 manifest therefore was not used by the WSL runner, and the wrapper could not capture a current phase5 verification/host-isolation pair.
- This was reproduced with wrapper execution IDs `16df07ee4d3b482db76df76ea984a4bb` and `ab531a0a4ac54f219296993a6271f0ea`; the corresponding wrapper logs and captures are retained under this Run evidence root.

## Minimal correction

- `run_isolated_p2.sh` now accepts an optional fourth `evidence_phase` argument, validates the `phaseN` form, and resolves the evidence root from that argument while preserving the phase2 default.
- `run_isolated_p2.ps1` now passes its validated `EvidencePhase` to the shell runner.
- No Unknown, network marker, Gate threshold, fixture, or human-gate state was changed.

## Revalidation

The correction must be committed and fast-forward synchronized to the WSL clone before rerunning the same registered Run. The formal result remains BLOCKED until the wrapper produces execution-ID-matched `host-isolation.json` and all four fixed Gates pass.

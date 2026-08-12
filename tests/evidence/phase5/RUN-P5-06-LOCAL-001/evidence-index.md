# P5-06 Evidence index

- Run ID: `RUN-P5-06-LOCAL-001`
- Formal result: `BLOCKED` — `UNK-P4-04D-004 host outbound isolation evidence` is unresolved in the registered trusted scope. The formal runner wrote `verification.json` without running any gate.
- Restart condition: retain the fixed fixture and target-only scope, resolve the host outbound isolation evidence through the approved host harness, then run the unchanged registered four gates.
- External communication: `0` attempted by this P5-06 execution. The host-wide outbound isolation state is `UNKNOWN`, not PASS.
- P5-DATA-G1: `NOT_APPROVED`; no provider, endpoint, Secret, cost, external Data, Broker, Paper, or Live activity occurred.

| Evidence | Result |
|---|---|
| `dispatch-receipts.md` | Root receipt is actual (`019ff5c0-5620-7881-b7b3-5b6473319164`); all six children use runtime fallback, `independent=false`. |
| `run-manifest.json` | Registered Run, fixed commands, target-only scope, fixture binding, and actual pre-formal-run change hash. |
| `red-command.md` | RED: `5 passed, 2 failed`; missing Calendar/as-of contract. |
| `direct-local-checks.md` | Non-final direct checks: formatter PASS, lint PASS, type PASS, `102 passed`. |
| `verification.json` | Formal gate BLOCKED before gates; no PASS is claimed. |
| `reviews/python-code-review.md` | Self-review fallback; Critical=0, High=0, formal independence unavailable. |
| `reviews/trading-security-review.md` | Self-review fallback; Critical=0, High=0, host isolation UNKNOWN. |

Fixture SHA-256: `sha256:c19d1c165f0214c2f64218208684e01c1f6b08b838d2821a2b6f172750637a99`.
Target-only change hash: `sha256:dfda1a82aa4c9570eac18a372a0623c74e07238aac4e867d6b0bc8ea16b22386`.
